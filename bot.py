#!/usr/bin/env python3
"""
Main bot logic and event handlers for AskLab AI Bot
"""
import asyncio
import json
import discord
from datetime import datetime
from discord.ext import commands

# Import configurations and utilities
from config import (
    conversation_history,
    user_model_preferences,
    groq_client,
    DISCORD_BOT_TOKEN
)
import os
from supermemory import SupermemoryClient
from discord_ui import ModelSelectView
from ai_utils import get_tools, clean_output, get_system_prompt
from wikipedia import search_wikipedia, get_wikipedia_page

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize Supermemory
supermemory = SupermemoryClient(config.SUPERMEMORY_API_KEY)

async def select_model(interaction: discord.Interaction):
    """Handle model selection."""
    view = ModelSelectView(interaction.user.id)
    await interaction.response.send_message("Choose an AI model:", view=view, ephemeral=True)

async def memory_stats(interaction: discord.Interaction):
    """Handle memory statistics request."""
    if not supermemory.enabled:
        await interaction.response.send_message("❌ Supermemory is not enabled.", ephemeral=True)
        return
    
    # Test connection
    connected = await supermemory.test_connection()
    if not connected:
        await interaction.response.send_message("❌ Cannot connect to Supermemory.", ephemeral=True)
        return
    
    await interaction.response.send_message(
        "✅ Supermemory is enabled and connected!",
        ephemeral=True
    )

async def bot_ready():
    """Bot startup event."""
    print(f'🚀 {bot.user} is now online!')
    print(f'📊 Connected to {len(bot.guilds)} servers')
    print(f'👥 Serving {len(bot.users)} users')
    
    # Sync commands if needed
    try:
        await bot.tree.sync()
        print("✅ Commands synced successfully")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    
    # Test Supermemory connection if enabled
    if supermemory.enabled:
        await supermemory.test_connection()

