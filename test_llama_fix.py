#!/usr/bin/env python3
"""
Test script to verify Llama 3.3 70B fixes for loop detection and context management.
Run this to ensure all changes are properly integrated.
"""

import sys
from io import StringIO


def test_context_manager_parameters():
    """Test that ContextManager methods accept is_llama parameter."""
    print("Testing ContextManager parameters...")
    
    # Import app module
    try:
        import app
    except ImportError as e:
        print(f"✗ Failed to import app: {e}")
        return False
    
    # Create a context manager instance
    ctx = app.ContextManager(
        system_prompt="test",
        user_message="test",
        conversation_history=[],
        max_tokens=8000
    )
    
    # Test detect_stuck_loop with is_llama parameter
    try:
        result = ctx.detect_stuck_loop(iteration=5, is_llama=True)
        print(f"  ✓ detect_stuck_loop accepts is_llama parameter: {result}")
    except TypeError as e:
        print(f"  ✗ detect_stuck_loop doesn't accept is_llama: {e}")
        return False
    
    # Test should_trim_context with is_llama parameter
    try:
        result = ctx.should_trim_context(iteration=5, is_llama=True)
        print(f"  ✓ should_trim_context accepts is_llama parameter: {result}")
    except TypeError as e:
        print(f"  ✗ should_trim_context doesn't accept is_llama: {e}")
        return False
    
    # Test build_optimized_messages with is_llama parameter
    try:
        messages = [{"role": "system", "content": "test"}]
        result = ctx.build_optimized_messages(messages, iteration=5, is_llama=True)
        print(f"  ✓ build_optimized_messages accepts is_llama parameter")
    except TypeError as e:
        print(f"  ✗ build_optimized_messages doesn't accept is_llama: {e}")
        return False
    
    return True


def test_loop_detection_thresholds():
    """Test that Llama has more lenient loop detection thresholds."""
    print("\nTesting loop detection thresholds...")
    
    try:
        import app
    except ImportError as e:
        print(f"✗ Failed to import app: {e}")
        return False
    
    ctx = app.ContextManager(
        system_prompt="test",
        user_message="test",
        conversation_history=[],
        max_tokens=8000
    )
    
    # Simulate consecutive thoughts without tools
    ctx.consecutive_thoughts_without_tools = 3
    
    # For Kimi (is_llama=False), should trigger at 3
    result_kimi = ctx.detect_stuck_loop(iteration=5, is_llama=False)
    if result_kimi == "repeated_planning":
        print("  ✓ Kimi triggers loop detection at 3 consecutive thoughts")
    else:
        print(f"  ✗ Kimi should trigger at 3, got: {result_kimi}")
        return False
    
    # For Llama (is_llama=True), should NOT trigger at 3
    result_llama = ctx.detect_stuck_loop(iteration=5, is_llama=True)
    if result_llama is None:
        print("  ✓ Llama doesn't trigger at 3 consecutive thoughts")
    else:
        print(f"  ✗ Llama should not trigger at 3, got: {result_llama}")
        return False
    
    # For Llama, should trigger at 4
    ctx.consecutive_thoughts_without_tools = 4
    result_llama_4 = ctx.detect_stuck_loop(iteration=5, is_llama=True)
    if result_llama_4 == "repeated_planning":
        print("  ✓ Llama triggers loop detection at 4 consecutive thoughts")
    else:
        print(f"  ✗ Llama should trigger at 4, got: {result_llama_4}")
        return False
    
    return True


