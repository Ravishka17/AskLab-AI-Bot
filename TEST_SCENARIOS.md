# Test Scenarios for Context Management

## Automated Tests

### Unit Tests (test_context_simple.py)

Run: `python3 test_context_simple.py`

**Tests:**
1. ✅ Repeated planning detection - 3+ thoughts without tools triggers
2. ✅ Theme loop detection - 3+ same themes triggers
3. ✅ Tool calls reset counters - action taken clears loop state
4. ✅ Theme extraction - semantic categorization works
5. ✅ Consecutive thought tracking - counter increments correctly

**Expected:** All tests pass

## Manual Integration Tests

### Test 1: Simple Conversation (No Research)

**Input:** "@bot How are you?"

**Expected Behavior:**
- No tools called
- Direct response
- No context management kicks in (iteration stays at 0-1)
- No loop detection alerts

**Success Criteria:**
- Response is friendly and natural
- No research UI shown
- No Wikipedia tool calls

---

### Test 2: Basic Research Query

**Input:** "@bot Who is the president of Sri Lanka?"

**Expected Behavior:**
1. Iteration 1: Planning thought
2. Iteration 2: search_wikipedia("Sri Lanka president")
3. Iteration 3: List pages thought
4. Iteration 4: get_wikipedia_page("Anura Kumara Dissanayake")
5. Iteration 5+: Read more pages, synthesize
6. Final: Answer with citations

**Success Criteria:**
- Completes in under 15 iterations
- Reads 3+ pages
- No loop detection alerts
- Provides answer with Wikipedia citations
- No planning loops

**Console output should NOT show:**
- ❌ "Loop detected"
- ❌ "Context optimized" (if completes before iteration 10)

---

### Test 3: Repeated Research Pattern

**Input sequence:**
1. "@bot Who is the president of Sri Lanka?"
2. (Wait for response)
3. "@bot Tell me about yourself"
4. (Wait for response)
5. "@bot Who is the president of Sri Lanka?" (SAME QUERY)

**Expected Behavior:**

**Query 1:**
- Normal research flow
- Success in ~7-10 iterations

**Query 2 (personal):**
- No tools
- Direct conversational response
- Fast (1-2 iterations)

**Query 3 (repeated research):**
- Normal research flow again
- NO planning loops (this was the bug!)
- Success in ~7-10 iterations
- Context manager starts fresh

**Success Criteria:**
- Query 3 does NOT get stuck planning
- Query 3 completes successfully
- No "theme_loop" or "repeated_planning" alerts for Query 3 early iterations
- All three queries succeed

---

### Test 4: Context Limit Stress Test

**Input:** "@bot Who is the president of Sri Lanka? Provide extensive details about their background, political career, education, family, achievements, and policies."

**Expected Behavior:**
1. Iterations 1-9: Normal research (full context)
2. Iteration 10: Moderate trim activates
   - Console: `📊 Context optimized at iteration 10: ~5000 chars`
3. Iteration 15: Aggressive trim activates
   - Console: `📊 Context optimized at iteration 15: ~3000 chars`
4. If reaches iteration 20: Emergency mode
   - Console: `📊 Context optimized at iteration 20: ~2000 chars`
   - Emergency urgency injected

**Success Criteria:**
- Never exceeds Groq context limit
- System prompt always visible (check logs)
- Provides answer eventually
- Progress markers visible: `[PROGRESS: Iteration X/30 | Y tools used | Z pages read]`

---

### Test 5: Stuck Planning Loop (Intentional)

**Note:** This test verifies loop detection works. The AI should NOT get stuck, but if it tries, the system should catch it.

**Scenario:** If the AI (for some reason) starts planning repeatedly without taking action:

**Expected Behavior:**
```
Iteration N: <think>Planning...</think>
Iteration N+1: <think>I need to plan...</think>
Iteration N+2: <think>Let me plan...</think>
→ Console: 🚨 Loop detected: theme_loop at iteration N+2
→ System injects: "ERROR: You're repeating yourself. Take action immediately."
Iteration N+3: search_wikipedia(...) or final answer
```

**Success Criteria:**
- Loop detected within 3 iterations of pattern
- Urgency message injected
- AI takes action or provides answer on next iteration
- Research completes successfully

**To test manually:** This should rarely happen with the new system, but if you notice repeated thinking without tools, check console for loop detection.

---

### Test 6: Mixed Query Types

