# Creating Custom Agents

This guide walks through creating custom agents for the Agentic AI Framework.

## Agent Basics

### Minimal Agent Implementation

Every agent must:
1. Inherit from `BaseAgent`
2. Implement the `execute()` method
3. Accept a task dictionary
4. Return a result dictionary
```python
from src.agents.base import BaseAgent, AgentConfig
from typing import Dict, Any

class MinimalAgent(BaseAgent):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Your logic here
        return {"status": "completed"}
```

### Agent Configuration

Configure your agent with `AgentConfig`:
```python
config = AgentConfig(
    name="my_agent",
    description="What this agent does",
    max_retries=3,
    timeout=30
)

agent = MinimalAgent(config)
```

## Task Structure

### Input Format

Tasks must have this structure:
```python
task = {
    "type": "task_type",      # Required: task identifier
    "data": {                 # Required: task-specific data
        "key1": "value1",
        "key2": "value2"
    }
}
```

### Output Format

Return a dictionary with your results:
```python
return {
    "result": "some value",
    "metadata": {"key": "value"},
    "status": "completed"
}
```

The framework wraps this in a standard response:
```python
{
    "success": True,
    "result": {...},          # Your return value
    "agent": "agent_name"
}
```

## Advanced Features

### Custom Validation

Override `validate_task()` for custom validation:
```python
class ValidatingAgent(BaseAgent):
    def validate_task(self, task: Dict[str, Any]) -> bool:
        # Call parent validation
        if not super().validate_task(task):
            return False
        
        # Custom validation
        data = task.get("data", {})
        return "required_field" in data
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Task is already validated
        required_value = task["data"]["required_field"]
        return {"processed": required_value}
```

### Task Routing

Implement `can_handle()` for intelligent routing:
```python
class SpecializedAgent(BaseAgent):
    async def can_handle(self, task: Dict[str, Any]) -> bool:
        # Only handle specific task types
        return task.get("type") == "specialized_task"
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Handle specialized tasks
        return {"result": "specialized processing"}
```

### Stateful Agents

Maintain state across executions:
```python
class StatefulAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.execution_count = 0
        self.cache = {}
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.execution_count += 1
        
        # Use cache
        cache_key = task.get("data", {}).get("key")
        if cache_key in self.cache:
            return {"cached": True, "value": self.cache[cache_key]}
        
        # Process and cache
        result = self.process(task)
        self.cache[cache_key] = result
        
        return {
            "cached": False,
            "value": result,
            "total_executions": self.execution_count
        }
    
    def process(self, task: Dict[str, Any]):
        # Your processing logic
        return task.get("data", {})
```

### Error Handling

Custom error handling and recovery:
```python
from src.utils.logger import get_logger

class RobustAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self.risky_operation(task)
            return {"success": True, "result": result}
        
        except SpecificError as e:
            # Handle specific errors
            self.logger.warning(f"Specific error: {e}")
            return {"success": False, "error": str(e), "recoverable": True}
        
        except Exception as e:
            # Log and re-raise for framework handling
            self.logger.error(f"Unexpected error: {e}")
            raise
    
    async def risky_operation(self, task: Dict[str, Any]):
        # Operation that might fail
        pass
```

## Real-World Examples

### Database Query Agent
```python
class DatabaseAgent(BaseAgent):
    def __init__(self, config: AgentConfig, db_connection):
        super().__init__(config)
        self.db = db_connection
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query_type = task["data"].get("query_type")
        params = task["data"].get("params", {})
        
        if query_type == "select":
            results = await self.db.fetch(params["table"], params["filters"])
            return {"rows": results, "count": len(results)}
        
        elif query_type == "insert":
            row_id = await self.db.insert(params["table"], params["data"])
            return {"inserted_id": row_id}
        
        else:
            return {"error": f"Unknown query type: {query_type}"}
```

### API Integration Agent
```python
import aiohttp

class APIAgent(BaseAgent):
    def __init__(self, config: AgentConfig, api_key: str):
        super().__init__(config)
        self.api_key = api_key
        self.base_url = "https://api.example.com"
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = task["data"].get("endpoint")
        method = task["data"].get("method", "GET")
        payload = task["data"].get("payload", {})
        
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
                    return {"status": response.status, "data": data}
            
            elif method == "POST":
                async with session.post(url, headers=headers, json=payload) as response:
                    data = await response.json()
                    return {"status": response.status, "data": data}
```

### Text Processing Agent
```python
class TextProcessorAgent(BaseAgent):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        text = task["data"].get("text", "")
        operation = task["data"].get("operation", "analyze")
        
        if operation == "analyze":
            return self.analyze_text(text)
        
        elif operation == "summarize":
            return await self.summarize_text(text)
        
        elif operation == "translate":
            target_lang = task["data"].get("target_language", "en")
            return await self.translate_text(text, target_lang)
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        words = text.split()
        return {
            "word_count": len(words),
            "char_count": len(text),
            "sentence_count": text.count('.') + text.count('!') + text.count('?'),
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0
        }
    
    async def summarize_text(self, text: str) -> Dict[str, Any]:
        # Integration with LLM for summarization
        # Simplified example
        return {"summary": text[:100] + "..."}
    
    async def translate_text(self, text: str, target: str) -> Dict[str, Any]:
        # Integration with translation service
        return {"translated": text, "target_language": target}
```

### LLM-Powered Agent

Integrate language models using the built-in factory:
```python
from src.utils import get_llm

class LLMAgent(BaseAgent):
    """Agent that uses LLM for processing."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        # Uses provider from .env by default
        self.llm = get_llm(temperature=0.7)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using LLM."""
        prompt = task.get("data", {}).get("prompt", "")
        
        # Invoke LLM
        response = await self.llm.ainvoke(prompt)
        
        return {
            "response": response.content if hasattr(response, 'content') else str(response),
            "prompt": prompt
        }


class MultiModelAgent(BaseAgent):
    """Agent using different models for different tasks."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        # Fast model for simple tasks
        self.fast_llm = get_llm(model="gpt-3.5-turbo", temperature=0.3)
        # Powerful model for complex tasks
        self.smart_llm = get_llm(model="gpt-4", temperature=0.7)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate model based on complexity."""
        prompt = task.get("data", {}).get("prompt", "")
        complexity = task.get("data", {}).get("complexity", "simple")
        
        llm = self.smart_llm if complexity == "complex" else self.fast_llm
        response = await llm.ainvoke(prompt)
        
        return {
            "response": response.content,
            "model_used": "gpt-4" if complexity == "complex" else "gpt-3.5-turbo"
        }


class CrossProviderAgent(BaseAgent):
    """Agent using different LLM providers."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.openai_llm = get_llm(provider="openai", model="gpt-4")
        self.anthropic_llm = get_llm(provider="anthropic", model="claude-3-5-sonnet-20241022")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Use different providers for different task types."""
        task_type = task.get("data", {}).get("task_type", "general")
        prompt = task.get("data", {}).get("prompt", "")
        
        if task_type == "coding":
            # Use Claude for coding tasks
            response = await self.anthropic_llm.ainvoke(prompt)
            provider = "anthropic"
        else:
            # Use GPT-4 for general tasks
            response = await self.openai_llm.ainvoke(prompt)
            provider = "openai"
        
        return {
            "response": response.content,
            "provider": provider
        }
```

**Configuration**: LLM providers are configured in `.env`:
```bash
# Default provider
LLM_PROVIDER=ollama

# Provider-specific settings
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

See `examples/llm_agent.py` for a complete working example.

## Best Practices

### 1. Single Responsibility

Each agent should do one thing well:
```python
# Good: Focused agent
class EmailSenderAgent(BaseAgent):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Only sends emails
        pass

# Bad: Too many responsibilities
class CommunicationAgent(BaseAgent):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Sends emails, SMS, push notifications, etc.
        pass
```

### 2. Clear Interfaces

Use clear, documented task structures:
```python
class WellDocumentedAgent(BaseAgent):
    """
    Processes customer orders.
    
    Task Structure:
        {
            "type": "process_order",
            "data": {
                "order_id": str,
                "customer_id": str,
                "items": List[Dict],
                "total": float
            }
        }
    
    Returns:
        {
            "order_status": str,
            "confirmation_id": str,
            "estimated_delivery": str
        }
    """
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        pass
```

### 3. Logging

Use the framework logger:
```python
from src.utils.logger import get_logger

class LoggingAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Processing task: {task['type']}")
        
        try:
            result = self.process(task)
            self.logger.info("Task completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Task failed: {e}")
            raise
    
    def process(self, task: Dict[str, Any]):
        # Your processing logic
        return {"status": "completed"}
```

### 4. Testability

Design for easy testing:
```python
class TestableAgent(BaseAgent):
    def __init__(self, config: AgentConfig, dependency=None):
        super().__init__(config)
        # Accept dependencies for easy mocking
        self.dependency = dependency or RealDependency()
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Logic can be tested with mock dependencies
        data = await self.dependency.fetch_data()
        return {"result": self.process_data(data)}
    
    def process_data(self, data):
        # Pure function - easy to unit test
        return data.upper()
```

## Testing Your Agent

### Unit Test Example
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_my_agent():
    config = AgentConfig(
        name="test_agent",
        description="Test"
    )
    
    agent = MyAgent(config)
    
    task = {
        "type": "test",
        "data": {"input": "test value"}
    }
    
    result = await agent.process(task)
    
    assert result["success"] == True
    assert "result" in result
    assert result["agent"] == "test_agent"
```

### Testing LLM Agents
```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_llm_agent():
    config = AgentConfig(name="llm_test", description="Test")
    
    # Mock the LLM
    with patch('src.utils.llm_factory.get_llm') as mock_get_llm:
        mock_llm = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = "Mocked response"
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        agent = LLMAgent(config)
        
        task = {
            "type": "query",
            "data": {"prompt": "Test prompt"}
        }
        
        result = await agent.process(task)
        
        assert result["success"] == True
        assert result["result"]["response"] == "Mocked response"
        mock_llm.ainvoke.assert_called_once_with("Test prompt")
```

## Next Steps

- Read [Workflow Patterns](workflow-patterns.md) to learn about coordinating multiple agents
- Check [Architecture Overview](architecture.md) for design principles
- Explore `examples/` for more complete examples