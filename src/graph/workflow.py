"""
Workflow orchestration using LangGraph.

This module provides the workflow engine that coordinates agent execution
using a graph-based approach with conditional routing.

IMPORTANT: Workflow nodes must return partial state updates as dictionaries,
not complete AgentState objects. LangGraph will automatically merge these updates.

Example node:
    async def my_node(state: AgentState) -> dict:
        # Process state
        result = await process(state)
        
        # Return only the fields to update
        return {
            "results": {**state["results"], "my_node": result},
            "metadata": {**state["metadata"], "processed": True}
        }
"""

from typing import Dict, Any, Callable
from langgraph.graph import StateGraph, END
from .state import AgentState
from ..agents.base import BaseAgent


class AgentWorkflow:
    """
    Workflow manager for coordinating multiple agents.
    
    This class builds and executes workflows using LangGraph. It manages
    agent registration, node creation, edge definition, and workflow execution.
    
    Attributes:
        agents: Dictionary mapping agent names to agent instances
        graph: LangGraph StateGraph object
        compiled_graph: Compiled executable graph
    """
    
    def __init__(self):
        """Initialize an empty workflow."""
        self.agents: Dict[str, BaseAgent] = {}
        self.graph = StateGraph(AgentState)
        self.compiled_graph = None
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the workflow.
        
        Args:
            agent: BaseAgent instance to register
        """
        self.agents[agent.name] = agent
    
    def add_node(self, name: str, func: Callable):
        """
        Add a processing node to the workflow graph.
        
        Node functions must return partial state updates as dictionaries.
        
        Args:
            name: Unique name for the node
            func: Async function that takes AgentState and returns dict of updates
            
        Example:
            async def process_node(state: AgentState) -> dict:
                return {"results": {"node1": "done"}}
            
            workflow.add_node("process", process_node)
        """
        self.graph.add_node(name, func)
    
    def add_edge(self, from_node: str, to_node: str):
        """
        Add a direct edge between two nodes.
        
        Args:
            from_node: Source node name
            to_node: Destination node name
        """
        self.graph.add_edge(from_node, to_node)
    
    def add_conditional_edges(
        self, 
        source: str, 
        path_func: Callable,
        path_map: Dict[str, str] = None
    ):
        """
        Add conditional routing between nodes.
        
        Conditional edges allow dynamic routing based on state. The path_func
        determines which path to take based on the current state.
        
        Args:
            source: Source node name
            path_func: Function that takes AgentState and returns path key string
            path_map: Dictionary mapping path keys to destination node names
                     (optional in newer LangGraph, can be inferred)
            
        Example:
            def router(state: AgentState) -> str:
                return "success" if state["error"] is None else "error"
            
            workflow.add_conditional_edges(
                "process",
                router,
                {"success": "next_step", "error": END}
            )
        """
        if path_map is not None:
            self.graph.add_conditional_edges(source, path_func, path_map)
        else:
            self.graph.add_conditional_edges(source, path_func)
    
    def set_entry_point(self, node: str):
        """
        Set the starting node for workflow execution.
        
        Args:
            node: Name of the entry node
        """
        self.graph.set_entry_point(node)
    
    def compile(self):
        """
        Compile the workflow graph for execution.
        
        This method must be called after all nodes and edges are defined
        and before executing the workflow.
        
        Returns:
            Compiled graph ready for execution
        """
        self.compiled_graph = self.graph.compile()
        return self.compiled_graph
    
    async def execute(self, initial_state: AgentState) -> AgentState:
        """
        Execute the workflow with the given initial state.
        
        Args:
            initial_state: Starting state for the workflow (TypedDict)
            
        Returns:
            Final state after workflow completion
            
        Raises:
            ValueError: If workflow is not compiled before execution
        """
        # Compile if not already compiled
        if not self.compiled_graph:
            self.compile()
        
        # Execute the workflow
        final_state = await self.compiled_graph.ainvoke(initial_state)
        return final_state