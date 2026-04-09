"""
KarmaForge Capital Claim Script
Claims the 0.05 ETH sandbox capital from the HackathonVault.
"""
import os
import json
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL      = os.environ["SEPOLIA_RPC_URL"]
PRIVATE_KEY  = os.environ["AGENT_WALLET_PRIVATE_KEY"]
VAULT_ADDR   = os.environ.get("HACKATHON_VAULT_ADDRESS", "0x0E7CD8ef9743FEcf94f9103033a044caBD45fC90")
AGENT_ID     = int(os.environ.get("AGENT_ID", "0"))

VAULT_ABI = [
    {"inputs":[{"name":"agentId","type":"uint256"}],"name":"claimAllocation","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agentId","type":"uint256"}],"name":"getBalance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agentId","type":"uint256"}],"name":"hasClaimed","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"}
]

if AGENT_ID == 0:
    raise SystemExit("❌ AGENT_ID not found in .env. Run mint_agent.py first.")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
pk = PRIVATE_KEY if PRIVATE_KEY.startswith("0x") else f"0x{PRIVATE_KEY}"
account = w3.eth.account.from_key(pk)

vault = w3.eth.contract(address=Web3.to_checksum_address(VAULT_ADDR), abi=VAULT_ABI)

print(f"💰 Checking vault status for Agent #{AGENT_ID}...")
already_claimed = vault.functions.hasClaimed(AGENT_ID).call()

if already_claimed:
    bal = vault.functions.getBalance(AGENT_ID).call()
    print(f"✅ Allocation already claimed! Current Sandbox Balance: {w3.from_wei(bal, 'ether')} ETH")
else:
    print(f"🚀 Claiming mapping 0.05 ETH sandbox capital...")
    tx = vault.functions.claimAllocation(AGENT_ID).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 150000,
        "gasPrice": int(w3.eth.gas_price * 1.5)
    })
    signed = w3.eth.account.sign_transaction(tx, private_key=pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"📡 Claim Tx sent: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print("✅ Sandbox capital successfully claimed!")
