#!/usr/bin/env python3
import os
import json
import discord
import wikipedia
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv
import re

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
                tool_calls = response_msg.tool_calls
                
                # ALWAYS check for and display thinking first
                if response_msg.content:
                    thinking = extract_thinking(response_msg.content)
                    if thinking:
                        thinking_msg = f"🧠 **Thinking...**\n\n> {thinking}"
                        await ctx.send(thinking_msg)
                
                # If no tool calls, this is the final answer
                if not tool_calls:
                    assistant_message = remove_thinking_tags(response_msg.content) if response_msg.content else ""
                    if assistant_message.strip():
                        break
                    else:
                        # Empty response, continue
                        messages.append({"role": "assistant", "content": response_msg.content or ""})
                        continue
                
                # Add assistant's response with tool calls
                messages.append({
                    "role": "assistant",
                    "content": response_msg.content or "",
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
                    fargs = json.loads(tool_call.function.arguments)
                    
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
