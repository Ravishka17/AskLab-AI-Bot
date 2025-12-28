#!/usr/bin/env python3
import os
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

# Load environment variables
load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'moonshotai/kimi-k2-instruct-0905') 
GROQ_TEMPERATURE = float(os.getenv('GROQ_TEMPERATURE', '0.6'))

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
            "description": "Search Wikipedia to find article titles. Use this when you need to find information that may have changed after 2023 or when you need to verify current facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search term"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_wikipedia_page",
            "description": "Read a Wikipedia page by its exact title using the official Wikipedia API. Use this after searching to get detailed information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The exact Wikipedia page title"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_html",
            "description": "Deploy HTML code to a public URL using EdgeOne MCP. The AI should provide the HTML code and this tool will host it, returning a hyperlink to the hosted page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "string", "description": "The HTML code to deploy"}
                },
                "required": ["value"]
            }
        }
    }
]

async def execute_wiki_search(query):
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": "5"  # Changed to string
            }
            headers = {
                "User-Agent": "AskLab-AI-Discord-Bot/1.0 (https://github.com/yourusername/yourrepo)"
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    search_results = data.get("query", {}).get("search", [])
                    titles = [result["title"] for result in search_results]
                    return json.dumps({"results": titles})
                else:
                    error_text = await response.text()
                    print(f"Wikipedia search error: HTTP {response.status} - {error_text}")
                    return json.dumps({"results": [], "error": f"HTTP {response.status}: {error_text}"})
    except Exception as e:
        print(f"Exception in Wikipedia search: {str(e)}")
        return json.dumps({"results": [], "error": str(e)})

async def execute_wiki_page(title):
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "prop": "extracts",
                "explaintext": "1",  # Use string "1" instead of boolean True
                "titles": title,
                "format": "json",
                "exlimit": "1"  # Use string "1" instead of integer
            }
            headers = {
                "User-Agent": "AskLab-AI-Discord-Bot/1.0 (https://github.com/yourusername/yourrepo)"
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data.get("query", {}).get("pages", {})
                    
                    if not pages:
                        return f"No page data found for '{title}'"
                    
                    # Get the first page (there should only be one)
                    page_id = list(pages.keys())[0]
                    page_data = pages[page_id]
                    
                    if "missing" in page_data:
                        return f"Page '{title}' not found."
                    
                    if page_data.get("redirect"):  # Check if it's a redirect
                        return f"Page '{title}' is a redirect. Use the target page title instead."
                    
                    title_text = page_data.get("title", title)
                    extract = page_data.get("extract", "")
                    
                    # Handle disambiguation pages
                    if extract.startswith(f"{title_text} may refer to:"):
                        # Extract disambiguation options
                        lines = extract.split("\n")[1:]  # Skip the first line
                        options = []
                        for line in lines:
                            if line.strip().startswith("•"):
                                option = line.strip("• ").split("(")[0].strip()
                                if option and option != title_text and len(options) < 5:
                                    options.append(option)
                        return f"Ambiguous title. Options: {', '.join(options)}"
                    
                    summary = extract[:500] if extract else ""
                    details = extract[500:2000] if len(extract) > 500 else ""
                    
                    content = f"Summary: {summary}"
                    if details:
                        content += f"\n\nDetails: {details}"
                    
                    return content
                else:
                    error_text = await response.text()
                    print(f"Wikipedia page error: HTTP {response.status} - {error_text}")
                    return f"Error reading page: HTTP {response.status}: {error_text}"
    except Exception as e:
        print(f"Exception in Wikipedia page fetch: {str(e)}")
        return f"Error reading page: {str(e)}"

async def execute_deploy_html(html_content):
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://mcp-on-edge.edgeone.app/mcp-server"
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "deploy-html",
                    "arguments": {
                        "value": html_content
                    }
                }
            }
            headers = {"Content-Type": "application/json"}
            
            print(f"Making MCP deployment request to {url}")
            async with session.post(url, json=payload, headers=headers) as response:
                response_text = await response.text()
                print(f"MCP Response status: {response.status}")
                print(f"MCP Response body: {response_text[:500]}")
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError as json_error:
                        print(f"JSON decode error: {json_error}")
                        return json.dumps({"success": False, "error": f"Invalid JSON response: {response_text[:500]}"})
                    
                    if "error" in data:
                        # MCP returned an error
                        error_data = data.get("error", {})
                        error_message = error_data.get("message", str(error_data))
                        return json.dumps({"success": False, "error": f"MCP Error: {error_message}"})
                    
                    result = data.get("result", {})
                    
                    # Try multiple possible response formats
                    share_url = ""
                    
                    # Format 1: result.shareUrl (original format)
                    if "shareUrl" in result:
                        share_url = result["shareUrl"]
                    # Format 2: result.content[0].text (current format from logs)
                    elif "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                        content_item = result["content"][0]
                        if isinstance(content_item, dict) and "text" in content_item:
                            share_url = content_item["text"]
                    # Format 3: result.content as string
                    elif "content" in result and isinstance(result["content"], str):
                        share_url = result["content"]
                    
                    if share_url:
                        # If it's already a proper share URL, return it directly
                        if "mcp.edgeone.site/share/" in share_url:
                            return json.dumps({"success": True, "url": share_url})
                        
                        # Check if it's a COS URL and convert to the proper share URL format
                        if "cos.accelerate.myqcloud.com" in share_url:
                            # Extract the filename (UUID) from the COS URL
                            # Format: https://mcp-1253240811.cos.accelerate.myqcloud.com/{uuid}.html
                            filename = share_url.split("/")[-1]  # Gets {uuid}.html
                            file_id = filename.replace(".html", "")  # Remove .html extension
                            
                            # Construct the proper share URL format
                            # Format: https://mcp.edgeone.site/share/{id}
                            proper_url = f"https://mcp.edgeone.site/share/{file_id}"
                            return json.dumps({"success": True, "url": proper_url})
                        else:
                            # Already in correct format (direct share URL)
                            return json.dumps({"success": True, "url": share_url})
                    else:
                        error_msg = f"No share URL found in result. Response: {data}"
                        print(error_msg)
                        return json.dumps({"success": False, "error": error_msg})
                else:
                    error_msg = f"HTTP {response.status}: {response_text[:500]}"
                    print(error_msg)
                    return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        import traceback
        error_msg = f"Exception in execute_deploy_html: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return json.dumps({"success": False, "error": str(e)})

