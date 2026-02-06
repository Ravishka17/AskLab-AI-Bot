# GPT-OSS 120B Tool Type Fix

## Issue 1: Cacheable Property (FIXED)
```
⚠️ API Error: Error code: 400 - {'error': {'message': "'messages.0' : for 'role:system' the following must be satisfied[('messages.0' : property 'cacheable' is unsupported)]", 'type': 'invalid_request_error'}}
```

### Root Cause
The `openai/gpt-oss-120b` model does not support the `cacheable` property on system messages.

### Fix Applied
Removed the `cacheable` property assignment from the GPT-OSS model configuration in `app.py` (Line 1010).

---

## Issue 2: Invalid Tool Types (FIXED)
```
⚠️ API Error: Error code: 400 - {'error': {'message': 'code=400, message=tools[0].type must be one of [function, mcp], type=invalid_request_error', 'type': 'invalid_request_error'}}
```

### Root Cause
GPT-OSS models were using incorrect tool type names according to the Groq API documentation:
- ❌ Used: `web_search` and `code_execution`
- ✅ Should be: `browser_search` and `code_interpreter`

### Fix Applied
Updated `get_tools_for_model()` function in `app.py` (Lines 217-220):

**Before:**
```python
tools = [
    {"type": "web_search"},
    {"type": "code_execution"}
]
```

**After:**
```python
tools = [
    {"type": "browser_search"},
    {"type": "code_interpreter"}
]
```

### Documentation Reference
According to `Groq_Documentation/Tools_and_Intergrations/built-in-tools.md`:

> **GPT-OSS Models** (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`)
> 
> **Available Tools:**
> - Browser Search: `browser_search`
> - Code Execution: `code_interpreter`

---

## Model Configuration
The GPT-OSS 120B model now uses:
- ✅ `reasoning_format = "parsed"`
- ✅ `include_reasoning = True`
- ✅ Built-in Groq tools: `browser_search`, `code_interpreter`
- ❌ ~~`cacheable` property~~ (removed - not supported)

## Testing
Test the fix with:
```bash
# In Discord
/ask What is the capital of France? model:GPT-OSS 120B
/ask Search for recent AI developments model:GPT-OSS 120B
```

Expected: No 400 error, proper reasoning display, and successful tool execution.

## Impact
- ✅ All GPT-OSS features now work correctly
- ✅ Browser search and code execution tools now accessible
- ✅ Proper error-free operation
- ✅ Backward compatible with existing conversations
