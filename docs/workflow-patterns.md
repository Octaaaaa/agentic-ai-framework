# Workflow Patterns

This guide covers common patterns for building multi-agent workflows using the Agentic AI Framework.

## Workflow Basics

Workflows coordinate multiple agents to accomplish complex tasks. They use LangGraph for state management and conditional routing.

### Important: State Management

**AgentState is a TypedDict**, not a Pydantic model. Workflow nodes must:
1. Accept `AgentState` as input parameter
2. Return a **dictionary** with partial state updates (not full state)
3. Access state using dict syntax: `state["field"]`
4. Never mutate state directly

### Basic Workflow Structure
```python
from src.graph.workflow import AgentWorkflow
from src.graph.state import AgentState
from langgraph.graph import END

# Create workflow
workflow = AgentWorkflow()

# Define nodes - MUST return dict of updates
async def step1_node(state: AgentState) -> dict:
    # Your logic here
    return {
        "results": {**state["results"], "step1": {"done": True}},
        "current_agent": "step1"
    }

async def step2_node(state: AgentState) -> dict:
    # Your logic here
    return {
        "results": {**state["results"], "step2": {"done": True}},
        "current_agent": "step2"
    }

# Add nodes
workflow.add_node("step1", step1_node)
workflow.add_node("step2", step2_node)

# Define flow
workflow.set_entry_point("step1")
workflow.add_edge("step1", "step2")
workflow.add_edge("step2", END)

# Compile
workflow.compile()

# Execute
initial_state: AgentState = {
    "messages": [],
    "current_agent": None,
    "task_queue": [{"type": "test", "data": {}}],
    "results": {},
    "metadata": {},
    "error": None
}

final_state = await workflow.execute(initial_state)
```

## Common Patterns

### 1. Sequential Processing

Process data through multiple agents in sequence.
```python
async def extractor_node(state: AgentState) -> dict:
    """Extract data from input."""
    if state["task_queue"]:
        task = state["task_queue"][0]
        
        extractor = DataExtractorAgent(AgentConfig(
            name="extractor",
            description="Extracts structured data"
        ))
        
        result = await extractor.process(task)
        
        return {
            "results": {**state["results"], "extractor": result},
            "current_agent": "extractor"
        }
    return {}


async def validator_node(state: AgentState) -> dict:
    """Validate extracted data."""
    extractor_result = state["results"].get("extractor")
    
    if extractor_result and extractor_result.get("success"):
        task = {
            "type": "validate",
            "data": extractor_result.get("result", {})
        }
        
        validator = DataValidatorAgent(AgentConfig(
            name="validator",
            description="Validates data integrity"
        ))
        
        result = await validator.process(task)
        
        return {
            "results": {**state["results"], "validator": result},
            "current_agent": "validator"
        }
    
    return {}


async def storage_node(state: AgentState) -> dict:
    """Store validated data."""
    validator_result = state["results"].get("validator")
    
    if validator_result and validator_result.get("success"):
        task = {
            "type": "store",
            "data": validator_result.get("result", {})
        }
        
        storage = StorageAgent(AgentConfig(
            name="storage",
            description="Stores data"
        ))
        
        result = await storage.process(task)
        
        return {
            "results": {**state["results"], "storage": result},
            "current_agent": "storage"
        }
    
    return {}


# Build workflow
workflow = AgentWorkflow()
workflow.add_node("extract", extractor_node)
workflow.add_node("validate", validator_node)
workflow.add_node("store", storage_node)

workflow.set_entry_point("extract")
workflow.add_edge("extract", "validate")
workflow.add_edge("validate", "store")
workflow.add_edge("store", END)

workflow.compile()
```

### 2. Conditional Routing