def extract_thinking(text):
    if not text:
        return None
    pattern = r'<think>(.*?)</think>'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[-1].strip()
    return None

def remove_thinking_tags(text):
    if not text:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE).strip()

def format_blockquote(text: str) -> str:
    """Format text as blockquote with clean structure"""
    if not text:
        return ""
    
    lines = text.strip().splitlines()
    formatted = []
    
    for line in lines:
        line = line.strip()
        if not line:
            # Skip empty lines entirely
            continue
        elif line.startswith("**") and line.endswith("**"):
            # Section headers - add spacing before (except first)
            if formatted:
                formatted.append("")  # Blank line before header
            formatted.append(f"> {line}")
        else:
            # Regular content
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
            "You MUST include <think>...</think> blocks in EVERY response. This is non-negotiable.\n"
            "- For questions requiring research: Think BEFORE calling tools\n"
            "- For simple greetings: Think about how you'll respond\n"
            "- Never respond without thinking first\n\n"
            
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
            "- Once you say 'Synthesizing the Information', that should be your LAST thinking block\n"
            "- Immediately after your </think> closing tag, write the actual answer\n"
            "- The pattern is: <think>...**Synthesizing the Information**...</think>WRITE ANSWER HERE\n"
            "- DO NOT put MORE thinking after synthesizing - ANSWER IMMEDIATELY\n\n"
            
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
            
            "<think>\n"
            "**Understanding the Request**\n"
            "Brief explanation of what the user wants.\n"
            "**Planning My Approach**\n"
            "What I'll do to address this.\n"
            "</think>\n\n"
            
            "For greetings:\n"
            "<think>\n"
            "**Initiating the Dialogue**\n"
            "I've received a greeting. I'll respond warmly.\n"
            "**Drafting the Response**\n"
            "A simple 'Hello! How can I help you today?' sets the right tone.\n"
            "</think>\n\n"
            "Hello! How can I help you today?\n\n"
            
            "For research questions about current world leaders:\n"
            "<think>\n"
            "**Understanding the Request**\n"
            "User wants to know about the current president of Sri Lanka.\n"
            "**Planning My Approach**\n"
            "I need to search Wikipedia to get current information since my training is outdated.\n"
            "</think>\n\n"
            "Then the system will call search_wikipedia with your query and show the results.\n\n"
            "<think>\n"
            "**Evaluating Search Results**\n" 
            "I see search results. Now I need to read the actual Wikipedia pages to get details.\n"
            "</think>\n\n"
            "Then the system will call get_wikipedia_page and show you the content.\n\n"
            "<think>\n"
            "**Analyzing Information**\n"
            "I found the current president's name. To provide a complete answer, I should also read their bio page.\n"
            "</think>\n\n"
            "Then the system calls get_wikipedia_page again for the bio.\n\n"
            "<think>\n"
            "**Preparing the Answer**\n"
            "Now I have information from both pages and can provide a complete answer.\n"
            "</think>\n\n"
            "Then provide your final answer. The system will automatically add sources.\n\n"
            "⚠️ WHAT NOT TO DO:\n"
            "- DO NOT write '[Call: ...]' or fake tool calls - that doesn't actually call anything\n"
            "- DO NOT write 'System: calls...' - that's just describing, not doing\n"
            "- DO NOT create markdown source links - system adds them automatically\n"
            "- DO NOT show HTML code blocks - only provide the deployment link\n"
            "- DO NOT make up URLs - only use actual links from tools\n"
            "- DO NOT say 'From Wikipedia I can see...' before actually reading it\n\n"
            "✅ WHAT TO DO:\n"
            "- Write <think> blocks with **bold headers** explaining your reasoning\n"
            "- Let the system automatically call tools based on your thinking\n"
            "- See the tool results that appear after your thinking\n"
            "- Write more <think> blocks as needed\n"
            "- Provide final answer based on what you learned\n"
            "- System automatically adds sources at the end\n\n"
            "📋 CORRECT RESPONSE FORMAT:\n\n"
            "For a question about current leader:\n\n"
            "<think>\n"
            "**Understanding the Request**\n"
            "User asks who is current president of Sri Lanka.\n"
            "**Planning the Research**\n"
            "Need to search Wikipedia for current info.\n"
            "</think>\n\n"
            "<think>\n"
            "**Analyzing the Results**\n"
            "See search returned 'President of Sri Lanka', will read that page.\n"
            "</think>\n\n"
            "<think>\n"
            "**Reviewing the Information**\n"
            "Read position page, found president's name. Need bio page too.\n"
            "</think>\n\n"
            "<think>\n"
            "**Synthesizing the Information**\n"
            "Read bio page, now have complete information.\n"
            "</think>\n\n"
            "The current president of Sri Lanka is Anura Kumara Dissanayake, who took office on September 23, 2024. He was elected in the 2024 presidential election.\n\n"
            "[Sources automatically added by system]\n"
            
            "⚠️ CRITICAL RULES:\n"
            "- MANDATORY: Every <think> block MUST have bold section headers (e.g., **Planning the Research**)\n"
            "- MANDATORY: Think BEFORE calling your first function\n"
            "- MANDATORY: Use EXACT header names: **Planning the Research**, **Analyzing the Results**, **Reviewing the Information**, **Synthesizing the Information**\n"
            "- Common section headers to use:\n"
            "  - **Understanding the Request** / **Analyzing the Request**\n"
            "  - **Planning the Research** / **Planning My Approach**\n"
            "  - **Analyzing the Results** / **Evaluating Search Results**\n"
            "  - **Reviewing the Information** / **Assessing the Data**\n"
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
            "- The ONLY valid HTML deployment URLs come from calling the deploy_html tool successfully\n"
            
            "🔄 CONVERSATION CONTEXT:\n"
            "You have access to conversation history. Use it to:\n"
            "- Understand follow-up questions\n"
            "- Maintain context\n"
            "- Provide coherent responses\n\n"
            
            "Remember: Think in <think> tags, then either call functions OR provide your answer!"
        )
    }

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

            while iteration < max_iterations:
                iteration += 1

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
                except Exception as api_error:
                    print(f"API Error on iteration {iteration}: {api_error}")
                    if iteration <= 2:
                        # Retry on first two attempts
                        await update_progress("⚠️ Retrying...")
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
                                # Later iterations, continue with fallback
                                assistant_message = "I encountered an issue while researching. Please try asking your question again."
                                break
                    else:
                        raise api_error

                response_msg = response.choices[0].message
                raw_content = response_msg.content or ""
                tool_calls = response_msg.tool_calls or []

                # Extract and display thinking
                thinking = extract_thinking(raw_content)
                if thinking:
                    await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(thinking)}")
                    consecutive_no_thinking = 0
                    first_response = False
                else:
                    consecutive_no_thinking += 1

                # If no tool calls, this is the final answer
                if not tool_calls:
                    # Extract final thinking before processing answer
                    final_thinking = extract_thinking(raw_content)
                    if final_thinking:
                        thinking_key = re.sub(r'\s+', ' ', final_thinking).strip().lower()[:100]
                        if thinking_key and thinking_key != last_thinking_key:
                            await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(final_thinking)}")
                    
                    assistant_message = remove_thinking_tags(raw_content)
                    
                    # Don't send correction messages - let the model complete naturally
                    # The system prompt will guide it to get 2+ sources for leaders
                    
                    # Clean up AI-generated source citations, URLs, and duplicate sources
                    assistant_message = re.sub(
                        r'## Sources.*?(?=\n\n|$)',
                        '',
                        assistant_message,
                        flags=re.DOTALL | re.IGNORECASE
                    ).strip()
                    
                    assistant_message = re.sub(
                        r'\[Wikipedia\]\(https?://[^\)]+\)',
                        '',
                        assistant_message,
                        flags=re.IGNORECASE
                    ).strip()
                    
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
                    
                    # Remove markdown links the AI might generate
                    assistant_message = re.sub(
                        r'\[([^\]]+)\]\(https?://[^\)]+\)',  
                        r'\1',
                        assistant_message
                    ).strip()
                    
                    # Clean up any leftover source citations
                    assistant_message = re.sub(
                        r'\*Source:.*?\*',
                        '',
                        assistant_message,
                        flags=re.IGNORECASE
                    ).strip()
                    
                    # Remove any tool call leak patterns
                    assistant_message = re.sub(
                        r'\[Calls? .*?\]',
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
