import os
import json
import time
import logging
from dotenv import load_dotenv

from db_init import init_db
from graph import build_graph
from tools.web3_utils import ERC8004Client

# Setup basic logging for VPS Screen/Tmux session
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

def get_recent_trades_summary(db_conn):
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT action, amount, pair FROM trades ORDER BY timestamp DESC LIMIT 10")
        rows = cursor.fetchall()
        if not rows:
            return "No recent trades."
        
        summary = "Last 10 trades:\n"
        buy_count = 0
        sell_count = 0
        for i, row in enumerate(rows):
            action = row[0]
            summary += f"- {action} {row[1]} of {row[2]}\n"
            if action == "BUY": buy_count += 1
            if action == "SELL": sell_count += 1
        summary += f"Total: {buy_count} BUYs, {sell_count} SELLs."
        return summary
    except Exception as e:
        logger.error(f"Error fetching trades summary: {e}")
        return "Error fetching trades."

def insert_checkpoint(db_conn, target, old_val, new_val, reason):
    try:
        cursor = db_conn.cursor()
        cursor.execute('''
            INSERT INTO evolution_checkpoints (timestamp, target_key, old_value, new_value, reason) 
            VALUES (?, ?, ?, ?, ?)
        ''', (int(time.time()), target, old_val, new_val, reason))
        db_conn.commit()
    except Exception as e:
        logger.error(f"Error saving evolution checkpoint: {e}")

def run_loop():
    logger.info("Initializing KarmaForge Swarm...")
    load_dotenv()
    
    # Setup persistent memory
    db_conn = init_db("karmaforge.db")
    if not db_conn:
        logger.error("Aborting start. Database failed.")
        return
        
    # Setup Web3/ERC-8004 connection
    rpc_url = os.environ.get("SEPOLIA_RPC_URL", "")
    pk = os.environ.get("AGENT_WALLET_PRIVATE_KEY", "")
    w3_client = ERC8004Client(rpc_url, pk) if rpc_url and pk else None
    
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    
    # Compile the LangGraph
    swarm = build_graph(db_conn, w3_client, ollama_url)
    
    # Main cycle
    cycle_count = 0
    while True:
        try:
            config = load_config()
            logger.info(f"--- Starting KarmaForge Cycle {cycle_count} ---")
            
            # Use db helper
            trades_summary = get_recent_trades_summary(db_conn)
            
            # Initial state mapping
            agent_id = os.environ.get("AGENT_ID", "0")
            
            # Fetch reputation once at start of cycle for the initial state if possible
            reputation = 75
            if w3_client:
                reputation = w3_client.get_reputation_score()
            
            initial_state = {
                "agent_id": agent_id,
                "trading_pair": "XBTUSD",
                "reputation_score": reputation,
                "config": config,
                "recent_trades_summary": trades_summary,
                "proposed_evolution": None
            }
            
            # Execute standard trade pipeline
            final_state = swarm.invoke(initial_state)
            
            # Execute Reflector every 4 hours (simplified as every N cycles for demo code)
            reflector_interval = config.get("swarm", {}).get("reflector_interval_hours", 4)
            if cycle_count > 0 and cycle_count % 16 == 0: # 16 * 15m = 4 hours
                logger.info(">>> Triggering 4-Hour Karma Reflector Loop <<<")
                
                # We specifically invoke the reflector node logic directly for the interval
                from agents.reflector_agent import ReflectorAgent
                reflector = ReflectorAgent(ollama_url)
                reflection_state = reflector.invoke(final_state)
                
                evolution = reflection_state.get("proposed_evolution")
                if evolution:
                    logger.info("Applying Checkpoint and Updating config.json...")
                    target = evolution.get("target")
                    new_val = evolution.get("new_value")
                    reason = evolution.get("reason", "No reason provided")
                    
                    if target and new_val is not None:
                        keys = target.split('.')
                        curr = config
                        old_val = None
                        for key in keys[:-1]:
                            curr = curr.setdefault(key, {})
                        
                        last_key = keys[-1]
                        if last_key in curr:
                            old_val = curr[last_key]
                            curr[last_key] = float(new_val)
                            
                            save_config(config)
                            insert_checkpoint(db_conn, target, old_val, new_val, reason)
                            
                            if w3_client:
                                logger.info("Broadcasting Evolution Checkpoint to Validation Registry...")
                                # Note: the validator agent already posts trade-specific checkpoints.
                                # Here we post the STRATEGY EVOLUTION checkpoint.
                                checkpoint_msg = f"EVOLUTION: Updated {target} from {old_val} to {new_val} | Reason: {reason}"
                                w3_client.post_checkpoint(checkpoint_msg, "EVOLUTION", score=100)
                                
                            logger.info(f"Evolution applied: {target} = {new_val}")
                        else:
                            logger.warning(f"Invalid config target: {target}")
            
            logger.info("Waiting for next execution block...")
            time.sleep(60 * 15) # Wait 15 minutes between signal checks
            cycle_count += 1
            
        except KeyboardInterrupt:
            logger.info("KarmaForge Swarm manually stopped. Shutting down gracefully.")
            db_conn.close()
            break
        except Exception as e:
            logger.error(f"Critical Cycle Error: {e}. Recovering in 60s...")
            time.sleep(60)

if __name__ == "__main__":
    run_loop()