Route to different agents based on conditions.
```python
async def analyzer_node(state: AgentState) -> dict:
    """Analyze input and determine complexity."""
    if state["task_queue"]:
        task = state["task_queue"][0]
        
        analyzer = ComplexityAnalyzerAgent(AgentConfig(
            name="analyzer",
            description="Analyzes task complexity"
        ))
        
        result = await analyzer.process(task)
        
        # Store complexity in metadata for routing decision
        complexity = result.get("result", {}).get("complexity", "medium")
        
        return {
            "results": {**state["results"], "analyzer": result},
            "metadata": {**state["metadata"], "complexity": complexity},
            "current_agent": "analyzer"
        }
    return {}


def routing_decision(state: AgentState) -> str:
    """Decide which path to take based on analysis."""
    analyzer_result = state["results"].get("analyzer")
    
    if not analyzer_result or not analyzer_result.get("success"):
        return "error"
    
    complexity = state["metadata"].get("complexity", "medium")
    
    if complexity == "simple":
        return "simple_processor"
    elif complexity == "complex":
        return "complex_processor"
    else:
        return "standard_processor"


async def simple_processor_node(state: AgentState) -> dict:
    """Handle simple tasks."""
    analyzer_result = state["results"].get("analyzer")
    task = {
        "type": "simple",
        "data": analyzer_result.get("result", {})
    }
    
    processor = SimpleProcessorAgent(AgentConfig(
        name="simple_processor",
        description="Processes simple tasks"
    ))
    
    result = await processor.process(task)
    
    return {
        "results": {**state["results"], "processor": result},
        "current_agent": "simple_processor"
    }


async def standard_processor_node(state: AgentState) -> dict:
    """Handle standard tasks."""
    analyzer_result = state["results"].get("analyzer")
    task = {
        "type": "standard",
        "data": analyzer_result.get("result", {})
    }
    
    processor = StandardProcessorAgent(AgentConfig(
        name="standard_processor",
        description="Processes standard tasks"
    ))
    
    result = await processor.process(task)
    
    return {
        "results": {**state["results"], "processor": result},
        "current_agent": "standard_processor"
    }


async def complex_processor_node(state: AgentState) -> dict:
    """Handle complex tasks."""
    analyzer_result = state["results"].get("analyzer")
    task = {
        "type": "complex",
        "data": analyzer_result.get("result", {})
    }
    
    processor = ComplexProcessorAgent(AgentConfig(
        name="complex_processor",
        description="Processes complex tasks"
    ))
    
    result = await processor.process(task)
    
    return {
        "results": {**state["results"], "processor": result},
        "current_agent": "complex_processor"
    }


async def error_handler_node(state: AgentState) -> dict:
    """Handle errors."""
    return {
        "results": {
            **state["results"],
            "error_handler": {"success": True, "handled": True}
        },
        "error": None  # Clear error
    }


# Build workflow with conditional routing
workflow = AgentWorkflow()
workflow.add_node("analyzer", analyzer_node)
workflow.add_node("simple_processor", simple_processor_node)
workflow.add_node("standard_processor", standard_processor_node)
workflow.add_node("complex_processor", complex_processor_node)
workflow.add_node("error_handler", error_handler_node)

workflow.set_entry_point("analyzer")

workflow.add_conditional_edges(
    "analyzer",
    routing_decision,
    {
        "simple_processor": "simple_processor",
        "standard_processor": "standard_processor",
        "complex_processor": "complex_processor",
        "error": "error_handler"
    }
)

# All processors lead to end
workflow.add_edge("simple_processor", END)
workflow.add_edge("standard_processor", END)
workflow.add_edge("complex_processor", END)
workflow.add_edge("error_handler", END)

workflow.compile()
```

### 3. Iterative Processing

