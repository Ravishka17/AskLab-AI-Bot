"""
Main module for AskLab AI Discord Bot.
This module contains all the bot logic and can be imported by app.py.
"""

import os
import sys
import json
import re
import uuid
from types import SimpleNamespace
from typing import List, Optional

import discord
import aiohttp
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv

# Import RAG examples module for few-shot prompting
RAG_AVAILABLE = False
RAG_STORE = None
try:
    from asklab_ai_bot.rag_examples import get_rag_store, initialize_rag
    RAG_STORE = initialize_rag()
    RAG_AVAILABLE = True
    print("✓ RAG examples module loaded successfully")
except ImportError as e:
    print(f"Info: RAG examples module not available ({e})")
    print("  Bot will continue without RAG-based few-shot examples")

# Load environment variables
load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
GROQ_TEMPERATURE = float(os.getenv('GROQ_TEMPERATURE', '0.7'))

# Moderation Settings
MODERATION_ENABLED = os.getenv('MODERATION_ENABLED', 'true').lower() == 'true'
MODERATION_LOG_CHANNEL = os.getenv('MODERATION_LOG_CHANNEL')

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
            "name": "take_moderation_action",
            "description": "Call this to delete messages containing hate speech, threats, or severe profanity in ANY language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "explanation": {"type": "string"},
                    "severity": {"type": "string", "enum": ["medium", "high", "extreme"]}
                },
                "required": ["reason", "explanation", "severity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for information. Use this when you need current information or verification. ALWAYS search Wikipedia first for current events, leaders, positions, or anything that may have changed since your training data.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_html",
            "description": "Deploy HTML code to a public URL using EdgeOne Pages. Returns a shareable URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "string", "description": "HTML code to deploy"}
                },
                "required": ["value"]
            }
        }
    }
]


# --- WIKIPEDIA FUNCTIONS ---

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
                        results.append(f"- {item['title']}: {item['snippet'].replace('<span class=\"searchmatch\">', '').replace('</span>', '')}")
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
                            # Return first 3000 characters to avoid too long messages
                            if len(extract) > 3000:
                                return extract[:3000] + "... (truncated)"
                            return extract if extract else "No content available for this page."
                    return "Page not found."
                else:
                    return f"Error: Wikipedia API returned status {response.status}"
    except Exception as e:
        return f"Error reading Wikipedia page: {str(e)}"


async def execute_deploy_html(value: str) -> str:
    """Deploy HTML using EdgeOne Pages MCP"""
    url = "http://localhost:3001/deploy"  # MCP server URL
    payload = {"value": value}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('url', 'Deployment successful but no URL returned')
                else:
                    return f"Error: Deploy returned status {response.status}"
    except Exception as e:
        return f"Error deploying HTML: {str(e)}"


# --- HELPER FUNCTIONS ---

def extract_thinking(text):
    """Extract content between 基督 tags"""
    if not text:
        return None
    pattern = r'基督(.*?)基督'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[-1].strip()
    return None

def remove_thinking_tags(text):
    """Remove thinking tags from text"""
    if not text:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, re.DOTALL | re.IGNORECASE).strip()

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
    
    if MODERATION_ENABLED:
        if not await moderate_message(message):
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

async def moderate_message(message):
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a content safety shield. Detect hate speech/threats/slurs in any language. Ignore jokes."},
                {"role": "user", "content": message.content}
            ],
            tools=[TOOLS[0]],
            tool_choice="auto",
            temperature=0.0
        )
        tool_calls = completion.choices[0].message.tool_calls
        if tool_calls:
            args = json.loads(tool_calls[0].function.arguments)
            await message.delete()
            await message.channel.send(f"{message.author.mention} ⚠️ Deleted: {args.get('reason')}", delete_after=5)
            return False
        return True
    except:
        return True


