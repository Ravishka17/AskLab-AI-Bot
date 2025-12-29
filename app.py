#!/usr/bin/env python3
"""
Main entry point for AskLab AI Discord Bot on fps.ms.
This file is the required entry point for fps.ms container hosting.

IMPORTANT: fps.ms requires this file to be named 'app.py'
"""

import os
import sys

# Ensure the project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import RAG examples module for few-shot prompting
RAG_AVAILABLE = False
RAG_STORE = None
try:
    from rag_examples import RAGExampleStore
    RAG_STORE = RAGExampleStore()
    RAG_AVAILABLE = True
    print("✓ RAG examples module loaded successfully")
except ImportError as e:
    print(f"Info: RAG examples module not available ({e})")
    print("  Bot will continue without RAG-based few-shot examples")

# Import bot modules
import json
import re
from typing import List
import discord
import aiohttp
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
GROQ_TEMPERATURE = float(os.getenv('GROQ_TEMPERATURE', '0.7'))

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

conversation_history = {}

# --- TOOLS ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for information. Use this when you need current information or verification.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query for Wikipedia"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_wikipedia_page",
            "description": "Read the full content of a Wikipedia article.",
            "parameters": {
                "type": "object",
                "properties": {"title": {"type": "string", "description": "Exact Wikipedia article title to read"}},
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_html",
            "description": "Deploy HTML code to a public URL using EdgeOne Pages.",
            "parameters": {
                "type": "object",
                "properties": {"value": {"type": "string", "description": "HTML code to deploy"}},
                "required": ["value"]
            }
        }
    }
]


# --- WIKIPEDIA FUNCTIONS ---

