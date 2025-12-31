"""
AskLab AI Bot - Main Module
A Discord bot that uses Groq AI with Wikipedia research capabilities.
"""

import os
import sys
import json
import re
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

# Initialize bot with prefix commands
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Conversation history per channel
conversation_history = {}

# --- TOOL DEFINITIONS ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for information. Use this to find articles about current events, people, or topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for Wikipedia"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_wikipedia_page",
            "description": "Read the full content of a Wikipedia article. Use the exact title from search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Exact Wikipedia article title to read"}
                },
                "required": ["title"]
            }
        }
    }
]

# --- WIKIPEDIA API FUNCTIONS ---

async def execute_wiki_search(query: str) -> str:
    """Execute Wikipedia search using the official API"""
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
        "User-Agent": "AskLab-AI-Bot/1.0 (Discord Bot; +https://github.com/AskLab-AI/Discord-Bot)"
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
        return f"Error searching Wikipedia: {str(e)}"


async def execute_wiki_page(title: str) -> str:
    """Execute Wikipedia page read using the official API"""
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
        "User-Agent": "AskLab-AI-Bot/1.0 (Discord Bot; +https://github.com/AskLab-AI/Discord-Bot)"
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
                            return extract if extract else "No content available for this page."
                    return "Page not found."
                else:
                    return f"Error: Wikipedia API returned status {response.status}"
    except Exception as e:
        return f"Error reading Wikipedia page: {str(e)}"


# --- HELPER FUNCTIONS ---

def extract_thinking(text: str) -> str | None:
    """Extract content between <think> tags"""
    if not text:
        return None
    pattern = r'<think>(.*?)</think>'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[-1].strip() if matches else None


def remove_thinking_tags(text: str) -> str:
    """Remove <think> tags from text"""
    if not text:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, re.DOTALL).strip()


