"""
Main orchestrator for agent coordination.

This module implements the central orchestration logic that manages agents,
routes tasks, and coordinates workflow execution.
"""

import inspect
from typing import Dict, Any, Optional
from ..agents.base import BaseAgent
from ..graph.state import AgentState
from ..graph.workflow import AgentWorkflow


class Orchestrator:
    """
    Central coordinator for all agent operations.
    
    The Orchestrator manages agent registration, task routing, and workflow
    execution. It provides both simple single-agent task execution and
    complex multi-agent workflow orchestration.
    
    Attributes:
        agents: Dictionary of registered agents indexed by name
        workflow: Optional AgentWorkflow for complex orchestrations
    """
    
    def __init__(self):
        """Initialize an empty orchestrator."""
        self.agents: Dict[str, BaseAgent] = {}
        self.workflow: Optional[AgentWorkflow] = None
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the orchestrator.
        
        Registered agents become available for task routing and workflow
        execution. If a workflow is configured, the agent is also registered
        with the workflow.
        
        Args:
            agent: BaseAgent instance to register
        """
        self.agents[agent.name] = agent
        if self.workflow:
            self.workflow.register_agent(agent)
    
    def set_workflow(self, workflow: AgentWorkflow):
        """
        Configure a workflow for complex orchestrations.
        
        Sets the workflow and registers all currently registered agents
        with the workflow.
        
        Args:
            workflow: AgentWorkflow instance to use
        """
        self.workflow = workflow
        # Register all existing agents with the workflow
        for agent in self.agents.values():
            self.workflow.register_agent(agent)
    
    async def route_task(self, task: Dict[str, Any]) -> str:
        """
        Determine which agent should handle a task.
        
        This method implements the routing logic to select the appropriate
        agent for a given task. Agents can optionally implement a can_handle
        method for custom routing logic.
        
        Args:
            task: Task dictionary to route
            
        Returns:
            Name of the agent that should handle the task, or 'default'
        """
        task_type = task.get("type", "")
        
        # Check each agent to see if it can handle the task
        for agent_name, agent in self.agents.items():
            if hasattr(agent, "can_handle"):
                fn = getattr(agent, "can_handle")
                try:
                    res = fn(task)
                    can = await res if inspect.isawaitable(res) else bool(res)
                    if can:
                        return agent_name
                except Exception:
                    continue
        
        # No specific handler found
        return "default"
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task using the appropriate agent.
        
        Routes the task to an agent and executes it. If no specific agent
        is found, uses the first registered agent.
        
        Args:
            task: Task dictionary with 'type' and 'data' keys
            
        Returns:
            Dictionary with execution results including success status
        """
        # Check if any agents are registered
        if not self.agents:
            return {
                "success": False,
                "error": "No agents registered"
            }
        
        # Route the task to an appropriate agent
        agent_name = await self.route_task(task)
        
        # Use first agent if routing returned default
        if agent_name == "default" and self.agents:
            agent_name = list(self.agents.keys())[0]
        
        # Validate agent exists
        if agent_name not in self.agents:
            return {
                "success": False,
                "error": f"Agent {agent_name} not found"
            }
        
        # Execute task with selected agent
        agent = self.agents[agent_name]
        result = await agent.process(task)
        
        return result
    
    async def execute_workflow(self, initial_task: Dict[str, Any]) -> AgentState:
        """
        Execute a complex multi-agent workflow.
        
        Initializes workflow state with the given task and executes the
        configured workflow graph.
        
        Args:
            initial_task: Starting task for the workflow
            
        Returns:
            Final AgentState after workflow completion
            
        Raises:
            ValueError: If no workflow is configured
        """
        if not self.workflow:
            raise ValueError("No workflow configured. Use set_workflow() first")
        
        # Initialize state with the initial task
        initial_state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [initial_task],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        # Execute the workflow
        final_state = await self.workflow.execute(initial_state)
        
        return final_state