import logging
import json
from langchain_ollama import OllamaLLM

logger = logging.getLogger(__name__)

class ReflectorAgent:
    """
    Runs every 4 hours. Uses Ollama to critique performance and emit strategy tweaks.
    """
    def __init__(self, ollama_url="http://127.0.0.1:11434", model="llama3.1"):
        self.llm = OllamaLLM(model=model, base_url=ollama_url)

    def invoke(self, state: dict) -> dict:
        logger.info("Reflector Agent starting 4-hour Karma loop...")
        
        # Context limited to prevent hallucination
        recent_trades = state.get("recent_trades_summary", "No recent trades.")
        karma = state.get("reputation_score", 50)
        
        prompt = f"""
        You are the Reflector Agent for KarmaForge Swarm. 
        Your current ERC-8004 Reputation (Karma) is {karma}/100.
        Recent activity summary: {recent_trades}
        
        Propose exactly ONE conservative numeric tweak to the configuration to improve risk-adjusted returns.
        You MUST return ONLY valid raw JSON with precisely these 3 keys:
        - "target": string, representing the config key (e.g. "strategy.rsi_oversold" or "risk.max_drawdown_limit_pct")
        - "new_value": float, the new conservative value
        - "reason": string, a short 1-sentence logic explanation for the change.
        
        Do not output markdown code blocks. Just output raw JSON.
        """
        
        try:
            # Query the local Ollama persona
            response = self.llm.invoke(prompt)
            
            # Simple sanitization
            response = response.strip().strip("```json").strip("```").strip()
            evolution = json.loads(response)
            
            state["proposed_evolution"] = evolution
            logger.info(f"Evolution checkpoint proposed: {evolution}")
            
        except json.JSONDecodeError:
            logger.warning("Ollama returned invalid JSON. Skipping evolution step.")
        except Exception as e:
            logger.error(f"Reflexion Error: {e}")
            
        return state