Loop until a condition is met.
```python
async def processor_node(state: AgentState) -> dict:
    """Process and increment iteration counter."""
    iteration = state["metadata"].get("iteration", 0)
    
    task = state["task_queue"][0] if state["task_queue"] else {}
    
    processor = IterativeProcessorAgent(AgentConfig(
        name="processor",
        description="Iterative processor"
    ))
    
    result = await processor.process(task)
    
    # Check convergence
    converged = result.get("result", {}).get("converged", False)
    
    return {
        "results": {**state["results"], f"iteration_{iteration}": result},
        "metadata": {
            **state["metadata"],
            "iteration": iteration + 1,
            "converged": converged
        },
        "current_agent": "processor"
    }


def should_continue(state: AgentState) -> str:
    """Check if we should continue iterating."""
    iteration = state["metadata"].get("iteration", 0)
    converged = state["metadata"].get("converged", False)
    
    # Stop if converged or reached max iterations
    if converged or iteration >= 10:
        return "end"
    
    return "continue"


# Build iterative workflow
workflow = AgentWorkflow()
workflow.add_node("processor", processor_node)

workflow.set_entry_point("processor")

workflow.add_conditional_edges(
    "processor",
    should_continue,
    {
        "continue": "processor",  # Loop back
        "end": END
    }
)

workflow.compile()
```

### 4. Parallel Processing with Aggregation

Process multiple subtasks and combine results.
```python
async def splitter_node(state: AgentState) -> dict:
    """Split work into parallel subtasks."""
    if state["task_queue"]:
        original_task = state["task_queue"][0]
        data = original_task.get("data", {})
        
        # Create subtasks for parallel processing
        subtasks = [
            {"type": "process_a", "data": data, "partition": "A"},
            {"type": "process_b", "data": data, "partition": "B"},
            {"type": "process_c", "data": data, "partition": "C"}
        ]
        
        return {
            "metadata": {**state["metadata"], "subtasks": subtasks},
            "current_agent": "splitter"
        }
    return {}


async def processor_a_node(state: AgentState) -> dict:
    """Process partition A."""
    subtasks = state["metadata"].get("subtasks", [])
    if subtasks:
        task_a = subtasks[0]
        
        agent = ProcessorAgentA(AgentConfig(
            name="processor_a",
            description="Processes partition A"
        ))
        
        result = await agent.process(task_a)
        
        return {
            "results": {**state["results"], "processor_a": result}
        }
    return {}


async def processor_b_node(state: AgentState) -> dict:
    """Process partition B."""
    subtasks = state["metadata"].get("subtasks", [])
    if len(subtasks) > 1:
        task_b = subtasks[1]
        
        agent = ProcessorAgentB(AgentConfig(
            name="processor_b",
            description="Processes partition B"
        ))
        
        result = await agent.process(task_b)
        
        return {
            "results": {**state["results"], "processor_b": result}
        }
    return {}


async def processor_c_node(state: AgentState) -> dict:
    """Process partition C."""
    subtasks = state["metadata"].get("subtasks", [])
    if len(subtasks) > 2:
        task_c = subtasks[2]
        
        agent = ProcessorAgentC(AgentConfig(
            name="processor_c",
            description="Processes partition C"
        ))
        
        result = await agent.process(task_c)
        
        return {
            "results": {**state["results"], "processor_c": result}
        }
    return {}


async def aggregator_node(state: AgentState) -> dict:
    """Aggregate results from parallel processors."""
    results_a = state["results"].get("processor_a", {})
    results_b = state["results"].get("processor_b", {})
    results_c = state["results"].get("processor_c", {})
    
    # Combine results
    aggregated = {
        "combined": True,
        "partitions": {
            "a": results_a.get("result") if results_a.get("success") else None,
            "b": results_b.get("result") if results_b.get("success") else None,
            "c": results_c.get("result") if results_c.get("success") else None
        },
        "summary": "All processors completed"
    }
    
    return {
        "results": {
            **state["results"],
            "aggregator": {"success": True, "result": aggregated}
        },
        "current_agent": "aggregator"
    }


# Build parallel workflow
# Note: True parallelism requires asyncio.gather in nodes
workflow = AgentWorkflow()
workflow.add_node("splitter", splitter_node)
workflow.add_node("processor_a", processor_a_node)
workflow.add_node("processor_b", processor_b_node)
workflow.add_node("processor_c", processor_c_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("splitter")

# Sequential execution (for simplicity)
workflow.add_edge("splitter", "processor_a")
workflow.add_edge("processor_a", "processor_b")
workflow.add_edge("processor_b", "processor_c")
workflow.add_edge("processor_c", "aggregator")
workflow.add_edge("aggregator", END)

workflow.compile()
```

