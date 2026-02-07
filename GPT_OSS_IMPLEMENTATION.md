# GPT-OSS 120B Implementation Guide

## Overview
This document describes the implementation of OpenAI GPT-OSS 120B as a replacement for Llama 3.3 70B, utilizing Groq's built-in reasoning, web search, and code execution capabilities.

## Key Changes

### 1. Model Replacement
- **Old**: `llama-3.3-70b-versatile`
- **New**: `openai/gpt-oss-120b`
- **UI Label**: "GPT-OSS 120B" with 🧠 emoji
- **Default Model**: Changed from Kimi K2 to GPT-OSS 120B

### 2. Built-in Tools Integration

#### GPT-OSS 120B Tools
```python
tools = [
    {"type": "web_search"},
    {"type": "code_execution"}
]
```

**Key Features:**
- `web_search`: Real-time web search for current information
- `code_execution`: Python code execution for calculations and analysis
- Tools are handled automatically by Groq's API
- No manual result processing required

#### Kimi K2 Tools (Unchanged)
- Custom `search_wikipedia` function
- Custom `get_wikipedia_page` function
- Manual result processing and formatting

### 3. Reasoning Format

#### GPT-OSS Reasoning
```python
api_params = {
    "reasoning_format": "parsed",
    "include_reasoning": True
}
```

**Features:**
- Reasoning separated into `message.reasoning_content` field
- No `<think>` tags in content
- Displayed in UI as: `🧠 **Reasoning**`
- Preserved in message history for context

#### Kimi K2 Reasoning (Unchanged)
- Uses `<think>` tags in content
- Manual extraction with `extract_reasoning()`
- Displayed as: `🧠 **Thought**`

### 4. Prompt Caching

**Implementation:**
```python
if len(messages) > 1 and messages[0].get("role") == "system":
    messages[0]["cacheable"] = True
```

**Benefits:**
- Faster response times for repeated queries
- Reduced latency on subsequent interactions
- Lower costs for cached system prompts

### 5. System Prompt

#### GPT-OSS System Prompt
```
You are AskLab AI, a research assistant. Current Date: January 2026.

### RESPONSE TYPES
1. **Simple conversations**: Respond directly without tools
2. **Research queries**: Use the research workflow

### BUILT-IN TOOLS
You have access to powerful built-in tools:
- **web_search**: Search the web for current information
- **code_execution**: Execute Python code for calculations and analysis

### RESEARCH WORKFLOW
1. For factual questions: Use web_search to find current information
2. For calculations: Use code_execution to run Python code
3. Synthesize findings into a clear answer with citations

### CRITICAL RULES
- Use web_search for factual, current information
- Use code_execution for math, data analysis, and computations
- Cite sources from web search results
- Provide clear, comprehensive answers
```

### 6. Tool Handling

#### Built-in Tools (GPT-OSS)
```python
if is_builtin_tool:
    # Display in UI
    if tool_type == "web_search":
        display_sections.append(f"🔍 **Web Search**\n\n> {query}")
    elif tool_type == "code_execution":
        display_sections.append(f"💻 **Code Execution**\n\n> Running Python code...")
    # No manual processing - Groq handles it
    continue
```

#### Custom Tools (Kimi K2)
```python
# Manual processing
if fn_name == "search_wikipedia":
    result = await search_wikipedia(query)
elif fn_name == "get_wikipedia_page":
    result = await get_wikipedia_page(title)

# Add result to messages
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "name": fn_name,
    "content": result
})
```

### 7. Model-Aware Logic

#### Iteration Limits
- **GPT-OSS**: 25 iterations
- **Kimi K2**: 30 iterations
- **Llama** (removed): 18 iterations

#### Minimum Page Requirements
- **GPT-OSS**: No minimum (uses web_search)
- **Kimi K2**: 3 pages minimum

#### Hallucination Checks
- **GPT-OSS**: Skipped (uses built-in tools)
- **Kimi K2**: Checks for hallucinated function calls

