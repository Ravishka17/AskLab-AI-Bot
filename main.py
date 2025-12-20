#!/usr/bin/env python3
import os
import json
import re
import uuid
from types import SimpleNamespace
from typing import List, Optional

import discord
import wikipedia
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
            "description": "Search Wikipedia to find article titles.",
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
            "description": "Read a Wikipedia page by its exact title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The exact Wikipedia page title"}
                },
                "required": ["title"]
            }
        }
    }
]

async def execute_wiki_search(query):
    try:
        results = wikipedia.search(query)
        if not results:
            return "No results found."
        return f"Found Page Titles: {json.dumps(results[:5])}"
    except Exception as e:
        return f"Search error: {str(e)}"

async def execute_wiki_page(title):
    try:
        page = wikipedia.page(title, auto_suggest=False)
        content = f"Summary: {page.summary}\n\nDetails: {page.content[:1500]}"
        return content
    except wikipedia.DisambiguationError as e:
        return f"Ambiguous title. Options: {', '.join(e.options[:5])}"
    except Exception as e:
        return f"Error reading page: {str(e)}"

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


def remove_tool_tags(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<search_wikipedia>.*?</search_wikipedia>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<get_wikipedia_page>.*?</get_wikipedia_page>', '', text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def clean_llm_text(text: str) -> str:
    return remove_tool_tags(remove_thinking_tags(text or "")).strip()


def format_blockquote(text: str) -> str:
    lines = (text or "").strip().splitlines() or [""]
    return "\n".join(f"> {line}" if line else ">" for line in lines)


def make_tool_call(name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=f"call_{uuid.uuid4().hex}",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments))
    )


def extract_tagged_tool_calls(text: str) -> List[SimpleNamespace]:
    if not text:
        return []

    calls: List[SimpleNamespace] = []

    for block in re.findall(r'<search_wikipedia>(.*?)</search_wikipedia>', text, flags=re.DOTALL | re.IGNORECASE):
        query = None
        m = re.search(r'<query>(.*?)</query>', block, flags=re.DOTALL | re.IGNORECASE)
        if m:
            query = m.group(1).strip()
        else:
            try:
                obj = json.loads(block.strip())
                query = (obj or {}).get('query')
            except Exception:
                query = None

        if not query:
            candidate = block.strip()
            if candidate and '<' not in candidate and '>' not in candidate:
                query = candidate

        if query:
            calls.append(make_tool_call('search_wikipedia', {'query': str(query)}))

    for block in re.findall(r'<get_wikipedia_page>(.*?)</get_wikipedia_page>', text, flags=re.DOTALL | re.IGNORECASE):
        title = None
        m = re.search(r'<title>(.*?)</title>', block, flags=re.DOTALL | re.IGNORECASE)
        if m:
            title = m.group(1).strip()
        else:
            try:
                obj = json.loads(block.strip())
                title = (obj or {}).get('title')
            except Exception:
                title = None

        if not title:
            candidate = block.strip()
            if candidate and '<' not in candidate and '>' not in candidate:
                title = candidate

        if title:
            calls.append(make_tool_call('get_wikipedia_page', {'title': str(title)}))

    return calls


