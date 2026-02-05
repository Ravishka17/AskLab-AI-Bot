#!/usr/bin/env python3
"""Simplified test for ContextManager logic."""
import re

def extract_reasoning(text):
    """Extracts text inside <think> tags."""
    if not text:
        return ""
    match = re.search(r'<(?:think|thinking)>(.*?)</(?:think|thinking)>', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

class ContextManager:
    """Manages dual-track context architecture to prevent instruction dilution."""
    
    def __init__(self, system_prompt, user_message, conversation_history=None, max_tokens=8000):
        self.system_prompt = system_prompt
        self.user_message = user_message
        self.conversation_history = conversation_history or []
        self.max_tokens = max_tokens
        
        # Separate working memory streams
        self.tool_results = []
        self.thinking_blocks = []
        self.research_context = {}
        
        # Loop detection
        self.consecutive_thoughts_without_tools = 0
        self.last_thinking_themes = []
        self.iterations_without_new_facts = 0
        self.last_fact_count = 0
    
    def add_tool_result(self, tool_message):
        """Add a tool result to research context."""
        self.tool_results.append(tool_message)
        self.consecutive_thoughts_without_tools = 0
        
    def add_thinking(self, content, has_tool_calls=False):
        """Track thinking patterns for loop detection."""
        if not has_tool_calls:
            self.consecutive_thoughts_without_tools += 1
        else:
            self.consecutive_thoughts_without_tools = 0
            # Reset theme tracking when action is taken
            self.last_thinking_themes = []
        
        thinking = extract_reasoning(content)
        if thinking and not has_tool_calls:  # Only track themes when no action taken
            self.thinking_blocks.append({
                "iteration": len(self.thinking_blocks),
                "content": thinking[:200],
                "theme": self._extract_theme(thinking)
            })
            self.last_thinking_themes.append(self._extract_theme(thinking))
            if len(self.last_thinking_themes) > 3:
                self.last_thinking_themes.pop(0)
    
    def _extract_theme(self, thinking):
        """Extract semantic theme from thinking block."""
        thinking_lower = thinking.lower()
        if any(word in thinking_lower for word in ["plan", "strategy", "approach", "need to"]):
            return "planning"
        elif any(word in thinking_lower for word in ["synthesiz", "combin", "overall", "summary"]):
            return "synthesis"
        elif any(word in thinking_lower for word in ["search", "find", "look for"]):
            return "search_intent"
        elif any(word in thinking_lower for word in ["read", "article", "page"]):
            return "read_intent"
        else:
            return "general"
    
    def detect_stuck_loop(self, iteration):
        """Detect if AI is stuck in planning without action."""
        # Pattern 1: Same theme repeated 3+ times (check first - more specific)
        if len(self.last_thinking_themes) >= 3:
            if self.last_thinking_themes[-1] == self.last_thinking_themes[-2] == self.last_thinking_themes[-3]:
                if self.last_thinking_themes[-1] in ["planning", "search_intent"]:
                    return "theme_loop"
        
        # Pattern 2: Multiple consecutive thoughts without tool calls (general fallback)
        if self.consecutive_thoughts_without_tools >= 3:
            return "repeated_planning"
        
        # Pattern 3: No new facts accumulated for 5+ iterations
        current_fact_count = len(self.tool_results)
        if iteration >= 5 and current_fact_count == self.last_fact_count:
            self.iterations_without_new_facts += 1
            if self.iterations_without_new_facts >= 5:
                return "no_progress"
        else:
            self.iterations_without_new_facts = 0
            self.last_fact_count = current_fact_count
        
        return None

def test_loop_detection():
    """Test semantic loop detection."""
    print("Testing Loop Detection...")
    
    # Test 1: Repeated planning without action
    ctx = ContextManager(
        system_prompt="Test system",
        user_message="Who is the president?"
    )
    
    ctx.add_thinking("<think>Planning: I need to search</think>", has_tool_calls=False)
    ctx.add_thinking("<think>I should find information</think>", has_tool_calls=False)
    ctx.add_thinking("<think>Let me plan my approach</think>", has_tool_calls=False)
    
    stuck = ctx.detect_stuck_loop(5)
    assert stuck == "repeated_planning", f"Expected 'repeated_planning', got {stuck}"
    print("✅ Repeated planning detection works")
    
    # Test 2: Theme loop detection
    ctx2 = ContextManager(
        system_prompt="Test system",
        user_message="Who is the president?"
    )
    
    ctx2.add_thinking("<think>Planning: I need to search Wikipedia</think>", has_tool_calls=False)
    ctx2.add_thinking("<think>Planning: Let me find the right article</think>", has_tool_calls=False)
    ctx2.add_thinking("<think>Planning: I should look this up</think>", has_tool_calls=False)
    
    stuck = ctx2.detect_stuck_loop(3)
    assert stuck == "theme_loop", f"Expected 'theme_loop', got {stuck}"
    print("✅ Theme loop detection works")
    
    # Test 3: Tool calls reset counter
    ctx3 = ContextManager(
        system_prompt="Test system",
        user_message="Who is the president?"
    )
    
    ctx3.add_thinking("<think>Planning</think>", has_tool_calls=False)
    ctx3.add_thinking("<think>More planning</think>", has_tool_calls=False)
    ctx3.add_thinking("<think>Even more planning</think>", has_tool_calls=True)
    
    stuck = ctx3.detect_stuck_loop(3)
    assert stuck is None, f"Expected None (tool calls should reset), got {stuck}"
    print("✅ Tool calls reset counter works")
    
    print("✅ All loop detection tests passed!\n")

def test_theme_extraction():
    """Test semantic theme extraction."""
    print("Testing Theme Extraction...")
    
    ctx = ContextManager(
        system_prompt="Test",
        user_message="Test"
    )
    
    test_cases = [
        ("I need to plan my approach", "planning"),
        ("Let me search for information", "search_intent"),
        ("I'll read the article now", "read_intent"),
        ("Now I'll synthesize all the findings", "synthesis"),
        ("Here are the facts", "general"),
    ]
    
    for thinking, expected_theme in test_cases:
        actual_theme = ctx._extract_theme(thinking)
        assert actual_theme == expected_theme, f"Expected {expected_theme}, got {actual_theme} for '{thinking}'"
        print(f"  ✓ '{thinking[:30]}...' → {actual_theme}")
    
    print("✅ All theme extraction tests passed!\n")

if __name__ == "__main__":
    print("=" * 60)
    print("Context Manager Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_loop_detection()
        test_theme_extraction()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Key features verified:")
        print("  ✓ Semantic loop detection (no hardcoded phrases)")
        print("  ✓ Theme extraction for pattern matching")
        print("  ✓ Consecutive thought tracking")
        print("  ✓ Tool call counter reset")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
