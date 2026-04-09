import os
import logging
from typing import Dict, Any, Optional
from web3 import Web3
from eth_account.messages import encode_typed_data

logger = logging.getLogger(__name__)

class ERC8004Client:
    """
    Handles interactions with the ERC-8004 Smart Contracts on Sepolia.
    Primarily manages EIP-712 structured data signing for TradeIntents 
    and Validation/Reputation checkpoints.
    """
    def __init__(self, rpc_url: str, private_key: str):
        if not rpc_url or not private_key:
            raise ValueError("RPC URL and Private Key must be provided.")
        
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            logger.warning("Failed to connect to the Ethereum node via RPC.")
            
        # Standardize private key formatting
        pk = private_key if private_key.startswith("0x") else f"0x{private_key}"
        self.account = self.w3.eth.account.from_key(pk)
        self.chain_id = self.w3.eth.chain_id

    def sign_trade_intent(self, intent_data: Dict[str, Any], risk_router_address: str) -> Optional[str]:
        """
        Signs a TradeIntent according to EIP-712 standard for the RiskRouter.
        """
        domain_data = {
            "name": "RiskRouter",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": risk_router_address
        }
        
        # This structure maps EXACLTY to the Stephen-Kimoi template RiskRouter contract struct.
        message_types = {
            "TradeIntent": [
                {"name": "agentId", "type": "uint256"},
                {"name": "agentWallet", "type": "address"},
                {"name": "pair", "type": "string"},
                {"name": "action", "type": "string"},
                {"name": "amountUsdScaled", "type": "uint256"},
                {"name": "maxSlippageBps", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"}
            ]
        }
        
        try:
            signable_message = encode_typed_data(
                domain_data=domain_data,
                message_types=message_types,
                message_data=intent_data
            )
            signed_message = self.account.sign_message(signable_message)
            return signed_message.signature.hex()
        except Exception as e:
            logger.error(f"EIP-712 Signing Error: {e}")
            return None

    def sign_validation_artifact(self, artifact_hash: bytes, validation_registry_address: str) -> Optional[str]:
        """
        Signs a generic validation artifact (e.g. strategy checkpoint) to broadcast
        on the ERC-8004 Validation Registry.
        """
        domain_data = {
            "name": "ValidationRegistry",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": validation_registry_address
        }
        
        message_types = {
            "Artifact": [
                {"name": "agentId", "type": "uint256"},
                {"name": "payloadHash", "type": "bytes32"},
                {"name": "timestamp", "type": "uint256"},
            ]
        }
        
        try:
            signable_message = encode_typed_data(
                domain_data=domain_data,
                message_types=message_types,
                message_data=artifact_hash
            )
            signed_message = self.account.sign_message(signable_message)
            return signed_message.signature.hex()
        except Exception as e:
            logger.error(f"EIP-712 Artifact Signing Error: {e}")
            return None
