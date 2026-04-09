"""Check if wallet is already registered on AgentRegistry"""
from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider('https://ethereum-sepolia-rpc.publicnode.com'))

ABI = [
    {"inputs":[{"name":"agentWallet","type":"address"}],"name":"walletToAgentId","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agentId","type":"uint256"}],"name":"getAgent","outputs":[{"components":[{"name":"operatorWallet","type":"address"},{"name":"agentWallet","type":"address"},{"name":"name","type":"string"},{"name":"description","type":"string"},{"name":"capabilities","type":"string[]"},{"name":"registeredAt","type":"uint256"},{"name":"active","type":"bool"}],"name":"","type":"tuple"}],"stateMutability":"view","type":"function"}
]

registry = w3.eth.contract(address='0x97b07dDc405B0c28B17559aFFE63BdB3632d0ca3', abi=ABI)
wallet = '0x1DCc32097941b199E0292D4E5d0C4492149CFd4b'

agent_id = registry.functions.walletToAgentId(wallet).call()
print(f'walletToAgentId result: {agent_id}')

if agent_id > 0:
    info = registry.functions.getAgent(agent_id).call()
    print(f'Already registered!')
    print(f'agentId  : {agent_id}')
    print(f'Name     : {info[2]}')
    print(f'Active   : {info[6]}')
else:
    print('Not registered yet - need to call register()')
