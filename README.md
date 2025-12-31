# Agentic AI Framework

![CI](https://github.com/Octaaaaa/agentic-ai-framework/workflows/CI/badge.svg)

A production-ready, open-source framework for building multi-agent AI systems with LangGraph orchestration.

## Overview

The Agentic AI Framework provides a flexible, extensible architecture for creating intelligent agent systems that can handle complex workflows. Built on LangGraph and LangChain, it offers a clean abstraction for agent coordination, state management, and workflow orchestration.

## Key Features

- **Flexible Agent Architecture**: Simple base class for creating custom agents
- **Workflow Orchestration**: Built-in support for complex multi-agent workflows using LangGraph
- **State Management**: Robust state handling for maintaining context across agent executions
- **Multi-LLM Support**: Flexible integration with multiple LLM providers
- **Type Safety**: Full type hints and Pydantic validation throughout
- **Async-First**: Built for high performance with async/await patterns
- **Extensible**: Easy to extend with custom agents and workflow logic
- **Production Ready**: Comprehensive error handling, logging, and validation

## Architecture

The framework follows a layered architecture:
```
┌─────────────────────────────────────┐
│        Orchestrator Layer           │
│  (Task routing & coordination)      │
└─────────────────────────────────────┘
              ↕
┌─────────────────────────────────────┐
│         Workflow Layer              │
│   (LangGraph state management)      │
└─────────────────────────────────────┘
              ↕
┌─────────────────────────────────────┐
│          Agent Layer                │
│    (Custom business logic)          │
└─────────────────────────────────────┘
```

### Core Components

- **BaseAgent**: Abstract base class for all agents
- **Orchestrator**: Central coordinator for agent execution
- **AgentWorkflow**: LangGraph-based workflow engine
- **AgentState**: State container passed between agents (TypedDict)

## Installation

### Prerequisites

- Python 3.10 or higher
- Ollama (for local LLM support, optional)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/Octaaaaa/agentic-ai-framework.git
cd agentic-ai-framework

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run tests to verify installation
python -m pytest tests/

# Run a simple example
python examples/simple_agent.py
```

## Usage

### Creating a Custom Agent
```python
from src.agents.base import BaseAgent, AgentConfig
from typing import Dict, Any

class MyCustomAgent(BaseAgent):
    """
    Custom agent that implements your specific logic.
    """
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Your custom logic here
        data = task.get("data", {})
        
        # Process the data
        result = self.process_data(data)
        
        return {
            "result": result,
            "status": "completed"
        }
    
    def process_data(self, data: Dict[str, Any]) -> Any:
        # Your processing logic
        return data
```

### Simple Task Execution
```python
import asyncio
from src.core.orchestrator import Orchestrator
from src.agents.base import AgentConfig

async def main():
    # Create agent configuration
    config = AgentConfig(
        name="my_agent",
        description="My custom agent"
    )
    
    # Initialize agent
    agent = MyCustomAgent(config)
    
    # Create orchestrator and register agent
    orchestrator = Orchestrator()
    orchestrator.register_agent(agent)
    
    # Execute task
    task = {
        "type": "process",
        "data": {"input": "some data"}
    }
    
    result = await orchestrator.execute_task(task)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Multi-Agent Workflow

**Important**: Workflow nodes must return **partial state updates as dictionaries**, not complete `AgentState` objects. LangGraph automatically merges these updates.
```python
from src.graph.workflow import AgentWorkflow
from src.graph.state import AgentState
from langgraph.graph import END
import asyncio

async def main():
    # Create workflow
    workflow = AgentWorkflow()
    
    # Define workflow nodes - MUST return dict of updates
    async def agent1_node(state: AgentState) -> dict:
        """Process task and return state updates."""
        task = state["task_queue"][0] if state["task_queue"] else None
        
        result = {"processed": True, "data": "from agent1"}
        
        # Return ONLY the fields to update
        return {
            "results": {**state["results"], "agent1": result},
            "current_agent": "agent1"
        }
    
    async def agent2_node(state: AgentState) -> dict:
        """Finalize processing."""
        agent1_result = state["results"].get("agent1", {})
        final_result = {"finalized": True, "based_on": agent1_result}
        
        return {
            "results": {**state["results"], "agent2": final_result},
            "current_agent": "agent2"
        }
    
    # Conditional routing
    def routing_function(state: AgentState) -> str:
        return "agent2" if state["error"] is None else "end"
    
    # Build workflow
    workflow.add_node("agent1", agent1_node)
    workflow.add_node("agent2", agent2_node)
    workflow.set_entry_point("agent1")
    
    workflow.add_conditional_edges(
        "agent1",
        routing_function,
        {"agent2": "agent2", "end": END}
    )
    workflow.add_edge("agent2", END)
    
    # Compile
    workflow.compile()
    
    # Initialize state as dict
    initial_state: AgentState = {
        "messages": [],
        "current_agent": None,
        "task_queue": [{"type": "start", "data": {}}],
        "results": {},
        "metadata": {},
        "error": None
    }
    
    # Execute
    final_state = await workflow.execute(initial_state)
    print(final_state["results"])

if __name__ == "__main__":
    asyncio.run(main())
```

### Working with State

`AgentState` is a TypedDict, so you work with it like a regular Python dict:
```python
# ✅ CORRECT: Accessing state
messages = state["messages"]
results = state["results"]

# ✅ CORRECT: Updating state in nodes (return partial updates)
async def my_node(state: AgentState) -> dict:
    return {
        "messages": state["messages"] + [{"role": "user", "content": "hello"}],
        "metadata": {**state["metadata"], "step": 1}
    }

# ✅ CORRECT: Merge dicts with spread operator
return {
    "results": {**state["results"], "new_key": "value"}
}
```

**Common Patterns:**
```python
# Pattern 1: Adding to lists
async def node(state: AgentState) -> dict:
    new_msg = {"role": "user", "content": "hello"}
    return {"messages": state["messages"] + [new_msg]}

# Pattern 2: Updating nested dicts
async def node(state: AgentState) -> dict:
    return {
        "results": {**state["results"], "agent1": {"done": True}},
        "metadata": {**state["metadata"], "step": 1}
    }

# Pattern 3: Conditional updates
async def node(state: AgentState) -> dict:
    if state["error"] is None:
        return {"results": {**state["results"], "success": True}}
    return {"error": None}  # Clear error
```

## Configuration

Configuration is managed through environment variables. Copy `.env.example` to `.env` and customize:
```bash
# LLM Provider Selection
# LLM_PROVIDER=ollama

# Ollama Configuration
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3

# OpenAI Configuration
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4

# Logging
# LOG_LEVEL=INFO
```

## LLM Providers

The framework supports multiple LLM providers out of the box:

- **Ollama** (default, local)
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude)
- **Google** (Gemini)
- **Azure OpenAI**

