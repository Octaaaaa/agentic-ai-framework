"""
Unit tests for workflow functionality.

Tests the AgentWorkflow class and LangGraph integration.
"""

import pytest
from langgraph.graph import END
from src.graph.workflow import AgentWorkflow
from src.graph.state import AgentState
from src.agents.base import BaseAgent, AgentConfig
from typing import Dict, Any


class WorkflowTestAgent(BaseAgent):
    """Simple agent for workflow testing."""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"processed": True, "agent": self.name}


@pytest.mark.asyncio
class TestAgentWorkflow:
    """Test suite for AgentWorkflow functionality."""
    
    async def test_workflow_initialization(self):
        """Test workflow initializes correctly."""
        workflow = AgentWorkflow()
        
        assert workflow.agents == {}
        assert workflow.graph is not None
        assert workflow.compiled_graph is None
    
    async def test_register_agent(self):
        """Test registering agents with workflow."""
        workflow = AgentWorkflow()
        
        config = AgentConfig(name="test", description="Test agent")
        agent = WorkflowTestAgent(config)
        
        workflow.register_agent(agent)
        
        assert "test" in workflow.agents
        assert workflow.agents["test"] == agent
    
    async def test_add_node(self):
        """Test adding nodes to workflow."""
        workflow = AgentWorkflow()
        
        async def test_node(state: AgentState) -> dict:
            return {}
        
        workflow.add_node("test_node", test_node)
        
        # Node should be added to graph
        # We can't easily verify this directly, but compilation should work
        workflow.set_entry_point("test_node")
        workflow.add_edge("test_node", END)
        compiled = workflow.compile()
        
        assert compiled is not None
    
    async def test_simple_sequential_workflow(self):
        """Test simple sequential workflow execution."""
        workflow = AgentWorkflow()
        
        execution_order = []
        
        async def node1(state: AgentState) -> dict:
            execution_order.append("node1")
            return {
                "results": {**state["results"], "node1": {"executed": True}}
            }
        
        async def node2(state: AgentState) -> dict:
            execution_order.append("node2")
            return {
                "results": {**state["results"], "node2": {"executed": True}}
            }
        
        workflow.add_node("node1", node1)
        workflow.add_node("node2", node2)
        
        workflow.set_entry_point("node1")
        workflow.add_edge("node1", "node2")
        workflow.add_edge("node2", END)
        
        initial_state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        final_state = await workflow.execute(initial_state)
        
        assert execution_order == ["node1", "node2"]
        assert final_state["results"]["node1"]["executed"] is True
        assert final_state["results"]["node2"]["executed"] is True
    
    async def test_conditional_routing(self):
        """Test conditional edge routing."""
        workflow = AgentWorkflow()
        
        async def decision_node(state: AgentState) -> dict:
            return {
                "metadata": {**state["metadata"], "decision": "path_a"}
            }
        
        async def path_a_node(state: AgentState) -> dict:
            return {
                "results": {**state["results"], "path_a": {"executed": True}}
            }
        
        async def path_b_node(state: AgentState) -> dict:
            return {
                "results": {**state["results"], "path_b": {"executed": True}}
            }
        
        def router(state: AgentState) -> str:
            return state["metadata"].get("decision", "path_b")
        
        workflow.add_node("decision", decision_node)
        workflow.add_node("path_a", path_a_node)
        workflow.add_node("path_b", path_b_node)
        
        workflow.set_entry_point("decision")
        workflow.add_conditional_edges(
            "decision",
            router,
            {
                "path_a": "path_a",
                "path_b": "path_b"
            }
        )
        workflow.add_edge("path_a", END)
        workflow.add_edge("path_b", END)
        
        initial_state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        final_state = await workflow.execute(initial_state)
        
        # Should have taken path_a
        assert final_state["results"].get("path_a") is not None
        assert final_state["results"].get("path_b") is None
    
    async def test_workflow_with_agents(self):
        """Test workflow using actual agents."""
        workflow = AgentWorkflow()
        
        agent1 = WorkflowTestAgent(AgentConfig(
            name="agent1",
            description="First agent"
        ))
        agent2 = WorkflowTestAgent(AgentConfig(
            name="agent2",
            description="Second agent"
        ))
        
        workflow.register_agent(agent1)
        workflow.register_agent(agent2)
        
        async def agent1_node(state: AgentState) -> dict:
            task = {"type": "test", "data": {}}
            result = await agent1.process(task)
            return {
                "results": {**state["results"], "agent1": result}
            }
        
        async def agent2_node(state: AgentState) -> dict:
            task = {"type": "test", "data": {}}
            result = await agent2.process(task)
            return {
                "results": {**state["results"], "agent2": result}
            }
        
        workflow.add_node("agent1", agent1_node)
        workflow.add_node("agent2", agent2_node)
        
        workflow.set_entry_point("agent1")
        workflow.add_edge("agent1", "agent2")
        workflow.add_edge("agent2", END)
        
        initial_state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        final_state = await workflow.execute(initial_state)
        
        # Verify both agents executed
        assert final_state["results"]["agent1"]["success"] is True
        assert final_state["results"]["agent2"]["success"] is True
    
    async def test_workflow_state_passing(self):
        """Test state is properly passed between nodes."""
        workflow = AgentWorkflow()
        
        async def producer_node(state: AgentState) -> dict:
            return {
                "metadata": {**state["metadata"], "produced_value": "test_data"},
                "results": {**state["results"], "producer": {"data": "test_data"}}
            }
        
        async def consumer_node(state: AgentState) -> dict:
            # Should be able to access data from producer
            produced_value = state["metadata"].get("produced_value")
            return {
                "results": {**state["results"], "consumer": {"received": produced_value}}
            }
        
        workflow.add_node("producer", producer_node)
        workflow.add_node("consumer", consumer_node)
        
        workflow.set_entry_point("producer")
        workflow.add_edge("producer", "consumer")
        workflow.add_edge("consumer", END)
        
        initial_state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        final_state = await workflow.execute(initial_state)
        
        # Verify data was passed
        assert final_state["results"]["consumer"]["received"] == "test_data"
    
    async def test_compile_before_execute(self):
        """Test workflow auto-compiles if not already compiled."""
        workflow = AgentWorkflow()
        
        async def simple_node(state: AgentState) -> dict:
            return {"current_agent": "simple"}
        
        workflow.add_node("simple", simple_node)
        workflow.set_entry_point("simple")
        workflow.add_edge("simple", END)
        
        # Don't manually compile
        assert workflow.compiled_graph is None
        
        initial_state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        await workflow.execute(initial_state)
        
        # Should have auto-compiled
        assert workflow.compiled_graph is not None