def synthesize_thinking(question: str, tool_call: SimpleNamespace) -> Optional[str]:
    try:
        args = json.loads(tool_call.function.arguments)
    except Exception:
        args = {}

    if tool_call.function.name == 'search_wikipedia':
        query = args.get('query')
        if query:
            return (
                "The user is asking a current-events question. Since I don't have information after 2023, "
                f"I need to search Wikipedia. I'll start by searching for '{query}'."
            )

    if tool_call.function.name == 'get_wikipedia_page':
        title = args.get('title')
        if title:
            return f"I'll read the Wikipedia article '{title}' to extract the up-to-date information I need."

    return None

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
    
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    
    conversation_history[channel_id].append({"role": "user", "content": question})
    if len(conversation_history[channel_id]) > 10:
        conversation_history[channel_id] = conversation_history[channel_id][-10:]

    system_message = {
        "role": "system",
        "content": (
            "You are AskLab AI - a reasoning assistant with Wikipedia research capabilities.\n\n"
            "🎯 YOUR THINKING PROCESS:\n"
            "You must ALWAYS think BEFORE taking action. Your workflow is:\n\n"
            "1. <think>Plan what you need to find and what to search</think> → Then call search/read tool\n"
            "2. [Tool executes and returns results]\n"
            "3. <think>Analyze what you found and plan next step</think> → Then call next tool OR give final answer\n"
            "4. Repeat until you have complete information\n\n"
            "⚠️ CRITICAL RULES:\n"
            "- You have NO knowledge after 2023. MUST research current information.\n"
            "- ALWAYS write <think>...</think> BEFORE calling any tool\n"
            "- When calling tools, do NOT write XML-like tool tags (e.g. <search_wikipedia>...</search_wikipedia>) in your text. Use tool calling only.\n"
            "- In <think> blocks, explain: what you need, why, and what you'll do\n"
            "- After getting tool results, write another <think> about what you learned\n"
            "- Continue researching until you have comprehensive information\n"
            "- For current president/PM questions: research the position page AND the person's biographical page\n"
            "- Your final answer should NOT contain <think> tags\n\n"
            "📝 EXAMPLE FOR 'Who is the current president of Sri Lanka?':\n\n"
            "Response 1:\n"
            "<think>The user is asking about the current president of Sri Lanka. Since I don't have information after 2023, I need to search Wikipedia. I'll start by searching for 'President of Sri Lanka' to find who currently holds this position.</think>\n"
            "[Then the system will call search_wikipedia]\n\n"
            "After search results come back:\n"
            "Response 2:\n"
            "<think>Good, I found the 'President of Sri Lanka' page. Let me read this article to find out who the current president is.</think>\n"
            "[Then the system will call get_wikipedia_page('President of Sri Lanka')]\n\n"
            "After reading the position page:\n"
            "Response 3:\n"
            "<think>Alright, I found out that the current president is Anura Kumara Dissanayake. He took office in September 2024. Now I need to search for more detailed information about him by reading his biographical page on Wikipedia.</think>\n"
            "[Then the system will call get_wikipedia_page('Anura Kumara Dissanayake')]\n\n"
            "After reading his biographical page:\n"
            "Response 4:\n"
            "<think>Perfect! I now have comprehensive information. He won the 2024 election on September 21, took office September 23, leads the JVP and NPP alliance, and his victory was historic for requiring second-preference vote counting. I have all the information needed to provide a complete answer.</think>\n\n"
            "The current President of Sri Lanka is **Anura Kumara Dissanayake**.\n\n"
            "He assumed office on September 23, 2024...\n"
            "[Full detailed answer]\n\n"
            "🔑 KEY POINTS:\n"
            "- Think → Act → Think → Act → Think → Final Answer\n"
            "- NEVER skip thinking steps\n"
            "- Research thoroughly (multiple pages for complete info)\n"
            "- Only give final answer when you have all information needed"
        )
    }

    try:
        async with ctx.typing():
            messages = [system_message] + conversation_history[channel_id]
            sources_used = []
            max_iterations = 20
            iteration = 0
            last_thinking_sent_key = None
            assistant_message = ""

            while iteration < max_iterations:
                iteration += 1

                response = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    tools=TOOLS[1:],
                    tool_choice="auto",
                    temperature=GROQ_TEMPERATURE,
                    max_tokens=2000
                )

                response_msg = response.choices[0].message
                raw_content = response_msg.content or ""
                tool_calls = response_msg.tool_calls or []
                assistant_content = raw_content

                if not tool_calls and raw_content:
                    tagged_tool_calls = extract_tagged_tool_calls(raw_content)
                    if tagged_tool_calls:
                        tool_calls = tagged_tool_calls
                        assistant_content = remove_tool_tags(raw_content)

                thinking = extract_thinking(raw_content)
                if not thinking and tool_calls:
                    thinking = synthesize_thinking(question, tool_calls[0])

                if thinking:
                    thinking_key = re.sub(r'\s+', ' ', thinking).strip().lower()
                    if thinking_key and thinking_key != last_thinking_sent_key:
                        await ctx.send(f"🧠 **Thinking...**\n\n{format_blockquote(thinking)}")
                        last_thinking_sent_key = thinking_key

                if not tool_calls:
                    assistant_message = clean_llm_text(raw_content)
                    if assistant_message.strip():
                        break

                    messages.append({"role": "assistant", "content": assistant_content or raw_content or ""})
                    continue
                
                # Add assistant's response with tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_content or "",
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

                # Execute tools and display actions
                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    try:
                        fargs = json.loads(tool_call.function.arguments)
                    except Exception:
                        fargs = {}

                    tool_result = ""
                    if fname == "search_wikipedia":
                        query = fargs.get('query', '')
                        search_msg = f"🔍 **Searching Wikipedia...**\n\n> \"{query}\""
                        await ctx.send(search_msg)
                        tool_result = await execute_wiki_search(query)
                        
                    elif fname == "get_wikipedia_page":
                        title = fargs.get('title', '')
                        read_msg = f"📖 **Reading Article...**\n\n> \"{title}\""
                        await ctx.send(read_msg)
                        tool_result = await execute_wiki_page(title)
                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        if wiki_url not in sources_used:
                            sources_used.append(wiki_url)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fname,
                        "content": str(tool_result)
                    })
            
            # If max iterations reached
            if iteration >= max_iterations:
                assistant_message = "I've conducted extensive research but need to conclude. Based on what I found:\n\n[Provide summary]"

            assistant_message = assistant_message.strip()
            conversation_history[channel_id].append({"role": "assistant", "content": assistant_message})
            
            # Add sources with markdown links
            if sources_used and assistant_message:
                sources_text = "\n\n📚 **Sources**\n\n"
                for idx, source in enumerate(sources_used, 1):
                    # Extract page title from URL for display
                    page_title = source.split('/wiki/')[-1].replace('_', ' ')
                    sources_text += f"{idx}. [wikipedia.org]({source})\n"
                assistant_message += sources_text
            
            # Send final answer
            if assistant_message:
                if len(assistant_message) > 2000:
                    chunks = [assistant_message[i:i+1990] for i in range(0, len(assistant_message), 1990)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(assistant_message)
            else:
                await ctx.send("I couldn't generate a response. Please try again.")

    except Exception as e:
        await ctx.send(f"❌ **Error:** {str(e)}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN missing")
        exit(1)
    bot.run(DISCORD_BOT_TOKEN)