**Input sequence:**
1. "@bot Hello!"
2. "@bot Who discovered penicillin?"
3. "@bot Thanks!"
4. "@bot What is quantum computing?"
5. "@bot What's your favorite color?"

**Expected Behavior:**
- Query 1: Conversational (no tools)
- Query 2: Research (tools)
- Query 3: Conversational (no tools)
- Query 4: Research (tools)
- Query 5: Conversational (no tools)

**Success Criteria:**
- Each query type handled appropriately
- No context pollution between queries
- Research queries complete successfully
- Conversation history kept to last 6 messages (lines 961-962)

---

### Test 7: Progress Visibility

**Input:** "@bot Who is the president of Brazil?"

**What to check:**
1. Start research
2. At iteration 5+, check reasoning embed in Discord
3. System should inject progress markers internally

**Expected internal state (won't see in Discord, but in logs):**
```
Iteration 5: System prompt includes: [PROGRESS: Iteration 5/30 | 2 tools used | 1 pages read]
Iteration 10: System prompt includes: [PROGRESS: Iteration 10/30 | 4 tools used | 2 pages read]
```

**Success Criteria:**
- AI aware of iteration count
- AI aware of tools used
- AI aware of pages read
- Creates natural urgency to complete

---

### Test 8: Error Recovery

**Input:** (Trigger context too large error by very long query)

**Expected Behavior:**
1. Groq API returns 413 or "too large" error
2. Code catches at lines 911-915
3. Console: `⚠️ Context too large. Using emergency mode...`
4. Emergency mode forces: `context_mgr.build_optimized_messages(messages, 25)`
5. Retry succeeds with minimal context

**Success Criteria:**
- No crash
- Error handled gracefully
- Research completes with emergency context
- User gets answer

---

## Performance Benchmarks

### Expected Iteration Counts

| Query Type | Expected Iterations | Max Acceptable |
|------------|-------------------|----------------|
| Simple conversation | 1-2 | 3 |
| Basic research (1 topic) | 7-12 | 15 |
| Complex research (multiple topics) | 15-20 | 25 |
| Edge case (challenging) | 20-25 | 28 |

### Expected Behavior By Iteration

| Iteration Range | Context State | Expected Behavior |
|----------------|---------------|-------------------|
| 0-9 | Full | Normal research flow |
| 10-14 | Moderate trim | Some thinking dropped |
| 15-19 | Aggressive trim | Only facts + urgency |
| 20+ | Emergency | Minimal context + force completion |

---

## Console Output to Monitor

### Good Signs ✅
```
✅ Bot Online: AskLabBot
✅ Supermemory: ✅ Connected
✅ Synced 2 command(s)
```

### Loop Detection (Working as designed) ⚠️
```
🚨 Loop detected: theme_loop at iteration 5
📊 Context optimized at iteration 10: 4523 chars
```

### Bad Signs (Should NOT see) ❌
```
❌ API Error: context_length_exceeded
❌ Reasoning exceeded maximum iterations (30+)
❌ Multiple consecutive "Loop detected" with no resolution
```

---

## Debugging Checks

If issues occur, verify:

1. **Context Manager initialized?**
   - Check line 834-838
   - Should see: `context_mgr = ContextManager(...)`

2. **Loop detection active?**
   - Check lines 882-888
   - Should call `detect_stuck_loop()` before API

3. **Progressive trimming active?**
   - Check lines 891-893
   - Should call `build_optimized_messages()` at iteration 10+

4. **Thinking tracked?**
   - Check line 927
   - Should call `context_mgr.add_thinking()`

5. **Tool results tracked?**
   - Check lines 1104-1107
   - Should call `context_mgr.add_tool_result()`

---

## Success Criteria Summary

✅ **Must pass:**
- Unit tests (test_context_simple.py) all pass
- Simple conversation works (Test 1)
- Basic research works (Test 2)
- Repeated query pattern works (Test 3) ← **This was the main bug**

✅ **Should pass:**
- Context limit handling (Test 4)
- Loop detection triggers if needed (Test 5)
- Mixed queries work (Test 6)

✅ **Nice to have:**
- Progress visibility working (Test 7)
- Error recovery graceful (Test 8)

---

## Rollback Triggers

Consider rollback if:
- Test 3 fails (repeated query gets stuck)
- Test 2 fails (basic research broken)
- Test 1 fails (conversations broken)
- Loop detection fires on every query
- Research never completes

Otherwise, individual test failures can be debugged and fixed incrementally.
