# Deployment Checklist: GPT-OSS 120B Integration

## Pre-Deployment Verification

### Code Quality
- [x] Syntax validation passed
- [x] Import checks passed
- [x] Unit tests passed (all 7 tests)
- [x] No compilation errors
- [x] Model detection logic verified

### Functionality Tests
- [x] Model definitions correct
- [x] Tool configuration for GPT-OSS (web_search, code_execution)
- [x] Tool configuration for Kimi K2 (Wikipedia)
- [x] System prompts validated
- [x] Memory integration compatible
- [x] Backward compatibility maintained

### Configuration
- [x] Default model set to `openai/gpt-oss-120b`
- [x] Available models updated in UI
- [x] Model dropdown reflects changes
- [x] Environment variables unchanged

## Deployment Steps

### 1. Environment Setup
```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Verify environment variables
export DISCORD_BOT_TOKEN="your_token"
export GROQ_API_KEY="your_groq_key"
export SUPERMEMORY_API_KEY="your_supermemory_key"  # Optional
```

### 2. Verify Installation
```bash
# Run syntax check
python3 -m py_compile app.py

# Run tests
python3 test_gpt_oss.py
```

### 3. Start Bot
```bash
# Run the bot
python3 app.py

# Or use main.py
python3 main.py
```

## Post-Deployment Testing

### Manual Test Cases

#### Test 1: GPT-OSS Web Search
1. Mention bot: `@AskLabBot What are the latest developments in quantum computing?`
2. Expected behavior:
   - ✅ Shows reasoning: `🧠 **Reasoning**`
   - ✅ Shows web search: `🔍 **Web Search**`
   - ✅ Provides answer with citations
   - ✅ Completes within 25 iterations

#### Test 2: GPT-OSS Code Execution
1. Mention bot: `@AskLabBot Calculate the factorial of 100`
2. Expected behavior:
   - ✅ Shows reasoning: `🧠 **Reasoning**`
   - ✅ Shows code execution: `💻 **Code Execution**`
   - ✅ Provides calculated result
   - ✅ Shows Python code used

#### Test 3: Model Switching
1. Run: `/model`
2. Select "Kimi K2 Instruct"
3. Ask: `@AskLabBot Tell me about artificial intelligence`
4. Expected behavior:
   - ✅ Uses Wikipedia tools
   - ✅ Shows `🧠 **Thought**` (not Reasoning)
   - ✅ Shows `🔍 **Searching Wikipedia...**`
   - ✅ Shows `📖 **Reading Article...**`

#### Test 4: Memory Integration (if Supermemory enabled)
1. Ask: `@AskLabBot What is quantum entanglement?`
2. Later: `@AskLabBot What did we discuss about quantum?`
3. Expected behavior:
   - ✅ Uses `search_memory` tool
   - ✅ Retrieves past conversation
   - ✅ References previous discussion

#### Test 5: Simple Conversation
1. Ask: `@AskLabBot Hello, how are you?`
2. Expected behavior:
   - ✅ Responds directly without tools
   - ✅ No reasoning display
   - ✅ Quick response time

## Monitoring

### Key Metrics to Track
- [ ] Average response time per model
- [ ] Tool usage frequency (web_search vs code_execution)
- [ ] Error rates per model
- [ ] User model preferences
- [ ] Prompt cache hit rate

### Logging
Monitor console output for:
- `✅ Bot Online`
- `🧠 Supermemory: ✅ Connected` (if enabled)
- `✅ Synced X command(s)`
- API errors or rate limits
- Context optimization messages

## Rollback Plan

If issues occur, rollback by:
1. Stop the bot
2. Revert to previous version:
   ```bash
   git checkout <previous-commit>
   ```
3. Restart bot
4. Alternative: Switch default model back to Kimi K2:
   ```python
   # In app.py, change:
   selected_model = user_model_preferences.get(user_id, "moonshotai/kimi-k2-instruct-0905")
   ```

## Known Limitations

1. **Browser Search**: Not compatible with structured outputs (per Groq docs)
2. **Built-in Tools**: Automatically handled by Groq (no manual result processing)
3. **Iteration Limits**: GPT-OSS limited to 25 iterations (vs 30 for Kimi K2)
4. **Memory**: Custom tools (Wikipedia) not available for GPT-OSS

## Troubleshooting

### Issue: Tool not executing
**Symptoms**: No web_search or code_execution displayed
**Solutions**:
- Verify Groq API key is valid
- Check model name is exactly `openai/gpt-oss-120b`
- Ensure tools array correctly formatted

### Issue: Reasoning not displaying
**Symptoms**: No reasoning content in UI
**Solutions**:
- Verify `reasoning_format: "parsed"` is set
- Check `include_reasoning: true` is set
- Ensure `hasattr(msg, 'reasoning_content')` check works

### Issue: Context too large error
**Symptoms**: 413 or "too large" error
**Solutions**:
- Automatic: Emergency mode trimming activates
- Manual: Reduce iteration limit further
- Check: Progressive context optimization is working

### Issue: Model switch not working
**Symptoms**: Wrong model behavior after switch
**Solutions**:
- Verify `user_model_preferences` dict updates
- Check model name matches `AVAILABLE_MODELS`
- Restart conversation (clear history)

## Success Criteria

Deployment is successful when:
- [x] Bot starts without errors
- [ ] GPT-OSS responds to queries with web_search
- [ ] Code execution works for calculations
- [ ] Reasoning displays correctly
- [ ] Kimi K2 still works with Wikipedia tools
- [ ] Model switching works correctly
- [ ] Memory integration works (if enabled)
- [ ] No increase in error rates
- [ ] Response times acceptable

## Documentation

Reference documents:
1. `GPT_OSS_IMPLEMENTATION.md` - Complete implementation guide
2. `IMPLEMENTATION_SUMMARY_GPT_OSS.md` - Summary of changes
3. `test_gpt_oss.py` - Test suite
4. `DEPLOYMENT_CHECKLIST.md` - This checklist

## Support

If issues arise:
1. Check console logs for errors
2. Review `IMPLEMENTATION_SUMMARY_GPT_OSS.md`
3. Run test suite: `python3 test_gpt_oss.py`
4. Verify Groq API documentation for changes
5. Check Discord.py version compatibility

## Sign-off

- [ ] Code reviewed
- [ ] Tests passed
- [ ] Documentation complete
- [ ] Environment configured
- [ ] Rollback plan ready
- [ ] Monitoring setup complete
- [ ] Team notified

**Deployed by**: _____________  
**Date**: _____________  
**Version**: GPT-OSS 120B Integration v1.0