**Note**: For true parallel execution, combine agents in a single node with `asyncio.gather`:
```python
async def parallel_processing_node(state: AgentState) -> dict:
    """Process all partitions in parallel."""
    subtasks = state["metadata"].get("subtasks", [])
    
    if not subtasks:
        return {}
    
    # Create agents
    agent_a = ProcessorAgentA(AgentConfig(name="processor_a", description="A"))
    agent_b = ProcessorAgentB(AgentConfig(name="processor_b", description="B"))
    agent_c = ProcessorAgentC(AgentConfig(name="processor_c", description="C"))
    
    # Execute in parallel
    results = await asyncio.gather(
        agent_a.process(subtasks[0]),
        agent_b.process(subtasks[1]),
        agent_c.process(subtasks[2])
    )
    
    return {
        "results": {
            **state["results"],
            "processor_a": results[0],
            "processor_b": results[1],
            "processor_c": results[2]
        }
    }
```

### 5. Error Recovery

Handle errors gracefully with fallback paths.
```python
async def risky_operation_node(state: AgentState) -> dict:
    """Attempt risky operation."""
    try:
        task = state["task_queue"][0] if state["task_queue"] else {}
        
        agent = RiskyAgent(AgentConfig(
            name="risky",
            description="Risky operation"
        ))
        
        result = await agent.process(task)
        
        return {
            "results": {**state["results"], "risky": result},
            "current_agent": "risky"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "current_agent": "risky_failed",
            "metadata": {**state["metadata"], "failure_reason": str(e)}
        }


async def fallback_node(state: AgentState) -> dict:
    """Fallback when primary fails."""
    task = state["task_queue"][0] if state["task_queue"] else {}
    
    agent = FallbackAgent(AgentConfig(
        name="fallback",
        description="Safe fallback"
    ))
    
    result = await agent.process(task)
    
    return {
        "results": {**state["results"], "fallback": result},
        "error": None,  # Clear error
        "current_agent": "fallback"
    }


async def error_logger_node(state: AgentState) -> dict:
    """Log error for monitoring."""
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    
    error_msg = state["error"]
    logger.error(f"Workflow error: {error_msg}")
    
    return {
        "results": {
            **state["results"],
            "error_logged": {"success": True, "error": error_msg}
        }
    }


def check_error(state: AgentState) -> str:
    """Route based on error state."""
    risky_result = state["results"].get("risky")
    
    if risky_result and risky_result.get("success"):
        return "success"
    else:
        return "fallback"


# Build error recovery workflow
workflow = AgentWorkflow()
workflow.add_node("risky_operation", risky_operation_node)
workflow.add_node("fallback", fallback_node)
workflow.add_node("error_logger", error_logger_node)

workflow.set_entry_point("risky_operation")

workflow.add_conditional_edges(
    "risky_operation",
    check_error,
    {
        "success": END,
        "fallback": "fallback"
    }
)

workflow.add_edge("fallback", "error_logger")
workflow.add_edge("error_logger", END)

workflow.compile()
```

## Best Practices

### 1. Keep Nodes Focused

Each node should have a single responsibility:
```python
# ✅ Good: Focused node
async def validate_input_node(state: AgentState) -> dict:
    """Only validates input."""
    task = state["task_queue"][0] if state["task_queue"] else {}
    
    is_valid = validate_task_data(task)
    
    return {
        "metadata": {**state["metadata"], "input_valid": is_valid}
    }

# ❌ Bad: Too much in one node
async def do_everything_node(state: AgentState) -> dict:
    """Validates, processes, and stores."""
    # Too many responsibilities - split into separate nodes
    pass
```

### 2. Use Metadata for Workflow State

