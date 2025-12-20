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
    # Moderation
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
    # Research: Search
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia to find article titles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term"
                    }
                },
                "required": ["query"]
            }
        }
    },
    # Research: Read
    {
        "type": "function",
        "function": {
            "name": "get_wikipedia_page",
            "description": "Read a Wikipedia page by its exact title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The exact Wikipedia page title"
                    }
                },
                "required": ["title"]
            }
        }
    }
]

# --- HELPER FUNCTIONS ---
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
    """Extract content from <think> tags"""
    if not text:
        return None
    pattern = r'<think>(.*?)</think>'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[-1].strip()
    return None

def remove_thinking_tags(text):
    """Remove <think> tags and their content from text"""
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
            "You are AskLab AI - a reasoning assistant with Wikipedia access.\n\n"
            "⚠️ CRITICAL: You have NO information after 2023. You MUST research using Wikipedia for ANY current information.\n\n"
            "📋 MANDATORY RESEARCH PROCESS:\n\n"
            "When asked about a current president/PM/leader:\n"
            "1. Use search_wikipedia to find the position page\n"
            "2. Use get_wikipedia_page to read that position page\n"
            "3. Write <think>I found [name] is the current holder. Now I need to learn more about them.</think>\n"
            "4. Use get_wikipedia_page to read the person's biographical page\n"
            "5. Write <think>I now have comprehensive information about [name] including [key facts]. This answers the question completely.</think>\n"
            "6. Provide detailed final answer\n\n"
            "⚠️ YOU MUST:\n"
            "- Call tools to actually research (don't just describe researching)\n"
            "- Write <think>...</think> AFTER each tool result explaining what you learned and what to do next\n"
            "- ALWAYS read at least 2 pages: the position page AND the person's page\n"
            "- Never answer without researching first\n"
            "- Put ALL reasoning inside <think> tags\n"
            "- Your final answer should NOT contain <think> tags\n\n"
            "EXAMPLE FOR 'Who is the current president of Sri Lanka?':\n"
            "Step 1: Call search_wikipedia('President of Sri Lanka')\n"
            "Step 2: Call get_wikipedia_page('President of Sri Lanka')\n"
            "Step 3: <think>I found that Anura Kumara Dissanayake is the current president. I need to read his page to provide complete information about him.</think>\n"
            "Step 4: Call get_wikipedia_page('Anura Kumara Dissanayake')\n"
            "Step 5: <think>Perfect! I now have all the details: he took office September 23, 2024, won the election on September 21, leads the JVP/NPP alliance, and his victory was historic due to requiring second-preference counting. I have everything needed for a comprehensive answer.</think>\n"
            "Step 6: Provide final answer with all details\n\n"
            "Remember: <think> blocks should ONLY appear BETWEEN tool uses, not before the first tool or in the final answer!"
        )
    }

    try:
        async with ctx.typing():
            messages = [system_message] + conversation_history[channel_id]
            sources_used = []
            max_iterations = 15
            iteration = 0
            tools_used_count = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Force tool use on first iteration for current questions
                tool_choice = "auto"
                if iteration == 1 and any(word in question.lower() for word in ['current', 'who is', 'now', 'today', 'latest', 'recent', 'president', 'prime minister', 'pm']):
                    tool_choice = "required"
                
                response = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    tools=TOOLS[1:],
                    tool_choice=tool_choice,
                    temperature=GROQ_TEMPERATURE,
                    max_tokens=2000
                )
                
                response_msg = response.choices[0].message
                tool_calls = response_msg.tool_calls
                
                # If no tool calls
                if not tool_calls:
                    # Check if we've researched enough (at least 2 tool uses)
                    if tools_used_count >= 2:
                        # Extract thinking if present
                        if response_msg.content:
                            thinking = extract_thinking(response_msg.content)
                            if thinking:
                                thinking_msg = f"🧠 **Thinking...**\n\n> {thinking}"
                                await ctx.send(thinking_msg)
                        
                        # Get final answer
                        assistant_message = remove_thinking_tags(response_msg.content) if response_msg.content else ""
                        if assistant_message.strip():
                            break
                    else:
                        # Haven't researched enough - force more research
                        messages.append({
                            "role": "assistant",
                            "content": response_msg.content or ""
                        })
                        messages.append({
                            "role": "user",
                            "content": f"You've only used {tools_used_count} tool(s). You MUST read at least 2 Wikipedia pages: the position page AND the person's biographical page. Continue researching."
                        })
                        continue
                
                # Tools were called
                tools_used_count += len(tool_calls)
                
                # Add assistant message with tool calls
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
                
                # Execute tools
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
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fname,
                        "content": str(tool_result)
                    })
                
                # After tool execution, prompt for thinking
                if tools_used_count < 3:  # Still in research phase
                    messages.append({
                        "role": "user",
                        "content": "Now write <think>...</think> explaining what you found and what you'll research next."
                    })
            
            if iteration >= max_iterations:
                assistant_message = "I've reached the research limit. Let me provide what I found so far."
                # Try one more time to get a summary
                messages.append({"role": "user", "content": "Provide your final answer based on the research so far."})
                final_response = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    temperature=GROQ_TEMPERATURE,
                    max_tokens=2000
                )
                assistant_message = remove_thinking_tags(final_response.choices[0].message.content or assistant_message)

            assistant_message = assistant_message.strip()
            conversation_history[channel_id].append({"role": "assistant", "content": assistant_message})
            
            # Add sources
            if sources_used and assistant_message:
                sources_text = "\n\n📚 **Sources**\n"
                for idx, source in enumerate(sources_used, 1):
                    sources_text += f"{idx}. {source}\n"
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
