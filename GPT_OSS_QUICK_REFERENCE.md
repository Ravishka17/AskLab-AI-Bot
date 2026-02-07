# GPT-OSS Quick Reference Card

## ✅ Correct Configuration

### API Parameters
```python
{
    "model": "openai/gpt-oss-120b",  # or gpt-oss-20b
    "messages": [...],
    "tools": [
        {"type": "browser_search"},
        {"type": "code_interpreter"}
    ],
    "include_reasoning": True,  # ✅ Use this
    "max_tokens": 2000,
    "temperature": 0.7
}
# DO NOT include:
# - reasoning_format (not supported)
# - cacheable (not supported)
```

### Accessing Response
```python
msg = response.choices[0].message

# Content
content = msg.content

# Reasoning (when include_reasoning=True)
if hasattr(msg, 'reasoning') and msg.reasoning:
    reasoning = msg.reasoning  # ✅ Correct field

# Tool calls
tool_calls = msg.tool_calls
```

## ❌ Common Mistakes

### DO NOT Use These
```python
# ❌ WRONG - Not supported by GPT-OSS
api_params["reasoning_format"] = "parsed"

# ❌ WRONG - Mutually exclusive
api_params["reasoning_format"] = "parsed"
api_params["include_reasoning"] = True

# ❌ WRONG - Not supported
api_params["cacheable"] = True

# ❌ WRONG - Old tool names
tools = [
    {"type": "web_search"},      # Should be browser_search
    {"type": "code_execution"}   # Should be code_interpreter
]

# ❌ WRONG - Field name
reasoning = msg.reasoning_content  # Should be msg.reasoning
```

## 📚 Documentation References

- **Reasoning:** `Groq_Documentation/Core_Features/reasoning.md`
- **Browser Search:** `Groq_Documentation/Tools_and_Intergrations/browser-search-gpt-oss-models.md`
- **Built-in Tools:** `Groq_Documentation/Tools_and_Intergrations/built-in-tools.md`

## 🎯 Key Rules

1. **Reasoning Parameters:** Use `include_reasoning` only (NOT `reasoning_format`)
2. **Tool Names:** Use `browser_search` and `code_interpreter`
3. **Reasoning Field:** Access via `msg.reasoning` (NOT `msg.reasoning_content`)
4. **No Cacheable:** Don't use `cacheable` property
5. **Mutually Exclusive:** Never use both `reasoning_format` and `include_reasoning`

## 🔍 Model Compatibility

| Feature | GPT-OSS 20B/120B | Qwen 3 32B | Other Models |
|---------|------------------|------------|--------------|
| `reasoning_format` | ❌ No | ✅ Yes | ✅ Yes |
| `include_reasoning` | ✅ Yes | ❌ Or format | ❌ Or format |
| `browser_search` | ✅ Yes | ❌ No | ❌ No |
| `code_interpreter` | ✅ Yes | ❌ No | ❌ No |
| `cacheable` | ❌ No | ✅ Yes | ✅ Yes |

## 💡 Best Practices

### For GPT-OSS Models
```python
# Simple reasoning request
{
    "model": "openai/gpt-oss-120b",
    "messages": [{"role": "user", "content": "Explain quantum physics"}],
    "include_reasoning": True
}

# With tools
{
    "model": "openai/gpt-oss-120b",
    "messages": [{"role": "user", "content": "Search for latest AI news"}],
    "tools": [{"type": "browser_search"}],
    "include_reasoning": True,
    "tool_choice": "auto"
}

# Without reasoning
{
    "model": "openai/gpt-oss-120b",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "include_reasoning": False  # Or omit (defaults to True)
}
```

### Processing Response
```python
response = client.chat.completions.create(**params)
msg = response.choices[0].message

# Always check for reasoning
if hasattr(msg, 'reasoning') and msg.reasoning:
    print(f"Reasoning: {msg.reasoning}")

# Main content
print(f"Answer: {msg.content}")

# Tool calls
if msg.tool_calls:
    for tool_call in msg.tool_calls:
        print(f"Tool: {tool_call.function.name}")
```

## 🐛 Troubleshooting

| Error Message | Fix |
|---------------|-----|
| "cannot specify both `include_reasoning` and `reasoning_format`" | Remove `reasoning_format` parameter |
| "property 'cacheable' is unsupported" | Remove `cacheable` from system message |
| "tools[0].type must be one of [function, mcp]" | Change `web_search` → `browser_search` |
| AttributeError: 'Message' object has no attribute 'reasoning_content' | Use `msg.reasoning` instead |

## 📊 Testing Checklist

- [ ] No `reasoning_format` parameter used
- [ ] `include_reasoning` set to True/False
- [ ] Tools use `browser_search` and `code_interpreter`
- [ ] Reasoning accessed via `msg.reasoning`
- [ ] No `cacheable` property on messages
- [ ] API calls return 200 (no 400 errors)
- [ ] Reasoning content displays correctly
- [ ] Tools execute successfully