Store workflow-specific data in metadata:
```python
async def tracking_node(state: AgentState) -> dict:
    """Track workflow progress."""
    import time
    
    current_step = state["metadata"].get("steps_completed", 0)
    start_time = state["metadata"].get("start_time", time.time())
    
    # Your processing logic here
    # ...
    
    return {
        "metadata": {
            **state["metadata"],
            "steps_completed": current_step + 1,
            "start_time": start_time,
            "last_update": time.time()
        }
    }
```

### 3. Handle Errors Gracefully

Always account for error scenarios:
```python
async def safe_node(state: AgentState) -> dict:
    """Safely process with error checking."""
    previous_result = state["results"].get("previous_agent")
    
    # Check if previous step succeeded
    if not previous_result or not previous_result.get("success"):
        return {
            "error": "Previous step failed",
            "results": {
                **state["results"],
                "current_node": {"success": False, "skipped": True}
            }
        }
    
    # Continue with processing
    task = {"type": "process", "data": previous_result.get("result", {})}
    agent = MyAgent(AgentConfig(name="my_agent", description="Processes data"))
    result = await agent.process(task)
    
    return {
        "results": {**state["results"], "current_node": result}
    }
```

### 4. Document Routing Logic

Make routing decisions clear:
```python
def routing_logic(state: AgentState) -> str:
    """
    Route based on data type.
    
    Routing Rules:
        - 'image_processor': for image data (type='image')
        - 'text_processor': for text data (type='text')
        - 'error': for unknown or missing types
    
    Args:
        state: Current workflow state
        
    Returns:
        Next node name as string
    """
    data_type = state["metadata"].get("data_type")
    
    if data_type == "image":
        return "image_processor"
    elif data_type == "text":
        return "text_processor"
    else:
        return "error"
```

### 5. Return Empty Dict When No Updates

If a node has nothing to update, return empty dict:
```python
async def conditional_node(state: AgentState) -> dict:
    """Only processes if condition is met."""
    should_process = state["metadata"].get("process_flag", False)
    
    if not should_process:
        return {}  # No updates needed
    
    # Process and return updates
    return {
        "results": {**state["results"], "processed": True}
    }
```

### 6. Use Spread Operator for Merging

Always use spread operator to merge dicts:
```python
# ✅ Good: Preserve existing data
return {
    "results": {**state["results"], "new_key": "value"},
    "metadata": {**state["metadata"], "counter": state["metadata"].get("counter", 0) + 1}
}

# ❌ Bad: Overwrites existing data
return {
    "results": {"new_key": "value"},  # Lost all previous results!
    "metadata": {"counter": 1}  # Lost all previous metadata!
}
```

## Testing Workflows

Test each path through your workflow:
```python
import pytest

@pytest.mark.asyncio
async def test_successful_path():
    """Test the happy path."""
    workflow = create_my_workflow()
    
    initial_state: AgentState = {
        "messages": [],
        "current_agent": None,
        "task_queue": [{"type": "test", "data": {"valid": True}}],
        "results": {},
        "metadata": {},
        "error": None
    }
    
    final_state = await workflow.execute(initial_state)
    
    assert final_state["results"]["final_agent"]["success"]
    assert final_state["error"] is None


@pytest.mark.asyncio
async def test_error_path():
    """Test error handling."""
    workflow = create_my_workflow()
    
    initial_state: AgentState = {
        "messages": [],
        "current_agent": None,
        "task_queue": [{"type": "test", "data": {"valid": False}}],
        "results": {},
        "metadata": {},
        "error": None
    }
    
    final_state = await workflow.execute(initial_state)
    
    # Check that error was handled
    assert final_state["results"].get("error_handler") is not None
    assert final_state["results"]["error_handler"]["handled"] is True


@pytest.mark.asyncio
async def test_conditional_routing():
    """Test that routing works correctly."""
    workflow = create_conditional_workflow()
    
    # Test simple path
    simple_state: AgentState = {
        "messages": [],
        "current_agent": None,
        "task_queue": [{"type": "test", "data": {"complexity": "simple"}}],
        "results": {},
        "metadata": {},
        "error": None
    }
    
    final_state = await workflow.execute(simple_state)
    assert "simple_processor" in final_state["results"]
    assert "complex_processor" not in final_state["results"]
```

