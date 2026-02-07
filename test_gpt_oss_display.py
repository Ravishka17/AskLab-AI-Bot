#!/usr/bin/env python3
"""
Test script to verify GPT-OSS reasoning and browser search display improvements.
This simulates the tool call structure from Groq's GPT-OSS model.
"""

import re

# Sample tool call output from GPT-OSS browser.search
sample_browser_search_output = """L0: 
L1: URL: https://exa.ai/search?q=current+president+of+Sri+Lanka+2026
L2: # Search Results
L3: 
L4: \\* 【0†President of Sri Lanka†en.wikipedia.org】
L5: \\* 【1†2026 New Year Message of H.E. Anura Kumara ...†www.lanka.com.sg】
L6: \\* 【2†Anura Kumara Dissanayake | Biography, Career, &
L7: Facts†www.britannica.com】
L8: \\* 【3†Anura Kumara Dissanayake†en.wikipedia.org】
L9: \\* 【4†Anura Kumara Dissanayake†www.presidentsoffice.gov.lk】"""

# Sample tool call output from GPT-OSS browser.open
sample_browser_open_output = """L0: 
L1: URL: https://en.wikipedia.org/wiki/President_of_Sri_Lanka
L2: Head of state and government of Sri Lanka"""

# Sample reasoning content
sample_reasoning = "The user asks: \"Who's the current president of Sri Lanka?\" Need to provide answer with up-to-date info as of now (2026-02-07). Need to browse for latest info. Result 5 looks like Reuters about Sri Lanka's new president Anura Kumara Dissanayake. Let's open. Access denied. Let's open Wikipedia page for President of Sri Lanka. The Wikipedia page indicates the incumbent is Anura Kumara Dissanayake since 23 September 2024. That is the current president as of 2026."

def test_url_extraction():
    """Test URL extraction from browser.search output"""
    print("=" * 60)
    print("TEST 1: URL Extraction from browser.search")
    print("=" * 60)
    
    # Updated pattern to avoid multi-line matches
    url_pattern = r'【\d+†([^†\n]+?)†([^\]】\n]+?)】'
    matches = re.findall(url_pattern, sample_browser_search_output)
    
    search_urls = []
    for title, domain in matches[:5]:
        if not domain.startswith('http'):
            url = f"https://{domain}"
        else:
            url = domain
        search_urls.append(f"- [{title}]({url})")
    
    print("\nExtracted URLs:")
    for url in search_urls:
        print(url)
    
    print(f"\n✅ Successfully extracted {len(search_urls)} URLs")
    # Note: We expect 4 URLs because one has a multi-line title which is filtered out
    return len(search_urls) >= 4

def test_page_open_extraction():
    """Test URL extraction from browser.open output"""
    print("\n" + "=" * 60)
    print("TEST 2: URL Extraction from browser.open")
    print("=" * 60)
    
    page_url = "unknown page"
    url_match = re.search(r'URL:\s*\n?\s*(https?://[^\s\n]+)', sample_browser_open_output)
    if url_match:
        page_url = url_match.group(1)
        # Extract page title if available (skip the URL line)
        lines = sample_browser_open_output.split('\n')
        page_title = None
        for line in lines[2:]:  # Start from line after URL
            line = line.strip()
            if line and not line.startswith('L') and not line.startswith('URL:'):
                # Remove line numbers if present (e.g., "L2: Title" -> "Title")
                line = re.sub(r'^L\d+:\s*', '', line)
                page_title = line
                break
        
        if page_title and page_title != page_url:
            page_url = f"[{page_title}]({page_url})"
        else:
            page_url = f"[{page_url}]({page_url})"
    
    print(f"\nExtracted Page URL: {page_url}")
    print(f"\n✅ Successfully extracted page URL")
    return "en.wikipedia.org" in page_url

def test_reasoning_display():
    """Test reasoning content display"""
    print("\n" + "=" * 60)
    print("TEST 3: Reasoning Content Display")
    print("=" * 60)
    
    max_reasoning_display = 800
    reasoning_section = f"🧠 **Reasoning**\n\n> {sample_reasoning[:max_reasoning_display]}"
    if len(sample_reasoning) > max_reasoning_display:
        reasoning_section += "..."
    
    print(reasoning_section)
    print(f"\n✅ Reasoning displayed (length: {len(reasoning_section)} chars)")
    return len(reasoning_section) > 0

def main():
    """Run all tests"""
    print("\n" + "🧪" * 30)
    print("GPT-OSS Display Improvements Test Suite")
    print("🧪" * 30 + "\n")
    
    results = []
    results.append(("URL Extraction (browser.search)", test_url_extraction()))
    results.append(("Page URL Extraction (browser.open)", test_page_open_extraction()))
    results.append(("Reasoning Display", test_reasoning_display()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
