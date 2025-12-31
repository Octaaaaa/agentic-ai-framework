"""
State management for agent workflows.

This module defines the state structure used throughout the agent execution
lifecycle. State is passed between agents and tracks messages, tasks, and results.
"""

from typing import TypedDict, Annotated, Sequence
from operator import add


class AgentState(TypedDict):
    """
    State object passed between agents in a workflow.
    
    This class maintains the complete state of a workflow execution, including
    conversation history, task queue, results from individual agents, and
    any error information.
    
    Attributes:
        messages: List of conversation messages with role and content
        current_agent: Name of the currently executing agent
        task_queue: Queue of pending tasks to be processed
        results: Dictionary mapping agent names to their execution results
        metadata: Additional metadata for workflow execution
        error: Error message if workflow encountered an error
    """
    
    messages: Annotated[Sequence[dict], add]
    current_agent: str | None
    task_queue: Annotated[Sequence[dict], add]
    results: dict
    metadata: dict
    error: str | None