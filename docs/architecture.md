# Architecture Overview

## Introduction

The Agentic AI Framework is built on a layered architecture designed for scalability, maintainability, and extensibility. This document explains the design decisions and architectural patterns used throughout the framework.

## Design Principles

### 1. Separation of Concerns

Each layer has a single, well-defined responsibility:

- **Agent Layer**: Implements business logic
- **Workflow Layer**: Manages state and orchestration
- **Orchestrator Layer**: Routes tasks and coordinates execution

### 2. Abstraction

The framework provides clear abstractions:

- `BaseAgent`: Abstract interface for all agents
- `AgentState`: Container for workflow state
- `AgentWorkflow`: Workflow execution engine

### 3. Async-First

All operations use async/await for:

- Non-blocking I/O operations
- Concurrent agent execution
- Scalable performance

### 4. Type Safety

Full type hints throughout:

- Better IDE support
- Catch errors at development time
- Self-documenting code

## Architecture Layers

### Agent Layer

The foundation of the framework. Agents encapsulate specific capabilities.
```python
BaseAgent (Abstract)
    │
    ├── validate_task()    # Input validation
    ├── execute()          # Core logic (abstract)
    └── process()          # Wrapper with error handling
```

**Responsibilities:**
- Execute specific tasks
- Validate inputs
- Return structured outputs
- Handle errors gracefully

**Design Pattern:** Template Method Pattern

The `process()` method provides a template that calls `validate_task()` and `execute()`, allowing subclasses to customize execution while maintaining consistent validation and error handling.

### Workflow Layer

Manages complex multi-agent interactions using LangGraph.
```python
AgentWorkflow
    │
    ├── register_agent()           # Agent registration
    ├── add_node()                 # Add workflow steps
    ├── add_edge()                 # Sequential flow
    ├── add_conditional_edges()    # Conditional routing
    └── compile()                  # Build executable graph
```

**Responsibilities:**
- Define workflow structure
- Manage state transitions
- Route between agents
- Coordinate execution

**Design Pattern:** State Pattern + Graph-based Routing

State is explicitly managed and passed between nodes, allowing complex conditional logic without tightly coupling agents.

### Orchestrator Layer

High-level coordination and task routing.
```python
Orchestrator
    │
    ├── register_agent()      # Register available agents
    ├── route_task()          # Determine handler
    ├── execute_task()        # Simple execution
    └── execute_workflow()    # Complex workflows
```

**Responsibilities:**
- Agent registry management
- Task routing logic
- Execution coordination
- Workflow integration

**Design Pattern:** Facade Pattern

Provides a simplified interface to the complex subsystem of agents and workflows.

## State Management

### AgentState

The state object flows through the workflow carrying context:
```python
AgentState (TypedDict)
    │
    ├── messages          # Conversation history (List)
    ├── current_agent     # Active agent (str | None)
    ├── task_queue        # Pending tasks (List)
    ├── results           # Agent outputs (Dict)
    ├── metadata          # Additional context (Dict)
    └── error             # Error information (str | None)
```

**Implementation Note**: AgentState is implemented as a TypedDict rather than a Pydantic model. This design choice provides:

1. **Better LangGraph Integration**: Native compatibility with LangGraph's state management
2. **Performance**: Reduced overhead compared to Pydantic validation on every state update
3. **Simplicity**: Standard Python dict operations without custom methods
4. **Immutability Pattern**: Workflow nodes return partial state updates as dicts, which LangGraph merges automatically

**Key Characteristics:**

1. **Immutable Updates**: Nodes return new dict updates, never mutate state directly
2. **Type-Safe**: TypedDict provides type hints and IDE support
3. **Serializable**: Can be persisted or transmitted as standard JSON
4. **Extensible**: Custom fields can be added via metadata dict

**State Access Pattern:**
```python
# Accessing state (dict syntax)
messages = state["messages"]
current_agent = state["current_agent"]
results = state["results"]

# Updating state in workflow nodes (return dict of updates)
async def my_node(state: AgentState) -> dict:
    return {
        "messages": state["messages"] + [new_message],
        "results": {**state["results"], "my_node": result},
        "current_agent": "my_node"
    }
```

