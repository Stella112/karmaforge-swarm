import logging
from tools.kraken_cli import KrakenCLIAdapter

logger = logging.getLogger(__name__)

class SignalAgent:
    """
    Fetches real-time market data via Kraken CLI public commands.
    """
    def __init__(self):
        self.cli = KrakenCLIAdapter()

    def invoke(self, state: dict) -> dict:
        logger.info("Signal Agent fetching Kraken data...")
        pair = state.get("trading_pair", "XBTUSD")
        
        # Fetching data using public endpoints
        ticker = self.cli.get_ticker(pair)
        ohlc = self.cli.get_ohlc(pair)
        
        # Store in state
        state["signals"] = {
            "ticker": ticker,
            "ohlc": ohlc
        }
        return state
