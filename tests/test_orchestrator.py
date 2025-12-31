"""
Unit tests for orchestrator functionality.

Tests the Orchestrator class and task routing.
"""

import pytest
from src.core.orchestrator import Orchestrator
from src.agents.base import BaseAgent, AgentConfig
from src.graph.workflow import AgentWorkflow
from src.graph.state import AgentState
from typing import Dict, Any


class RoutableAgent(BaseAgent):
    """Agent with custom routing logic."""
    
    def __init__(self, config: AgentConfig, handles_type: str):
        super().__init__(config)
        self.handles_type = handles_type
    
    async def can_handle(self, task: Dict[str, Any]) -> bool:
        """Check if this agent can handle the task."""
        return task.get("type") == self.handles_type
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the task."""
        return {"handled_by": self.name, "type": task.get("type")}


@pytest.mark.asyncio
class TestOrchestrator:
    """Test suite for Orchestrator functionality."""
    
    async def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        orchestrator = Orchestrator()
        
        assert orchestrator.agents == {}
        assert orchestrator.workflow is None
    
    async def test_agent_registration(self, mock_agent):
        """Test registering agents."""
        orchestrator = Orchestrator()
        
        orchestrator.register_agent(mock_agent)
        
        assert "test_agent" in orchestrator.agents
        assert orchestrator.agents["test_agent"] == mock_agent
    
    async def test_multiple_agent_registration(self, agent_config):
        """Test registering multiple agents."""
        orchestrator = Orchestrator()
        
        agent1 = RoutableAgent(
            AgentConfig(name="agent1", description="First"),
            "type1"
        )
        agent2 = RoutableAgent(
            AgentConfig(name="agent2", description="Second"),
            "type2"
        )
        
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        
        assert len(orchestrator.agents) == 2
        assert "agent1" in orchestrator.agents
        assert "agent2" in orchestrator.agents
    
    async def test_execute_task_no_agents(self):
        """Test executing task with no agents registered."""
        orchestrator = Orchestrator()
        
        task = {"type": "test", "data": {}}
        result = await orchestrator.execute_task(task)
        
        assert result["success"] is False
        assert "No agents registered" in result["error"]
    
    async def test_execute_task_success(self, mock_agent, sample_task):
        """Test successful task execution."""
        orchestrator = Orchestrator()
        orchestrator.register_agent(mock_agent)
        
        result = await orchestrator.execute_task(sample_task)
        
        assert result["success"] is True
        assert result["agent"] == "test_agent"
        assert mock_agent.execution_count == 1
    
    async def test_task_routing(self):
        """Test intelligent task routing."""
        orchestrator = Orchestrator()
        
        agent1 = RoutableAgent(
            AgentConfig(name="type1_handler", description="Handles type1"),
            "type1"
        )
        agent2 = RoutableAgent(
            AgentConfig(name="type2_handler", description="Handles type2"),
            "type2"
        )
        
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        
        # Task should route to agent1
        task1 = {"type": "type1", "data": {}}
        result1 = await orchestrator.execute_task(task1)
        
        assert result1["success"] is True
        assert result1["result"]["handled_by"] == "type1_handler"
        
        # Task should route to agent2
        task2 = {"type": "type2", "data": {}}
        result2 = await orchestrator.execute_task(task2)
        
        assert result2["success"] is True
        assert result2["result"]["handled_by"] == "type2_handler"
    
    async def test_default_routing(self, mock_agent):
        """Test default routing when no specific handler found."""
        orchestrator = Orchestrator()
        orchestrator.register_agent(mock_agent)
        
        # Task with unknown type
        task = {"type": "unknown_type", "data": {}}
        result = await orchestrator.execute_task(task)
        
        # Should route to first registered agent by default
        assert result["success"] is True
        assert result["agent"] == "test_agent"
    
    async def test_workflow_integration(self, mock_agent):
        """Test workflow integration."""
        orchestrator = Orchestrator()
        workflow = AgentWorkflow()
        
        orchestrator.register_agent(mock_agent)
        orchestrator.set_workflow(workflow)
        
        assert orchestrator.workflow == workflow
        assert "test_agent" in workflow.agents
    
    async def test_execute_workflow_no_workflow(self):
        """Test executing workflow when none is configured."""
        orchestrator = Orchestrator()
        
        task = {"type": "test", "data": {}}
        
        with pytest.raises(ValueError, match="No workflow configured"):
            await orchestrator.execute_workflow(task)
    
    async def test_agent_not_found(self, mock_agent):
        """Test handling of non-existent agent after routing."""
        orchestrator = Orchestrator()
        orchestrator.register_agent(mock_agent)
        
        # Override route_task to return non-existent agent
        async def mock_route(task):
            return "nonexistent_agent"
        
        orchestrator.route_task = mock_route
        
        task = {"type": "test", "data": {}}
        result = await orchestrator.execute_task(task)
        
        assert result["success"] is False
        assert "not found" in result["error"]


@pytest.mark.asyncio
class TestOrchestratorWorkflow:
    """Test orchestrator workflow execution."""
    
    async def test_simple_workflow_execution(self, mock_agent):
        """Test executing a simple workflow."""
        from langgraph.graph import END
        
        orchestrator = Orchestrator()
        workflow = AgentWorkflow()
        
        # Define simple workflow node
        async def process_node(state: AgentState) -> dict:
            if state["task_queue"]:
                task = state["task_queue"][0]
                result = await mock_agent.process(task)
                return {
                    "results": {**state["results"], "processor": result}
                }
            return {}
        
        # Build workflow
        workflow.add_node("process", process_node)
        workflow.set_entry_point("process")
        workflow.add_edge("process", END)
        
        orchestrator.set_workflow(workflow)
        
        # Execute workflow
        task = {"type": "test", "data": {"input": "test"}}
        final_state = await orchestrator.execute_workflow(task)
        
        # Verify execution
        assert "processor" in final_state["results"]
        assert mock_agent.execution_count == 1