def format_blockquote(text: str) -> str:
    """Format text as blockquote with clean structure"""
    if not text:
        return ""
    
    lines = text.strip().splitlines()
    formatted = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        formatted.append(f"> {line}")
    
    return "\n".join(formatted)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('✅ AskLab AI Bot: ONLINE')


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
    """Process a user question with Wikipedia research capabilities"""
    channel_id = ctx.channel.id
    
    # Initialize conversation history for this channel
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    
    # Add user message to history
    conversation_history[channel_id].append({"role": "user", "content": question})
    
    # Keep only last 10 exchanges
    if len(conversation_history[channel_id]) > 20:
        conversation_history[channel_id] = conversation_history[channel_id][-20:]

    # System prompt with explicit thinking requirements
    system_message = {
        "role": "system",
        "content": (
            "You are AskLab AI - a helpful reasoning assistant with Wikipedia research capabilities.\n\n"
            "🎯 YOUR CORE CAPABILITIES:\n"
            "- Answer questions using your training knowledge\n"
            "- Research current information on Wikipedia when needed\n"
            "- Think step-by-step using <think> tags\n\n"
            "⚠️ MANDATORY REQUIREMENTS:\n"
            "1. ALL thinking MUST be wrapped in <think>...</think> tags\n"
            "2. Thinking MUST use section headers like **Planning the Research**\n"
            "3. NEVER write thinking as plain text - it MUST be in <think> tags\n"
            "4. Let the SYSTEM call tools - don't describe calling them\n"
            "5. For current leaders: search position page AND biography page\n\n"
            "📋 EXACT FORMAT FOR CURRENT LEADERS:\n\n"
            "<think>\n"
            "**Planning the Research**\n"
            "I need to find who is the current president of [Country].\n"
            "</think>\n\n"
            "[SYSTEM calls search_wikipedia automatically]\n\n"
            "<think>\n"
            "**Analyzing Results**\n"
            "I see 'President of [Country]' in the search results. I'll read this page.\n"
            "</think>\n\n"
            "[SYSTEM calls get_wikipedia_page and shows results]\n\n"
            "<think>\n"
            "**Reviewing Information**\n"
            "The current president is [Name]. I need their biography too.\n"
            "</think>\n\n"
            "[SYSTEM calls search and read for biography]\n\n"
            "<think>\n"
            "**Synthesizing Information**\n"
            "From both sources, I have complete information.\n"
            "</think>\n\n"
            "[NOW provide final answer below, system adds sources automatically]\n\n"
            "❌ ERRORS TO AVOID:\n"
            "- NEVER generate fake tool results like '🔍 Searching Wikipedia > query'\n"
            "- NEVER use XML tags like <function_calls> - only <think> for thinking\n"
            "- ALWAYS use <think> tags with proper section headers\n"
            "- Let the SYSTEM handle tool execution, don't describe it"
        )
    }

    progress_msg = None
    sources_used = []
    has_done_research = False

    try:
        async with ctx.typing():
            # Build messages array
            messages = [system_message] + conversation_history[channel_id]
            
            max_iterations = 15
            iteration = 0
            assistant_message = ""
            progress_entries = []
            
            # Create reasoning embed
            reasoning_embed = discord.Embed(
                title="Reasoning",
                description="🤔 **Processing...**",
                color=0x5865F2
            )
            progress_msg = await ctx.send(embed=reasoning_embed)

            async def update_progress(entry: str):
                """Update the reasoning embed with new information"""
                nonlocal progress_entries, progress_msg, reasoning_embed
                if not progress_msg:
                    return
                
                entry = entry.strip()
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

                # Call Groq API
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
                            await ctx.send("I encountered an issue. Please try again.")
                            return
                    else:
                        raise api_error

                response_msg = response.choices[0].message
                raw_content = response_msg.content or ""
                tool_calls = response_msg.tool_calls or []

                # Extract thinking from <think> tags (present means the AI is thinking, not a final answer)
                thinking = extract_thinking(raw_content)
                if thinking:
                    await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(thinking)}")
                
                # If no tool calls, this is the final answer
                if not tool_calls:
                    # Extract final thinking if present
                    final_thinking = extract_thinking(raw_content)
                    if final_thinking:
                        await update_progress(f"🧠 **Finalizing...**\n\n{format_blockquote(final_thinking)}")
                    
                    # Get the answer (remove thinking tags)
                    assistant_message = remove_thinking_tags(raw_content)
                    
                    # Clean up any AI-generated source markers
                    assistant_message = re.sub(
                        r'📚\s*\*\*Sources\*\*.*?(?=\n\n|$)',
                        '',
                        assistant_message,
                        flags=re.DOTALL
                    ).strip()
                    
                    # Add sources if we have any
                    if sources_used:
                        sources_text = "\n\n📚 **Sources**\n"
                        for idx, source in enumerate(sources_used, 1):
                            sources_text += f"{idx}. [Wikipedia]({source})\n"
                        assistant_message += sources_text
                    
                    # Add to conversation history
                    clean_content = remove_thinking_tags(raw_content)
                    conversation_history[channel_id].append({
                        "role": "assistant",
                        "content": clean_content if clean_content else assistant_message
                    })
                    
                    # Send final answer
                    while assistant_message:
                        await ctx.send(assistant_message[:1990])
                        assistant_message = assistant_message[1990:]
                    
                    break

                # Process tool calls
                tool_results = []
                
                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    fargs = json.loads(tool_call.function.arguments)
                    tool_result = ""
                    
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
                        
                        # Track source URL
                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        if wiki_url not in sources_used:
                            sources_used.append(wiki_url)
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fname,
                        "content": str(tool_result)
                    })
                
                # Add assistant message (with tool calls) to history
                messages.append({
                    "role": "assistant",
                    "content": f"Calling {len(tool_calls)} tool(s)",
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
                
                # Add tool results to messages
                messages.extend(tool_results)

            # Max iterations reached
            if iteration >= max_iterations:
                await ctx.send("I couldn't complete the research within the time limit. Please try rephrasing your question.")

    except Exception as e:
        error_text = f"❌ **Error:** {str(e)}"
        try:
            if progress_msg:
                error_embed = discord.Embed(
                    title="Reasoning",
                    description=error_text[:4096],
                    color=0xED4245
                )
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