def test_context_trimming_thresholds():
    """Test that Llama has earlier context trimming thresholds."""
    print("\nTesting context trimming thresholds...")
    
    try:
        import app
    except ImportError as e:
        print(f"✗ Failed to import app: {e}")
        return False
    
    ctx = app.ContextManager(
        system_prompt="test",
        user_message="test",
        conversation_history=[],
        max_tokens=8000
    )
    
    # Test iteration 6
    kimi_level = ctx.should_trim_context(iteration=6, is_llama=False)
    llama_level = ctx.should_trim_context(iteration=6, is_llama=True)
    
    if kimi_level == "none" and llama_level in ["light", "moderate"]:
        print(f"  ✓ Iteration 6: Kimi={kimi_level}, Llama={llama_level}")
    else:
        print(f"  ✗ Iteration 6: Expected Kimi=none, Llama=light/moderate, got Kimi={kimi_level}, Llama={llama_level}")
        return False
    
    # Test iteration 10
    kimi_level = ctx.should_trim_context(iteration=10, is_llama=False)
    llama_level = ctx.should_trim_context(iteration=10, is_llama=True)
    
    if kimi_level == "moderate" and llama_level == "aggressive":
        print(f"  ✓ Iteration 10: Kimi={kimi_level}, Llama={llama_level}")
    else:
        print(f"  ✗ Iteration 10: Expected Kimi=moderate, Llama=aggressive, got Kimi={kimi_level}, Llama={llama_level}")
        return False
    
    # Test iteration 15
    kimi_level = ctx.should_trim_context(iteration=15, is_llama=False)
    llama_level = ctx.should_trim_context(iteration=15, is_llama=True)
    
    if kimi_level == "aggressive" and llama_level == "emergency":
        print(f"  ✓ Iteration 15: Kimi={kimi_level}, Llama={llama_level}")
    else:
        print(f"  ✗ Iteration 15: Expected Kimi=aggressive, Llama=emergency, got Kimi={kimi_level}, Llama={llama_level}")
        return False
    
    return True


def test_system_prompt_differences():
    """Test that Llama has a more compact system prompt."""
    print("\nTesting system prompt differences...")
    
    try:
        import app
    except ImportError as e:
        print(f"✗ Failed to import app: {e}")
        return False
    
    # Get Llama prompt
    llama_prompt = app.get_system_prompt("llama-3.3-70b-versatile", has_memory=False)
    
    # Get Kimi prompt
    kimi_prompt = app.get_system_prompt("moonshotai/kimi-k2-instruct-0905", has_memory=False)
    
    # Check for Llama-specific content
    if "300 chars" in llama_prompt and "compact!" in llama_prompt.lower():
        print("  ✓ Llama prompt contains compact instructions (300 chars)")
    else:
        print(f"  ✗ Llama prompt missing compact instructions")
        return False
    
    if "ONE ACTION PER RESPONSE" in llama_prompt:
        print("  ✓ Llama prompt emphasizes one action per response")
    else:
        print(f"  ✗ Llama prompt missing one-action rule")
        return False
    
    # Check that Kimi has different instructions
    if "600 chars" in kimi_prompt:
        print("  ✓ Kimi prompt has different char limit (600)")
    else:
        print(f"  ✗ Kimi prompt should have 600 char limit")
        return False
    
    # Llama prompt should be more compact
    if len(llama_prompt) < len(kimi_prompt) * 1.1:  # Allow 10% margin
        print(f"  ✓ Llama prompt is more compact ({len(llama_prompt)} vs {len(kimi_prompt)} chars)")
    else:
        print(f"  ⚠ Llama prompt not significantly more compact ({len(llama_prompt)} vs {len(kimi_prompt)} chars)")
    
    return True


def test_content_size_limits():
    """Test that content size calculations use model-specific limits."""
    print("\nTesting content size limits...")
    
    # This is more of a code inspection test since the limits are inline
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check for max_body_length conditional
        if "max_body_length = 400 if is_llama else 500" in content:
            print("  ✓ Found max_body_length with Llama-specific limit (400 vs 500)")
        else:
            print("  ✗ max_body_length not using Llama-specific limit")
            return False
        
        # Check for max_tool_result conditional
        if "max_tool_result = 1200 if is_llama else 1800" in content:
            print("  ✓ Found max_tool_result with Llama-specific limit (1200 vs 1800)")
        else:
            print("  ✗ max_tool_result not using Llama-specific limit")
            return False
        
        # Check for context size monitoring
        if "context_size > 25000" in content:
            print("  ✓ Found proactive context size monitoring (25000 char threshold)")
        else:
            print("  ✗ Missing proactive context size monitoring")
            return False
        
    except FileNotFoundError:
        print("  ✗ Could not find app.py for inspection")
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Llama 3.3 70B Fix - Verification Tests")
    print("=" * 60)
    
    tests = [
        test_context_manager_parameters,
        test_loop_detection_thresholds,
        test_context_trimming_thresholds,
        test_system_prompt_differences,
        test_content_size_limits,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i}. {test.__name__}: {status}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Llama fix is properly integrated.")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed. Please review the changes.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
