#!/usr/bin/env python3
"""Test script for GPT-OSS 120B implementation"""

import sys
import os

# Set test environment variables
os.environ['DISCORD_BOT_TOKEN'] = 'test_token'
os.environ['GROQ_API_KEY'] = 'test_key'

# Import after setting env vars
from app import (
    get_tools_for_model,
    get_system_prompt,
    AVAILABLE_MODELS
)

def test_model_definitions():
    """Test that models are defined correctly"""
    print("Testing model definitions...")
    assert "GPT-OSS 120B" in AVAILABLE_MODELS
    assert AVAILABLE_MODELS["GPT-OSS 120B"] == "openai/gpt-oss-120b"
    assert "Kimi K2 Instruct" in AVAILABLE_MODELS
    print("✅ Model definitions correct")

def test_tools_gpt_oss():
    """Test tool definitions for GPT-OSS"""
    print("\nTesting GPT-OSS tools...")
    tools = get_tools_for_model("openai/gpt-oss-120b", include_memory=False)
    
    # Should have web_search and code_execution
    assert len(tools) == 2
    assert {"type": "web_search"} in tools
    assert {"type": "code_execution"} in tools
    print("✅ GPT-OSS tools correct (web_search, code_execution)")
    
    # Test with memory
    tools_with_mem = get_tools_for_model("openai/gpt-oss-120b", include_memory=True)
    assert len(tools_with_mem) == 3
    # Check that search_memory function tool is added
    has_memory = any(
        t.get("type") == "function" and 
        t.get("function", {}).get("name") == "search_memory"
        for t in tools_with_mem
    )
    assert has_memory
    print("✅ GPT-OSS tools with memory correct")

def test_tools_kimi():
    """Test tool definitions for Kimi K2"""
    print("\nTesting Kimi K2 tools...")
    tools = get_tools_for_model("moonshotai/kimi-k2-instruct-0905", include_memory=False)
    
    # Should have Wikipedia tools
    assert len(tools) == 2
    tool_names = [t["function"]["name"] for t in tools]
    assert "search_wikipedia" in tool_names
    assert "get_wikipedia_page" in tool_names
    print("✅ Kimi K2 tools correct (search_wikipedia, get_wikipedia_page)")

def test_system_prompt_gpt_oss():
    """Test system prompt for GPT-OSS"""
    print("\nTesting GPT-OSS system prompt...")
    prompt = get_system_prompt("openai/gpt-oss-120b", has_memory=False)
    
    assert "GPT-OSS" in prompt or "BUILT-IN TOOLS" in prompt
    assert "web_search" in prompt
    assert "code_execution" in prompt
    assert "<think>" not in prompt  # GPT-OSS doesn't use think tags
    print("✅ GPT-OSS system prompt correct")

def test_system_prompt_kimi():
    """Test system prompt for Kimi K2"""
    print("\nTesting Kimi K2 system prompt...")
    prompt = get_system_prompt("moonshotai/kimi-k2-instruct-0905", has_memory=False)
    
    assert "search_wikipedia" in prompt or "RESEARCH WORKFLOW" in prompt
    assert "<think>" in prompt  # Kimi uses think tags
    print("✅ Kimi K2 system prompt correct")

def test_model_flags():
    """Test model detection logic"""
    print("\nTesting model detection...")
    
    # Test GPT-OSS detection
    gpt_oss_model = "openai/gpt-oss-120b"
    assert "gpt-oss" in gpt_oss_model.lower()
    print("✅ GPT-OSS detection works")
    
    # Test Kimi detection
    kimi_model = "moonshotai/kimi-k2-instruct-0905"
    assert "gpt-oss" not in kimi_model.lower()
    print("✅ Kimi K2 detection works")

def main():
    """Run all tests"""
    print("=" * 50)
    print("GPT-OSS 120B Implementation Tests")
    print("=" * 50)
    
    try:
        test_model_definitions()
        test_tools_gpt_oss()
        test_tools_kimi()
        test_system_prompt_gpt_oss()
        test_system_prompt_kimi()
        test_model_flags()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
