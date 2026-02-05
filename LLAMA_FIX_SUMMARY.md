# Llama 3.3 70B Loop Detection & Context Management Fixes

## Issues Identified

The `llama-3.3-70b-versatile` model was experiencing:

1. **Loop Detection Errors**: "Loop Detected: no_progress" messages
2. **Context Size Issues**: "⚠️ Context too large. Using emergency mode..." warnings
3. **Max Iterations**: Hitting the maximum 30 iteration limit without completing

## Root Causes

### 1. Llama's Alternating Pattern
Unlike Kimi, Llama has a strict constraint: **ONE ACTION PER RESPONSE** (thinking OR tool call, NEVER BOTH).

This means:
- Iteration 1: `<think>Planning</think>` (thinking only)
- Iteration 2: `search_wikipedia()` (tool only)
- Iteration 3: `<think>List pages</think>` (thinking only)
- Iteration 4: `get_wikipedia_page()` (tool only)
- And so on...

This alternating pattern doubles the number of iterations needed compared to Kimi.

### 2. Aggressive Loop Detection
The loop detection logic was too strict for Llama's alternating pattern:
- **"no_progress" detection**: Triggered after 5 iterations without new tool results
- **Problem**: Llama alternates between thinking and tool calls, so 5 iterations = only 2-3 tool calls
- This caused false positives where the model was actually making progress

### 3. Context Accumulation
With double the iterations, context grew much faster:
- Each iteration adds assistant message (thinking) + tool result
- Llama's alternating pattern = more messages in the context
- Context trimming started too late (iteration 10+)

## Solutions Implemented

### 1. Model-Aware Loop Detection

```python
def detect_stuck_loop(self, iteration, is_llama=False):
    # Pattern 2: More lenient threshold for Llama
    threshold = 4 if is_llama else 3
    if self.consecutive_thoughts_without_tools >= threshold:
        return "repeated_planning"
    
    # Pattern 3: More lenient progress check
    if iteration >= 8 and current_fact_count == self.last_fact_count:
        threshold = 8 if is_llama else 5  # Allow more iterations
        if self.iterations_without_new_facts >= threshold:
            return "no_progress"
```

**Changes:**
- Llama gets 4 consecutive thoughts before triggering vs 3 for Kimi
- Progress check starts at iteration 8 instead of 5
- "no_progress" threshold: 8 iterations for Llama vs 5 for Kimi

### 2. Aggressive Context Trimming for Llama

```python
def should_trim_context(self, iteration, is_llama=False):
    if is_llama:
        if iteration >= 15: return "emergency"
        elif iteration >= 10: return "aggressive"
        elif iteration >= 6: return "moderate"
        else: return "light"
    else:
        if iteration >= 20: return "emergency"
        elif iteration >= 15: return "aggressive"
        elif iteration >= 10: return "moderate"
        else: return "none"
```

**Changes:**
- Llama starts trimming at iteration 6 (vs 10 for Kimi)
- New "light" mode: keeps only last 3 thinking blocks + all tool results
- Emergency mode at iteration 15 (vs 20 for Kimi)

### 3. Compact System Prompt for Llama

```python
"### CRITICAL RULES\n"
"- ONE ACTION PER RESPONSE: <think> OR tool call, NEVER BOTH\n"
"- Keep ALL thinking under 300 chars (compact!)\n"  # Reduced from 400
"- Minimum 3 pages before answering\n"
"- Use compact thinking - just key points\n"
```

**Changes:**
- Thinking limit reduced from 400 to 300 characters
- Emphasized compact thinking style
- Clearer instructions about the one-action rule

### 4. Truncated Content Sizes

```python
# Thinking blocks
max_body_length = 400 if is_llama else 500

# Tool results
max_tool_result = 1200 if is_llama else 1800
```

**Changes:**
- Thinking blocks: 400 chars for Llama (vs 500 for Kimi)
- Tool results: 1200 chars for Llama (vs 1800 for Kimi)

### 5. Proactive Context Size Monitoring

```python
context_size = len(str(messages))
if context_size > 25000:  # ~6250 tokens
    print(f"⚠️ Large context detected ({context_size} chars), forcing emergency mode")
    messages = context_mgr.build_optimized_messages(messages, 20, is_llama=is_llama)
```

**Changes:**
- Check context size before every API call
- Automatically trigger emergency mode if context > 25K chars
- Prevents hitting API limits

### 6. Enhanced Error Recovery

```python
elif "rate_limit" in error_msg.lower() or "413" in error_msg or "too large" in error_msg.lower():
    print(f"⚠️ Context too large error at iteration {iteration}")
    messages = context_mgr.build_optimized_messages(messages, 25, is_llama=is_llama)
    messages.append({
        "role": "user",
        "content": "CRITICAL: Context limit reached. Provide final answer NOW."
    })
    continue
```

**Changes:**
- Better error detection for context limit errors
- Force emergency mode + inject urgency message
- Continue instead of failing

## Expected Improvements

### For Llama 3.3 70B:

1. **No More False Loop Detections**: Alternating pattern is now properly handled
2. **Smaller Context Size**: Earlier and more aggressive trimming
3. **Faster Completion**: Compact prompts and truncated content reduce token usage
4. **Better Error Recovery**: Automatic emergency mode when context grows too large

### Comparison: Llama vs Kimi

| Aspect | Llama 3.3 70B | Kimi K2 Instruct |
|--------|---------------|------------------|
| **Thinking + Tool** | Never (strict separation) | Allowed |
| **Iterations Needed** | ~16-20 (alternating) | ~8-10 (combined) |
| **Context Trimming Start** | Iteration 6 (light) | Iteration 10 (moderate) |
| **Thinking Char Limit** | 300 | 600 |
| **Tool Result Limit** | 1200 | 1800 |
| **Loop Detection Threshold** | 4/8 iterations | 3/5 iterations |

## Testing Recommendations

Test with queries that require multiple Wikipedia pages:

```
Who is the current president of Sri Lanka?
What is quantum computing?
Explain the history of the Roman Empire.
```

Expected behavior:
- ✅ No "Loop Detected: no_progress" errors
- ✅ No "Context too large" warnings (or only 1-2 max)
- ✅ Completes within 20 iterations
- ✅ Provides answer with proper citations

## Monitoring

Watch for these log messages:
- `📊 Context optimized at iteration X: Y chars` - Shows trimming is working
- `⚠️ Large context detected (X chars), forcing emergency mode` - Proactive prevention
- `🚨 Loop detected: X at iteration Y` - Should be rare now

## Backward Compatibility

All changes are model-aware using the `is_llama` flag:
- Kimi K2 Instruct behavior unchanged
- Only Llama gets the optimized settings
- Both models work correctly with their respective patterns