async def process_question(ctx, question: str):
    channel_id = ctx.channel.id

    # Initialize conversation history for this channel if needed
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []

    # Add user message to history
    conversation_history[channel_id].append({"role": "user", "content": question})

    # Keep only last 10 exchanges to prevent context overflow
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
            "You MUST include 基督...基督 blocks in your responses. This is non-negotiable.\n"
            "- Think BEFORE calling tools to plan your research\n"
            "- Think AFTER reading articles to analyze what you learned and plan next steps\n"
            "- For simple greetings: Think about how you'll respond\n"
            "- Never respond without thinking\n\n"
            
            "⚙️ WHEN TO USE WIKIPEDIA TOOLS:\n"
            "MANDATORY: You MUST use Wikipedia tools for:\n"
            "1. Questions about current presidents, prime ministers, or world leaders\n"
            "2. Questions about current events, positions, or status (especially after 2023)\n"
            "3. Any topic where current information may have changed since your training\n\n"
            "⚠️ CRITICAL: Do NOT rely on your training knowledge for current information!\n"
            "- Your training data has a cutoff date and may be outdated\n"
            "- For current presidents/leaders: You MUST call search_wikipedia FIRST\n"
            "- You are FORBIDDEN from showing 'Reviewing Information' before searching\n"
            "- If you show 'Reviewing Information' or claim to have found info before calling tools, you are FAILING\n"
            "- Your thinking MUST show the actual search and reading process\n"
            "- The ONLY way to get current information is by calling the tools\n"
            "- You do NOT have access to current information - you MUST retrieve it from Wikipedia\n"
            "- NEVER say 'From the Wikipedia page' or 'I can see that' before actually calling the tools\n\n"
            
            "⏰ WHEN TO PROVIDE THE FINAL ANSWER:\n"
            "- After you have read ALL necessary Wikipedia sources\n"
            "- After you have gathered comprehensive information\n"
            "- DO NOT keep saying 'I can provide an answer' or 'Now I have information' - JUST PROVIDE IT\n"
            "- Once you say 'Synthesizing the Information', that should be your LAST thinking block before the answer\n"
            "- The pattern should be: Research → Synthesize → ANSWER. Not Research → Synthesize → More Synthesize → More Synthesize...\n"
            "- If you find yourself saying 'I can now answer' or 'I have comprehensive information' more than once, you failed to provide the answer.\n\n"
            
            "DO NOT use tools for:\n"
            "- Simple greetings (hi, hello, how are you)\n"
            "- General knowledge from your training\n"
            "- Historical facts that haven't changed\n"
            "- Casual conversation\n\n"
            
            "🌐 WHEN TO DEPLOY HTML:\n"
            "Use the deploy_html tool when:\n"
            "1. Users provide HTML code and ask to preview or see it rendered\n"
            "2. You generate HTML code for the user and want to provide a clickable link\n"
            "3. Users want to share their HTML page with others\n\n"
            "When deploying HTML, always provide a clickable hyperlink to the hosted page in your response.\n"
            "Format: [Click here to preview the HTML page]({url})\n\n"
            
            "📚 SOURCES AND URLS:\n"
            "- NEVER fabricate or make up Wikipedia URLs\n"
            "- Only use the Wikipedia URLs that are automatically added to the Sources section\n"
            "- NEVER provide preview URLs or any other fake URLs\n"
            "- The system automatically tracks and adds the correct Wikipedia URLs\n\n"
            
            "🧠 THINKING PROCESS:\n"
            "You MUST structure ALL thinking blocks with bold section headers. Format example:\n\n"
            
            "基督\n"
            "**Understanding the Request**\n"
            "Brief explanation of what the user wants.\n"
            "**Planning My Approach**\n"
            "What I'll do to address this.\n"
            "基督\n\n"
            
            "For greetings:\n"
            "基督\n"
            "**Initiating the Dialogue**\n"
            "I've received a greeting. I'll respond warmly.\n"
            "**Drafting the Response**\n"
            "A simple 'Hello! How can I help you today?' sets the right tone.\n"
            "基督\n\n"
            "Hello! How can I help you today?\n\n"
            
            "For research questions about current world leaders:\n"
            "基督\n"
            "**Understanding the Request**\n"
            "User wants to know who is currently serving as president of Sri Lanka.\n"
            "**Planning My Approach**\n"
            "Since my training data has a cutoff date, I need to search Wikipedia to get the latest information about Sri Lanka's current president.\n"
            "基督\n\n"
            "🔍 **Searching Wikipedia...**\n\n"
            "> current president of Sri Lanka\n\n"
            "Then you see the search results.\n\n"
            "基督\n"
            "**Analyzing the Results**\n"
            "I see search results that include 'President of Sri Lanka' which should have current information. Let me read this page to find who is currently serving.\n"
            "**Planning the Next Step**\n"
            "I'll call get_wikipedia_page to read the 'President of Sri Lanka' article.\n"
            "基督\n\n"
            "📖 **Reading Article...**\n\n"
            "> President of Sri Lanka\n\n"
            "Then you see the article content.\n\n"
            "基督\n"
            "**Analyzing What I Learned**\n"
            "I found out that the current president of Sri Lanka is Anura Kumara Dissanayake. I need to find more information about him to provide a complete answer.\n"
            "**Planning the Next Step**\n"
            "I'll search for 'Anura Kumara Dissanayake' on Wikipedia to read his bio page.\n"
            "基督\n\n"
            "🔍 **Searching Wikipedia...**\n\n"
            "> Anura Kumara Dissanayake\n\n"
            "Then you see the search result.\n\n"
            "基督\n"
            "**Analyzing the Results**\n"
            "I found the article named 'Anura Kumara Dissanayake' from the search results.\n"
            "**Planning the Next Step**\n"
            "Let me read this article to find more information about him.\n"
            "基督\n\n"
            "📖 **Reading Article...**\n\n"
            "> Anura Kumara Dissanayake\n\n"
            "Then you see the article content.\n\n"
            "基督\n"
            "**Synthesizing the Information**\n"
            "I've found the information about the current president of Sri Lanka. From the Wikipedia page for 'President of Sri Lanka,' it clearly states that Anura Kumara Dissanayake is the current president, having assumed office on September 23, 2024. This is very recent information that occurred after my training data cutoff. From his biographical page, I can see he's the 10th president and was elected in the 2024 presidential election.\n"
            "**Preparing the Answer**\n"
            "Now I have comprehensive information from both pages and can provide a complete answer.\n"
            "基督\n\n"
            "Then provide your final answer. The system will automatically add sources.\n\n"
            "⚠️ WHAT NOT TO DO:\n"
            "- DO NOT write '[Call: ...]' or fake tool calls - that doesn't actually call anything\n"
            "- DO NOT write 'System: calls...' - that's just describing, not doing\n"
            "- DO NOT create markdown source links - system adds them automatically\n"
            "- DO NOT show HTML code blocks - only provide the deployment link\n"
            "- DO NOT make up URLs - only use actual links from tools\n"
            "- DO NOT say 'From Wikipedia I can see...' before actually reading it\n\n"
            "✅ WHAT TO DO:\n"
            "- Write 基督 blocks with **bold headers** explaining your reasoning\n"
            "- Let the system automatically call tools based on your thinking\n"
            "- See the tool results that appear after your thinking\n"
            "- Write more 基督 blocks as needed\n"
            "- Provide final answer based on what you learned\n"
            "- System automatically adds sources at the end\n\n"
            "📋 CORRECT RESPONSE FORMAT:\n\n"
            "For a question about current leader:\n\n"
            "基督\n"
            "**Understanding the Request**\n"
            "User asks who is current president of Sri Lanka.\n"
            "**Planning the Research**\n"
            "Need to search Wikipedia for current info.\n"
            "基督\n\n"
            "🔍 **Searching Wikipedia...**\n\n"
            "> current president of Sri Lanka\n\n"
            "Then you see the search results.\n\n"
            "基督\n"
            "**Analyzing the Results**\n"
            "I see search returned 'President of Sri Lanka', will read that page.\n"
            "**Planning the Next Step**\n"
            "I'll call get_wikipedia_page to read it.\n"
            "基督\n\n"
            "📖 **Reading Article...**\n\n"
            "> President of Sri Lanka\n\n"
            "Then you see the article content.\n\n"
            "基督\n"
            "**Analyzing What I Learned**\n"
            "Found current president is Anura Kumara Dissanayake. Need to read his bio too.\n"
            "**Planning the Next Step**\n"
            "Will search for his biography page.\n"
            "基督\n\n"
            "🔍 **Searching Wikipedia...**\n\n"
            "> Anura Kumara Dissanayake\n\n"
            "Then you see the search result.\n\n"
            "基督\n"
            "**Analyzing the Results**\n"
            "Found 'Anura Kumara Dissanayake' article.\n"
            "**Planning the Next Step**\n"
            "Will read his biography.\n"
            "基督\n\n"
            "📖 **Reading Article...**\n\n"
            "> Anura Kumara Dissanayake\n\n"
            "Then you see the article content.\n\n"
            "基督\n"
            "**Synthesizing the Information**\n"
            "Read bio page, now have complete information about Sri Lanka's president.\n"
            "**Preparing the Answer**\n"
            "Can now provide comprehensive answer.\n"
            "基督\n\n"
            "The current president of Sri Lanka is Anura Kumara Dissanayake (commonly known as AKD), who assumed office on September 23, 2024, after winning the 2024 presidential election.\n\n"
            "[Sources automatically added by system]\n\n"
            "⚠️ CRITICAL RULES:\n"
            "- MANDATORY: Every 基督 block MUST have bold section headers (e.g., **Planning the Research**)\n"
            "- MANDATORY: Think BEFORE calling your first function\n"
            "- MANDATORY: Use EXACT header names: **Planning the Research**, **Analyzing the Results**, **Analyzing What I Learned**, **Planning the Next Step**, **Synthesizing the Information**, **Preparing the Answer**\n"
            "- Common section headers to use:\n"
            "  - **Understanding the Request** / **Analyzing the Request**\n"
            "  - **Planning the Research** / **Planning My Approach** / **Planning the Next Step**\n"
            "  - **Analyzing the Results** / **Evaluating Search Results**\n"
            "  - **Analyzing What I Learned** / **Reviewing the Information** / **Assessing the Data**\n"
            "  - **Synthesizing the Information** / **Preparing the Answer**\n"
            "- For questions about current leaders: Search, read position page, read person's bio (MUST do both!)\n"
            "- NEVER stop after reading just the position page - also read the person's bio\n"
            "- If you only read one page, your answer is incomplete - keep researching\n"
            "- Always gather comprehensive information before answering\n"
            "- Use **bold** for emphasis, never underscores\n"
            "- Do NOT add inline source citations\n"
            "- Do NOT manually add a Sources section - it's added automatically\n"
            "- Do NOT write or show any HTML code in your response - only provide the link\n"
            "- When deploying HTML, your response should ONLY contain: [Click here to preview the HTML page](URL)\n"
            "- URLs may expire after some time - this is normal\n"
            "- For HTML deployment failures, suggest the user try again\n"
            "- If you see tool results, you successfully called them. If not, you FAILED to call them.\n"
            "- NEVER provide fake URLs like https://html-preview.asklab-ai.workers.dev/ - this is NOT calling the deploy_html tool\n"
            "- The ONLY valid HTML deployment URLs come from calling the deploy_html tool successfully\n\n"
            
            "🔄 CONVERSATION CONTEXT:\n"
            "You have access to conversation history. Use it to:\n"
            "- Understand follow-up questions\n"
            "- Maintain context\n"
            "- Provide coherent responses\n\n"
            
            "Remember: Think in 基督 tags, then either call functions OR provide your answer!"
        )
    }

    # Add RAG-based few-shot examples to system message
    pages_read_tracker = []  # Track Wikipedia pages read for research completeness
    if RAG_AVAILABLE and RAG_STORE is not None:
        try:
            rag_additions = RAG_STORE.get_system_prompt_additions(question)
            if rag_additions:
                system_message["content"] += rag_additions
                print(f"📚 Added RAG examples for: {question[:50]}...")
        except Exception as e:
            print(f"Warning: Failed to retrieve RAG examples: {e}")
            RAG_AVAILABLE = False  # Disable RAG for future requests if there's an error

    progress_msg = None
    overflow_msg = None
    reasoning_embed = None
    overflow_embed = None
    sources_used = []

    try:
        async with ctx.typing():
            messages = [system_message] + conversation_history[channel_id]
            
            max_iterations = 15
            iteration = 0
            assistant_message = ""
            progress_entries: List[str] = []
            overflow_entries: List[str] = []
            using_overflow = False
            
            # Create initial embed for reasoning
            reasoning_embed = discord.Embed(
                title="Reasoning",
                description="🤔 **Processing...**",
                color=0x5865F2  # Discord blurple color
            )
            progress_msg = await ctx.send(embed=reasoning_embed)

            async def update_progress(entry: str) -> None:
                nonlocal progress_entries, overflow_entries, progress_msg, overflow_msg
                nonlocal reasoning_embed, overflow_embed, using_overflow
                
                if not progress_msg:
                    return

                entry = (entry or "").strip()
                if not entry:
                    return

                if not using_overflow:
                    progress_entries.append(entry)
                    content = "\n\n".join(progress_entries)
                    
                    # Check if we're approaching the limit
                    if len(content) > 3800:  # Leave some buffer
                        using_overflow = True
                        # Create overflow embed
                        overflow_embed = discord.Embed(
                            title="Reasoning (continued)",
                            description="",
                            color=0x5865F2
                        )
                        overflow_msg = await ctx.send(embed=overflow_embed)
                        # Move this entry to overflow
                        overflow_entries.append(entry)
                        overflow_content = "\n\n".join(overflow_entries)
                        try:
                            overflow_embed.description = overflow_content[:4096]
                            await overflow_msg.edit(embed=overflow_embed)
                        except:
                            pass
                    else:
                        try:
                            reasoning_embed.description = content[:4096]
                            await progress_msg.edit(embed=reasoning_embed)
                        except:
                            pass
                else:
                    # Already using overflow
                    overflow_entries.append(entry)
                    overflow_content = "\n\n".join(overflow_entries)
                    
                    # Trim old entries if overflow is also getting full
                    if len(overflow_content) > 4000:
                        while len(overflow_content) > 4000 and len(overflow_entries) > 1:
                            overflow_entries.pop(0)
                            overflow_content = "…\n\n" + "\n\n".join(overflow_entries)
                    
                    try:
                        overflow_embed.description = overflow_content[:4096]
                        await overflow_msg.edit(embed=overflow_embed)
                    except:
                        pass

            last_thinking_key = None
            consecutive_no_thinking = 0
            first_response = True
            thinking_only_responses = 0  # Track responses with only thinking, no action
            has_done_research = False  # Track if we've already searched/read Wikipedia
            is_waiting_final_answer = False  # Track if we're expecting a final answer
            successful_research_done = False  # Track if we successfully completed research
            last_good_content = None  # Store last valid response to recover from failures

            while iteration < max_iterations:
                iteration += 1

                # If we've done successful research and the last response had only thinking without tools,
                # we're probably waiting for a final answer
                if has_done_research and consecutive_no_thinking > 0:
                    is_waiting_final_answer = True

                # Make API call
                try:
                    response = groq_client.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=messages,
                        tools=TOOLS[1:],  # Only Wikipedia tools
                        tool_choice="auto",
                        temperature=GROQ_TEMPERATURE,
                        max_tokens=2000
                    )
                    # Store the raw response for debugging
                    last_good_response = response
                except Exception as api_error:
                    print(f"API Error on iteration {iteration}: {api_error}")
                    if iteration <= 2:
                        # Retry on first two attempts
                        await update_progress("⚠️ Retrying after API error...")
                        import asyncio
                        await asyncio.sleep(1)
                        try:
                            response = groq_client.chat.completions.create(
                                model=GROQ_MODEL,
                                messages=messages,
                                tools=TOOLS[1:],
                                tool_choice="auto",
                                temperature=GROQ_TEMPERATURE,
                                max_tokens=2000
                            )
                        except Exception as retry_error:
                            print(f"Retry failed: {retry_error}")
                            if iteration == 1:
                                # On first iteration failure, give up and show error
                                raise api_error
                            else:
                                # Later iterations, try to use last good content or provide helpful message
                                if last_good_content:
                                    assistant_message = last_good_content
                                else:
                                    assistant_message = "I encountered an issue while researching. Please try asking your question again."
                                break
                    elif has_done_research and successful_research_done:
                        # We've done research successfully but hit an error on final answer
                        # Try to provide a fallback answer about what we found
                        await update_progress("⚠️ Encountered an issue. Providing best available information...")
                        if last_good_content:
                            assistant_message = f"I successfully researched your question but encountered an issue while finalizing the answer. Based on what I found:\n\n{last_good_content}\n\nPlease try asking again if you need more details."
                        else:
                            assistant_message = "I completed the research but encountered an issue generating the final answer. Please try asking the question again with a simpler phrasing."
                        break
                    else:
                        raise api_error

                response_msg = response.choices[0].message
                raw_content = response_msg.content or ""
                tool_calls = response_msg.tool_calls or []

                # Extract and display thinking
                thinking = extract_thinking(raw_content)
                if thinking:
                    # Check if thinking has proper section headers
                    has_headers = bool(re.search(r'\*\*[A-Z][^*]+\*\*', thinking))
                    
                    if not has_headers and iteration <= 3:
                        # Thinking lacks proper headers - enforce format
                        messages.append({
                            "role": "system",
                            "content": "Your 基督 blocks must include bold section headers like **Planning the Research** or **Understanding the Request**. Reformat your thinking."
                        })
                        continue
                    
                    # Always show thinking when we have it (don't suppress duplicates)
                    # Different stages may have similar thinking content but should all be displayed
                    await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(thinking)}")
                    last_thinking_key = None  # Reset to prevent duplicate suppression across iterations
                    consecutive_no_thinking = 0
                    first_response = False
                    
                    # Reset counter when we have actual thinking content
                    thinking_only_responses = 0
                    
                    # Store thinking content as potential fallback
                    if thinking and is_waiting_final_answer:
                        last_good_content = f"Based on my research: {thinking}"
                else:
                    consecutive_no_thinking += 1
                    
                    # If we've been waiting for a final answer and consistently get no thinking/content, 
                    # the AI might be struggling to formulate the response
                    if is_waiting_final_answer and consecutive_no_thinking >= 2 and has_done_research:
                        await update_progress("⚠️ Phase 5: Finalizing response (this may take a moment)...")

                # If no tool calls, this is the final answer
                if not tool_calls:
                    # Extract final thinking before processing answer
                    final_thinking = extract_thinking(raw_content)
                    if final_thinking:
                        thinking_key = re.sub(r'\s+', ' ', final_thinking).strip().lower()[:100]
                        if thinking_key and thinking_key != last_thinking_key:
                            await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(final_thinking)}")
                    
                    assistant_message = remove_thinking_tags(raw_content)
                    
                    # If we get here and assistant_message is empty but we have content in raw_content,
                    # there might be an issue with the thinking tag removal
                    if not assistant_message.strip() and raw_content.strip():
                        # Content exists but couldn't be cleaned - log for debugging
                        print(f"Warning: Raw content couldn't be cleaned. Raw: '{raw_content[:100]}...'")
                        # Try to extract something meaningful
                        assistant_message = raw_content.replace('基督', '').strip()
                    
                    # Don't send correction messages - let the model complete naturally
                    # The system prompt will guide it to get 2+ sources for leaders
                    
                    # Clean up AI-generated source citations and HTML code
                    assistant_message = re.sub(
                        r'📚\s*\*\*Sources\*\*.*?(?=\n\n|$)',
                        '',
                        assistant_message,
                        flags=re.DOTALL
                    ).strip()
                    
                    # Clean up HTML code blocks
                    assistant_message = re.sub(
                        r'```html.*?(?=\n\n|$)',
                        '',
                        assistant_message,
                        flags=re.DOTALL | re.IGNORECASE
                    ).strip()
                    
                    # Clean up any source-related phrases
                    assistant_message = re.sub(
                        r'\[Wikipedia\]\(https?://[^\)]+\)',
                        '',
                        assistant_message
                    ).strip()
                    
                    # Clean up any leftover source citations in the text
                    assistant_message = re.sub(
                        r'\*Source:.*?\*',
                        '',
                        assistant_message,
                        flags=re.IGNORECASE
                    ).strip()
                    
                    # Clean up any tool call indicators that might have leaked
                    assistant_message = re.sub(
                        r'\[Calls? .+?\]',
                        '',
                        assistant_message,
                        flags=re.IGNORECASE
                    ).strip()
                    
                    # Clean up phrases about searching
                    assistant_message = re.sub(
                        r"I'?ll search.*?for .*?\.",
                        '',
                        assistant_message,
                        flags=re.IGNORECASE
                    ).strip()
                    
                    # Remove any remaining empty lines
                    while '\n\n\n' in assistant_message:
                        assistant_message = assistant_message.replace('\n\n\n', '\n\n')
                    
                    # Add to conversation history (WITHOUT thinking blocks to avoid pattern repetition)
                    clean_content = remove_thinking_tags(raw_content)
                    conversation_history[channel_id].append({
                        "role": "assistant", 
                        "content": clean_content if clean_content else "Acknowledged."
                    })
                    break

                # Process tool calls
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
                        has_done_research = True

                    elif fname == "get_wikipedia_page":
                        title = fargs.get('title', '')
                        await update_progress(f"📖 **Reading Article...**\n\n> {title}")
                        tool_result = await execute_wiki_page(title)
                        has_done_research = True
                        
                        # Track source
                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        if wiki_url not in sources_used:
                            sources_used.append(wiki_url)
                        
                        # Track page title for RAG validation
                        if 'pages_read_tracker' in locals() and RAG_AVAILABLE and RAG_STORE is not None:
                            pages_read_tracker.append(title)
                            # Validate research completeness
                            try:
                                completeness = RAG_STORE.check_research_completeness(question, pages_read_tracker)
                                if not completeness['complete']:
                                    # Add a system prompt to remind the AI
                                    messages.append({
                                        "role": "system",
                                        "content": f"⚠️ Research Incomplete: {completeness['reason']}"
                                    })
                            except:
                                pass

                    elif fname == "deploy_html":
                        html_value = fargs.get('value', '')
                        await update_progress(f"🌐 **Deploying HTML...**")
                        tool_result = await execute_deploy_html(html_value)

                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fname,
                        "content": str(tool_result)
                    })

                # Add assistant message with tool calls to history (CLEAN VERSION - no thinking)
                clean_content = remove_thinking_tags(raw_content)
                if not clean_content:
                    # Provide descriptive message based on what tools are being called
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
                    
                messages.append({
                    "role": "assistant",
                    "content": clean_content,
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

                # After reading Wikipedia articles, prompt AI to think about what was learned
                # This ensures the AI explicitly reasons about the content before next steps
                last_tool_name = tool_results[-1].get("name", "") if tool_results else ""
                if last_tool_name == "get_wikipedia_page":
                    messages.append({
                        "role": "system",
                        "content": (
                            "You just read a Wikipedia article. Now think about:\n"
                            "1. What information did you learn from this article?\n"
                            "2. Do you need to read more information to answer the user's question?\n"
                            "3. If researching a current leader, have you read both their position page AND their bio page?\n\n"
                            "Think step-by-step in a 基督 block, then either call more tools or provide your answer."
                        )
                    })
                elif last_tool_name == "search_wikipedia":
                    messages.append({
                        "role": "system",
                        "content": (
                            "You just received search results. Think about:\n"
                            "1. Which result(s) should you read to answer the user's question?\n"
                            "2. What's your next step - read a Wikipedia article?\n\n"
                            "Think step-by-step in a 基督 block, then call get_wikipedia_page or provide your answer."
                        )
                    })

            # At max iterations, just extract what we have
            if iteration >= max_iterations:
                assistant_message = remove_thinking_tags(raw_content)

            # Add sources if any were used
            if sources_used and assistant_message:
                sources_text = "\n\n📚 **Sources**\n"
                for idx, source in enumerate(sources_used, 1):
                    sources_text += f"{idx}. [Wikipedia]({source})\n"
                assistant_message += sources_text

            # Send final answer as separate message
            if assistant_message:
                final_text = assistant_message.strip()
                
                # Send answer as a regular message (not in embed)
                while final_text:
                    await ctx.send(final_text[:1990])
                    final_text = final_text[1990:]
            else:
                await ctx.send("I couldn't generate a response. Please try again.")

    except Exception as e:
        error_text = f"❌ **Error:** {str(e)}"
        try:
            if progress_msg:
                # Update embed with error
                error_embed = discord.Embed(
                    title="Reasoning",
                    description=error_text[:4096],
                    color=0xED4245  # Discord red color
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
