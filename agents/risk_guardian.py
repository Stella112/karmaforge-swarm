import logging

logger = logging.getLogger(__name__)

class RiskGuardian:
    """
    Reads LIVE ERC-8004 reputation score and dynamically scales position size,
    drawdown cap, and Kelly fraction — the core Karma Loop.
    """
    def __init__(self, db_conn, web3_client=None):
        self.db = db_conn
        self.w3 = web3_client   # ERC8004Client instance

    def invoke(self, state: dict) -> dict:
        logger.info("Risk Guardian executing Karma Loop...")

        # ── Fetch LIVE reputation score from chain ──────────────────────────
        if self.w3 and hasattr(self.w3, "get_reputation_score"):
            current_reputation = self.w3.get_reputation_score()
            state["reputation_score"] = current_reputation
        else:
            current_reputation = state.get("reputation_score", 50)

        config = state.get("config", {})
        risk   = config.get("risk", {})

        base_size      = risk.get("base_position_size_usd", 100)
        kelly_fraction = risk.get("kelly_fraction", 0.5)

        # KARMA LOOP: scale position size linearly with reputation (0-100)
        risk_multiplier       = current_reputation / 100.0
        allowed_position_size = base_size * risk_multiplier * kelly_fraction

        # Clamp to RiskRouter hard limit of $500/trade
        allowed_position_size = min(allowed_position_size, 500.0)
        allowed_position_size = max(allowed_position_size, 10.0)  # min $10

        drawdown_cap      = risk.get("max_drawdown_limit_pct", 0.05)  # 5% hard limit from router
        adjusted_drawdown = drawdown_cap * (1.0 + (risk_multiplier - 0.5) * 0.5)
        adjusted_drawdown = min(adjusted_drawdown, 0.05)  # never exceed router max

        state["risk_assessment"] = {
            "allowed_position_size_usd": round(allowed_position_size, 2),
            "adjusted_drawdown_limit":   round(adjusted_drawdown, 4),
            "karma_score":               current_reputation,
            "approved": True
        }
        logger.info(
            f"Karma:{current_reputation}/100 → "
            f"Allowed: ${allowed_position_size:.2f} | "
            f"Drawdown cap: {adjusted_drawdown*100:.2f}%"
        )
        return state
