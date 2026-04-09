import logging

logger = logging.getLogger(__name__)

class StrategyAgent:
    """
    Allocates between Kraken CEX trading and Simulated Aerodrome LP yield.
    """
    def invoke(self, state: dict) -> dict:
        logger.info("Strategy Agent calculating allocations...")
        config = state.get("config", {})
        risk = state.get("risk_assessment", {})
        total_allowed = risk.get("allowed_position_size_usd", 0)
        
        # 60/40 Split based on dynamic config
        cex_weight = config.get("strategy", {}).get("kraken_cex_weight", 0.6)
        lp_weight = config.get("strategy", {}).get("aerodrome_lp_weight", 0.4)
        
        cex_alloc = total_allowed * cex_weight
        lp_alloc = total_allowed * lp_weight
        
        # Simulated Aerodrome APY data (Static assumption for hackathon safety)
        simulated_yield_apy = 0.15 # 15% Base APY
        
        # Basic RSI crossover assumption (simplified logic)
        decision = "BUY" # Placeholder for actual momentum algo logic
        
        state["intents"] = {
            "kraken_trade": {
                "action": decision, 
                "amount_usd": cex_alloc, 
                "pair": state.get("trading_pair", "XBTUSD")
            },
            "aerodrome_sim": {
                "action": "LP_DEPOSIT", 
                "amount_usd": lp_alloc, 
                "assumed_apy": simulated_yield_apy
            }
        }
        return state
