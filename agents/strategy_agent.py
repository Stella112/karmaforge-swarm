import logging
import pandas as pd

logger = logging.getLogger(__name__)

class StrategyAgent:
    """
    Allocates between Kraken CEX trading and Simulated Aerodrome LP yield.
    """
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> float:
        if len(series) < period:
            return 50.0
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

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
        
        decision = "HOLD"
        try:
            ohlc_data = state.get("signals", {}).get("ohlc", {})
            closes = []
            if isinstance(ohlc_data, dict):
                # The CLI returns a flat dict with the pair name (e.g., XXBTZUSD) AND a 'last' key
                for k, v in ohlc_data.items():
                    if k != "last" and isinstance(v, list):
                        closes = [float(candle[4]) for candle in v]
                        break
            
            if len(closes) > 1:
                series = pd.Series(closes)
                rsi_val = self._calculate_rsi(series)
                momentum = (closes[-1] - closes[-2]) / closes[-2]
                
                oversold = config.get("strategy", {}).get("rsi_oversold", 30)
                overbought = config.get("strategy", {}).get("rsi_overbought", 70)
                mom_thresh = config.get("strategy", {}).get("momentum_threshold", 0.02)
                
                logger.info(f"RSI: {rsi_val:.2f}, Momentum: {momentum:.4f}")
                
                if rsi_val <= oversold and momentum >= -mom_thresh:
                    decision = "BUY"
                elif rsi_val >= overbought and momentum <= mom_thresh:
                    decision = "SELL"
        except Exception as e:
            logger.warning(f"RSI/Momentum calc failed, defaulting to HOLD. Error: {e}")
        
        state["intents"] = {
            "kraken_trade": {
                "action": decision, 
                "amount_usd": cex_alloc if decision in ["BUY", "SELL"] else 0, 
                "pair": state.get("trading_pair", "XBTUSD")
            },
            "aerodrome_sim": {
                "action": "LP_DEPOSIT", 
                "amount_usd": lp_alloc, 
                "assumed_apy": simulated_yield_apy
            }
        }
        return state
