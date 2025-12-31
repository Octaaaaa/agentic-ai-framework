"""
Unit tests for state management.

Tests the AgentState class and state operations.
"""

import pytest
from src.graph.state import AgentState


class TestAgentState:
    """Test suite for AgentState functionality."""
    
    def test_state_initialization(self):
        """Test state initializes with empty values."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        assert state["messages"] == []
        assert state["current_agent"] is None
        assert state["task_queue"] == []
        assert state["results"] == {}
        assert state["metadata"] == {}
        assert state["error"] is None
    
    def test_add_message(self):
        """Test adding messages to state."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        # Add first message
        state["messages"].append({"role": "user", "content": "Hello"})
        assert len(state["messages"]) == 1
        assert state["messages"][0]["role"] == "user"
        assert state["messages"][0]["content"] == "Hello"
        
        # Add second message
        state["messages"].append({"role": "assistant", "content": "Hi there"})
        assert len(state["messages"]) == 2
        assert state["messages"][1]["role"] == "assistant"
    
    def test_add_task(self):
        """Test adding tasks to queue."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        task1 = {"type": "task1", "data": {}}
        task2 = {"type": "task2", "data": {}}
        
        state["task_queue"].append(task1)
        assert len(state["task_queue"]) == 1
        assert state["task_queue"][0] == task1
        
        state["task_queue"].append(task2)
        assert len(state["task_queue"]) == 2
        assert state["task_queue"][1] == task2
    
    def test_set_and_get_result(self):
        """Test storing and retrieving results."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        result = {"status": "success", "data": "test"}
        state["results"]["agent1"] = result
        
        retrieved = state["results"].get("agent1")
        assert retrieved == result
        
        # Test non-existent agent
        assert state["results"].get("nonexistent") is None
    
    def test_has_error(self):
        """Test error checking."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        assert state["error"] is None
        
        state["error"] = "Something went wrong"
        assert state["error"] is not None
    
    def test_metadata_storage(self):
        """Test metadata operations."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        state["metadata"]["key1"] = "value1"
        state["metadata"]["key2"] = {"nested": "data"}
        
        assert state["metadata"]["key1"] == "value1"
        assert state["metadata"]["key2"]["nested"] == "data"
    
    def test_current_agent_tracking(self):
        """Test current agent tracking."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        assert state["current_agent"] is None
        
        state["current_agent"] = "agent1"
        assert state["current_agent"] == "agent1"
        
        state["current_agent"] = "agent2"
        assert state["current_agent"] == "agent2"
    
    def test_multiple_results(self):
        """Test storing results from multiple agents."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        state["results"]["agent1"] = {"data": "from agent 1"}
        state["results"]["agent2"] = {"data": "from agent 2"}
        state["results"]["agent3"] = {"data": "from agent 3"}
        
        assert len(state["results"]) == 3
        assert state["results"]["agent1"]["data"] == "from agent 1"
        assert state["results"]["agent2"]["data"] == "from agent 2"
        assert state["results"]["agent3"]["data"] == "from agent 3"
    
    def test_result_overwrite(self):
        """Test overwriting existing results."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        state["results"]["agent1"] = {"version": 1}
        assert state["results"]["agent1"]["version"] == 1
        
        state["results"]["agent1"] = {"version": 2}
        assert state["results"]["agent1"]["version"] == 2


class TestStateWorkflow:
    """Test state usage in workflow scenarios."""
    
    def test_workflow_progression(self):
        """Test state progression through workflow."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        # Initial task
        state["task_queue"].append({"type": "start", "data": {"input": "test"}})
        assert len(state["task_queue"]) == 1
        
        # Agent 1 processes
        state["current_agent"] = "agent1"
        state["results"]["agent1"] = {"processed": True}
        
        # Agent 2 processes
        state["current_agent"] = "agent2"
        state["results"]["agent2"] = {"finalized": True}
        
        # Verify workflow state
        assert state["current_agent"] == "agent2"
        assert "agent1" in state["results"]
        assert "agent2" in state["results"]
    
    def test_error_propagation(self):
        """Test error handling in workflow."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        state["task_queue"].append({"type": "test", "data": {}})
        state["current_agent"] = "agent1"
        state["results"]["agent1"] = {"success": True}
        
        # Agent 2 encounters error
        state["current_agent"] = "agent2"
        state["error"] = "Agent 2 failed"
        
        assert state["error"] is not None
        assert state["current_agent"] == "agent2"
        
        # Verify previous results preserved
        assert state["results"]["agent1"]["success"] is True
    
    def test_metadata_tracking(self):
        """Test metadata for workflow tracking."""
        state: AgentState = {
            "messages": [],
            "current_agent": None,
            "task_queue": [],
            "results": {},
            "metadata": {},
            "error": None
        }
        
        # Track workflow metadata
        state["metadata"]["workflow_id"] = "wf_123"
        state["metadata"]["start_time"] = "2025-01-01T00:00:00Z"
        state["metadata"]["steps_completed"] = 0
        
        # Simulate workflow steps
        state["current_agent"] = "agent1"
        state["results"]["agent1"] = {"done": True}
        state["metadata"]["steps_completed"] += 1
        
        state["current_agent"] = "agent2"
        state["results"]["agent2"] = {"done": True}
        state["metadata"]["steps_completed"] += 1
        
        # Verify tracking
        assert state["metadata"]["steps_completed"] == 2
        assert state["metadata"]["workflow_id"] == "wf_123"