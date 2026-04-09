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
            
            # Initial state mapping
            initial_state = {
                "trading_pair": "XBTUSD",
                "reputation_score": 75, # In a real implementation this is fetched from Web3
                "config": config,
                "recent_trades_summary": "10 BUYs, 2 SELLs. Profitable.",
                "proposed_evolution": None
            }
            
            # Execute standard trade pipeline
            final_state = swarm.invoke(initial_state)
            
            # Execute Reflector every 4 hours (simplified as every N cycles for demo code)
            reflector_interval = config.get("swarm", {}).get("reflector_interval_hours", 4)
            if cycle_count % 10 == 0: # Assume N cycles equals an interval
                logger.info(">>> Triggering 4-Hour Karma Reflector Loop <<<")
                
                # We specifically invoke the reflector node logic directly for the interval
                from agents.reflector_agent import ReflectorAgent
                reflector = ReflectorAgent(ollama_url)
                reflection_state = reflector.invoke(final_state)
                
                if reflection_state.get("proposed_evolution"):
                    logger.info("Writing Checkpoint and Updating config.json...")
                    # Update config.json logic would go here
            
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