## Code Structure

### Tool Selection Function
```python
def get_tools_for_model(model_name, include_memory=False):
    if "gpt-oss" in model_name.lower():
        tools = [
            {"type": "web_search"},
            {"type": "code_execution"}
        ]
        # Add memory search if enabled
        if include_memory:
            tools.append({...})
        return tools
    
    # Kimi K2 tools
    base_tools = [...]
    return base_tools
```

### API Call Configuration
```python
if is_gpt_oss:
    api_params["tools"] = get_tools_for_model(model_name, ...)
    api_params["reasoning_format"] = "parsed"
    api_params["include_reasoning"] = True
    # Enable prompt caching
    if len(messages) > 1 and messages[0].get("role") == "system":
        messages[0]["cacheable"] = True
else:
    api_params["tools"] = get_tools_for_model(model_name, ...)
    api_params["tool_choice"] = "auto"
```

### Message Building
```python
assistant_msg = {
    "role": "assistant",
    "content": content
}

# Add reasoning content if present (for GPT-OSS)
if reasoning_content:
    assistant_msg["reasoning_content"] = reasoning_content

# Add tool calls
assistant_msg["tool_calls"] = [...]
```

## User Experience

### Model Selection
Users can switch between models using `/model` command:
- **GPT-OSS 120B** 🧠: Advanced reasoning with web search
- **Kimi K2 Instruct** 🌙: Precise reasoning

### UI Display

#### GPT-OSS Reasoning Flow
```
🧠 **Reasoning**
> [Reasoning content from model...]

🔍 **Web Search**
> Searching: quantum computing

💻 **Code Execution**
> Running Python code...

[Final Answer with citations]
```

#### Kimi K2 Reasoning Flow
```
🧠 **Thought**
> **Planning**
> Strategy for research...

🔍 **Searching Wikipedia...**
> quantum computing

📖 **Reading Article...**
- [Quantum computing](https://en.wikipedia.org/wiki/Quantum_computing)

[Final Answer with citations]
```

## Testing Checklist

- [ ] GPT-OSS web_search displays correctly
- [ ] GPT-OSS code_execution works
- [ ] Reasoning content displays in UI
- [ ] Prompt caching reduces latency
- [ ] Kimi K2 still works with Wikipedia tools
- [ ] Model switching works correctly
- [ ] Memory search works for both models
- [ ] Default model is GPT-OSS 120B
- [ ] Citations included in answers

## Configuration

### Environment Variables
No changes to existing environment variables:
- `DISCORD_BOT_TOKEN`: Discord bot token
- `GROQ_API_KEY`: Groq API key
- `SUPERMEMORY_API_KEY`: (Optional) Supermemory API key

### Available Models
```python
AVAILABLE_MODELS = {
    "GPT-OSS 120B": "openai/gpt-oss-120b",
    "Kimi K2 Instruct": "moonshotai/kimi-k2-instruct-0905"
}
```

## Documentation References

- [Groq Reasoning Documentation](https://console.groq.com/docs/reasoning.md)
- [Browser Search Tool](https://console.groq.com/docs/tool-use/built-in-tools/web-search.md)
- [Code Execution Tool](https://console.groq.com/docs/tool-use/built-in-tools/code-execution.md)
- [Prompt Caching](https://console.groq.com/docs/prompt-caching.md)

## Notes

1. **No Structured Outputs**: Browser search is not compatible with structured outputs (as per Groq docs)
2. **Automatic Tool Selection**: GPT-OSS intelligently decides when to use tools
3. **Performance**: Prompt caching significantly improves response times for repeated queries
4. **Compatibility**: Both models work with Supermemory memory search

## Future Enhancements

- Add more Groq built-in tools (Wolfram Alpha, Visit Website, Browser Automation)
- Implement better reasoning visualization
- Add statistics tracking for tool usage
- Support for more reasoning models (GPT-OSS 20B, Qwen 3 32B)
