# Browser Tool Display Fix

## Summary
Added immediate visual feedback for GPT-OSS browser tools (`browser.search` and `browser.open`) to show "Searching..." and "Reading..." indicators, matching the user experience of the Kimi K2 model.

## Changes Made

### 1. Immediate Display for browser.search
**Location:** `app.py` lines 1146-1204

**Before:**
- Only showed search results after they were available
- No immediate feedback when search started

**After:**
- Immediately displays: `🔍 **Searching...**` when tool call is detected
- Shows query being searched: `> Searching: <query>`
- Updates to `🔍 **Searched**` with results when available
- Lists top 5 search results with clickable links

**Code Flow:**
```python
# Step 1: Immediate display
display_sections.append(f"🔍 **Searching...**\n\n> {query_display}")
await update_ui()

# Step 2: Extract results (if available)
if search_urls:
    display_sections[-1] = f"🔍 **Searched**\n\n> {query_display}\n\n" + "\n".join(search_urls)
    await update_ui()
```

### 2. Immediate Display for browser.open
**Location:** `app.py` lines 1206-1242

**Before:**
- Only showed page info after it was loaded
- No immediate feedback when reading started

**After:**
- Immediately displays: `📖 **Reading...**` when tool call is detected
- Shows status: `> Opening webpage...`
- Updates to `📖 **Read Article**` with page title and URL when available
- Displays clickable link: `[Page Title](url)`

**Code Flow:**
```python
# Step 1: Immediate display
display_sections.append(f"📖 **Reading...**\n\n> Opening webpage...")
await update_ui()

# Step 2: Extract page info (if available)
if page_url:
    display_sections[-1] = f"📖 **Read Article**\n\n> {page_url}"
    await update_ui()
```

### 3. Updated Past Tense Conversion
**Location:** `app.py` lines 436-448

Added conversions for new indicators:
- `**Searching...**` → `**Searched**`
- `**Reading...**` → `**Read Article**`

This ensures that when reasoning is complete, all active indicators are converted to past tense.

## User Experience Improvement

### Before
```
[User sees nothing until search completes]
🔍 **Web Search**
> Searching: current president of Sri Lanka 2026
- [Result 1](url)
- [Result 2](url)
```

### After
```
[Immediate feedback]
🔍 **Searching...**
> Searching: current president of Sri Lanka 2026

[Updates to]
🔍 **Searched**
> Searching: current president of Sri Lanka 2026
- [Result 1](url)
- [Result 2](url)
```

## Tool Type Mapping

The fix handles multiple tool type representations:

| Tool Call Type | Function Name | Display |
|---------------|---------------|---------|
| `browser_search` | N/A | 🔍 **Searching...** |
| `browser.search` | N/A | 🔍 **Searching...** |
| `function` | `browser.search` | 🔍 **Searching...** |
| `browser.open` | N/A | 📖 **Reading...** |
| `function` | `browser.open` | 📖 **Reading...** |

## Testing

Test script: `test_searching_display.py`

Verifies:
1. Past tense conversion works correctly
2. Display flow shows proper sequence
3. All tool types are handled

## Impact

- ✅ Matches Kimi K2 UX consistency
- ✅ Provides immediate user feedback
- ✅ Shows research progress in real-time
- ✅ Maintains backward compatibility
- ✅ Works with all GPT-OSS tool formats

## Example Scenario

**User asks:** "Who is the current president of Sri Lanka in 2026?"

**Display sequence:**
1. 🧠 **Reasoning** - AI thinks about approach
2. 🔍 **Searching...** - Searching: current president of Sri Lanka 2026
3. 🔍 **Searched** - Shows top 5 results with links
4. 📖 **Reading...** - Opening webpage...
5. 📖 **Read Article** - [Article Title](url)
6. [Final answer with citations]

**After completion (past tense):**
1. 🧠 **Reasoning** - [thought content]
2. 🔍 **Searched** - Searching: current president of Sri Lanka 2026
3. 📖 **Read Article** - [Article Title](url)

## Related Files
- `app.py` - Main implementation
- `test_searching_display.py` - Test script
- `BROWSER_TOOL_DISPLAY_FIX.md` - This documentation
