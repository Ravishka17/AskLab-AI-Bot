# GPT-OSS 120B Cacheable Property Fix

## Issue
```
⚠️ API Error: Error code: 400 - {'error': {'message': "'messages.0' : for 'role:system' the following must be satisfied[('messages.0' : property 'cacheable' is unsupported)]", 'type': 'invalid_request_error'}}
```

## Root Cause
The `openai/gpt-oss-120b` model does not support the `cacheable` property on system messages, which was being set in the API parameters.

## Fix Applied
Removed the `cacheable` property assignment from the GPT-OSS model configuration in `app.py`:

### Before (Line 1010-1012)
```python
# Enable prompt caching for better performance
if len(messages) > 1 and messages[0].get("role") == "system":
    messages[0]["cacheable"] = True
```

### After (Line 1010)
```python
# Note: cacheable property is not supported by openai/gpt-oss-120b
```

## Model Configuration
The GPT-OSS 120B model now uses:
- ✅ `reasoning_format = "parsed"`
- ✅ `include_reasoning = True`
- ✅ Built-in Groq tools
- ❌ ~~`cacheable` property~~ (removed)

## Testing
Test the fix with:
```bash
# In Discord
/ask What is the capital of France? model:GPT-OSS 120B
```

Expected: No 400 error, proper reasoning display, and successful completion.

## Impact
- No performance degradation expected (caching was just an optimization)
- All other GPT-OSS features remain functional
- Backward compatible with existing conversations