## Complete Example: Customer Support Workflow
```python
async def classifier_node(state: AgentState) -> dict:
    """Classify customer inquiry."""
    task = state["task_queue"][0] if state["task_queue"] else {}
    
    classifier = InquiryClassifierAgent(AgentConfig(
        name="classifier",
        description="Classifies customer inquiries"
    ))
    
    result = await classifier.process(task)
    category = result.get("result", {}).get("category", "unknown")
    
    return {
        "results": {**state["results"], "classifier": result},
        "metadata": {**state["metadata"], "inquiry_category": category},
        "current_agent": "classifier"
    }


async def faq_handler_node(state: AgentState) -> dict:
    """Handle FAQ inquiries."""
    classifier_result = state["results"].get("classifier", {})
    task = {
        "type": "faq",
        "data": classifier_result.get("result", {})
    }
    
    faq_agent = FAQAgent(AgentConfig(
        name="faq",
        description="FAQ handler"
    ))
    
    result = await faq_agent.process(task)
    
    return {
        "results": {**state["results"], "faq": result},
        "current_agent": "faq"
    }


async def technical_support_node(state: AgentState) -> dict:
    """Handle technical support."""
    classifier_result = state["results"].get("classifier", {})
    task = {
        "type": "technical",
        "data": classifier_result.get("result", {})
    }
    
    tech_agent = TechnicalSupportAgent(AgentConfig(
        name="technical",
        description="Technical support"
    ))
    
    result = await tech_agent.process(task)
    
    return {
        "results": {**state["results"], "technical": result},
        "current_agent": "technical"
    }


async def escalation_node(state: AgentState) -> dict:
    """Escalate to human agent."""
    task = {
        "type": "escalate",
        "data": {
            "inquiry": state["task_queue"][0] if state["task_queue"] else {},
            "previous_results": state["results"]
        }
    }
    
    escalation_agent = EscalationAgent(AgentConfig(
        name="escalation",
        description="Escalates to human"
    ))
    
    result = await escalation_agent.process(task)
    
    return {
        "results": {**state["results"], "escalation": result},
        "current_agent": "escalation"
    }


def route_inquiry(state: AgentState) -> str:
    """
    Route based on classification.
    
    Routes:
        - 'faq': For frequently asked questions
        - 'technical': For technical support issues
        - 'escalation': For complex issues or classification failures
    """
    classifier_result = state["results"].get("classifier")
    
    if not classifier_result or not classifier_result.get("success"):
        return "escalation"
    
    category = state["metadata"].get("inquiry_category", "unknown")
    
    if category == "faq":
        return "faq"
    elif category == "technical":
        return "technical"
    else:
        return "escalation"


# Build support workflow
workflow = AgentWorkflow()
workflow.add_node("classifier", classifier_node)
workflow.add_node("faq", faq_handler_node)
workflow.add_node("technical", technical_support_node)
workflow.add_node("escalation", escalation_node)

workflow.set_entry_point("classifier")

workflow.add_conditional_edges(
    "classifier",
    route_inquiry,
    {
        "faq": "faq",
        "technical": "technical",
        "escalation": "escalation"
    }
)

workflow.add_edge("faq", END)
workflow.add_edge("technical", END)
workflow.add_edge("escalation", END)

workflow.compile()

# Execute
initial_state: AgentState = {
    "messages": [],
    "current_agent": None,
    "task_queue": [{
        "type": "inquiry",
        "data": {
            "customer_id": "12345",
            "message": "How do I reset my password?"
        }
    }],
    "results": {},
    "metadata": {},
    "error": None
}

final_state = await workflow.execute(initial_state)
print(f"Handled by: {final_state['current_agent']}")
print(f"Response: {final_state['results'][final_state['current_agent']]}")
```

## Next Steps

- Review [Creating Custom Agents](creating-agents.md) for agent implementation details
- Check [Architecture Overview](architecture.md) for design principles
- Explore `examples/multi_agent.py` for working examples