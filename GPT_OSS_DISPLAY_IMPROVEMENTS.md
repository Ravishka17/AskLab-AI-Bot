# GPT-OSS Display Improvements

## Summary

Fixed the display issues for GPT-OSS (gpt-oss-120b) model reasoning and browser search functionality in the Discord bot. The AI now properly shows its thought process, embeds clickable URLs, and clarifies that it's searching the web (not just Wikipedia).

## Issues Fixed

### 1. **Reasoning Content Not Visible Enough**
- **Problem**: Reasoning was truncated to 500 characters, hiding most of the AI's thought process
- **Solution**: Increased display limit to 800 characters for GPT-OSS models
- **Impact**: Users can now see more of how the AI arrives at its answers

### 2. **Search Results Without Links**
- **Problem**: Browser search results showed search queries but no clickable URLs
- **Solution**: Added URL extraction from Groq's browser_search/browser.search tool outputs
- **Implementation**: Parses the special format `【0†Title†domain.com】` and creates Markdown links
- **Impact**: Users can now click on search result links directly in Discord

### 3. **Webpage Visits Not Displayed**
- **Problem**: When AI visited webpages (browser.open), users didn't see which pages were being read
- **Solution**: Added display for browser.open tool calls with page title and URL
- **Impact**: Users can see exactly which pages the AI is reading for information

### 4. **Misleading "Searching Wikipedia" Message**
- **Problem**: The AI uses `browser_search` which searches the entire web, but users thought it only searched Wikipedia
- **Solution**: Changed messaging from "Searching Wikipedia" to "Web Search" with actual query displayed
- **Impact**: Clearer communication about what the AI is actually doing

## Technical Changes

### Code Changes in `app.py`

#### 1. Increased Reasoning Display Limit (Lines 1043-1050)
```python
# Before: 500 characters
max_reasoning_display = 500

# After: 800 characters  
max_reasoning_display = 800
reasoning_section = f"🧠 **Reasoning**\n\n> {reasoning_content[:max_reasoning_display]}"
```

#### 2. Enhanced Browser Tool Detection (Lines 1130-1144)
```python
# Now detects multiple tool types and checks function names
tool_function_name = tool_call.function.name if hasattr(tool_call, 'function') and tool_call.function else None
is_builtin_browser_tool = (
    tool_call.type in ["browser_search", "code_interpreter", "browser.search", "browser.open"] or
    (tool_call.type == "function" and tool_function_name in ["browser.search", "browser.open"])
)
tool_type = tool_call.type if tool_call.type != "function" else tool_function_name
```

#### 3. URL Extraction from browser.search (Lines 1146-1190)
```python
# Extract URLs using regex pattern for Groq's format
url_pattern = r'【\d+†([^†\n]+?)†([^\]】\n]+?)】'
matches = re.findall(url_pattern, output_str)

for title, domain in matches[:5]:
    if not domain.startswith('http'):
        url = f"https://{domain}"
    else:
        url = domain
    search_urls.append(f"- [{title}]({url})")

# Display with "Web Search" label
search_display = f"🔍 **Web Search**\n\n> {query_display}"
if search_urls:
    search_display += "\n\n" + "\n".join(search_urls)
```

#### 4. Page Opening Display (Lines 1192-1232)
```python
# Extract URL and title from browser.open output
url_match = re.search(r'URL:\s*\n?\s*(https?://[^\s\n]+)', output_str)
if url_match:
    page_url = url_match.group(1)
    # Extract clean title from following lines
    lines = output_str.split('\n')
    page_title = None
    for line in lines[2:]:
        line = line.strip()
        if line and not line.startswith('L') and not line.startswith('URL:'):
            line = re.sub(r'^L\d+:\s*', '', line)
            page_title = line
            break
    
    if page_title and page_title != page_url:
        page_url = f"[{page_title}]({page_url})"

display_sections.append(f"📖 **Reading Webpage**\n\n> {page_url}")
```

## Example Output Comparison

### Before:
```
✅ Reasoning Complete

🧠 **Reasoning**
> We need to answer: current president of Switzerland. Need up-to-date info...

The current president of Switzerland is Guy Parmelin...【1†L21-L27】【2†L12-L16】
```
**Issues**: 
- Reasoning truncated
- No clickable links
- Citations don't work in Discord

### After:
```
🧠 **Reasoning**
> The user asks: "Who's the current president of Sri Lanka?" Need to provide answer with up-to-date info as of now (2026-02-07). Need to browse for latest info. Result 5 looks like Reuters about Sri Lanka's new president Anura Kumara Dissanayake. Let's open. Access denied. Let's open Wikipedia page for President of Sri Lanka. The Wikipedia page indicates the incumbent is Anura Kumara Dissanayake since 23 September 2024...

🔍 **Web Search**
> Searching: current president of Sri Lanka 2026

- [President of Sri Lanka](https://en.wikipedia.org)
- [2026 New Year Message](https://www.lanka.com.sg)
- [Anura Kumara Dissanayake](https://www.britannica.com)
- [Official Website](https://www.presidentsoffice.gov.lk)

📖 **Reading Webpage**
> [https://en.wikipedia.org/wiki/President_of_Sri_Lanka](https://en.wikipedia.org/wiki/President_of_Sri_Lanka)

✅ Reasoning Complete

The current President of Sri Lanka is **Anura Kumara Dissanayake**, who has been in office since 23 September 2024.
```
**Improvements**:
- Fuller reasoning visible
- All links are clickable
- Clear indication of web search (not just Wikipedia)
- Shows which pages are being read

## Testing

Created comprehensive test suite in `test_gpt_oss_display.py` that verifies:
1. URL extraction from browser.search output ✅
2. Page URL extraction from browser.open output ✅
3. Reasoning content display ✅

All tests pass successfully.

## Benefits to Users

1. **Transparency**: Users can see how the AI thinks and researches
2. **Verification**: Users can click source links to verify information themselves
3. **Understanding**: Clear labeling of web searches vs. Wikipedia-specific searches
4. **Trust**: Showing the full research process builds confidence in answers

## Compatibility

- Works with `openai/gpt-oss-120b` model
- Does not affect Kimi K2 Instruct model behavior (uses different reasoning system)
- Backward compatible with existing tool configurations

## Files Modified

1. `app.py` - Main bot logic with reasoning and tool display improvements
2. `test_gpt_oss_display.py` - New test suite for validation

## Future Improvements

Potential enhancements to consider:
1. Make reasoning display limit configurable per user
2. Add option to collapse/expand full reasoning in Discord
3. Support for additional Groq built-in tools as they become available
4. Better handling of very long webpage titles (truncate with ellipsis)
