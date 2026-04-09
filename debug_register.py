"""
Debug: Simulate register() call and capture revert reason
"""
from web3 import Web3
import json, urllib.parse

w3 = Web3(Web3.HTTPProvider('https://ethereum-sepolia-rpc.publicnode.com'))

pk = "0xccee2dd7b0451eecdfc8321612a309b87450f0a5c287dc37cf17a900d71ee328"
operator = w3.eth.account.from_key(pk)
wallet = operator.address

REGISTRY = "0x97b07dDc405B0c28B17559aFFE63BdB3632d0ca3"

ABI = [
    {
        "inputs": [
            {"name": "agentWallet",  "type": "address"},
            {"name": "name",         "type": "string"},
            {"name": "description",  "type": "string"},
            {"name": "capabilities", "type": "string[]"},
            {"name": "agentURI",     "type": "string"}
        ],
        "name": "register",
        "outputs": [{"name": "agentId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

registry = w3.eth.contract(address=REGISTRY, abi=ABI)

# Build inline data URI (same pattern as the official template)
meta = {
    "name": "KarmaForge Swarm",
    "version": "1.0.0",
    "agentWallet": wallet,
    "capabilities": ["trading", "risk_management", "yield_optimization", "self_evolution", "erc8004_validation"]
}
agent_uri = "data:application/json," + urllib.parse.quote(json.dumps(meta))

print(f"Wallet  : {wallet}")
print(f"AgentURI: {agent_uri[:80]}...")

# Try simulate with eth_call
try:
    result = registry.functions.register(
        wallet,
        "KarmaForge Swarm",
        "Self-Evolving Verifiable AI Trading Agent with On-Chain Reputation Feedback Loop",
        ["trading", "risk_management", "yield_optimization", "self_evolution", "erc8004_validation"],
        agent_uri
    ).call({"from": wallet})
    print(f"\n✅ Simulation OK — would mint agentId: {result}")
except Exception as e:
    print(f"\n❌ Revert reason: {e}")

# Also try gas estimate
try:
    gas = registry.functions.register(
        wallet,
        "KarmaForge Swarm",
        "Self-Evolving Verifiable AI Trading Agent with On-Chain Reputation Feedback Loop",
        ["trading", "risk_management", "yield_optimization", "self_evolution", "erc8004_validation"],
        agent_uri
    ).estimate_gas({"from": wallet})
    print(f"✅ Gas estimate: {gas}")
except Exception as e:
    print(f"❌ Gas estimate failed: {e}")
