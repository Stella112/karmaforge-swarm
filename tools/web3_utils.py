import os
import logging
import json
import hashlib
import time
from typing import Dict, Any, Optional
from web3 import Web3
from eth_account.messages import encode_defunct

logger = logging.getLogger(__name__)

# ── ABIs ──────────────────────────────────────────────────────────────────────
RISK_ROUTER_ABI = [
    {"inputs":[{"components":[{"name":"agentId","type":"uint256"},{"name":"agentWallet","type":"address"},{"name":"pair","type":"string"},{"name":"action","type":"string"},{"name":"amountUsdScaled","type":"uint256"},{"name":"maxSlippageBps","type":"uint256"},{"name":"nonce","type":"uint256"},{"name":"deadline","type":"uint256"}],"name":"intent","type":"tuple"},{"name":"signature","type":"bytes"}],"name":"submitTradeIntent","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"components":[{"name":"agentId","type":"uint256"},{"name":"agentWallet","type":"address"},{"name":"pair","type":"string"},{"name":"action","type":"string"},{"name":"amountUsdScaled","type":"uint256"},{"name":"maxSlippageBps","type":"uint256"},{"name":"nonce","type":"uint256"},{"name":"deadline","type":"uint256"}],"name":"intent","type":"tuple"}],"name":"simulateIntent","outputs":[{"name":"valid","type":"bool"},{"name":"reason","type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agentId","type":"uint256"}],"name":"getIntentNonce","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"anonymous":False,"inputs":[{"indexed":True,"name":"agentId","type":"uint256"},{"indexed":False,"name":"intentHash","type":"bytes32"},{"indexed":False,"name":"amountUsdScaled","type":"uint256"}],"name":"TradeApproved","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"name":"agentId","type":"uint256"},{"indexed":False,"name":"intentHash","type":"bytes32"},{"indexed":False,"name":"reason","type":"string"}],"name":"TradeRejected","type":"event"},
]

VALIDATION_REGISTRY_ABI = [
    {"inputs":[{"name":"agentId","type":"uint256"},{"name":"checkpointHash","type":"bytes32"},{"name":"score","type":"uint8"},{"name":"notes","type":"string"}],"name":"postEIP712Attestation","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agentId","type":"uint256"}],"name":"getAverageValidationScore","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
]

REPUTATION_REGISTRY_ABI = [
    {"inputs":[{"name":"agentId","type":"uint256"}],"name":"getAverageScore","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agentId","type":"uint256"},{"name":"score","type":"uint8"},{"name":"outcomeRef","type":"bytes32"},{"name":"comment","type":"string"},{"name":"feedbackType","type":"uint8"}],"name":"submitFeedback","outputs":[],"stateMutability":"nonpayable","type":"function"},
]


