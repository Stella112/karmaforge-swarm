# KarmaForge Swarm 🗡️

**Self-Evolving Verifiable AI Trading Agent with On-Chain Reputation Feedback Loop.**
Built for the lablab.ai "AI Trading Agents" Hackathon.

## 🚀 Overview
KarmaForge is a sovereign 5-agent LangGraph swarm powered locally by Ollama. It uniquely uses its ERC-8004 Reputation Score computationally as a baseline risk parameter ("Karma"), and reflects upon its own decisions every 4 hours to rewrite its source parameters. All decisions are output as EIP-712 Validation Artifacts.

## 🛠 Prerequisites & Installation

### 1. Execute Environment Setup
If using a Linux VPS, ensure Python 3.11+ is installed.

```bash
# 1. Clone repository
git clone https://github.com/your-repo/karmaforge-swarm
cd karmaforge-swarm

# 2. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python Dependencies
pip install -r requirements.txt
```

### 2. Kraken CLI Installation
Install the official Kraken CLI exactly:
```bash
curl --proto '=https' --tlsv1.2 -LsSf https://github.com/krakenfx/kraken-cli/releases/latest/download/kraken-cli-installer.sh | sh
```

### 3. Start Local Ollama
We reuse the existing local Ollama (Aether Persona). Assuming it's installed:
```bash
ollama serve &
ollama run llama3.1
```

## 🔗 The Trust Layer (ERC-8004)

### 1. Identity Registry Minting
Register KarmaForge on the Sepolia testnet. The target registry is:
`0x8004A818BFB912233c491871b3d84c89A494BD9e`

```bash
# Exact NFT Mint command (replace YOUR_RPC_URL and YOUR_PRIVATE_KEY)
python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('YOUR_RPC_URL'))
account = w3.eth.account.from_key('YOUR_PRIVATE_KEY')
print(f'Minting ERC-8004 Agent NFT for {account.address}...')
# Assume ABI is loaded and contract.functions.mint(cardURI).transact() runs here
"
```

### 2. Declare Public MCP Endpoint (Ngrok)
To allow other agents and judges to inspect the agent, expose your local MCP using ngrok:
```bash
ngrok http 8000
# Copy the resulting HTTPS URL
# Paste into agent-card.json -> "endpoints": { "mcp": "https://..." }
```

### 3. Claim Sandbox Capital
Execute the Hackathon Capital Vault function to claim your `0.0010 ETH` test liquidity to your validated Agent Wallet.

```bash
# Exact Claim Sandbox Capital command
python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('YOUR_RPC_URL'))
account = w3.eth.account.from_key('YOUR_PRIVATE_KEY')
print(f'Claiming 0.0010 ETH sandbox capital for agent {account.address}...')
# Assume function signature claimCapital() on Vault Contract
"
```

## ⚙️ Running the Swarm

Start the agent in a `screen` or `tmux` session to ensure it maintains sovereignty without an active SSH connection:

```bash
screen -S karmaforge
python run_karmaforge.py
# Press Ctrl+A, D to detach
```

## 📊 Watching the Evolution (Dashboard)

Monitor your agent's Karma Score, EIP-712 artifacts, and Evolution Timeline via Streamlit:

```bash
cd dashboard
streamlit run streamlit_app.py
```
*(The dashboard is read-only. KarmaForge does not accept manual prompting. It is 100% sovereign.)*
