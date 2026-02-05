# Quick Reference: Llama vs Kimi Configuration

## Summary of Changes

Fixed loop detection and context size issues for `llama-3.3-70b-versatile` model while maintaining compatibility with `kimi-k2-instruct-0905`.

## Key Differences

### Loop Detection Thresholds

| Metric | Llama | Kimi | Reason |
|--------|-------|------|--------|
| **Consecutive Thoughts** | 4 | 3 | Llama alternates thinking/tools |
| **No Progress Start** | Iteration 8 | Iteration 5 | More time for alternating pattern |
| **No Progress Threshold** | 8 iterations | 5 iterations | Double the leniency |

### Context Trimming Thresholds

| Level | Llama Start | Kimi Start | Description |
|-------|-------------|------------|-------------|
| **Light** | Iteration 6 | N/A | Keep last 3 thinking blocks |
| **Moderate** | Iteration 6 | Iteration 10 | Drop old thinking blocks |
| **Aggressive** | Iteration 10 | Iteration 15 | Only tool results + user message |
| **Emergency** | Iteration 15 | Iteration 20 | Last 3 tool results only |

### Content Size Limits

| Content Type | Llama | Kimi | Impact |
|--------------|-------|------|--------|
| **Thinking Blocks** | 300 chars | 600 chars | 50% reduction |
| **Display Thinking** | 400 chars | 500 chars | 20% reduction |
| **Tool Results** | 1200 chars | 1800 chars | 33% reduction |

### System Prompt Differences

**Llama Prompt (Compact):**
```
- ONE ACTION PER RESPONSE: <think> OR tool call, NEVER BOTH
- Keep ALL thinking under 300 chars (compact!)
- Use compact thinking - just key points
```

**Kimi Prompt (Flexible):**
```
- List pages as: [Title](URL)
- Cite inline like [1](URL)
- Keep thinking under 600 chars
```

## Testing Commands

### Test Llama Model
```bash
# In Discord, set model to Llama 3.3 70B
/model
# Select: Llama 3.3 70B

# Test with complex query
@AskLabBot Who is the current president of Sri Lanka?
```

### Test Kimi Model
```bash
# In Discord, set model to Kimi K2
/model
# Select: Kimi K2 Instruct

# Test with same query
@AskLabBot Who is the current president of Sri Lanka?
```

## Expected Behavior

### Llama 3.3 70B (After Fix)
- ✅ No "Loop Detected: no_progress" errors
- ✅ Context trimming starts at iteration 6
- ✅ Completes within 15-18 iterations typically
- ✅ Compact thinking output (300 chars max)
- ✅ Handles context size proactively

### Kimi K2 Instruct (Unchanged)
- ✅ Can combine thinking + tool calls
- ✅ Context trimming starts at iteration 10
- ✅ Completes within 8-12 iterations typically
- ✅ More detailed thinking output (600 chars)
- ✅ Original behavior maintained

## Log Messages to Watch

### Good Signs
```
📊 Context optimized at iteration 6: 15234 chars  # Llama trimming starts
📊 Context optimized at iteration 10: 18234 chars # Kimi trimming starts
💾 Saving to memory for user 12345              # Memory working
✅ Reasoning Complete                            # Successful completion
```

### Warning Signs (Should be Rare Now)
```
⚠️ Large context detected (25500 chars)         # Proactive prevention
🚨 Loop detected: theme_loop at iteration 8     # Repeated planning
```

### Error Signs (Should NOT Appear)
```
❌ Loop Detected: no_progress                   # FIXED: Should not happen
⚠️ Context too large. Using emergency mode...  # FIXED: Should be rare
⚠️ Reasoning exceeded maximum iterations        # FIXED: Should complete earlier
```

## Rollback Instructions

If issues occur, revert the changes:

```bash
git checkout HEAD~1 app.py
```

Or manually set all `is_llama` parameters to `False` in:
- `detect_stuck_loop(iteration, is_llama=False)`
- `should_trim_context(iteration, is_llama=False)`
- `build_optimized_messages(messages, iteration, is_llama=False)`

## Files Modified

- `app.py` - Main bot logic with model-aware optimizations
- `LLAMA_FIX_SUMMARY.md` - Detailed explanation of changes
- `QUICK_REFERENCE.md` - This file

## Key Code Locations

```python
# Line 659: Loop detection with Llama awareness
def detect_stuck_loop(self, iteration, is_llama=False):

# Line 687: Context trimming with Llama awareness  
def should_trim_context(self, iteration, is_llama=False):

# Line 708: Message optimization with Llama awareness
def build_optimized_messages(self, current_messages, iteration, is_llama=False):

# Line 440: Compact system prompt for Llama
if "llama" in model_name.lower():
    return base_prompt + (
        "- Keep ALL thinking under 300 chars (compact!)\n"
        ...
    )

# Line 918: Loop detection call in main loop
stuck_type = context_mgr.detect_stuck_loop(iteration, is_llama=is_llama)

# Line 926: Context optimization call in main loop
if iteration >= optimization_threshold:
    messages = context_mgr.build_optimized_messages(messages, iteration, is_llama=is_llama)

# Line 933: Proactive context size check
if context_size > 25000:
    messages = context_mgr.build_optimized_messages(messages, 20, is_llama=is_llama)
```