async def execute_wiki_search(query: str) -> str:
    """Execute Wikipedia search using the official API"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {"action": "query", "list": "search", "srsearch": query, "format": "json", "utf8": True, "limit": 10}
    headers = {"User-Agent": "AskLab-AI-Bot/1.0"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    for item in data.get('query', {}).get('search', []):
                        snippet = item['snippet'].replace('<span class="searchmatch">', '').replace('</span>', '')
                        results.append(f"- {item['title']}: {snippet}")
                    return "\n".join(results) if results else "No results found."
                return f"Error: Wikipedia API returned status {response.status}"
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"


async def execute_wiki_page(title: str) -> str:
    """Execute Wikipedia page read using the official API"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {"action": "query", "prop": "extracts", "explaintext": True, "titles": title, "format": "json", "utf8": True, "redirects": True}
    headers = {"User-Agent": "AskLab-AI-Bot/1.0"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data.get('query', {}).get('pages', {})
                    for page_id, page_content in pages.items():
                        if page_id != '-1':
                            extract = page_content.get('extract', '')
                            return extract[:3000] + "... (truncated)" if len(extract) > 3000 else (extract or "No content available.")
                    return "Page not found."
                return f"Error: Wikipedia API returned status {response.status}"
    except Exception as e:
        return f"Error reading Wikipedia page: {str(e)}"


async def execute_deploy_html(value: str) -> str:
    """Deploy HTML using EdgeOne Pages MCP"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:3001/deploy", json={"value": value}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('url', 'Deployment successful but no URL returned')
                return f"Error: Deploy returned status {response.status}"
    except Exception as e:
        return f"Error deploying HTML: {str(e)}"


# --- HELPER FUNCTIONS ---

def extract_thinking(text):
    if not text:
        return None
    pattern = r'<function_call>([^<]+)</func_call>'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    return matches[-1].strip() if matches else None

def remove_thinking_tags(text):
    if not text:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, re.DOTALL | re.IGNORECASE).strip()

def format_blockquote(text: str) -> str:
    if not text:
        return ""
    lines = text.strip().splitlines()
    formatted = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        elif line.startswith("**") and line.endswith("**"):
            if formatted:
                formatted.append("")
            formatted.append(f"> {line}")
        else:
            formatted.append(f"> {line}")
    return "\n".join(formatted)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('✅ Wikipedia System: Online')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        question = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if question:
            class MessageContext:
                def __init__(self, message):
                    self.channel = message.channel
                    self.send = message.channel.send
                    self.author = message.author
                    self.typing = message.channel.typing
            ctx = MessageContext(message)
            await process_question(ctx, question)
        return
    await bot.process_commands(message)


async def process_question(ctx, question: str):
    channel_id = ctx.channel.id
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    conversation_history[channel_id].append({"role": "user", "content": question})
    if len(conversation_history[channel_id]) > 20:
        conversation_history[channel_id] = conversation_history[channel_id][-20:]

    system_message = {
        "role": "system",
        "content": (
            "You are AskLab AI - a helpful reasoning assistant with Wikipedia research capabilities.\n\n"
            "🎯 YOUR CORE CAPABILITIES:\n"
            "- Answer questions using your training knowledge (up to January 2025)\n"
            "- Research current information on Wikipedia when needed\n"
            "- Deploy HTML code to public URLs for users to preview\n"
            "- Think step-by-step using <think>...</think> tags\n\n"
            "⚠️ MANDATORY REQUIREMENT:\n"
            "You MUST include <think>...</think> blocks in your responses.\n"
            "- Think BEFORE calling tools to plan your research\n"
            "- Think AFTER reading articles to analyze what you learned and plan next steps\n"
            "- Never respond without thinking\n\n"
            
            "⚙️ WHEN TO USE WIKIPEDIA TOOLS:\n"
            "MANDATORY: You MUST use Wikipedia tools for:\n"
            "1. Questions about current presidents, prime ministers, or world leaders\n"
            "2. Questions about current events, positions, or status (especially after 2023)\n"
            "3. Any topic where current information may have changed since your training\n\n"
            
            "⚠️ CRITICAL: Do NOT rely on your training knowledge for current information!\n"
            "- For current presidents/leaders: You MUST call search_wikipedia FIRST\n"
            "- Your thinking MUST show the actual search and reading process\n"
            "- The ONLY way to get current information is by calling the tools\n"
            "- NEVER say 'From the Wikipedia page' before actually calling the tools\n\n"
            
            "⏰ WHEN TO PROVIDE THE FINAL ANSWER:\n"
            "- After you have read ALL necessary Wikipedia sources\n"
            "- After you have gathered comprehensive information\n"
            "- Once you say 'Synthesizing the Information', that should be your LAST thinking block before the answer\n"
            "- The pattern should be: Research → Synthesize → ANSWER\n\n"
            
            "🧠 THINKING PROCESS:\n"
            "You MUST structure ALL thinking blocks with bold section headers. Format example:\n\n"
            "<think>\n"
            "**Understanding the Request**\n"
            "Brief explanation of what the user wants.\n"
            "**Planning My Approach**\n"
            "What I'll do to address this.\n"
            "</think>\n\n"
            
            "For research questions about current world leaders:\n\n"
            "<think>\n"
            "**Understanding the Request**\n"
            "User wants to know who is currently serving as president of Sri Lanka.\n"
            "**Planning My Approach**\n"
            "Since my training data has a cutoff date, I need to search Wikipedia to get the latest information.\n"
            "</think>\n\n"
            "🔍 **Searching Wikipedia...**\n\n"
            "> current president of Sri Lanka\n\n"
            "Then you see the search results.\n\n"
            "<think>\n"
            "**Analyzing the Results**\n"
            "I see search results that include 'President of Sri Lanka' which should have current information.\n"
            "**Planning the Next Step**\n"
            "I'll call get_wikipedia_page to read the 'President of Sri Lanka' article.\n"
            "</think>\n\n"
            "📖 **Reading Article...**\n\n"
            "> President of Sri Lanka\n\n"
            "Then you see the article content.\n\n"
            "<think>\n"
            "**Analyzing What I Learned**\n"
            "I found out that the current president of Sri Lanka is Anura Kumara Dissanayake.\n"
            "**Planning the Next Step**\n"
            "I'll search for 'Anura Kumara Dissanayake' on Wikipedia to read his bio page.\n"
            "</think>\n\n"
            "🔍 **Searching Wikipedia...**\n\n"
            "> Anura Kumara Dissanayake\n\n"
            "Then you see the search result.\n\n"
            "<think>\n"
            "**Analyzing the Results**\n"
            "I found the 'Anura Kumara Dissanayake' article.\n"
            "**Planning the Next Step**\n"
            "Let me read this article to find more information about him.\n"
            "</think>\n\n"
            "📖 **Reading Article...**\n\n"
            "> Anura Kumara Dissanayake\n\n"
            "Then you see the article content.\n\n"
            "<think>\n"
            "**Synthesizing the Information**\n"
            "I've found comprehensive information about the current president of Sri Lanka from both Wikipedia pages.\n"
            "**Preparing the Answer**\n"
            "Now I can provide a complete answer.\n"
            "</think>\n\n"
            "The current president of Sri Lanka is Anura Kumara Dissanayake (commonly known as AKD), who assumed office on September 23, 2024, after winning the 2024 presidential election.\n\n"
            "[Sources automatically added by system]\n\n"
            
            "⚠️ CRITICAL RULES:\n"
            "- MANDATORY: Every <think> block MUST have bold section headers\n"
            "- MANDATORY: Think BEFORE calling your first function\n"
            "- For questions about current leaders: Search, read position page, read person's bio (MUST do both!)\n"
            "- NEVER stop after reading just the position page - also read the person's bio\n"
            "- If you only read one page, your answer is incomplete - keep researching\n"
            "- Always gather comprehensive information before answering\n"
            "- Use **bold** for emphasis, never underscores\n"
            "- Do NOT manually add a Sources section - it's added automatically\n"
            "- When deploying HTML, your response should ONLY contain: [Click here to preview the HTML page](URL)\n"
            "- If you see tool results, you successfully called them. If not, you FAILED to call them.\n\n"
            
            "Remember: Think in <think> tags, then either call functions OR provide your answer!"
        )
    }

    # Add RAG-based few-shot examples to system message
    pages_read_tracker = []
    if RAG_AVAILABLE and RAG_STORE is not None:
        try:
            rag_additions = RAG_STORE.get_system_prompt_additions(question)
            if rag_additions:
                system_message["content"] += rag_additions
                print(f"📚 Added RAG examples for: {question[:50]}...")
        except Exception as e:
            print(f"Warning: Failed to retrieve RAG examples: {e}")

    progress_msg = None
    sources_used = []

    try:
        async with ctx.typing():
            messages = [system_message] + conversation_history[channel_id]
            max_iterations = 15
            iteration = 0
            assistant_message = ""
            progress_entries: List[str] = []
            
            reasoning_embed = discord.Embed(title="Reasoning", description="🤔 **Processing...**", color=0x5865F2)
            progress_msg = await ctx.send(embed=reasoning_embed)

            async def update_progress(entry: str) -> None:
                nonlocal progress_entries, progress_msg, reasoning_embed
                if not progress_msg:
                    return
                entry = (entry or "").strip()
                if not entry:
                    return
                progress_entries.append(entry)
                content = "\n\n".join(progress_entries)
                try:
                    reasoning_embed.description = content[:4096]
                    await progress_msg.edit(embed=reasoning_embed)
                except:
                    pass

            while iteration < max_iterations:
                iteration += 1

                try:
                    response = groq_client.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=messages,
                        tools=TOOLS,
                        tool_choice="auto",
                        temperature=GROQ_TEMPERATURE,
                        max_tokens=2000
                    )
                except Exception as api_error:
                    print(f"API Error on iteration {iteration}: {api_error}")
                    if iteration <= 2:
                        await update_progress("⚠️ Retrying...")
                        import asyncio
                        await asyncio.sleep(1)
                        try:
                            response = groq_client.chat.completions.create(
                                model=GROQ_MODEL,
                                messages=messages,
                                tools=TOOLS,
                                tool_choice="auto",
                                temperature=GROQ_TEMPERATURE,
                                max_tokens=2000
                            )
                        except:
                            if iteration == 1:
                                raise api_error
                            assistant_message = "I encountered an issue while researching. Please try again."
                            break
                    else:
                        raise api_error

                response_msg = response.choices[0].message
                raw_content = response_msg.content or ""
                tool_calls = response_msg.tool_calls or []

                thinking = extract_thinking(raw_content)
                if thinking:
                    has_headers = bool(re.search(r'\*\*[A-Z][^*]+\*\*', thinking))
                    if not has_headers and iteration <= 3:
                        messages.append({"role": "system", "content": "Your <think> blocks must include bold section headers. Reformat your thinking."})
                        continue
                    await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(thinking)}")
                else:
                    pass

                if not tool_calls:
                    final_thinking = extract_thinking(raw_content)
                    if final_thinking:
                        await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(final_thinking)}")
                    assistant_message = remove_thinking_tags(raw_content)
                    
                    # Clean up AI-generated content
                    assistant_message = re.sub(r'📚\s*\*\*Sources\*\*.*?(?=\n\n|$)', '', assistant_message, flags=re.DOTALL).strip()
                    assistant_message = re.sub(r'```html.*?(?=\n\n|$)', '', assistant_message, flags=re.DOTALL | re.IGNORECASE).strip()
                    assistant_message = re.sub(r'\[Wikipedia\]\(https?://[^\)]+\)', '', assistant_message).strip()
                    assistant_message = re.sub(r'\*Source:.*?\*', '', assistant_message, flags=re.IGNORECASE).strip()
                    assistant_message = re.sub(r'\[Calls? .+?\]', '', assistant_message, flags=re.IGNORECASE).strip()
                    while '\n\n\n' in assistant_message:
                        assistant_message = assistant_message.replace('\n\n\n', '\n\n')
                    
                    clean_content = remove_thinking_tags(raw_content)
                    conversation_history[channel_id].append({"role": "assistant", "content": clean_content if clean_content else "Acknowledged."})
                    break

                tool_results = []
                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    try:
                        fargs = json.loads(tool_call.function.arguments)
                    except:
                        fargs = {}
                    tool_result = ""
                    if fname == "search_wikipedia":
                        query = fargs.get('query', '')
                        await update_progress(f"🔍 **Searching Wikipedia...**\n\n> {query}")
                        tool_result = await execute_wiki_search(query)
                    elif fname == "get_wikipedia_page":
                        title = fargs.get('title', '')
                        await update_progress(f"📖 **Reading Article...**\n\n> {title}")
                        tool_result = await execute_wiki_page(title)
                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        if wiki_url not in sources_used:
                            sources_used.append(wiki_url)
                        if 'pages_read_tracker' in locals() and RAG_AVAILABLE and RAG_STORE is not None:
                            pages_read_tracker.append(title)
                            try:
                                completeness = RAG_STORE.check_research_completeness(question, pages_read_tracker)
                                if not completeness['complete']:
                                    messages.append({"role": "system", "content": f"⚠️ Research Incomplete: {completeness['reason']}"})
                            except:
                                pass
                    elif fname == "deploy_html":
                        html_value = fargs.get('value', '')
                        await update_progress(f"🌐 **Deploying HTML...**")
                        tool_result = await execute_deploy_html(html_value)
                    tool_results.append({"tool_call_id": tool_call.id, "role": "tool", "name": fname, "content": str(tool_result)})

                clean_content = remove_thinking_tags(raw_content)
                if not clean_content:
                    if tool_calls:
                        tool_names = [tc.function.name for tc in tool_calls]
                        if len(tool_names) == 1:
                            tool_name = tool_names[0]
                            if tool_name == "search_wikipedia":
                                clean_content = "Searching Wikipedia for information."
                            elif tool_name == "get_wikipedia_page":
                                clean_content = "Reading Wikipedia article."
                            elif tool_name == "deploy_html":
                                clean_content = "Deploying HTML to public URL."
                            else:
                                clean_content = f"Calling {tool_name} tool."
                        else:
                            clean_content = f"Calling tools: {', '.join(tool_names)}."
                    else:
                        clean_content = "Processing request."
                messages.append({"role": "assistant", "content": clean_content, "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in tool_calls]})
                messages.extend(tool_results)

                # After reading Wikipedia articles, prompt AI to think about what was learned
                last_tool_name = tool_results[-1].get("name", "") if tool_results else ""
                if last_tool_name == "get_wikipedia_page":
                    messages.append({"role": "system", "content": "You just read a Wikipedia article. Now think about:\n1. What information did you learn from this article?\n2. Do you need to read more information?\n3. If researching a current leader, have you read both their position page AND their bio page?\n\nThink step-by-step in a 基督 block, then either call more tools or provide your answer."})
                elif last_tool_name == "search_wikipedia":
                    messages.append({"role": "system", "content": "You just received search results. Think about:\n1. Which result(s) should you read?\n2. What's your next step?\n\nThink step-by-step in a 基督 block, then call get_wikipedia_page or provide your answer."})

            if sources_used and assistant_message:
                sources_text = "\n\n📚 **Sources**\n"
                for idx, source in enumerate(sources_used, 1):
                    sources_text += f"{idx}. [Wikipedia]({source})\n"
                assistant_message += sources_text

            if assistant_message:
                final_text = assistant_message.strip()
                while final_text:
                    await ctx.send(final_text[:1990])
                    final_text = final_text[1990:]
            else:
                await ctx.send("I couldn't generate a response. Please try again.")
    except Exception as e:
        error_text = f"❌ **Error:** {str(e)}"
        try:
            if progress_msg:
                error_embed = discord.Embed(title="Reasoning", description=error_text[:4096], color=0xED4245)
                await progress_msg.edit(embed=error_embed)
            else:
                await ctx.send(error_text)
        except:
            pass
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN missing")
        exit(1)
    bot.run(DISCORD_BOT_TOKEN)
