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
last_subject_by_channel = {}

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
        return json.dumps({"results": results[:5]})
    except Exception as e:
        return json.dumps({"results": [], "error": str(e)})

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


def extract_subject_from_context(text: str) -> Optional[str]:
    """Extract subject name from context when user asks follow-up questions"""
    if not text:
        return None
    
    # Simple extraction for common follow-up patterns
    patterns = [
        r'\b(Tell me more about|More about|Tell me about|Who is)\s+([A-Z][a-zA-Z\s]+?)(?:\.|\?|!|$)',
        r'\b(about him|about her|about them|about it|this|that)\b',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            if len(m.groups()) >= 2:
                subject = m.group(2).strip()
                if subject and len(subject.split()) <= 6:
                    return subject
            else:
                # Return the pronoun/context word
                return m.group(1).strip()
    
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

    # Handle follow-up questions using context
    last_subject = last_subject_by_channel.get(channel_id)
    if last_subject:
        extracted_subject = extract_subject_from_context(question)
        if extracted_subject and extracted_subject.lower() in ['him', 'her', 'them', 'it', 'this', 'that']:
            question = f"Tell me more about {last_subject}."
        elif any(word in question.lower() for word in ['tell me more', 'more about', 'who is he', 'who is she', 'who are they']):
            if not any(name in question for name in [last_subject]):
                question = f"Tell me more about {last_subject}."

    conversation_history[channel_id] = [{"role": "user", "content": question}]

    system_message = {
        "role": "system",
        "content": (
            "You are AskLab AI - a reasoning assistant with Wikipedia research capabilities.\n\n"
            "🎯 YOUR THINKING PROCESS:\n"
            "You must ALWAYS think BEFORE taking action. Your workflow is:\n\n"
            "1. <think>Initiating the Dialogue\n"
            "I've processed the user's [input] and recognized it as [type of request]. Now, I'm formulating my response and determining if research is needed.\n\n"
            "**Drafting a Response**\n"
            "I've crafted [my response]. My goal is to [reasoning about the response] and [intended purpose].</think> → Either respond naturally OR call research tool\n"
            "2. [Tool executes and returns results] (if research was needed)\n"
            "3. <think>Analyzing the Results\n"
            "I found [key information]. Now I need to [plan next step] OR provide the final answer based on what I learned.</think> → Either call next tool OR give final answer\n"
            "4. Continue until complete\n\n"
            "⚠️ CRITICAL RULES:\n"
            "- You have NO knowledge after 2023. MUST research current information when needed.\n"
            "- ALWAYS write <think>...</think> BEFORE calling any tool OR giving complex responses\n"
            "- When calling tools, use tool calling only. Do NOT write XML-like tags.\n"
            "- In <think> blocks, explain: what you need, why, and what you'll do\n"
            "- For greetings/conversational responses: provide natural, contextual replies\n"
            "- For research questions: continue until you have comprehensive information\n"
            "- search_wikipedia returns JSON: {\"results\": [\"Title 1\", ...]}\n"
            "- Your final answer should NOT contain <think> tags\n"
            "- For follow-up questions, use context from previous conversation\n\n"

            "**EXAMPLES:**\n\n"
            "For a greeting:\n"
            "<think>**Initiating the Dialogue**\n"
            "I've processed the user's initial \"Hi!\" and recognized it as a standard greeting. Now, I'm formulating a polite and welcoming response. My focus is on crafting a reply that establishes a friendly and open tone for the conversation ahead.\n\n"
            "**Drafting a Response**\n"
            "I've crafted a general, welcoming greeting: \"Hello! How can I help you today?\" I wanted to ensure it was universally applicable, given the lack of initial context. The goal is to set a friendly and helpful tone from the outset, paving the way for a productive conversation.</think>\n"
            "Hello! How can I help you today?\n\n"
            "For a research question:\n"
            "<think>**Initiating the Dialogue**\n"
            "I've processed the user's question about [topic]. This appears to be asking for current information, so I need to research this topic to provide accurate, up-to-date information.\n\n"
            "**Drafting a Response**\n"
            "I'll start by searching Wikipedia for relevant information. I need to find [specific information needed] to provide a comprehensive answer.</think>\n"
            "[Tool call would happen here]\n\n"
            "🔑 KEY POINTS:\n"
            "- Think → Act → Think → Act → Think → Final Answer (for research)\n"
            "- Think → Natural Response (for conversations)\n"
            "- NEVER skip thinking steps\n"
            "- Adapt your response style to the request type"
        )
    }

    progress_msg = None

    try:
        async with ctx.typing():
            messages = [system_message] + conversation_history[channel_id]
            sources_used = []
            max_iterations = 20
            iteration = 0
            last_thinking_sent_key = None
            assistant_message = ""

            # Let AI decide when to use tools - no rigid requirements
            min_search = 0
            min_pages = 0
            tool_counts = {"search_wikipedia": 0, "get_wikipedia_page": 0}
            last_search_results: List[str] = []
            last_read_title: Optional[str] = None

            progress_entries: List[str] = []
            progress_msg = await ctx.send("🧠 **Working...**")

            async def update_progress(entry: str) -> None:
                nonlocal progress_entries, progress_msg
                if not progress_msg:
                    return

                entry = (entry or "").strip()
                if not entry:
                    return

                progress_entries.append(entry)
                content = "\n\n".join(progress_entries)
                if len(content) > 1950:
                    while len(content) > 1950 and len(progress_entries) > 1:
                        progress_entries.pop(0)
                        content = "…\n\n" + "\n\n".join(progress_entries)

                await progress_msg.edit(content=content[:2000])

            while iteration < max_iterations:
                iteration += 1

                required_tool = None
                if tool_counts["search_wikipedia"] < min_search:
                    required_tool = "search_wikipedia"
                elif tool_counts["get_wikipedia_page"] < min_pages:
                    required_tool = "get_wikipedia_page"

                # Let AI decide what tools to use without specific guidance
                completion_tools = TOOLS[1:]
                completion_messages = messages

                response = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=completion_messages,
                    tools=completion_tools,
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
                if thinking:
                    thinking_key = re.sub(r'\s+', ' ', thinking).strip().lower()
                    if thinking_key and thinking_key != last_thinking_sent_key:
                        await update_progress(f"🧠 **Thinking...**\n\n{format_blockquote(thinking)}")
                        last_thinking_sent_key = thinking_key

                if not tool_calls:
                    assistant_message = clean_llm_text(raw_content)
                    if assistant_message.strip() and not required_tool:
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
                        await update_progress(search_msg)
                        tool_result = await execute_wiki_search(query)

                        try:
                            data = json.loads(tool_result)
                            last_search_results = list(data.get('results') or [])
                        except Exception:
                            last_search_results = []

                    elif fname == "get_wikipedia_page":
                        title = fargs.get('title', '')
                        last_read_title = title
                        read_msg = f"📖 **Reading Article...**\n\n> \"{title}\""
                        await update_progress(read_msg)
                        tool_result = await execute_wiki_page(title)

                        # Remove rigid incumbent extraction logic

                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        if wiki_url not in sources_used:
                            sources_used.append(wiki_url)

                    if fname in tool_counts:
                        tool_counts[fname] += 1

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
                    sources_text += f"{idx}. [wikipedia.org]({source})\n"
                assistant_message += sources_text

            last_subject = (
                (last_read_title or "").strip()
                or (last_search_results[0].strip() if last_search_results else "")
                or (question.split('about')[-1].strip() if 'about' in question.lower() else "")
            )
            if last_subject:
                last_subject_by_channel[channel_id] = last_subject

            # Send final answer (keep editing the same progress message; if it overflows, send extra messages)
            if assistant_message:
                final_text = assistant_message.strip()
                progress_text = "\n\n".join(progress_entries).strip()
                sep = "\n\n" if progress_text else ""

                available = 2000 - len(progress_text) - len(sep)
                if available <= 0:
                    if progress_msg:
                        await progress_msg.edit(content=progress_text[:2000])
                    remainder = final_text
                else:
                    first_chunk = final_text[:available]
                    remainder = final_text[available:]
                    combined = f"{progress_text}{sep}{first_chunk}".strip()
                    if progress_msg:
                        await progress_msg.edit(content=combined[:2000])
                    else:
                        await ctx.send(combined[:2000])

                remainder = remainder.lstrip()
                while remainder:
                    await ctx.send(remainder[:1990])
                    remainder = remainder[1990:]
            else:
                if progress_msg:
                    await progress_msg.edit(content="I couldn't generate a response. Please try again.")
                else:
                    await ctx.send("I couldn't generate a response. Please try again.")

    except Exception as e:
        error_text = f"❌ **Error:** {str(e)}"
        try:
            if progress_msg:
                await progress_msg.edit(content=error_text[:2000])
            else:
                await ctx.send(error_text)
        finally:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN missing")
        exit(1)
    bot.run(DISCORD_BOT_TOKEN)
