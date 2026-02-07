#!/usr/bin/env python3
"""Test script for ContextManager functionality."""
import sys
sys.path.insert(0, '/home/engine/project')

from app import ContextManager, extract_reasoning

def test_loop_detection():
    """Test semantic loop detection."""
    print("Testing Loop Detection...")
    
    # Test 1: Repeated planning without action
    ctx = ContextManager(
        system_prompt="Test system",
        user_message="Who is the president?"
    )
    
    # Simulate 3 consecutive thoughts without tools
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
    ctx3.add_thinking("<think>Even more planning</think>", has_tool_calls=True)  # Has tool calls
    
    stuck = ctx3.detect_stuck_loop(3)
    assert stuck is None, f"Expected None (tool calls should reset), got {stuck}"
    print("✅ Tool calls reset counter works")
    
    print("\n✅ All loop detection tests passed!")

def test_progressive_trimming():
    """Test progressive context trimming."""
    print("\nTesting Progressive Context Trimming...")
    
    ctx = ContextManager(
        system_prompt="Test system prompt",
        user_message="Test query"
    )
    
    # Add some tool results
    ctx.add_tool_result({
        "role": "tool",
        "tool_call_id": "1",
        "name": "search_wikipedia",
        "content": "Result 1"
    })
    ctx.add_tool_result({
        "role": "tool",
        "tool_call_id": "2",
        "name": "get_wikipedia_page",
        "content": "Result 2"
    })
    
    # Test iteration thresholds
    assert ctx.should_trim_context(5) == "none", "Iteration 5 should not trim"
    assert ctx.should_trim_context(10) == "moderate", "Iteration 10 should moderate trim"
    assert ctx.should_trim_context(15) == "aggressive", "Iteration 15 should aggressive trim"
    assert ctx.should_trim_context(20) == "emergency", "Iteration 20 should emergency trim"
    
    print("✅ Trim level thresholds correct")
    
    # Test message building
    messages = [
        {"role": "system", "content": "System"},
        {"role": "user", "content": "Query"},
        {"role": "assistant", "content": "<think>Planning</think>"}
    ]
    
    # Moderate trim
    result = ctx.build_optimized_messages(messages, 10)
    assert result[0]["role"] == "system", "System prompt should always be first"
    assert "PROGRESS" in result[0]["content"], "Progress marker should be added"
    print("✅ Moderate trimming builds correct messages")
    
    # Aggressive trim
    result = ctx.build_optimized_messages(messages, 15)
    assert result[0]["role"] == "system", "System prompt should always be first"
    assert any("iterations left" in str(m.get("content", "")).lower() for m in result), "Urgency should be injected"
    print("✅ Aggressive trimming injects urgency")
    
    # Emergency trim
    result = ctx.build_optimized_messages(messages, 20)
    assert result[0]["role"] == "system", "System prompt should always be first"
    assert any("EMERGENCY" in str(m.get("content", "")) for m in result), "Emergency message should be present"
    print("✅ Emergency trimming works")
    
    print("\n✅ All progressive trimming tests passed!")

def test_urgency_injection():
    """Test urgency message generation."""
    print("\nTesting Urgency Injection...")
    
    ctx = ContextManager(
        system_prompt="Test",
        user_message="Test query"
    )
    
    # Test different stuck types
    msg = ctx.inject_urgency(5, "repeated_planning")
    assert "Stop planning" in msg and "tool calls NOW" in msg, "Should force action"
    print("✅ Repeated planning urgency message correct")
    
    msg = ctx.inject_urgency(5, "theme_loop")
    assert "repeating" in msg.lower() and "action immediately" in msg.lower(), "Should break loop"
    print("✅ Theme loop urgency message correct")
    
    msg = ctx.inject_urgency(5, "no_progress")
    assert "progress" in msg.lower() and "tools" in msg.lower(), "Should encourage tools"
    print("✅ No progress urgency message correct")
    
    msg = ctx.inject_urgency(20, None)
    assert "CRITICAL" in msg or "iterations left" in msg, "Should have critical urgency"
    print("✅ Iteration-based urgency message correct")
    
    msg = ctx.inject_urgency(5, None)
    assert msg is None, "Should have no urgency at low iterations"
    print("✅ No urgency at low iterations correct")
    
    print("\n✅ All urgency injection tests passed!")

def test_research_context():
    """Test research context tracking."""
    print("\nTesting Research Context Tracking...")
    
    ctx = ContextManager(
        system_prompt="Test",
        user_message="Test query"
    )
    
    # Track pages read
    ctx.research_context['pages_read'] = 1
    ctx.add_tool_result({"role": "tool", "tool_call_id": "1", "name": "get_wikipedia_page", "content": "Page 1"})
    
    ctx.research_context['pages_read'] = 2
    ctx.add_tool_result({"role": "tool", "tool_call_id": "2", "name": "get_wikipedia_page", "content": "Page 2"})
    
    # Build messages with progress
    messages = [{"role": "system", "content": "System"}]
    result = ctx.build_optimized_messages(messages, 6)
    
    # Check progress marker includes pages read
    assert "2 pages read" in result[0]["content"], "Progress should show pages read"
    print("✅ Research context tracking works")
    
    print("\n✅ All research context tests passed!")

def test_theme_extraction():
    """Test semantic theme extraction."""
    print("\nTesting Theme Extraction...")
    
    ctx = ContextManager(
        system_prompt="Test",
        user_message="Test"
    )
    
    test_cases = [
        ("<think>I need to plan my approach</think>", "planning"),
        ("<think>Let me search for information</think>", "search_intent"),
        ("<think>I'll read the article now</think>", "read_intent"),
        ("<think>Now I'll synthesize all the findings</think>", "synthesis"),
        ("<think>Here are the facts</think>", "general"),
    ]
    
    for thinking, expected_theme in test_cases:
        ctx.add_thinking(thinking, has_tool_calls=False)
        actual_theme = ctx._extract_theme(thinking.replace("<think>", "").replace("</think>", ""))
        assert actual_theme == expected_theme, f"Expected {expected_theme}, got {actual_theme}"
    
    print("✅ Theme extraction works correctly")
    print("\n✅ All theme extraction tests passed!")

if __name__ == "__main__":
    print("=" * 60)
    print("Context Manager Test Suite")
    print("=" * 60)
    
    try:
        test_loop_detection()
        test_progressive_trimming()
        test_urgency_injection()
        test_research_context()
        test_theme_extraction()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
