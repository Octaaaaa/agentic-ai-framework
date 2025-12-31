"""
Base agent implementation.

This module defines the abstract base class that all agents must inherit from.
It provides the core structure for task execution, validation, and error handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """
    Configuration model for agent initialization.
    
    Attributes:
        name: Unique identifier for the agent
        description: Human-readable description of agent capabilities
        max_retries: Maximum number of retry attempts for failed tasks
        timeout: Maximum execution time in seconds for a single task
    """
    name: str
    description: str
    max_retries: int = Field(default=3, ge=1)
    timeout: Optional[int] = Field(default=30, ge=1)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the framework.
    
    All custom agents must inherit from this class and implement the execute method.
    This class provides common functionality for task validation and error handling.
    
    Attributes:
        config: Agent configuration object
        name: Agent name from config
        description: Agent description from config
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.
        
        Args:
            config: AgentConfig object containing agent settings
        """
        self.config = config
        self.name = config.name
        self.description = config.description
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the main agent logic.
        
        This method must be implemented by all subclasses. It contains the core
        business logic for processing tasks specific to each agent type.
        
        Args:
            task: Dictionary containing task data with 'type' and 'data' keys
            
        Returns:
            Dictionary containing the execution results
            
        Raises:
            NotImplementedError: If subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement execute method")
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate task structure before execution.
        
        Ensures that the task dictionary contains the required keys and is
        properly formatted for processing.
        
        Args:
            task: Task dictionary to validate
            
        Returns:
            True if task is valid, False otherwise
        """
        if not isinstance(task, dict):
            return False
        return "type" in task and "data" in task
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task with validation and error handling.
        
        This method wraps the execute method with validation and error handling
        to provide a consistent interface for task processing.
        
        Args:
            task: Task dictionary to process
            
        Returns:
            Dictionary with execution results including success status, result data,
            and agent name. On error, includes error message.
        """
        # Validate task structure
        if not self.validate_task(task):
            return {
                "success": False,
                "error": "Invalid task format. Must include 'type' and 'data' keys",
                "agent": self.name
            }
        
        try:
            # Execute agent-specific logic
            result = await self.execute(task)
            return {
                "success": True,
                "result": result,
                "agent": self.name
            }
        except Exception as e:
            # Catch and return any execution errors
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }