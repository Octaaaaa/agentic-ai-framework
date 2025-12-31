"""
Multi-agent workflow example.

This example demonstrates how to create multiple agents that work together
in a coordinated workflow using LangGraph for orchestration.
"""

import asyncio
from typing import Dict, Any
from langgraph.graph import END
from src.agents.base import BaseAgent, AgentConfig
from src.graph.workflow import AgentWorkflow
from src.graph.state import AgentState
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Agent that analyzes text input.
    
    This agent performs basic text analysis including word count and
    basic metrics that can be used by downstream agents.
    """
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze text from the task.
        
        Args:
            task: Task containing text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        data = task.get("data", {})
        text = data.get("text", "")
        
        logger.info(f"Analyzing text: {text[:50]}...")
        
        # Perform analysis
        word_count = len(text.split())
        char_count = len(text)
        
        return {
            "analysis": f"Analyzed: {text}",
            "word_count": word_count,
            "char_count": char_count,
            "avg_word_length": char_count / word_count if word_count > 0 else 0
        }


class ProcessorAgent(BaseAgent):
    """
    Agent that processes analysis results.
    
    This agent takes the output from the AnalyzerAgent and performs
    additional processing or formatting.
    """
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process analysis results.
        
        Args:
            task: Task containing analysis data
            
        Returns:
            Dictionary with processed results
        """
        data = task.get("data", {})
        logger.info("Processing analysis results")
        
        word_count = data.get("word_count", 0)
        char_count = data.get("char_count", 0)
        
        # Generate summary
        summary = f"Processed analysis: {word_count} words, {char_count} characters"
        
        return {
            "processed": True,
            "summary": summary,
            "metrics": {
                "words": word_count,
                "characters": char_count
            }
        }


async def analyzer_node(state: AgentState) -> dict:
    """
    Workflow node for the analyzer agent.
    
    This function wraps the AnalyzerAgent execution in a workflow node.
    It retrieves tasks from state, executes the agent, and stores results.
    
    Args:
        state: Current workflow state
        
    Returns:
        Partial state updates (dict)
    """
    logger.info("Executing analyzer node")
    
    if state["task_queue"]:
        task = state["task_queue"][0]
        
        analyzer = AnalyzerAgent(AgentConfig(
            name="analyzer",
            description="Analyzes input text"
        ))
        
        result = await analyzer.process(task)
        
        logger.info("Analyzer completed successfully")
        
        return {
            "results": {**state["results"], "analyzer": result},
            "current_agent": "analyzer"
        }
    
    return {}


async def processor_node(state: AgentState) -> dict:
    """
    Workflow node for the processor agent.
    
    This function retrieves the analyzer results from state and processes
    them using the ProcessorAgent.
    
    Args:
        state: Current workflow state
        
    Returns:
        Partial state updates (dict)
    """
    logger.info("Executing processor node")
    
    analyzer_result = state["results"].get("analyzer")
    
    if analyzer_result and analyzer_result.get("success"):
        task = {
            "type": "process",
            "data": analyzer_result.get("result", {})
        }
        
        processor = ProcessorAgent(AgentConfig(
            name="processor",
            description="Processes analysis results"
        ))
        
        result = await processor.process(task)
        
        logger.info("Processor completed successfully")
        
        return {
            "results": {**state["results"], "processor": result},
            "current_agent": "processor"
        }
    
    logger.warning("Analyzer did not complete successfully, skipping processor")
    return {}


def should_continue(state: AgentState) -> str:
    """
    Determine the next step in the workflow.
    
    This function implements the routing logic to decide which node
    should execute next based on the current state.
    
    Args:
        state: Current workflow state
        
    Returns:
        Key indicating next node to execute
    """
    if state["current_agent"] == "analyzer":
        logger.info("Routing to processor")
        return "processor"
    
    logger.info("Workflow complete")
    return "end"


async def main():
    """
    Main execution function demonstrating multi-agent workflow.
    """
    logger.info("Starting multi-agent workflow example")
    
    # Create workflow
    workflow = AgentWorkflow()
    
    # Add nodes to the workflow
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("processor", processor_node)
    
    # Set entry point
    workflow.set_entry_point("analyzer")
    
    # Add conditional routing from analyzer
    workflow.add_conditional_edges(
        "analyzer",
        should_continue,
        {
            "processor": "processor",
            "end": END
        }
    )
    
    # Add edge from processor to end
    workflow.add_edge("processor", END)
    
    # Compile the workflow
    logger.info("Compiling workflow")
    workflow.compile()
    
    # Create initial state with task (TypedDict as dict)
    initial_state: AgentState = {
        "messages": [],
        "current_agent": None,
        "task_queue": [{
            "type": "analyze",
            "data": {
                "text": "This is a test message for multi-agent processing workflow demonstration"
            }
        }],
        "results": {},
        "metadata": {},
        "error": None
    }
    
    # Execute workflow
    logger.info("Executing workflow")
    final_state = await workflow.execute(initial_state)
    
    # Display results
    print("\n" + "="*50)
    print("WORKFLOW EXECUTION RESULTS")
    print("="*50)
    
    analyzer_result = final_state["results"].get("analyzer")
    print("\nAnalyzer Results:")
    if analyzer_result and analyzer_result.get("success"):
        result_data = analyzer_result.get("result", {})
        print(f"  Word Count: {result_data.get('word_count')}")
        print(f"  Char Count: {result_data.get('char_count')}")
        print(f"  Avg Word Length: {result_data.get('avg_word_length', 0):.2f}")
    else:
        print(f"  Error: {analyzer_result.get('error') if analyzer_result else 'No result'}")
    
    processor_result = final_state["results"].get("processor")
    print("\nProcessor Results:")
    if processor_result and processor_result.get("success"):
        result_data = processor_result.get("result", {})
        print(f"  Summary: {result_data.get('summary')}")
        print(f"  Processed: {result_data.get('processed')}")
    else:
        print(f"  Error: {processor_result.get('error') if processor_result else 'No result'}")
    
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())