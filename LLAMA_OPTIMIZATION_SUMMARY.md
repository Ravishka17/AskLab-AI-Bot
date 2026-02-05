# Llama 3.3 70B Aggressive Optimization Summary

## Issue
llama-3.3-70b-versatile was hitting the 30 iteration maximum repeatedly, showing "⚠️ Reasoning exceeded maximum iterations" errors.

## Root Cause
Llama's "ONE ACTION PER RESPONSE" constraint (thinking OR tool call, never both) doubles iteration count compared to Kimi. Previous fixes weren't aggressive enough.

## Aggressive Optimizations Applied

### 1. Hard Iteration Limit: 30 → 18
```python
max_iterations = 18 if is_llama else 30
```

### 2. Thinking Limit: 300 chars → 80 chars
```python
"- ALL thinking MUST be under 80 chars (bullet points only!)\n"
max_body_length = 150 if is_llama else 500
```

### 3. Minimum Pages: 3 → 2
```python
min_pages = 2 if is_llama else 3
```

### 4. Tool Result Size: 1200 → 800 chars
```python
max_tool_result = 800 if is_llama else 1800
```

### 5. Context Trimming: Earlier & More Aggressive
```python
# Starts at iteration 4 (vs 6)
# Emergency mode at iteration 12 (vs 15)
optimization_threshold = 4 if is_llama else 10
```

### 6. Proactive Completion Detection
```python
# Forces completion after 12 iterations if 3+ tools used
if is_llama and iteration >= 12 and current_fact_count >= 3:
    return "sufficient_research"
```

### 7. Stricter Loop Detection
```python
# Detects stuck loops 2 iterations earlier
if iteration >= 6 and current_fact_count == self.last_fact_count:
    threshold = 4 if is_llama else 5
```

### 8. Compact System Prompt
```
### RESEARCH WORKFLOW (COMPACT - MAX 12 STEPS)
1. <think>Strategy (50 chars max)</think>
2. search_wikipedia
3. <think>Pick 2 best pages</think>
...
10. Answer with citations

- Complete within 15 iterations total
```

## Expected Behavior

### Before: 16-20+ iterations → Timeout
### After: 8-12 iterations → Success

**Typical Flow:**
1. Planning (1 iter)
2. Search (1 iter)
3. List pages (1 iter)
4. Read page 1 (1 iter)
5. Facts (1 iter)
6. Read page 2 (1 iter)
7. Synthesize (1 iter)
8. Answer (1 iter)

**Total: 8 iterations** ✅

## Backward Compatibility
 All changes are Llama-specific using `is_llama` flag
 Kimi K2 Instruct unchanged (30 iterations, 3 pages, 600 chars)

## Testing
Test with: "Who is the current president of Sri Lanka?"
Expected: Completes in 8-12 iterations with 2-3 pages read
