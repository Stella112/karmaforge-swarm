import logging
import json
import time
import hashlib

logger = logging.getLogger(__name__)

class ValidatorAgent:
    """
    Creates EIP-712 Validation Artifacts, logs to SQLite, and posts
    live checkpoints to the ValidationRegistry on-chain.
    """
    def __init__(self, w3_client, db_conn):
        self.w3 = w3_client   # ERC8004Client instance
        self.db = db_conn

    def invoke(self, state: dict) -> dict:
        logger.info("Validator Agent creating on-chain checkpoint...")

        intents    = state.get("intents", {})
        risk       = state.get("risk_assessment", {})
        signals    = state.get("signals", {})
        reputation = state.get("reputation_score", 50)

        kraken_intent = intents.get("kraken_trade", {})
        action = kraken_intent.get("action", "HOLD")
        pair   = kraken_intent.get("pair", "XBTUSD")
        amount = risk.get("allowed_position_size_usd", 50.0)

        # ── 1. Build artifact payload ─────────────────────────────────────
        artifact = {
            "timestamp":          int(time.time()),
            "agentId":            self.w3.agent_id if self.w3 else 0,
            "action":             action,
            "pair":               pair,
            "amount_usd":         amount,
            "karma_score":        reputation,
            "rsi":                signals.get("rsi", 0),
            "momentum":           signals.get("momentum", 0),
            "risk_assessment":    risk,
        }
        artifact_hash = hashlib.sha256(
            json.dumps(artifact, sort_keys=True).encode()
        ).hexdigest()
        artifact["hash"] = artifact_hash

        # ── 2. Persist to SQLite ──────────────────────────────────────────
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO trades (timestamp, action, amount, pair, artifact)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                artifact["timestamp"],
                action,
                amount,
                pair,
                json.dumps(artifact)
            ))
            self.db.commit()
            logger.info("Artifact logged to karmaforge.db")
        except Exception as e:
            logger.error(f"DB write error: {e}")

        # ── 3. Submit TradeIntent to RiskRouter on-chain ──────────────────
        trade_result = {"status": "skipped"}
        if action in ("BUY", "SELL") and self.w3:
            logger.info(f"Submitting {action} {pair} ${amount:.2f} to RiskRouter...")
            trade_result = self.w3.submit_trade_intent(pair, action, amount)
            logger.info(f"RiskRouter result: {trade_result.get('status')}")

        # ── 4. Post checkpoint to ValidationRegistry ──────────────────────
        checkpoint_tx = None
        if self.w3:
            reasoning = (
                f"{action} {pair} | karma={reputation} | "
                f"rsi={signals.get('rsi', 0):.1f} | "
                f"momentum={signals.get('momentum', 0):.4f} | "
                f"amount=${amount:.2f}"
            )
            # Score based on decision quality: HOLDs are always safe (85),
            # active trades score higher when karma is high
            score = min(85 + int(reputation / 10), 100) if action != "HOLD" else 85
            checkpoint_tx = self.w3.post_checkpoint(reasoning, action, score)

        state["validation_artifacts"] = [{
            **artifact,
            "trade_result":    trade_result,
            "checkpoint_tx":   checkpoint_tx,
        }]
        return state
