"""
Unit tests for agent functionality.

Tests the BaseAgent class and agent execution logic.
"""

import pytest
from src.agents.base import BaseAgent, AgentConfig
from typing import Dict, Any


class SimpleTestAgent(BaseAgent):
    """Simple agent for testing basic functionality."""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Return simple success response."""
        return {"result": "success", "input": task.get("data", {})}


class ValidationAgent(BaseAgent):
    """Agent with custom validation for testing."""
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """Custom validation requiring specific field."""
        if not super().validate_task(task):
            return False
        return "required_field" in task.get("data", {})
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process validated task."""
        return {"validated": True}


@pytest.mark.asyncio
class TestBaseAgent:
    """Test suite for BaseAgent functionality."""
    
    async def test_agent_initialization(self, agent_config):
        """Test agent initializes with correct configuration."""
        agent = SimpleTestAgent(agent_config)
        
        assert agent.name == "test_agent"
        assert agent.description == "Agent for testing"
        assert agent.config.max_retries == 3
        assert agent.config.timeout == 30
    
    async def test_successful_execution(self, agent_config, sample_task):
        """Test successful task execution."""
        agent = SimpleTestAgent(agent_config)
        result = await agent.process(sample_task)
        
        assert result["success"] is True
        assert "result" in result
        assert result["agent"] == "test_agent"
        assert result["result"]["result"] == "success"
    
    async def test_invalid_task_structure(self, agent_config):
        """Test handling of invalid task structure."""
        agent = SimpleTestAgent(agent_config)
        
        # Missing 'type' key
        invalid_task = {"data": {}}
        result = await agent.process(invalid_task)
        
        assert result["success"] is False
        assert "error" in result
        assert "Invalid task format" in result["error"]
    
    async def test_task_validation(self, agent_config):
        """Test task validation logic."""
        agent = SimpleTestAgent(agent_config)
        
        valid_task = {"type": "test", "data": {}}
        assert agent.validate_task(valid_task) is True
        
        invalid_task = {"type": "test"}
        assert agent.validate_task(invalid_task) is False
        
        invalid_task = {"data": {}}
        assert agent.validate_task(invalid_task) is False
        
        invalid_task = "not a dict"
        assert agent.validate_task(invalid_task) is False
    
    async def test_custom_validation(self, agent_config):
        """Test custom validation logic."""
        agent = ValidationAgent(agent_config)
        
        # Valid task with required field
        valid_task = {
            "type": "test",
            "data": {"required_field": "value"}
        }
        result = await agent.process(valid_task)
        assert result["success"] is True
        
        # Invalid task missing required field
        invalid_task = {
            "type": "test",
            "data": {"other_field": "value"}
        }
        result = await agent.process(invalid_task)
        assert result["success"] is False
    
    async def test_execution_error_handling(self, failing_agent, sample_task):
        """Test error handling during execution."""
        result = await failing_agent.process(sample_task)
        
        assert result["success"] is False
        assert "error" in result
        assert "Mock agent failure" in result["error"]
        assert result["agent"] == "failing_agent"
    
    async def test_agent_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = AgentConfig(
            name="test",
            description="test",
            max_retries=5,
            timeout=60
        )
        assert config.max_retries == 5
        assert config.timeout == 60
        
        # Test defaults
        config = AgentConfig(name="test", description="test")
        assert config.max_retries == 3
        assert config.timeout == 30
        
        # Test validation constraints
        with pytest.raises(Exception):
            AgentConfig(
                name="test",
                description="test",
                max_retries=0  # Must be >= 1
            )


@pytest.mark.asyncio
class TestAgentBehavior:
    """Test suite for agent behavioral patterns."""
    
    async def test_stateful_agent(self, agent_config):
        """Test agent that maintains state across executions."""
        
        class StatefulAgent(BaseAgent):
            def __init__(self, config):
                super().__init__(config)
                self.call_count = 0
            
            async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
                self.call_count += 1
                return {"call_number": self.call_count}
        
        agent = StatefulAgent(agent_config)
        
        task = {"type": "test", "data": {}}
        
        result1 = await agent.process(task)
        assert result1["result"]["call_number"] == 1
        
        result2 = await agent.process(task)
        assert result2["result"]["call_number"] == 2
    
    async def test_agent_with_dependencies(self, agent_config):
        """Test agent with external dependencies."""
        
        class MockDependency:
            async def fetch_data(self):
                return {"data": "from dependency"}
        
        class DependentAgent(BaseAgent):
            def __init__(self, config, dependency):
                super().__init__(config)
                self.dependency = dependency
            
            async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
                data = await self.dependency.fetch_data()
                return {"fetched": data}
        
        dependency = MockDependency()
        agent = DependentAgent(agent_config, dependency)
        
        task = {"type": "test", "data": {}}
        result = await agent.process(task)
        
        assert result["success"] is True
        assert result["result"]["fetched"]["data"] == "from dependency"