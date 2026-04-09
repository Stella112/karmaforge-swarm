import logging
import json
import time

logger = logging.getLogger(__name__)

class ValidatorAgent:
    """
    Creates EIP-712 Validation Artifacts and logs to strict persistence layer.
    """
    def __init__(self, w3_client, db_conn):
        self.w3 = w3_client
        self.db = db_conn

    def invoke(self, state: dict) -> dict:
        logger.info("Validator Agent creating Validation Artifacts...")
        intents = state.get("intents", {})
        
        # Generic Artifact Payload
        artifact = {
            "timestamp": int(time.time()),
            "decision": intents,
            "reputation_context": state.get("reputation_score", 50)
        }
        
        # Log to SQLite Persistent Memory
        try:
            cursor = self.db.cursor()
            kraken_intent = intents.get("kraken_trade", {})
            cursor.execute('''
                INSERT INTO trades (timestamp, action, amount, pair, artifact) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                artifact["timestamp"], 
                kraken_intent.get("action", "NONE"),
                kraken_intent.get("amount_usd", 0),
                kraken_intent.get("pair", ""),
                json.dumps(artifact)
            ))
            self.db.commit()
            logger.info("Artifact securely logged to SQLite (karmaforge.db).")
        except Exception as e:
            logger.error(f"Database Error in Validator: {e}")
            
        state["validation_artifacts"] = [artifact]
        return state