class ERC8004Client:
    """
    Full on-chain integration with the ERC-8004 hackathon contracts.
    Handles EIP-712 TradeIntent signing, RiskRouter submission,
    ValidationRegistry attestations, and live reputation reads.
    """
    def __init__(self, rpc_url: str, private_key: str):
        if not rpc_url or not private_key:
            raise ValueError("RPC URL and Private Key must be provided.")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            logger.warning("⚠️  Cannot connect to Sepolia node.")

        pk = private_key if private_key.startswith("0x") else f"0x{private_key}"
        self.account = self.w3.eth.account.from_key(pk)
        self.pk = pk
        self.chain_id = self.w3.eth.chain_id

        # Load real contract addresses
        self.agent_id          = int(os.environ.get("AGENT_ID", "0") or "0")
        self.risk_router_addr  = os.environ.get("RISK_ROUTER_ADDRESS", "")
        self.validation_addr   = os.environ.get("VALIDATION_REGISTRY_ADDRESS", "")
        self.reputation_addr   = os.environ.get("REPUTATION_REGISTRY_ADDRESS", "")

        # Instantiate contracts
        if self.risk_router_addr:
            self.risk_router = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.risk_router_addr),
                abi=RISK_ROUTER_ABI
            )
        else:
            self.risk_router = None

        if self.validation_addr:
            self.validation_registry = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.validation_addr),
                abi=VALIDATION_REGISTRY_ABI
            )
        else:
            self.validation_registry = None

        if self.reputation_addr:
            self.reputation_registry = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.reputation_addr),
                abi=REPUTATION_REGISTRY_ABI
            )
        else:
            self.reputation_registry = None

        logger.info(f"✅ ERC8004Client ready | wallet={self.account.address} | agentId={self.agent_id}")

    # ── Reputation ───────────────────────────────────────────────────────────

    def get_reputation_score(self) -> int:
        """Fetch live reputation score from ReputationRegistry. Returns 50 if unavailable."""
        try:
            if self.reputation_registry and self.agent_id > 0:
                score = self.reputation_registry.functions.getAverageScore(self.agent_id).call()
                logger.info(f"🏆 Live reputation score: {score}/100")
                return int(score)
        except Exception as e:
            logger.warning(f"Reputation fetch failed (using default 50): {e}")
        return 50

    # ── TradeIntent ─────────────────────────────────────────────────────────

    def sign_trade_intent(self, intent_data: Dict[str, Any], risk_router_address: str) -> Optional[str]:
        """EIP-712 sign a TradeIntent for the RiskRouter."""
        domain_data = {
            "name": "RiskRouter",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": risk_router_address
        }
        message_types = {
            "TradeIntent": [
                {"name": "agentId",         "type": "uint256"},
                {"name": "agentWallet",     "type": "address"},
                {"name": "pair",            "type": "string"},
                {"name": "action",          "type": "string"},
                {"name": "amountUsdScaled", "type": "uint256"},
                {"name": "maxSlippageBps",  "type": "uint256"},
                {"name": "nonce",           "type": "uint256"},
                {"name": "deadline",        "type": "uint256"},
            ]
        }
        try:
            from eth_account.messages import encode_typed_data
            signable = encode_typed_data(
                domain_data=domain_data,
                message_types=message_types,
                message_data=intent_data
            )
            signed = self.account.sign_message(signable)
            return signed.signature.hex()
        except Exception as e:
            logger.error(f"EIP-712 signing error: {e}")
            return None

    def submit_trade_intent(self, pair: str, action: str, amount_usd: float) -> Dict[str, Any]:
        """
        Build, sign, simulate, then submit a TradeIntent through the RiskRouter.
        Returns a dict with tx_hash or rejection reason.
        """
        if not self.risk_router or self.agent_id == 0:
            logger.warning("RiskRouter not configured — skipping on-chain submission.")
            return {"status": "skipped", "reason": "no router or agentId"}

        try:
            nonce    = self.risk_router.functions.getIntentNonce(self.agent_id).call()
            deadline = int(time.time()) + 300  # 5 min window
            amount_scaled = int(amount_usd * 100)  # $USD * 100

            intent = {
                "agentId":         self.agent_id,
                "agentWallet":     self.account.address,
                "pair":            pair,
                "action":          action,
                "amountUsdScaled": amount_scaled,
                "maxSlippageBps":  100,
                "nonce":           nonce,
                "deadline":        deadline,
            }

            # Dry-run first
            valid, reason = self.risk_router.functions.simulateIntent(
                tuple(intent.values())
            ).call()
            if not valid:
                logger.warning(f"RiskRouter simulation rejected: {reason}")
                return {"status": "rejected", "reason": reason}

            # Sign it
            sig = self.sign_trade_intent(intent, self.risk_router_addr)
            if not sig:
                return {"status": "error", "reason": "signing failed"}

            sig_bytes = bytes.fromhex(sig[2:] if sig.startswith("0x") else sig)

            # Submit on-chain
            gas_est = self.risk_router.functions.submitTradeIntent(
                tuple(intent.values()), sig_bytes
            ).estimate_gas({"from": self.account.address})

            tx = self.risk_router.functions.submitTradeIntent(
                tuple(intent.values()), sig_bytes
            ).build_transaction({
                "from":     self.account.address,
                "nonce":    self.w3.eth.get_transaction_count(self.account.address, "latest"),
                "gas":      int(gas_est * 1.3),
                "gasPrice": int(self.w3.eth.gas_price * 1.5),
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.pk)
            tx_hash   = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"📡 TradeIntent submitted: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            status  = "confirmed" if receipt["status"] == 1 else "reverted"
            logger.info(f"TradeIntent {status} in block {receipt['blockNumber']}")
            return {"status": status, "tx_hash": tx_hash.hex(), "intent": intent}

        except Exception as e:
            logger.error(f"TradeIntent submission error: {e}")
            return {"status": "error", "reason": str(e)}

    # ── Validation Checkpoint ────────────────────────────────────────────────

    def post_checkpoint(self, reasoning: str, action: str, score: int = 80) -> Optional[str]:
        """
        Post an EIP-712 checkpoint to ValidationRegistry after every decision.
        Returns tx_hash or None.
        """
        if not self.validation_registry or self.agent_id == 0:
            logger.warning("ValidationRegistry not configured — skipping checkpoint.")
            return None

        try:
            # Build checkpoint hash from reasoning content
            payload = json.dumps({
                "agentId":   self.agent_id,
                "timestamp": int(time.time()),
                "action":    action,
                "reasoning": reasoning,
            }, sort_keys=True)
            checkpoint_hash = bytes.fromhex(hashlib.sha256(payload.encode()).hexdigest())

            gas_est = self.validation_registry.functions.postEIP712Attestation(
                self.agent_id, checkpoint_hash, score, reasoning[:200]
            ).estimate_gas({"from": self.account.address})

            tx = self.validation_registry.functions.postEIP712Attestation(
                self.agent_id, checkpoint_hash, score, reasoning[:200]
            ).build_transaction({
                "from":     self.account.address,
                "nonce":    self.w3.eth.get_transaction_count(self.account.address, "latest"),
                "gas":      int(gas_est * 1.3),
                "gasPrice": int(self.w3.eth.gas_price * 1.5),
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.pk)
            tx_hash   = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"📋 Checkpoint posted: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt["status"] == 1:
                logger.info(f"✅ Checkpoint confirmed (score={score}/100)")
            return tx_hash.hex()

        except Exception as e:
            if "not an authorized validator" in str(e).lower():
                logger.warning(f"⚠️  Validation skipped: Agent wallet {self.account.address} is not an authorized validator on this registry yet. Scoring will be handled by hackathon judges.")
            else:
                logger.error(f"Checkpoint post error: {e}")
            return None

    # ── Legacy compat ────────────────────────────────────────────────────────
    def sign_validation_artifact(self, artifact_hash: bytes, addr: str) -> Optional[str]:
        """Legacy stub kept for backward compatibility."""
        return self.post_checkpoint("legacy_artifact", "CHECKPOINT")