## Workflow Patterns

### Sequential Workflow
```
Agent A → Agent B → Agent C → End
```

Simple linear flow where each agent processes in order.

### Conditional Workflow
```
         ┌─→ Agent B → End
Agent A ─┤
         └─→ Agent C → End
```

Dynamic routing based on Agent A's output.

### Parallel Workflow
```
         ┌─→ Agent B ─┐
Agent A ─┤            ├─→ Aggregator → End
         └─→ Agent C ─┘
```

Multiple agents process concurrently, results aggregated.

### Loop Workflow
```
Agent A ─→ Agent B ─→ Decision
             ↑            │
             └────────────┘
              (if retry)
```

Iterative processing with conditional loops.

## Error Handling Strategy

### Layers of Error Handling

1. **Agent Level**: Catch execution errors, return error in result
2. **Workflow Level**: Detect failed agents, route to error handlers
3. **Orchestrator Level**: Top-level error recovery

### Error Response Format
```python
{
    "success": False,
    "error": "Error message",
    "agent": "agent_name"
}
```

### Workflow Error Handling
```python
# Store error in state
return {"error": "Something went wrong"}

# Check for errors in routing
def check_error(state: AgentState) -> str:
    return "error_handler" if state["error"] else "continue"
```

## Performance Considerations

### Async Execution

All agent operations are async, enabling:
- Concurrent task processing
- Non-blocking I/O
- Efficient resource utilization

### State Passing

State updates are merged efficiently by LangGraph:
- Nodes return only changed fields
- Automatic merging with spread operator
- Minimal memory overhead

### Lazy Compilation

Workflows are compiled once and reused, avoiding repeated compilation overhead.

## Security Considerations

### Input Validation

All inputs validated through:
- Pydantic models (agent configs)
- Agent-level validation
- Type checking (TypedDict)

### Error Messages

Error messages sanitized to avoid leaking sensitive information.

### Configuration

Sensitive configuration loaded from environment variables, never hardcoded.

## LLM Integration

The framework provides a flexible LLM integration layer:

### LLM Factory Pattern
```python
from src.utils import get_llm

# Use default from config
llm = get_llm()

# Override provider/model per agent
llm = get_llm(provider="openai", model="gpt-4")
```

### Supported Providers

- **Ollama** (local, default)
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude)
- **Google** (Gemini)
- **Azure OpenAI**

### Design Benefits

1. **Configuration-Driven**: Provider selection via environment variables
2. **Per-Agent Flexibility**: Each agent can use different models/providers
3. **Security**: API keys always from config, never in code
4. **Extensibility**: Easy to add new providers

## Extensibility Points

### Custom Agents

Extend `BaseAgent` to add:
- New capabilities
- Custom validation
- Specialized error handling
- LLM integration

### Custom Workflow Nodes

Create workflow nodes that:
- Return dict of state updates
- Implement conditional logic
- Handle errors gracefully
- Coordinate multiple agents

### Custom Routing

Implement intelligent routing:
- Agent `can_handle()` method
- Conditional edge functions
- Load balancing
- Failover logic

## Testing Strategy

### Unit Tests

Test individual components in isolation:
- Agent logic
- State operations
- Utility functions

### Integration Tests

Test component interactions:
- Agent + Orchestrator
- Workflow execution
- Error propagation

### End-to-End Tests

Test complete workflows:
- Multi-agent scenarios
- Error recovery
- Performance

## Future Enhancements

### Planned Features

1. **Agent Discovery**: Dynamic agent registration and discovery
2. **Monitoring**: Built-in metrics and observability
3. **Caching**: Result caching for expensive operations
4. **Persistence**: State persistence and recovery
5. **Distributed Execution**: Multi-process/multi-machine support
6. **Streaming**: Real-time streaming responses
7. **Additional LLM Providers**: Cohere, Hugging Face, etc.

## Conclusion

This architecture balances simplicity with power, providing a clean foundation for building sophisticated multi-agent systems while remaining accessible to developers of all skill levels. The TypedDict-based state management provides excellent performance and LangGraph compatibility, while the LLM factory pattern enables flexible model selection across agents.