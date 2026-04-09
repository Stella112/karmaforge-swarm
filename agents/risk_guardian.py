import logging

logger = logging.getLogger(__name__)

class RiskGuardian:
    """
    Reads live ERC-8004 reputation score and dynamically scales rules.
    """
    def __init__(self, db_conn, web3_client=None):
        self.db = db_conn
        self.w3 = web3_client

    def invoke(self, state: dict) -> dict:
        logger.info("Risk Guardian executing Karma Loop...")
        # In a prod environment, this fetches from the ERC-8004 contract.
        current_reputation = state.get("reputation_score", 50)
        config = state.get("config", {})
        
        base_size = config.get("risk", {}).get("base_position_size_usd", 100)
        kelly_fraction = config.get("risk", {}).get("kelly_fraction", 0.5)
        
        # KARMA LOOP: Dynamically scale position based on reputation (0-100)
        risk_multiplier = current_reputation / 100.0
        allowed_position_size = base_size * risk_multiplier * kelly_fraction
        
        drawdown_cap = config.get("risk", {}).get("max_drawdown_limit_pct", 0.10)
        # Higher karma allows slightly looser drawdown limits
        adjusted_drawdown = drawdown_cap * (1.0 + (risk_multiplier - 0.5))
        
        state["risk_assessment"] = {
            "allowed_position_size_usd": allowed_position_size,
            "adjusted_drawdown_limit": adjusted_drawdown,
            "approved": True
        }
        logger.info(f"Karma:{current_reputation} -> Allowed Size: ${allowed_position_size:.2f}")
        return state
