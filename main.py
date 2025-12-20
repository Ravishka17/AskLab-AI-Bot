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


def detect_tool_intent(text: str) -> bool:
    if not text:
        return False
    patterns = [
        r'\bsearch\b.*\bwikipedia\b',
        r'\bsearch wikipedia\b',
        r'\bsearching wikipedia\b',
        r'\bread\b.*\bwikipedia\b',
        r"\b(i\s*(?:'m| am| will|\s*'ll)\s+search)\b",
        r"\b(i\s*(?:'m| am| will|\s*'ll)\s+look\s+up)\b",
        r'\bsince i don\s*\x27?t have information after 2023\b'
    ]
    return any(re.search(p, text, flags=re.IGNORECASE | re.DOTALL) for p in patterns)


def is_current_affairs_question(question: str) -> bool:
    q = (question or "").lower()
    if any(word in q for word in ["current", "today", "now", "latest", "as of"]):
        return True

    roles = [
        "president",
        "prime minister",
        "pm",
        "ceo",
        "leader",
        "monarch",
        "king",
        "queen",
        "chancellor",
        "governor",
        "mayor"
    ]

    if ("who" in q or "who's" in q or "whos" in q) and any(role in q for role in roles):
        return True

    if any(role in q for role in ["president", "prime minister", "pm"]) and any(word in q for word in ["current", "incumbent"]):
        return True

    return False


def requires_position_and_bio(question: str) -> bool:
    q = (question or "").lower()
    return is_current_affairs_question(q) and any(role in q for role in ["president", "prime minister", "pm"])


def is_followup_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False

    if re.search(r'\b(him|her|them|it|this|that|he|she|they)\b', q) and len(q) <= 80:
        return True

    if any(q.startswith(prefix) for prefix in [
        "tell me more",
        "more about",
        "tell me about",
        "who is he",
        "who is she",
        "who are they",
        "what is it",
        "what about"
    ]):
        return True

    return False


def resolve_followup_question(question: str, subject: str) -> str:
    subject = (subject or "").strip()
    if not subject:
        return question

    q = (question or "").strip()
    ql = q.lower()

    if re.search(r'\b(tell me more about|more about)\s+(him|her|them|it|this|that)\b', ql):
        return f"Tell me more about {subject}."

    if re.search(r'^tell me more\b', ql):
        return f"Tell me more about {subject}."

    if re.search(r'^tell me about\b', ql) and re.search(r'\b(him|her|them|it|this|that)\b', ql):
        return f"Tell me about {subject}."

    if re.search(r'^who is\s+(he|she|they)\b', ql):
        return f"Who is {subject}?"

    if re.search(r'^what about\s+(him|her|them|it|this|that)\b', ql):
        return f"What about {subject}?"

    return f"{q.rstrip('?.!')} (referring to: {subject})."


def suggest_wikipedia_query(question: str) -> str:
    q = (question or "").strip()
    m = re.search(r'\b(president|prime minister)\s+of\s+([^\?\.\n]+)', q, flags=re.IGNORECASE)
    if m:
        role = m.group(1).title()
        subject = m.group(2).strip()
        return f"{role} of {subject}"

    m = re.search(r"\b(?:tell me about|what is|who is|who's|whos)\s+(.+)", q, flags=re.IGNORECASE)
    if m:
        subject = m.group(1).strip().rstrip('?.!')
        if subject:
            return subject

    return q.rstrip('?.!')


def choose_wikipedia_title(desired: str, results: List[str]) -> str:
    desired_norm = (desired or "").strip().lower()
    if desired_norm:
        for r in results or []:
            if (r or "").strip().lower() == desired_norm:
                return r
        for r in results or []:
            r_norm = (r or "").strip().lower()
            if desired_norm in r_norm or r_norm in desired_norm:
                return r

    return (results[0] if results else desired).strip()


def extract_incumbent_title_from_position_page(text: str) -> Optional[str]:
    if not text:
        return None

    patterns = [
        r'\bThe incumbent is\s+([^\n\.;:,]{2,80})',
        r'\bincumbent is\s+([^\n\.;:,]{2,80})',
        r'\bIncumbent\s*[:\-]\s*([^\n\.;:,]{2,80})'
    ]

    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if not m:
            continue

        name = re.sub(r'\s+', ' ', m.group(1)).strip()
        name = re.sub(r'\s*\(.*?\)\s*', '', name).strip()
        if name and len(name.split()) <= 6:
            return name

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

    if is_followup_question(question):
        last_subject = last_subject_by_channel.get(channel_id)
        if last_subject:
            question = resolve_followup_question(question, last_subject)

    conversation_history[channel_id] = [{"role": "user", "content": question}]

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
            "- search_wikipedia returns JSON: {\"results\": [\"Title 1\", ...]}\n"
            "- Your final answer should NOT contain <think> tags\n\n"

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

    progress_msg = None

    try:
        async with ctx.typing():
            messages = [system_message] + conversation_history[channel_id]
            sources_used = []
            max_iterations = 20
            iteration = 0
            last_thinking_sent_key = None
            assistant_message = ""

            needs_position_and_bio = requires_position_and_bio(question)
            min_search = 1
            min_pages = 2 if needs_position_and_bio else 1
            tool_counts = {"search_wikipedia": 0, "get_wikipedia_page": 0}
            last_search_results: List[str] = []
            incumbent_title: Optional[str] = None
            last_read_title: Optional[str] = None
            desired_query = suggest_wikipedia_query(question)

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

                completion_tools = TOOLS[1:]
                completion_messages = messages

                if required_tool:
                    completion_tools = [
                        t for t in TOOLS[1:]
                        if t.get("function", {}).get("name") == required_tool
                    ]

                    guidance = None
                    if required_tool == "search_wikipedia":
                        guidance = (
                            "Your next message must call the search_wikipedia tool. "
                            f"Search for: {desired_query}. "
                            "Include your reasoning ONLY inside <think>...</think>."
                        )
                    elif required_tool == "get_wikipedia_page":
                        if tool_counts["get_wikipedia_page"] == 0:
                            guidance = (
                                "Your next message must call the get_wikipedia_page tool using one of the titles from the last search results. "
                                "Include your reasoning ONLY inside <think>...</think>."
                            )
                        elif needs_position_and_bio:
                            if incumbent_title:
                                guidance = (
                                    "Your next message must call the get_wikipedia_page tool for the incumbent's biography page. "
                                    f"Use this title: {incumbent_title}. "
                                    "Include your reasoning ONLY inside <think>...</think>."
                                )
                            else:
                                guidance = (
                                    "Your next message must call the get_wikipedia_page tool for the incumbent's biography page (the person's name you identified from the position page). "
                                    "Include your reasoning ONLY inside <think>...</think>."
                                )

                    if guidance:
                        completion_messages = messages + [{"role": "system", "content": guidance}]

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

                        if needs_position_and_bio and tool_counts.get("get_wikipedia_page", 0) == 0 and not incumbent_title:
                            incumbent_title = extract_incumbent_title_from_position_page(tool_result)

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
                or (incumbent_title or "").strip()
                or (last_search_results[0].strip() if last_search_results else "")
                or desired_query
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
