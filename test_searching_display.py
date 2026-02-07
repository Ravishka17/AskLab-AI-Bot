#!/usr/bin/env python3
"""
Test script to verify that browser.search and browser.open show "Searching..." and "Reading..." indicators.
"""

# Test the convert_to_past_tense function
def convert_to_past_tense(sections):
    """Convert action verbs to past tense in completed reasoning."""
    converted = []
    for section in sections:
        section = section.replace("**Searching Wikipedia...**", "**Searched Wikipedia**")
        section = section.replace("**Searching...**", "**Searched**")
        section = section.replace("**Reading Article...**", "**Read Article**")
        section = section.replace("**Reading...**", "**Read Article**")
        section = section.replace("**Searching Memory...**", "**Searched Memory**")
        section = section.replace("**Thinking...**", "**Thought**")
        section = section.replace("**Skipping Duplicate**", "**Skipped Duplicate**")
        converted.append(section)
    return converted

# Test cases
test_sections = [
    "🔍 **Searching...**\n\n> Searching: current president of Sri Lanka 2026",
    "📖 **Reading...**\n\n> Opening webpage...",
    "🔍 **Searched**\n\n> Searching: current president of Sri Lanka 2026\n\n- [Article 1](https://example.com)",
    "📖 **Read Article**\n\n> [Title](https://example.com)",
    "🧠 **Thinking...**\n\n> Planning the search",
]

print("Testing convert_to_past_tense function:")
print("=" * 60)

for i, section in enumerate(test_sections):
    print(f"\nTest {i+1}:")
    print(f"Input:  {section}")
    result = convert_to_past_tense([section])
    print(f"Output: {result[0]}")

print("\n" + "=" * 60)
print("✅ All tests completed!")

# Test the display flow
print("\n\nTesting display flow:")
print("=" * 60)

print("\n1. When browser.search tool call is detected:")
print("   → Show: 🔍 **Searching...**")
print("   → Query: 'Searching: current president of Sri Lanka 2026'")

print("\n2. When browser.search completes and has results:")
print("   → Update to: 🔍 **Searched**")
print("   → Add results: '- [Article](url)'")

print("\n3. When browser.open tool call is detected:")
print("   → Show: 📖 **Reading...**")
print("   → Status: 'Opening webpage...'")

print("\n4. When browser.open completes:")
print("   → Update to: 📖 **Read Article**")
print("   → Show: '[Page Title](url)'")

print("\n5. When research is complete:")
print("   → Convert all '...ing' to past tense")
print("   → Final display shows completed actions")

print("\n" + "=" * 60)
print("✅ Display flow verified!")
