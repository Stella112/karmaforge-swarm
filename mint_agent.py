"""
KarmaForge Agent Registration Script
Registers the agent on the official ERC-8004 AgentRegistry (Sepolia)
and saves the returned agentId to .env
"""
import os, json, re, urllib.parse
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL          = os.environ["SEPOLIA_RPC_URL"]
PRIVATE_KEY      = os.environ["AGENT_WALLET_PRIVATE_KEY"]
REGISTRY_ADDRESS = os.environ.get("AGENT_REGISTRY_ADDRESS",
                                  "0x97b07dDc405B0c28B17559aFFE63BdB3632d0ca3")

AGENT_REGISTRY_ABI = [
    {"inputs":[{"name":"agentWallet","type":"address"},{"name":"name","type":"string"},{"name":"description","type":"string"},{"name":"capabilities","type":"string[]"},{"name":"agentURI","type":"string"}],"name":"register","outputs":[{"name":"agentId","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agentWallet","type":"address"}],"name":"walletToAgentId","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"anonymous":False,"inputs":[{"indexed":True,"name":"agentId","type":"uint256"},{"indexed":True,"name":"operatorWallet","type":"address"},{"indexed":True,"name":"agentWallet","type":"address"},{"indexed":False,"name":"name","type":"string"}],"name":"AgentRegistered","type":"event"}
]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise SystemExit("❌ Cannot connect to Sepolia.")

pk = PRIVATE_KEY if PRIVATE_KEY.startswith("0x") else f"0x{PRIVATE_KEY}"
operator = w3.eth.account.from_key(pk)
print(f"✅ Connected to Sepolia")
print(f"🔑 Wallet : {operator.address}")
print(f"💰 Balance: {w3.from_wei(w3.eth.get_balance(operator.address), 'ether'):.6f} ETH")

registry = w3.eth.contract(
    address=Web3.to_checksum_address(REGISTRY_ADDRESS),
    abi=AGENT_REGISTRY_ABI
)

# Check if already registered
existing = registry.functions.walletToAgentId(operator.address).call()
if existing > 0:
    print(f"\n✅ Wallet already registered! agentId = {existing}")
    # Save to .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, "r") as f: content = f.read()
    content = re.sub(r'^AGENT_ID=.*', f'AGENT_ID="{existing}"', content, flags=re.MULTILINE)
    with open(env_path, "w") as f: f.write(content)
    print(f"✅ AGENT_ID={existing} saved to .env")
    raise SystemExit(0)

# Build inline data URI (same as official template pattern)
meta = {
    "name": "KarmaForge Swarm",
    "version": "1.0.0",
    "agentWallet": operator.address,
    "capabilities": ["trading", "risk_management", "yield_optimization", "self_evolution", "erc8004_validation"]
}
agent_uri = "data:application/json," + urllib.parse.quote(json.dumps(meta))

# Estimate gas accurately
gas_estimate = registry.functions.register(
    operator.address,
    "KarmaForge Swarm",
    "Self-Evolving Verifiable AI Trading Agent with On-Chain Reputation Feedback Loop",
    ["trading", "risk_management", "yield_optimization", "self_evolution", "erc8004_validation"],
    agent_uri
).estimate_gas({"from": operator.address})

gas_limit = int(gas_estimate * 1.3)  # 30% buffer
gas_price  = int(w3.eth.gas_price * 1.5)  # 50% above base
nonce      = w3.eth.get_transaction_count(operator.address, 'latest')

print(f"\n🚀 Registering KarmaForge Swarm...")
print(f"   Gas estimate : {gas_estimate:,}  |  Gas limit: {gas_limit:,}")
print(f"   Gas price    : {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
print(f"   Nonce        : {nonce}")

tx = registry.functions.register(
    operator.address,
    "KarmaForge Swarm",
    "Self-Evolving Verifiable AI Trading Agent with On-Chain Reputation Feedback Loop",
    ["trading", "risk_management", "yield_optimization", "self_evolution", "erc8004_validation"],
    agent_uri
).build_transaction({
    "from":     operator.address,
    "nonce":    nonce,
    "gas":      gas_limit,
    "gasPrice": gas_price,
})

signed  = w3.eth.account.sign_transaction(tx, private_key=pk)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
print(f"📡 Tx: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
print("⏳ Waiting for confirmation (up to 3 min)...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

if receipt["status"] == 0:
    raise SystemExit(f"❌ Transaction reverted. Check: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

print(f"✅ Confirmed in block {receipt['blockNumber']}")

logs = registry.events.AgentRegistered().process_receipt(receipt)
if not logs:
    raise SystemExit("❌ AgentRegistered event not found in receipt.")

agent_id = logs[0]["args"]["agentId"]
print(f"\n🎉 KarmaForge Swarm is LIVE on-chain!")
print(f"   agentId  : {agent_id}")
print(f"   Etherscan: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

# Save agentId to .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
with open(env_path, "r") as f:
    content = f.read()
content = re.sub(r'^AGENT_ID=.*', f'AGENT_ID="{agent_id}"', content, flags=re.MULTILINE)
with open(env_path, "w") as f:
    f.write(content)

print(f"✅ AGENT_ID={agent_id} saved to .env — swarm is ready to trade!")