### Setup

1. **Choose your provider** in `.env`:
```bash
LLM_PROVIDER=openai  # or ollama, anthropic, google, azure
```

2. **Install the required package**:
```bash
# For OpenAI
pip install langchain-openai

# For Anthropic
pip install langchain-anthropic

# For Google
pip install langchain-google-genai
```

3. **Add your API key** to `.env`:
```bash
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

### Usage in Agents
```python
from src.utils import get_llm

class MyLLMAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        # Uses provider configured in .env
        self.llm = get_llm(temperature=0.7)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = task.get("data", {}).get("prompt", "")
        response = await self.llm.ainvoke(prompt)
        return {"response": response.content}
```

**Per-Agent Model Override:**
```python
# Agent 1 uses GPT-4
class Agent1(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.llm = get_llm(provider="openai", model="gpt-4")

# Agent 2 uses Claude
class Agent2(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.llm = get_llm(provider="anthropic", model="claude-3-5-sonnet-20241022")
```

See `examples/llm_agent.py` for a complete working example.

## Examples

The `examples/` directory contains complete working examples:

- **simple_agent.py**: Basic single-agent task execution
- **multi_agent.py**: Multi-agent workflow with coordination
- **llm_agent.py**: LLM-powered agent with conversation

Run examples:
```bash
python examples/simple_agent.py
python examples/multi_agent.py
python examples/llm_agent.py
```

## Development Guide

### Adding Custom Agents

1. Create a new class inheriting from `BaseAgent`
2. Implement the `execute` method with your logic
3. Optionally implement `can_handle` for custom routing
4. Register the agent with the orchestrator

See `docs/creating-agents.md` for detailed instructions.

### Building Workflows

**Key Rules for Workflow Nodes:**

1. **Nodes must return dictionaries** with partial state updates
2. **Use spread operator** to merge: `{**state["results"], ...}`
3. **Don't mutate state directly** - always return new values
4. **Access state** using dict syntax: `state["field"]`
5. **Return empty dict** `{}` if no updates needed

Steps to build a workflow:

1. Define workflow nodes as async functions that return dict updates
2. Create an `AgentWorkflow` instance
3. Add nodes and define edges
4. Set entry points and compile

See `docs/workflow-patterns.md` for patterns and best practices.

## Testing
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src

# Run specific test file
python -m pytest tests/test_workflow.py -v
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Creating Custom Agents](docs/creating-agents.md)
- [Workflow Patterns](docs/workflow-patterns.md)

## Use Cases

This framework is designed for building:

- Multi-agent AI assistants
- Workflow automation systems
- Complex task orchestration
- AI-powered business process automation
- Custom LLM applications with multiple specialized agents
- Conversational AI with multiple capabilities
- Data processing pipelines with AI decision points

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: See `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/Octaaaaa/agentic-ai-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Octaaaaa/agentic-ai-framework/discussions)

## Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph-based workflow orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation

