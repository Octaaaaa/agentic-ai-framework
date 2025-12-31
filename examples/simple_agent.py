"""
Simple single-agent example.

This example demonstrates how to create a basic agent that inherits from
BaseAgent and use it with the Orchestrator for simple task execution.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from src.agents.base import BaseAgent, AgentConfig
from src.core.orchestrator import Orchestrator
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class SimpleAgent(BaseAgent):
    """
    Example agent that processes simple query tasks.
    
    This agent demonstrates the minimal implementation required to create
    a functional agent. It processes text queries and returns formatted responses.
    """
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a simple query processing task.
        
        Args:
            task: Task dictionary containing query data
            
        Returns:
            Dictionary with processed response and metadata
        """
        # Extract query from task data
        data = task.get("data", {})
        query = data.get("query", "")
        
        logger.info(f"Processing query: {query}")
        
        # Process the query (simplified example)
        response = f"Processed query: {query}"
        
        # Return structured result
        return {
            "response": response,
            "query_length": len(query),
            "processed_at": datetime.now(timezone.utc).isoformat()
        }


async def main():
    """
    Main execution function demonstrating simple agent usage.
    """
    logger.info("Starting simple agent example")
    
    # Create agent configuration
    config = AgentConfig(
        name="simple_agent",
        description="A simple example agent that processes text queries"
    )
    
    # Initialize the agent
    agent = SimpleAgent(config)
    
    # Create orchestrator and register agent
    orchestrator = Orchestrator()
    orchestrator.register_agent(agent)
    
    # Create a task
    task = {
        "type": "query",
        "data": {
            "query": "Hello, world! This is a test query."
        }
    }
    
    # Execute the task
    logger.info("Executing task")
    result = await orchestrator.execute_task(task)
    
    # Display results
    print("\n" + "="*50)
    print("EXECUTION RESULT")
    print("="*50)
    print(f"Success: {result.get('success')}")
    print(f"Agent: {result.get('agent')}")
    if result.get('success'):
        print(f"Response: {result['result']['response']}")
        print(f"Query Length: {result['result']['query_length']}")
    else:
        print(f"Error: {result.get('error')}")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())