@pytest.mark.asyncio
class TestWorkflowPatterns:
    """Test common workflow patterns."""
    
    async def test_error_handling_workflow(self):
        """Test workflow with error handling."""
        workflow = AgentWorkflow()
        
        async def risky_node(state: AgentState) -> dict:
            # Simulate an error condition
            return {
                "error": "Something went wrong",
                "results": {**state["results"], "risky": {"success": False}}
            }
        
        async def error_handler_node(state: AgentState) -> dict:
            return {
                "results": {
                    **state["results"],
                    "error_handler": {
                        "handled": True,
                        "original_error": state["error"]
                    }
                },
                "error": None  # Clear error
            }
        
        def check_error(state: AgentState) -> str:
            return "error_handler" if state["error"] is not None else "end"
        
        workflow.add_node("risky", risky_node)
        workflow.add_node("error_handler", error_handler_node)
        
        workflow.set_entry_point("risky")
        workflow.add_conditional_edges(
            "risky",
            check_error,
            {
                "error_handler": "error_handler",
                "end": END
            }
        )
        workflow.add_edge("error_handler", END)
        
        initial_state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        final_state = await workflow.execute(initial_state)
        
        # Error should have been handled
        assert final_state["results"]["error_handler"]["handled"] is True
        assert final_state["error"] is None
    
    async def test_iterative_workflow(self):
        """Test workflow with iteration."""
        workflow = AgentWorkflow()
        
        async def increment_node(state: AgentState) -> dict:
            counter = state["metadata"].get("counter", 0)
            counter += 1
            return {
                "metadata": {**state["metadata"], "counter": counter},
                "results": {**state["results"], f"iteration_{counter}": {"count": counter}}
            }
        
        def should_continue(state: AgentState) -> str:
            counter = state["metadata"].get("counter", 0)
            return "continue" if counter < 3 else "end"
        
        workflow.add_node("increment", increment_node)
        
        workflow.set_entry_point("increment")
        workflow.add_conditional_edges(
            "increment",
            should_continue,
            {
                "continue": "increment",
                "end": END
            }
        )
        
        initial_state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        final_state = await workflow.execute(initial_state)
        
        # Should have iterated 3 times
        assert final_state["metadata"]["counter"] == 3
        assert final_state["results"].get("iteration_1") is not None
        assert final_state["results"].get("iteration_2") is not None
        assert final_state["results"].get("iteration_3") is not None