#!/usr/bin/env python3
"""
AI utilities and text processing for AskLab AI Bot
"""
import re

def get_tools(include_memory=False):
    """Get available tools for the AI model."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_wikipedia",
                "description": "Search Wikipedia for articles related to a query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for Wikipedia"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_wikipedia_page",
                "description": "Get the content of a specific Wikipedia page",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the Wikipedia page"
                        }
                    },
                    "required": ["title"]
                }
            }
        }
    ]
    
    if include_memory:
        tools.append({
            "type": "function",
            "function": {
                "name": "search_memory",
                "description": "Search through past conversations and memories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for memory search"
                        }
                    },
                    "required": ["query"]
                }
            }
        })
    
    return tools

def clean_output(text):
    """Removes thinking tags and hallucinated tool calls from final output."""
    if not text:
        return ""
    
    # Remove internal thinking content between thinking tags
    text = re.sub(r'<(?:think|thinking)>.*?</(?:think|thinking)>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<function_calls?>.*?</function_calls?>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</minimax:tool_call>.*?</function_call>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<function=.*?</function>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<invoke.*?</invoke>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<result>.*?</result>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<parameter.*?</parameter>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\n\n(?:search_wikipedia|get_wikipedia_page|search_memory)\([^)]+\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'I\'ll (?:search|get|fetch|retrieve)[^\n]*\.', '', text, flags=re.IGNORECASE)
    
    # Remove Discord UI elements that should not appear in final responses
    text = re.sub(r'✅ Reasoning Complete\s*', '', text)
    text = re.sub(r'🧠 \*\*Thought\*\*\s*>\s*.*?(?=\n🧠|\n🔍|\n📖|\n⚠️|\n📚|\n\n|\Z)', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'🔍 \*\*Searched Wikipedia\*\*\s*>\s*.*?(?=\n🧠|\n📖|\n⚠️|\n📚|\n\n|\Z)', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'📖 \*\*Read Article\*\*\s*\n\s*- \[.*?\]\(.*?\)', '', text)
    text = re.sub(r'⚠️ \*\*Skipped Duplicate\*\*\s*>\s*.*?(?=\n🧠|\n🔍|\n📖|\n📚|\n\n|\Z)', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'📚 \*\*Sources\*\*.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up any remaining thinking-related fragments
    text = re.sub(r'^(The user is asking|Let me search|Key findings|Synthesis:).*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\(AKD|first non-dynastic|unprecedented NPP\)\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*Anura Kumara Dissanayake Sri Lanka president\s*$', '', text, flags=re.MULTILINE)
    
    return text.strip()

def get_system_prompt(model_name, has_memory=False):
    """Get model-specific system prompt."""
    memory_instruction = ""
    if has_memory:
        memory_instruction = (
            "\n### MEMORY SYSTEM\n"
            "You have access to search_memory tool to recall past conversations and research.\n"
            "Use it when:\n"
            "- User asks 'what did we discuss about X?'\n"
            "- User references 'last time' or 'before'\n"
            "- Context from previous conversations would be helpful\n\n"
        )
    
    base_prompt = (
        "You are AskLab AI, a research assistant. Current Date: January 2026.\n\n"
        "### RESPONSE TYPES\n"
        "1. **Simple conversations**: Respond directly without tools\n"
        "2. **Research queries**: Use the research workflow\n"
        + memory_instruction
    )
    
    if "llama" in model_name.lower():
        return base_prompt + (
            "### RESEARCH WORKFLOW\n"
            "1. <think>**Planning**\nStrategy</think>\n"
            "2. Call search_wikipedia (NO THINKING)\n"
            "3. <think>List 2-3 pages as links</think>\n"
            "4. Call get_wikipedia_page (NO THINKING)\n"
            "5. <think>Summarize facts</think>\n"
            "6. Repeat for more pages\n"
            "7. <think>Synthesize findings</think>\n"
            "8. Final answer with citations\n\n"
            "### CRITICAL RULES\n"
            "- ONE ACTION PER RESPONSE: thinking OR tool, NEVER BOTH\n"
            "- Keep thinking under 400 chars\n"
            "- Read at least 3 pages\n"
        )
    else:
        return base_prompt + (
            "### RESEARCH WORKFLOW\n"
            "1. <think>**Planning**\nStrategy</think>\n"
            "2. Call search_wikipedia\n"
            "3. <think>List 2-3 pages as links</think>\n"
            "4. Call get_wikipedia_page\n"
            "5. <think>Summarize information</think>\n"
            "6. Read more pages (at least 3 total)\n"
            "7. <think>Synthesize ALL information\n</think>\n"
            "8. Final answer with citations [1](URL)\n\n"
            "### CRITICAL RULES\n"
            "- List pages as: [Title](URL)\n"
            "- Cite inline like [1](URL)\n"
            "- Keep thinking under 600 chars\n"
            "- Read at least 3 pages\n"
        )