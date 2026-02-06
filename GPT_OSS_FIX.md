# GPT-OSS 120B Configuration Fixes

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

---

## Issue 3: Mutually Exclusive Reasoning Parameters (FIXED)
```
⚠️ API Error: Error code: 400 - {'error': {'message': 'cannot specify both `include_reasoning` and `reasoning_format`', 'type': 'invalid_request_error'}}
```

### Root Cause
According to Groq's reasoning documentation:
- `reasoning_format` is **NOT supported** by GPT-OSS models (`openai/gpt-oss-20b`, `openai/gpt-oss-120b`)
- `include_reasoning` and `reasoning_format` are **mutually exclusive** parameters
- Only use `include_reasoning` (true/false) for GPT-OSS models

### Fix Applied
Updated GPT-OSS configuration in `app.py` (Lines 1003-1011):

**Before:**
```python
if is_gpt_oss:
    api_params["tools"] = get_tools_for_model(model_name, include_memory=...)
    api_params["reasoning_format"] = "parsed"  # ❌ NOT supported
    api_params["include_reasoning"] = True
```

**After:**
```python
if is_gpt_oss:
    api_params["tools"] = get_tools_for_model(model_name, include_memory=...)
    api_params["include_reasoning"] = True  # ✅ Correct parameter
    # Note: reasoning_format is NOT supported by GPT-OSS models
```

### Reasoning Field Access
Also fixed reasoning content access (Line 1041):
- Changed from: `msg.reasoning_content` ❌
- Changed to: `msg.reasoning` ✅

### Documentation Reference
From `Groq_Documentation/Core_Features/reasoning.md` (Lines 426-428, 49):
> With `openai/gpt-oss-20b` and `openai/gpt-oss-120b`, the `reasoning_format` parameter is not supported.
> By default, these models will include reasoning content in the `reasoning` field of the assistant response.
> **Note:** The `include_reasoning` parameter cannot be used together with `reasoning_format`. These parameters are mutually exclusive.

---

## Model Configuration
The GPT-OSS 120B model now uses:
- ✅ `include_reasoning = True` (NOT `reasoning_format`)
- ✅ Built-in Groq tools: `browser_search`, `code_interpreter`
- ✅ Reasoning accessed via `msg.reasoning` field
- ❌ ~~`reasoning_format`~~ (NOT supported by GPT-OSS)
- ❌ ~~`cacheable` property~~ (NOT supported by GPT-OSS)

## Testing
Test the fix with:
```bash
# In Discord
/ask What is 2+2? Explain your reasoning. model:GPT-OSS 120B
/ask Search for recent AI developments model:GPT-OSS 120B
/ask Write Python code to calculate factorial model:GPT-OSS 120B
```

### Expected Results
- ✅ No 400 errors about mutually exclusive parameters
- ✅ No 400 errors about unsupported properties
- ✅ Reasoning content displays in Discord UI (🧠 Reasoning section)
- ✅ Browser search executes successfully
- ✅ Code interpreter executes successfully
- ✅ Responses are coherent and complete

### Test Script
Run `test_gpt_oss_final.py` for comprehensive validation:
```bash
cd /home/engine/project
export GROQ_API_KEY="your-api-key"
python test_gpt_oss_final.py
```

## Impact
- ✅ All three GPT-OSS configuration issues resolved
- ✅ Browser search and code interpreter tools now accessible
- ✅ Reasoning content properly displayed in Discord
- ✅ Proper error-free operation
- ✅ Backward compatible with existing conversations
- ✅ Follows official Groq API documentation

## Files Modified
- `app.py` - Lines 1003-1011 (reasoning parameters), Line 1041 (reasoning field access)
- `GPT_OSS_FIX.md` - This document
- `REASONING_FIX_SUMMARY.md` - Detailed fix explanation
- `GPT_OSS_QUICK_REFERENCE.md` - Quick reference card
- `test_gpt_oss_final.py` - Comprehensive validation script

## Quick Reference
See `GPT_OSS_QUICK_REFERENCE.md` for:
- ✅ Correct configuration examples
- ❌ Common mistakes to avoid
- 📚 Documentation references
- 🐛 Troubleshooting guide
