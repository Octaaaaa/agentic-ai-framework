"""
Example of using LLM-powered agent.

This example shows how to create an agent that uses the configured LLM.
"""

import asyncio
from typing import Dict, Any
from src.agents.base import BaseAgent, AgentConfig
from src.core.orchestrator import Orchestrator
from src.utils import get_llm


class LLMAgent(BaseAgent):
    """Agent that uses LLM for processing."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm = get_llm(temperature=0.7)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using LLM."""
        prompt = task.get("data", {}).get("prompt", "")
        
        # Invoke LLM
        response = await self.llm.ainvoke(prompt)
        
        return {
            "response": response.content if hasattr(response, 'content') else str(response),
            "prompt": prompt
        }


async def main():
    # Create LLM agent
    config = AgentConfig(
        name="llm_agent",
        description="Agent powered by LLM"
    )
    agent = LLMAgent(config)
    
    # Create orchestrator
    orchestrator = Orchestrator()
    orchestrator.register_agent(agent)
    
    # Execute task
    task = {
        "type": "llm_query",
        "data": {
            "prompt": "Explain what an AI agent is in one sentence."
        }
    }
    
    result = await orchestrator.execute_task(task)
    
    if result["success"]:
        print(f"Prompt: {result['result']['prompt']}")
        print(f"Response: {result['result']['response']}")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())