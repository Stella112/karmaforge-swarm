import subprocess
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class KrakenCLIAdapter:
    """
    Wrapper for the Kraken CLI Rust binary.
    Executes commands securely using subprocess and parses JSON output.
    """
    def __init__(self):
        self.base_cmd = ["kraken"]

    def _execute(self, args: list) -> Optional[Dict[str, Any]]:
        cmd = self.base_cmd + args
        try:
            # We assume the CLI can output JSON format, which is standard for programmatic CLI tools
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Depending on CLI output format, you may need to parse standard text or JSON. 
            # We assume JSON for safe structure.
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Fallback if the CLI outputs raw text instead of JSON
                return {"raw_output": result.stdout.strip()}
        except subprocess.CalledProcessError as e:
            logger.error(f"Kraken CLI Error: {e.stderr}")
            return None
        except FileNotFoundError:
            logger.error("Kraken CLI binary not found in PATH. Ensure it is installed and accessible.")
            return None
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            return None

    def get_ticker(self, pair: str) -> Optional[Dict[str, Any]]:
        """Fetches the latest ticker data for a given pair."""
        return self._execute(["ticker", pair])
        
    def get_ohlc(self, pair: str, interval: str = "60") -> Optional[Dict[str, Any]]:
        """Fetches OHLC (candlestick) data."""
        return self._execute(["ohlc", pair, "--interval", interval])
        
    def get_orderbook(self, pair: str, depth: str = "10") -> Optional[Dict[str, Any]]:
        """Fetches the current orderbook."""
        return self._execute(["orderbook", pair, "--depth", depth])