async def bot_message(message):
    """Handle incoming messages."""
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Check if bot is mentioned
    if bot.user in message.mentions:
        user_id = message.author.id
        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not prompt:
            await message.channel.send("Hi! Ask me a question and I'll research it for you. 🔍")
            return
        
        # Get user's model preference
        from config import user_model_preferences
        model_name = user_model_preferences.get(user_id, "llama-3.3-70b-versatile")
        
        # Send thinking message
        embed = discord.Embed(
            title="🤔 Thinking...",
            description="Researching your question...",
            color=0x7289da
        )
        thinking_msg = await message.channel.send(embed=embed)
        
        try:
            # Run research
            await run_research(
                channel=message.channel,
                prompt=prompt,
                model_name=model_name,
                user_id=user_id,
                thinking_msg=thinking_msg
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            await thinking_msg.edit(embed=discord.Embed(
                title="❌ Error",
                description="Something went wrong. Please try again.",
                color=0xe74c3c
            ))

async def run_research(channel, prompt, model_name, user_id, thinking_msg=None):
    """Run the research workflow."""
    cid = f"{channel.id}_{user_id}"
    
    # Initialize conversation history for this channel
    if cid not in config.conversation_history:
        config.conversation_history[cid] = []
    
    # Get Supermemory context if available
    memory_context = ""
    has_memory = supermemory.enabled
    
    if supermemory.enabled:
        try:
            memories = await supermemory.search_memory(
                query=prompt,
                container_tag=str(user_id),
                limit=3
            )
            if memories:
                memory_context = "Context from previous conversations:\n"
                for i, mem in enumerate(memories, 1):
                    if isinstance(mem, dict):
                        content = mem.get('memory', mem.get('chunk', str(mem)))
                        similarity = mem.get('similarity', 0)
                        memory_context += f"{i}. [{similarity:.2f}] {content[:200]}...\n"
        except Exception as e:
            print(f"Memory search error: {e}")
    
    # Build messages for the AI
    messages = [
        {
            "role": "system",
            "content": get_system_prompt(model_name, has_memory)
        }
    ]
    
    # Add memory context
    if memory_context:
        messages.append({
            "role": "system",
            "content": f"Relevant past context:\n{memory_context}"
        })
    
    # Add conversation history (last 3 exchanges)
    messages.extend(config.conversation_history[cid][-6:])
    
    # Add current prompt
    messages.append({"role": "user", "content": prompt})
    
    # Initialize tracking variables
    display_sections = []
    failed_pages = set()
    pages_read = 0
    sources = {}
    is_research_query = True
    has_synthesis = False
    iteration = 0
    
    # Update UI function
    async def update_ui(final=False):
        embed_title = "✅ Reasoning Complete" if final else "🤔 Thinking..."
        embed_color = 0x57F287 if final else 0x7289da
        
        embed = discord.Embed(
            title=embed_title,
            description="\n".join(display_sections[-5:]) if display_sections else "Processing...",
            color=embed_color
        )
        
        if thinking_msg:
            await thinking_msg.edit(embed=embed)
    
    # Main research loop
    while iteration < 30:
        iteration += 1
        
        try:
            # Get AI response
            tools = get_tools(has_memory)
            
            response = config.groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                max_tokens=1500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            messages.append({"role": "assistant", "content": content})
            
            # Check for tool calls
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    
                    if fn_name == "search_memory":
                        if not (supermemory and supermemory.enabled):
                            result = "Memory search unavailable. Enable Supermemory to use this feature."
                        else:
                            query = fn_args.get('query', '')
                            display_sections.append(f"🧠 **Searching Memory...**\n\n> {query}")
                            await update_ui()
                            
                            memories = await supermemory.search_memory(
                                query=query,
                                container_tag=str(user_id),
                                limit=3
                            )
                            
                            if memories:
                                memory_texts = []
                                for mem in memories:
                                    if isinstance(mem, dict):
                                        content_text = mem.get('memory', mem.get('chunk', str(mem)))
                                        similarity = mem.get('similarity', 0)
                                        memory_texts.append(f"[Similarity: {similarity:.2f}] {content_text[:200]}")
                                    else:
                                        memory_texts.append(str(mem)[:200])
                                
                                result = "Past conversations found:\n" + "\n\n".join(memory_texts)
                            else:
                                result = "No relevant past conversations found for this query."
                    
                    elif fn_name == "search_wikipedia":
                        query = fn_args.get('query', '')
                        display_sections.append(f"🔍 **Searching Wikipedia...**\n\n> {query}")
                        await update_ui()
                        result = await search_wikipedia(query)
                    
                    elif fn_name == "get_wikipedia_page":
                        title = fn_args.get('title', '')
                        
                        if title in failed_pages:
                            result = f"Already tried '{title}'."
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": fn_name,
                                "content": result
                            })
                            display_sections.append(f"⚠️ **Skipped Duplicate**\n\n> {title}")
                            await update_ui()
                            continue
                        
                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        display_sections.append(f"📖 **Reading Article...**\n\n- [{title}]({wiki_url})")
                        await update_ui()
                        result = await get_wikipedia_page(title)
                        
                        if "Failed" in result or "not found" in result or "no readable text" in result:
                            failed_pages.add(title)
                        else:
                            pages_read += 1
                            sources[title] = wiki_url
                    
                    else:
                        result = "ERROR: Unknown function"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": str(result)[:1800]
                    })
            
            else:
                final_answer = clean_output(content)
                
                if is_research_query:
                    if pages_read < 3 and not has_synthesis:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({
                            "role": "user",
                            "content": f"Read {3 - pages_read} more page(s)."
                        })
                        continue
                    
                    if not has_synthesis and final_answer.strip() and pages_read >= 3:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({
                            "role": "user",
                            "content": "Use <think> to synthesize findings briefly."
                        })
                        continue
                
                if not final_answer.strip():
                    if iteration < 28:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({
                            "role": "user",
                            "content": "Provide final answer with citations."
                        })
                        continue
                    else:
                        final_answer = "I apologize, but I wasn't able to find a clear answer."
                
                # Add sources to final answer
                if sources and is_research_query:
                    final_answer += "\n\n📚 **Sources**"
                    for idx, (title, url) in enumerate(sorted(sources.items()), 1):
                        final_answer += f"\n{idx}. [{title}]({url})"
                
                # Save to Supermemory if enabled
                if supermemory and supermemory.enabled and final_answer and len(final_answer) > 50:
                    memory_content = f"User: {prompt}\n\nAssistant: {final_answer[:1500]}"
                    metadata = {
                        "timestamp": datetime.now().isoformat(),
                        "model": model_name,
                        "type": "research_qa" if is_research_query else "conversation",
                        "channel_id": str(channel.id),
                        "sources_count": len(sources) if sources else 0
                    }
                    
                    asyncio.create_task(supermemory.add_memory(
                        content=memory_content,
                        container_tag=str(user_id),
                        metadata=metadata
                    ))
                    print(f"💾 Saving to memory for user {user_id}")
                
                # Update conversation history
                config.conversation_history[cid].append({"role": "user", "content": prompt})
                config.conversation_history[cid].append({"role": "assistant", "content": final_answer[:400]})
                
                # Trim conversation history
                if len(config.conversation_history[cid]) > 6:
                    config.conversation_history[cid] = config.conversation_history[cid][-6:]
                
                # Update UI to show completion
                await update_ui(final=True)
                
                # Send final answer
                if len(final_answer) > 2000:
                    chunks = [final_answer[i:i+2000] for i in range(0, len(final_answer), 2000)]
                    for chunk in chunks:
                        await channel.send(chunk)
                else:
                    await channel.send(final_answer)
                
                return
        
        except Exception as e:
            print(f"Error in research loop: {e}")
            await channel.send("❌ An error occurred during research. Please try again.")
            return
    
    # If loop exhausted
    await channel.send("⚠️ Reasoning exceeded maximum iterations.")

# Set up event handlers
@bot.event
async def on_ready():
    await bot_ready()

@bot.event
async def on_message(message):
    await bot_message(message)

# Set up slash commands
@bot.tree.command(name="model", description="Select your preferred AI model")
async def model_command(interaction: discord.Interaction):
    await select_model(interaction)

@bot.tree.command(name="memory", description="Check Supermemory status")
async def memory_command(interaction: discord.Interaction):
    await memory_stats(interaction)