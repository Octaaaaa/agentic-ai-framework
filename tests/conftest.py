"""
Pytest configuration and shared fixtures.

This module provides common test fixtures and configuration used across
all test modules.
"""

import pytest
from typing import Dict, Any
from src.agents.base import BaseAgent, AgentConfig
from src.graph.state import AgentState


class MockAgent(BaseAgent):
    """
    Mock agent for testing.
    
    This agent allows testing of orchestration logic without
    requiring actual agent implementations.
    """
    
    def __init__(self, config: AgentConfig, return_value: Dict[str, Any] = None):
        """
        Initialize mock agent.
        
        Args:
            config: Agent configuration
            return_value: Value to return from execute (default: success response)
        """
        super().__init__(config)
        self.return_value = return_value or {"status": "completed"}
        self.execution_count = 0
        self.last_task = None
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute mock logic.
        
        Tracks execution and returns predetermined value.
        """
        self.execution_count += 1
        self.last_task = task
        return self.return_value


class FailingAgent(BaseAgent):
    """
    Agent that always fails for testing error handling.
    """
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Always raise an exception."""
        raise ValueError("Mock agent failure")


@pytest.fixture
def agent_config():
    """
    Provide a standard agent configuration for tests.
    
    Returns:
        AgentConfig instance with test values
    """
    return AgentConfig(
        name="test_agent",
        description="Agent for testing",
        max_retries=3,
        timeout=30
    )


@pytest.fixture
def mock_agent(agent_config):
    """
    Provide a mock agent instance.
    
    Returns:
        MockAgent instance ready for testing
    """
    return MockAgent(agent_config)


@pytest.fixture
def failing_agent(agent_config):
    """
    Provide a failing agent for error testing.
    
    Returns:
        FailingAgent instance that always fails
    """
    config = AgentConfig(
        name="failing_agent",
        description="Agent that fails",
        max_retries=1,
        timeout=10
    )
    return FailingAgent(config)


@pytest.fixture
def sample_task():
    """
    Provide a standard task for testing.
    
    Returns:
        Dictionary with standard task structure
    """
    return {
        "type": "test_task",
        "data": {
            "input": "test data",
            "param1": "value1"
        }
    }


@pytest.fixture
def agent_state():
    """
    Provide a clean agent state for testing.
    
    Returns:
        Empty AgentState dict (TypedDict cannot be instantiated)
    """
    return {
        "messages": [],
        "current_agent": None,
        "task_queue": [],
        "results": {},
        "metadata": {},
        "error": None
    }