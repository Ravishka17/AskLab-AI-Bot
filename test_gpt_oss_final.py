#!/usr/bin/env python3
"""
Final comprehensive test for GPT-OSS 120B model configuration.
Tests all three fixes:
1. No cacheable property
2. Correct tool types (browser_search, code_interpreter)
3. Only include_reasoning (no reasoning_format)
"""

import os
from groq import Groq

def test_gpt_oss_configuration():
    """Test GPT-OSS 120B with correct configuration."""
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    print("🧪 Testing GPT-OSS 120B Configuration")
    print("=" * 60)
    
    # Correct configuration per Groq documentation
    config = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {
                "role": "user",
                "content": "What is 2+2? Be brief."
            }
        ],
        "tools": [
            {"type": "browser_search"},      # ✅ Correct tool type
            {"type": "code_interpreter"}     # ✅ Correct tool type
        ],
        "include_reasoning": True,           # ✅ Correct parameter
        # NOTE: reasoning_format is NOT included (not supported by GPT-OSS)
        # NOTE: cacheable is NOT included (not supported by GPT-OSS)
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    print("\n📋 Configuration:")
    print(f"  Model: {config['model']}")
    print(f"  Tools: {config['tools']}")
    print(f"  Include Reasoning: {config['include_reasoning']}")
    print(f"  ❌ reasoning_format: NOT INCLUDED (not supported)")
    print(f"  ❌ cacheable: NOT INCLUDED (not supported)")
    
    try:
        print("\n🚀 Making API call...")
        response = client.chat.completions.create(**config)
        
        print("\n✅ SUCCESS! API call completed")
        print("=" * 60)
        
        msg = response.choices[0].message
        
        # Check content
        print("\n📝 Response Content:")
        print(f"  {msg.content[:200]}")
        if len(msg.content) > 200:
            print("  ...")
        
        # Check reasoning field
        if hasattr(msg, 'reasoning') and msg.reasoning:
            print("\n🧠 Reasoning Field (first 200 chars):")
            print(f"  {msg.reasoning[:200]}")
            if len(msg.reasoning) > 200:
                print("  ...")
            print("\n✅ Reasoning field is present and accessible!")
        else:
            print("\n⚠️ No reasoning field found (model may not have used reasoning)")
        
        # Check usage
        if hasattr(response, 'usage'):
            print(f"\n📊 Token Usage:")
            print(f"  Prompt: {response.usage.prompt_tokens}")
            print(f"  Completion: {response.usage.completion_tokens}")
            print(f"  Total: {response.usage.total_tokens}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! GPT-OSS 120B configuration is correct.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("=" * 60)
        return False

def test_invalid_configurations():
    """Test that invalid configurations are properly rejected."""
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    print("\n\n🧪 Testing Invalid Configurations (Expected to Fail)")
    print("=" * 60)
    
    # Test 1: Using reasoning_format (not supported)
    print("\n❌ Test 1: Using reasoning_format (should fail)")
    try:
        client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hello"}],
            reasoning_format="parsed",  # ❌ Not supported
            max_tokens=100
        )
        print("⚠️ UNEXPECTED: Request succeeded (should have failed)")
    except Exception as e:
        if "cannot specify both" in str(e).lower() or "reasoning_format" in str(e).lower():
            print(f"✅ EXPECTED: Correctly rejected - {str(e)[:100]}")
        else:
            print(f"⚠️ Unexpected error: {e}")
    
    # Test 2: Using both reasoning_format and include_reasoning
    print("\n❌ Test 2: Using both parameters (should fail)")
    try:
        client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hello"}],
            reasoning_format="parsed",  # ❌ Not supported
            include_reasoning=True,     # ✅ Supported
            max_tokens=100
        )
        print("⚠️ UNEXPECTED: Request succeeded (should have failed)")
    except Exception as e:
        if "cannot specify both" in str(e).lower():
            print(f"✅ EXPECTED: Correctly rejected - {str(e)[:100]}")
        else:
            print(f"⚠️ Unexpected error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Test valid configuration
    success = test_gpt_oss_configuration()
    
    # Test invalid configurations
    test_invalid_configurations()
    
    # Final summary
    print("\n\n" + "=" * 60)
    if success:
        print("🎉 GPT-OSS 120B is properly configured!")
        print("\nKey Configuration Points:")
        print("  ✅ Use include_reasoning=True (NOT reasoning_format)")
        print("  ✅ Use browser_search and code_interpreter tools")
        print("  ✅ Access reasoning via msg.reasoning field")
        print("  ❌ Do NOT use reasoning_format (not supported)")
        print("  ❌ Do NOT use cacheable property (not supported)")
    else:
        print("❌ Configuration issues detected. Review the errors above.")
    print("=" * 60)
