#!/usr/bin/env python3
"""
AskLab AI Bot - Pterodactyl Entry Point
Self-contained version for panel hosting
"""

import os
import sys
import json
import re
import asyncio
import aiohttp
import discord
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'moonshotai/kimi-k2-instruct-0905')
GROQ_TEMPERATURE = float(os.getenv('GROQ_TEMPERATURE', '0.7'))

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

conversation_history = {}

# --- TOOL DEFINITIONS ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_wikipedia_page",
            "description": "Read Wikipedia article",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Article title"}
                },
                "required": ["title"]
            }
        }
    }
]

# --- WIKIPEDIA FUNCTIONS ---

async def execute_wiki_search(query: str) -> str:
    """Execute Wikipedia search"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "utf8": True,
        "limit": 10
    }
    headers = {
        "User-Agent": "AskLab-AI-Bot/1.0 (Discord Bot)"
    }
    
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
                else:
                    return f"Error: Wikipedia API returned status {response.status}"
    except Exception as e:
        return f"Error: {str(e)}"


async def execute_wiki_page(title: str) -> str:
    """Execute Wikipedia page read"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": True,
        "titles": title,
        "format": "json",
        "utf8": True,
        "redirects": True
    }
    headers = {
        "User-Agent": "AskLab-AI-Bot/1.0 (Discord Bot)"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data.get('query', {}).get('pages', {})
                    for page_id, page_content in pages.items():
                        if page_id != '-1':
                            extract = page_content.get('extract', '')
                            if len(extract) > 3000:
                                return extract[:3000] + "... (truncated)"
                            return extract if extract else "No content available."
                    return "Page not found."
                else:
                    return f"Error: Wikipedia API returned status {response.status}"
    except Exception as e:
        return f"Error: {str(e)}"


# --- HELPER FUNCTIONS ---

def extract_thinking(text: str) -> str | None:
    """Extract content between <think> tags"""
    if not text:
        return None
    matches = re.findall(r'<think>(.*?)</think>', text, re.DOTALL)
    return matches[-1].strip() if matches else None


def remove_thinking_tags(text: str) -> str:
    """Remove <think> tags"""
    if not text:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


def format_blockquote(text: str) -> str:
    """Format as blockquote"""
    if not text:
        return ""
    return '\n'.join(f"> {line}" for line in text.strip().split('\n') if line.strip())


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('✅ Bot ready')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if bot.user in message.mentions:
        question = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if question:
            ctx = type('Context', (), {
                'channel': message.channel,
                'send': message.channel.send,
                'author': message.author,
                'typing': message.channel.typing
            })
            await bot.loop.create_task(process_question(ctx, question))
        return
    
    await bot.process_commands(message)


async def process_question(ctx, question: str):
    """Process user question with Wikipedia research"""
    channel_id = ctx.channel.id
    
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    
    conversation_history[channel_id].append({"role": "user", "content": question})
    
    if len(conversation_history[channel_id]) > 20:
        conversation_history[channel_id] = conversation_history[channel_id][-20:]
    
    # System prompt - ULTRA EXPLICIT INSTRUCTIONS
    system_message = {
        "role": "system",
        "content": (
            "You are AskLab AI - a helpful reasoning assistant with Wikipedia research capabilities.\n\n"
            "🎯 CORE CAPABILITIES:\n"
            "- Answer questions using training knowledge\n"
            "- Research current information on Wikipedia\n"
            "- Think step-by-step using <think> tags\n\n"
            "⚠️ ULTRA CRITICAL - READ CAREFULLY:\n"
            "1. Wrap ONLY your THINKING in <think>...</think> tags\n"
            "2. Use section headers like **Planning the Research** INSIDE think tags\n"
            "3. Let the SYSTEM call tools - DON'T describe "[SYSTEM: calls tools]"\n"
            "4. For current leaders: search AND read biography (2 pages)\n"
            "5. AFTER </think> tags, provide FINAL ANSWER (no tags around it)\n"
            "6. DON'T write fake actions: "[SYSTEM: Shows article]" is WRONG\n"
            "7. DON'T describe what system does - just THINK and ANSWER\n\n"
            "✅ CORRECT PATTERN:\n\n"
            "<think>\n"
            "**Planning the Research**\n"
            "I need to find who is current president of Sri Lanka.\n"
            "</think>\n\n"
            "<think>\n"
            "**Analyzing Search Results**\n"
            "I see 'President of Sri Lanka' in results. Will read this.\n"
            "</think>\n\n"
            "<think>\n"
            "**Reviewing Article**\n"
            "Found current president is Anura Kumara Dissanayake. Need bio too.\n"
            "</think>\n\n"
            "<think>\n"
            "**Synthesizing Information**\n"
            "From both pages: Current president is Anura Kumara Dissanayake, took office Sept 23, 2024, represents NPP coalition.\n"
            "</think>\n\n"
            "The current president of Sri Lanka is Anura Kumara Dissanayake, who took office on September 23, 2024, after winning the 2024 presidential election. He represents the National People's Power (NPP) coalition and is the first Sri Lankan president elected from outside the country's traditional political parties.\n\n"
            "❌ DEADLY ERRORS THAT WILL GET YOU FIRED:\n"
            "- [SYSTEM: Calls tools] ← WRONG! Don't write this!\n"
            "- <answer>text</answer> ← WRONG! No tags around final answer!\n"
            "- **Synthesizing** (in thinking) then **Finalizing...** (more thinking) ← TOO MUCH!\n"
            "- 🔍 **Searching** > query ← FAKE! Don't generate fake searches!"
        )
    }
    
    progress_msg = None
    sources_used = []
    has_done_research = False
    
    try:
        async with ctx.typing():
            messages = [system_message] + conversation_history[channel_id]
            
            max_iterations = 15
            iteration = 0
            assistant_message = ""
            progress_entries = []
            
            # Create embed
            reasoning_embed = discord.Embed(
                title="Reasoning",
                description="🤔 **Processing...**",
                color=0x5865F2
            )
            progress_msg = await ctx.send(embed=reasoning_embed)
            
            async def update_progress(entry: str):
                """Update reasoning embed"""
                nonlocal progress_entries, progress_msg, reasoning_embed
                if not progress_msg:
                    return
                progress_entries.append(entry.strip())
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
                except Exception as e:
                    print(f"API Error: {e}")
                    if iteration <= 2:
                        await update_progress("⚠️ Retrying...")
                        await asyncio.sleep(1)
                        continue
                    else:
                        await ctx.send("I encountered an issue. Please try again.")
                        return
                
                response_msg = response.choices[0].message
                raw_content = response_msg.content or ""
                tool_calls = response_msg.tool_calls or []
                
                # Extract thinking
                thinking = extract_thinking(raw_content)
                if thinking:
                    await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(thinking)}")
                
                # No tool calls = final answer
                if not tool_calls:
                    final_thinking = extract_thinking(raw_content)
                    if final_thinking:
                        await update_progress(f"🧠 **Finalizing...**\n\n{format_blockquote(final_thinking)}")
                    
                    assistant_message = remove_thinking_tags(raw_content)
                    
                    # SCRUB FAKE SYSTEM MARKERS: Remove any fake [SYSTEM: ...] text
                    assistant_message = re.sub(r'\[SYSTEM:[^\]]+\]', '', assistant_message).strip()
                    
                    # ERROR RECOVERY: If answer is empty but we have thinking,
                    # the AI may have put the answer inside <think> tags incorrectly
                    if not assistant_message.strip() and final_thinking:
                        print("WARNING: AI put answer inside <think> tags. Attempting recovery...")
                        # Try to extract answer from after the Synthesizing section
                        if "**Synthesizing" in final_thinking:
                            parts = final_thinking.split("**Synthesizing")
                            if len(parts) > 1:
                                after_synth = parts[1]
                                # Remove any remaining section headers
                                answer = re.sub(r'\*\*[^*]+\*\*', '', after_synth).strip()
                                if answer:
                                    assistant_message = answer
                                    print(f"Recovered answer: {answer[:50]}...")
                    
                    # Clean up and add sources
                    assistant_message = re.sub(r'📚\s*\*\*Sources\*\*.*?(?=\n\n|$)', '', assistant_message, flags=re.DOTALL).strip()
                    
                    if sources_used:
                        sources_text = "\n\n📚 **Sources**\n"
                        for idx, source in enumerate(sources_used, 1):
                            sources_text += f"{idx}. [Wikipedia]({source})\n"
                        assistant_message += sources_text
                    
                    # Update conversation history
                    clean_content = remove_thinking_tags(raw_content)
                    conversation_history[channel_id].append({
                        "role": "assistant",
                        "content": clean_content if clean_content else assistant_message
                    })
                    
                    # Send answer
                    while assistant_message:
                        await ctx.send(assistant_message[:1990])
                        assistant_message = assistant_message[1990:]
                    
                    break
                
                # Process tool calls
                tool_results = []
                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    fargs = json.loads(tool_call.function.arguments)
                    
                    if fname == "search_wikipedia":
                        query = fargs.get('query', '')
                        await update_progress(f"🔍 **Searching Wikipedia...**\n\n> {query}")
                        tool_result = await execute_wiki_search(query)
                        has_done_research = True
                    elif fname == "get_wikipedia_page":
                        title = fargs.get('title', '')
                        await update_progress(f"📖 **Reading Article...**\n\n> {title}")
                        tool_result = await execute_wiki_page(title)
                        has_done_research = True
                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        if wiki_url not in sources_used:
                            sources_used.append(wiki_url)
                    else:
                        tool_result = "Unknown tool"
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fname,
                        "content": str(tool_result)
                    })
                
                # Add to message history
                messages.append({
                    "role": "assistant",
                    "content": f"Called {len(tool_calls)} tool(s)",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in tool_calls
                    ]
                })
                messages.extend(tool_results)
            
            # Max iterations
            if iteration >= max_iterations:
                await ctx.send("I couldn't complete within the time limit. Please try rephrasing.")
    
    except Exception as e:
        error_text = f"❌ **Error:** {str(e)}"
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        await ctx.send(error_text)


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN missing")
        exit(1)
    bot.run(DISCORD_BOT_TOKEN)

