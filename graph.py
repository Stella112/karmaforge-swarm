from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
import logging

from agents.signal_agent import SignalAgent
from agents.risk_guardian import RiskGuardian
from agents.strategy_agent import StrategyAgent
from agents.validator_agent import ValidatorAgent
from agents.reflector_agent import ReflectorAgent

logger = logging.getLogger(__name__)

class SwarmState(TypedDict):
    trading_pair: str
    reputation_score: int
    config: dict
    signals: dict
    risk_assessment: dict
    intents: dict
    validation_artifacts: list
    recent_trades_summary: str
    proposed_evolution: Any

def build_graph(db_conn, w3_client, ollama_url):
    """
    Constructs the KarmaForge LangGraph pipeline.
    """
    # Instantiate agents
    signal = SignalAgent()
    risk = RiskGuardian(db_conn, w3_client)
    strategy = StrategyAgent()
    validator = ValidatorAgent(w3_client, db_conn)
    reflector = ReflectorAgent(ollama_url=ollama_url)

    # Initialize graph
    workflow = StateGraph(SwarmState)
    
    # Add Nodes
    workflow.add_node("signal", signal.invoke)
    workflow.add_node("risk", risk.invoke)
    workflow.add_node("strategy", strategy.invoke)
    workflow.add_node("validator", validator.invoke)
    workflow.add_node("reflector", reflector.invoke)
    
    # Define primary execution loop
    workflow.set_entry_point("signal")
    workflow.add_edge("signal", "risk")
    workflow.add_edge("risk", "strategy")
    workflow.add_edge("strategy", "validator")
    workflow.add_edge("validator", END)
    
    # Note: 'reflector' runs asynchronously over top of this main loop via cron/sleep intervals
    
    return workflow.compile()
