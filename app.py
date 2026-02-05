#!/usr/bin/env python3
import os
import json
import re
import asyncio
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
import requests

load_dotenv()

# --- CONFIGURATION ---
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
SUPERMEMORY_API_KEY = os.getenv('SUPERMEMORY_API_KEY')

groq_client = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

conversation_history = {}
user_model_preferences = {}
WIKI_HEADERS = {"User-Agent": "AskLabBot/2.0 (contact: admin@asklab.ai) aiohttp/3.8"}

# Available models
AVAILABLE_MODELS = {
    "Llama 3.3 70B": "llama-3.3-70b-versatile",
    "Kimi K2 Instruct": "moonshotai/kimi-k2-instruct-0905"
}

# --- SUPERMEMORY CLIENT ---
class SupermemoryClient:
    def __init__(self, api_key):
        self.enabled = False
        self.api_key = api_key
        self.base_url = "https://api.supermemory.ai"
        
        if not api_key:
            print("⚠️ SUPERMEMORY_API_KEY not set")
            return
        
        self.enabled = True
        print("✅ Supermemory client initialized")
    
    async def test_connection(self):
        """Test if Supermemory connection works."""
        if not self.enabled:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.base_url}/v4/search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"q": "test", "limit": 1}
                )
            )
            
            if response.status_code == 200:
                print(f"✅ Supermemory connection successful")
                return True
            else:
                print(f"❌ Supermemory test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Supermemory test failed: {e}")
            self.enabled = False
            return False
    
    async def add_memory(self, content, container_tag, metadata=None):
        """Add a memory to Supermemory using the v3/documents endpoint."""
        if not self.enabled:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Prepare payload according to API documentation
            payload = {
                "content": content,
                "containerTag": container_tag  # Using singular containerTag
            }
            
            # Add optional metadata
            if metadata:
                payload["metadata"] = metadata
            
            # Make API request
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.base_url}/v3/documents",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Memory saved: {content[:50]}...")
                return response.json()
            else:
                print(f"❌ Supermemory add failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Supermemory add error: {e}")
            return None
    
    async def search_memory(self, query, container_tag, limit=5):
        """Search memories using the v4/search endpoint with hybrid mode."""
        if not self.enabled:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            
            # Prepare search payload
            payload = {
                "q": query,
                "limit": limit,
                "containerTag": container_tag,  # Singular for v4/search
                "searchMode": "hybrid",  # Search both memories and chunks
                "threshold": 0.6,  # Balanced relevance
                "rerank": False,  # Skip for speed
                "rewriteQuery": False  # Skip for speed
            }
            
            # Make API request
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.base_url}/v4/search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract results from response
                results = data.get('results', [])
                print(f"🔍 Memory search found {len(results)} results for '{query}'")
                return results
            else:
                print(f"❌ Supermemory search failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Supermemory search error: {e}")
            return []
    
    async def get_profile(self, container_tag, query=None):
        """Get user profile using the v4/profile endpoint."""
        if not self.enabled:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Prepare profile payload
            payload = {
                "containerTag": container_tag
            }
            
            # Add optional search query
            if query:
                payload["q"] = query
            
            # Make API request
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.base_url}/v4/profile",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Profile retrieved for {container_tag}")
                return data
            else:
                print(f"❌ Profile retrieval failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Profile retrieval error: {e}")
            return None

# Initialize Supermemory client
supermemory = SupermemoryClient(SUPERMEMORY_API_KEY) if SUPERMEMORY_API_KEY else None

# --- TOOL DEFINITIONS ---
def get_tools(include_memory=False):
    """Get tool definitions, optionally including memory search."""
    base_tools = [
        {
            "type": "function",
            "function": {
                "name": "search_wikipedia",
                "description": "Search Wikipedia for article titles matching a query. Returns a list of titles and snippets.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "The search query"}},
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_wikipedia_page",
                "description": "Retrieve the full text content of a Wikipedia page by exact title.",
                "parameters": {
                    "type": "object",
                    "properties": {"title": {"type": "string", "description": "The exact Wikipedia page title"}},
                    "required": ["title"]
                }
            }
        }
    ]
    
    if include_memory:
        base_tools.append({
            "type": "function",
            "function": {
                "name": "search_memory",
                "description": "Search past conversations and research results from your memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What to search for in memory (e.g., 'python tutorial', 'last week discussion')"
                        }
                    },
                    "required": ["query"]
                }
            }
        })
    
    return base_tools

# --- WIKIPEDIA LOGIC ---
async def fetch_wiki(params, retries=3):
    """Fetch data from Wikipedia API with retries."""
    url = "https://en.wikipedia.org/w/api.php"
    params.update({"format": "json", "utf8": "1"})
    
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession(headers=WIKI_HEADERS) as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif attempt < retries - 1:
                        await asyncio.sleep(1 * (attempt + 1))
        except (asyncio.TimeoutError, Exception) as e:
            if attempt == retries - 1:
                print(f"Error fetching Wikipedia: {e}")
            elif attempt < retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
    
    return {"error": "Failed after maximum retries"}

async def search_wikipedia(query):
    """Search Wikipedia for articles."""
    data = await fetch_wiki({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": "5"
    })
    
    if not data or "error" in data:
        return f"Search failed: {data.get('error', 'Unknown error')}"
    
    items = data.get('query', {}).get('search', [])
    if not items:
        return "No results found. Try different search terms."
    
    results = []
    for i in items:
        title = i['title']
        snippet = re.sub(r'<[^>]+>', '', i.get('snippet', ''))
        results.append(f"• {title}: {snippet[:150]}")
    
    return "\n".join(results)

async def get_wikipedia_page(title):
    """Retrieve full text of a Wikipedia page."""
    data = await fetch_wiki({
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "exintro": "0",
        "titles": title,
        "redirects": "1"
    })
    
    if not data or "error" in data:
        return f"Failed to retrieve page: {data.get('error', 'Network error')}"
    
    pages = data.get('query', {}).get('pages', {})
    if not pages:
        return f"No page data returned for '{title}'."
    
    for p_id, p_val in pages.items():
        if p_id == '-1':
            return f"Page '{title}' not found."
        
        extract = p_val.get('extract', '').strip()
        if not extract:
            data2 = await fetch_wiki({
                "action": "query",
                "prop": "extracts",
                "explaintext": "1",
                "exintro": "1",
                "titles": title,
                "redirects": "1"
            })
            
            if data2 and "query" in data2:
                pages2 = data2.get('query', {}).get('pages', {})
                for p_id2, p_val2 in pages2.items():
                    extract2 = p_val2.get('extract', '').strip()
                    if extract2:
                        return extract2[:3000]
            
            return f"Page '{title}' exists but has no readable text content."
        
        return extract[:3500]
    
    return "Unable to parse Wikipedia response."

# --- TEXT PROCESSING ---
def extract_reasoning(text):
    """Extracts text inside <think> tags."""
    if not text:
        return ""
    match = re.search(r'<(?:think|thinking)>(.*?)</(?:think|thinking)>', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def parse_thinking_with_header(think_text):
    """Parses thinking text to extract header and body."""
    if not think_text:
        return None, None
    
    match = re.match(r'\*\*([^*]+)\*\*\s*(.*)', think_text, re.DOTALL)
    if match:
        header = match.group(1).strip()
        body = match.group(2).strip()
        return header, body
    
    return None, think_text

def clean_output(text):
    """Removes thinking tags and hallucinated tool calls from final output."""
    if not text:
        return ""
    
    text = re.sub(r'<(?:think|thinking)>.*?</(?:think|thinking)>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<function_calls?>.*?</function_calls?>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<function_call>.*?</function_call>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<function=.*?</function>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<invoke.*?</invoke>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<result>.*?</result>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<parameter.*?</parameter>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\n\n(?:search_wikipedia|get_wikipedia_page|search_memory)\([^)]+\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'I\'ll (?:search|get|fetch|retrieve)[^\n]*\.', '', text, flags=re.IGNORECASE)
    
    # Remove Discord UI elements that should not appear in final responses
    text = re.sub(r'✅ Reasoning Complete\s*', '', text)
    text = re.sub(r'🧠 \*\*Thought\*\*\s*>\s*.*?(?=\n🧠|\n🔍|\n📖|\n⚠️|\n📚|\n\n|\Z)', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'🔍 \*\*Searched Wikipedia\*\*\s*>\s*.*?(?=\n🧠|\n📖|\n⚠️|\n📚|\n\n|\Z)', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'📖 \*\*Read Article\*\*\s*\n\s*- \[.*?\]\(.*?\)', '', text)
    text = re.sub(r'⚠️ \*\*Skipped Duplicate\*\*\s*>\s*.*?(?=\n🧠|\n🔍|\n📖|\n📚|\n\n|\Z)', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'📚 \*\*Sources\*\*.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up any remaining thinking-related fragments
    text = re.sub(r'^(The user is asking|Let me search|Key findings|Synthesis:).*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\(AKD|first non-dynastic|unprecedented NPP\)\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*Anura Kumara Dissanayake Sri Lanka president\s*$', '', text, flags=re.MULTILINE)

    return text.strip()

def convert_to_past_tense(sections):
    """Convert action verbs to past tense in completed reasoning."""
    converted = []
    for section in sections:
        section = section.replace("**Searching Wikipedia...**", "**Searched Wikipedia**")
        section = section.replace("**Reading Article...**", "**Read Article**")
        section = section.replace("**Searching Memory...**", "**Searched Memory**")
        section = section.replace("**Thinking...**", "**Thought**")
        section = section.replace("**Skipping Duplicate**", "**Skipped Duplicate**")
        converted.append(section)
    return converted

# --- SYSTEM PROMPTS ---
def get_system_prompt(model_name, has_memory=False):
    """Get model-specific system prompt."""
    memory_instruction = ""
    if has_memory:
        memory_instruction = (
            "\n### MEMORY SYSTEM\n"
            "You have access to search_memory tool to recall past conversations and research.\n"
            "Use it when:\n"
            "- User asks 'what did we discuss about X?'\n"
            "- User references 'last time' or 'before'\n"
            "- Context from previous conversations would be helpful\n\n"
        )
    
    base_prompt = (
        "You are AskLab AI, a research assistant. Current Date: January 2026.\n\n"
        "### RESPONSE TYPES\n"
        "1. **Simple conversations**: Respond directly without tools\n"
        "2. **Research queries**: Use the research workflow\n"
        + memory_instruction
    )
    
    if "llama" in model_name.lower():
        return base_prompt + (
            "### RESEARCH WORKFLOW\n"
            "1. <think>**Planning**\nStrategy</think>\n"
            "2. Call search_wikipedia (NO THINKING)\n"
            "3. <think>List 2-3 pages as links</think>\n"
            "4. Call get_wikipedia_page (NO THINKING)\n"
            "5. <think>Summarize facts</think>\n"
            "6. Repeat for more pages\n"
            "7. <think>Synthesize findings</think>\n"
            "8. Final answer with citations\n\n"
            "### CRITICAL RULES\n"
            "- ONE ACTION PER RESPONSE: thinking OR tool, NEVER BOTH\n"
            "- Keep thinking under 400 chars\n"
            "- Read at least 3 pages\n"
        )
    else:
        return base_prompt + (
            "### RESEARCH WORKFLOW\n"
            "1. <think>**Planning**\nStrategy</think>\n"
            "2. Call search_wikipedia\n"
            "3. <think>List 2-3 pages as links</think>\n"
            "4. Call get_wikipedia_page\n"
            "5. <think>Summarize information</think>\n"
            "6. Read more pages (at least 3 total)\n"
            "7. <think>Synthesize ALL information</think>\n"
            "8. Final answer with citations [1](URL)\n\n"
            "### CRITICAL RULES\n"
            "- List pages as: [Title](URL)\n"
            "- Cite inline like [1](URL)\n"
            "- Keep thinking under 600 chars\n"
            "- Read at least 3 pages\n"
        )

# --- MODEL SELECTION VIEW ---
class ModelSelectView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.add_item(ModelDropdown(user_id))

class ModelDropdown(discord.ui.Select):
    def __init__(self, user_id):
        options = [
            discord.SelectOption(
                label="Llama 3.3 70B",
                description="Fast and versatile",
                value="llama-3.3-70b-versatile",
                emoji="🦙"
            ),
            discord.SelectOption(
                label="Kimi K2 Instruct",
                description="Precise reasoning",
                value="moonshotai/kimi-k2-instruct-0905",
                emoji="🌙"
            )
        ]
        super().__init__(
            placeholder="Choose AI model...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.user_id = user_id
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return
        
        selected_model = self.values[0]
        user_model_preferences[self.user_id] = selected_model
        
        model_names = {v: k for k, v in AVAILABLE_MODELS.items()}
        model_display = model_names.get(selected_model, selected_model)
        
        await interaction.response.send_message(
            f"✅ Model switched to **{model_display}**",
            ephemeral=True
        )

# --- CONTEXT MANAGEMENT ---
class ContextManager:
    def __init__(self, system_prompt, user_id, channel_id):
        self.system_prompt = system_prompt
        self.user_id = user_id
        self.channel_id = channel_id
        self.conversation_history = [] # Last 2 exchanges
        self.research_context = []     # Tool results and summaries
        self.working_memory = []       # Current/recent iterations
        self.facts = []
        self.sources = {}
        self.pages_read_count = 0
        self.iteration = 0
        self.consecutive_thoughts_without_tools = 0
        self.last_tool_call_iteration = -1
        
    def set_history(self, history):
        # Keep only last 2 exchanges (4 messages: user, assistant, user, assistant)
        self.conversation_history = history[-4:] if history else []

    def add_fact(self, fact):
        if fact not in self.facts:
            self.facts.append(fact)

    def add_source(self, title, url):
        self.sources[title] = url
        self.pages_read_count = len(self.sources)

    def build_messages(self, iteration):
        self.iteration = iteration
        
        # 1. System Prompt (Always First)
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # 2. Add Research Progress Marker for AI
        progress_info = f"[Iteration {iteration}/30] [Pages Read: {self.pages_read_count}/3]"
        if iteration > 15:
            progress_info += " [URGENT: Synthesize now]"
        
        messages[0]["content"] += f"\n\n### CURRENT STATUS\n{progress_info}\n"
        
        if self.facts:
            # Only include the last 15 facts to keep context clean
            facts_summary = "\n".join([f"- {f}" for f in self.facts[-15:]])
            messages[0]["content"] += f"\n### RESEARCH FACTS GATHERED SO FAR\n{facts_summary}\n"

        # 3. Conversation History (Personality/Context) - Only for non-emergency
        if iteration < 20:
            messages.extend(self.conversation_history)
        
        # 4. Working Memory (Recent interactions)
        if iteration <= 10:
            trimmed_working_memory = self.working_memory
        elif iteration <= 20:
            # Drop older thought-only blocks, keep all tool calls and results
            new_wm = []
            thoughts_to_keep = 2
            thought_msgs = [m for m in self.working_memory if m.get("role") == "assistant" and "<think>" in (m.get("content") or "") and not m.get("tool_calls")]
            last_thoughts = thought_msgs[-thoughts_to_keep:] if thought_msgs else []
            
            for msg in self.working_memory:
                if msg.get("role") == "assistant" and "<think>" in (msg.get("content") or "") and not msg.get("tool_calls"):
                    if msg in last_thoughts:
                        new_wm.append(msg)
                else:
                    new_wm.append(msg)
            trimmed_working_memory = new_wm
        else:
            # Emergency Mode: Keep ALL tool pairs, last user message, and ONLY the very last thought
            new_wm = []
            tool_call_ids = set()
            # First pass: identify all tool_call_ids in tool messages
            for msg in self.working_memory:
                if msg.get("role") == "tool":
                    tool_call_ids.add(msg.get("tool_call_id"))
            
            for msg in self.working_memory:
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    # Check if at least one tool_call in this message has a corresponding result
                    if any(tc.get("id") in tool_call_ids for tc in msg.get("tool_calls")):
                        new_wm.append(msg)
                elif msg.get("role") == "tool":
                    new_wm.append(msg)
                elif msg == self.working_memory[-1]: # Last message always kept
                    if msg not in new_wm: new_wm.append(msg)
                elif msg.get("role") == "user" and iteration > 25:
                    # Only keep last user message in extreme emergency
                    if msg == [m for m in self.working_memory if m.get("role") == "user"][-1]:
                        new_wm.append(msg)
                elif msg.get("role") == "assistant" and "<think>" in (msg.get("content") or ""):
                    # Keep only the very last thought
                    if msg == [m for m in self.working_memory if m.get("role") == "assistant" and "<think>" in (m.get("content") or "")][-1]:
                        new_wm.append(msg)

            # Ensure order is preserved
            trimmed_working_memory = sorted(new_wm, key=lambda x: self.working_memory.index(x) if x in self.working_memory else 0)

        messages.extend(trimmed_working_memory)
        
        # Token/Length Management (Approx 15k chars is safe for Groq)
        while len(str(messages)) > 15000 and len(messages) > 2:
            # Remove from the middle of working memory (after system and history)
            if len(messages) > 5:
                messages.pop(2) # Keep system (0) and history (1) and last ones
            else:
                messages.pop(1)
            
        return messages

    def add_message(self, role, content=None, tool_calls=None, tool_call_id=None, name=None):
        msg = {"role": role}
        if content is not None: msg["content"] = content
        if tool_calls is not None: msg["tool_calls"] = tool_calls
        if tool_call_id is not None: msg["tool_call_id"] = tool_call_id
        if name is not None: msg["name"] = name
        
        self.working_memory.append(msg)
        
        if role == "assistant" and tool_calls:
            self.last_tool_call_iteration = self.iteration
            self.consecutive_thoughts_without_tools = 0
        elif role == "assistant" and not tool_calls:
            if "<think>" in (content or ""):
                self.consecutive_thoughts_without_tools += 1

    def detect_stuck_loop(self):
        # AI keeps planning but doesn't call tools
        if self.consecutive_thoughts_without_tools >= 3:
            return "FORCE_ACTION"
        return None

# --- SLASH COMMANDS ---
@bot.tree.command(name="model", description="Select AI model")
async def select_model(interaction: discord.Interaction):
    view = ModelSelectView(interaction.user.id)
    current_model = user_model_preferences.get(interaction.user.id, "moonshotai/kimi-k2-instruct-0905")
    model_names = {v: k for k, v in AVAILABLE_MODELS.items()}
    current_display = model_names.get(current_model, current_model)
    
    await interaction.response.send_message(
        f"Current model: **{current_display}**\nSelect a new model:",
        view=view,
        ephemeral=True
    )

@bot.tree.command(name="memory_stats", description="Check Supermemory status")
async def memory_stats(interaction: discord.Interaction):
    if not supermemory or not supermemory.enabled:
        await interaction.response.send_message(
            "🧠 **Supermemory**: Disabled\n\nTo enable:\n1. Set `SUPERMEMORY_API_KEY` in .env\n2. Restart bot",
            ephemeral=True
        )
    else:
        # Get user profile to show stats
        user_id = str(interaction.user.id)
        profile_data = await supermemory.get_profile(user_id)
        
        if profile_data:
            profile = profile_data.get('profile', {})
            static_facts = profile.get('static', [])
            dynamic_context = profile.get('dynamic', [])
            
            stats_msg = (
                f"🧠 **Supermemory**: ✅ Enabled\n\n"
                f"**Your Profile:**\n"
                f"📌 Static Facts: {len(static_facts)}\n"
                f"🔄 Dynamic Context: {len(dynamic_context)}\n\n"
                f"Your conversations are being saved for future reference."
            )
        else:
            stats_msg = (
                "🧠 **Supermemory**: ✅ Enabled\n\n"
                "Your conversations are being saved for future reference."
            )
        
        await interaction.response.send_message(stats_msg, ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ Bot Online: {bot.user}')
    
    if supermemory and supermemory.enabled:
        test_result = await supermemory.test_connection()
        if test_result:
            print(f'🧠 Supermemory: ✅ Connected')
        else:
            print(f'🧠 Supermemory: ❌ Connection failed')
    else:
        print(f'🧠 Supermemory: ⚠️ Disabled (set SUPERMEMORY_API_KEY in .env)')
    
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if prompt:
            user_id = message.author.id
            selected_model = user_model_preferences.get(user_id, "moonshotai/kimi-k2-instruct-0905")
            await run_research(message.channel, prompt, selected_model, user_id)

async def run_research(channel, prompt, model_name, user_id):
    cid = channel.id
    container_tag = str(user_id)

    if cid not in conversation_history:
        conversation_history[cid] = []

    # Get user profile and search memory
    context_from_memory = ""
    if supermemory and supermemory.enabled:
        profile_data = await supermemory.get_profile(container_tag, query=prompt)
        if profile_data:
            profile = profile_data.get('profile', {})
            static_facts = profile.get('static', [])
            dynamic_context = profile.get('dynamic', [])
            if static_facts or dynamic_context:
                context_parts = []
                if static_facts: context_parts.append("**User Profile (Static):**\n" + "\n".join(f"- {fact}" for fact in static_facts[:5]))
                if dynamic_context: context_parts.append("**Recent Context:**\n" + "\n".join(f"- {ctx}" for ctx in dynamic_context[:5]))
                context_from_memory = "\n\n".join(context_parts)
            search_results = profile_data.get('searchResults', {}).get('results', [])
            if search_results:
                memory_texts = [res.get('memory', res.get('chunk', ''))[:200] for res in search_results[:3]]
                if any(memory_texts): context_from_memory += "\n\n**Relevant Memories:**\n" + "\n".join(f"- {mem}" for mem in memory_texts if mem)

    system_prompt = get_system_prompt(model_name, has_memory=(supermemory and supermemory.enabled))
    if context_from_memory:
        system_prompt += f"\n\n### USER CONTEXT FROM MEMORY\n{context_from_memory}\n"

    ctx = ContextManager(system_prompt, user_id, cid)
    ctx.set_history(conversation_history[cid])
    ctx.add_message("user", prompt)

    embed = discord.Embed(title="Reasoning", color=0x5865F2)
    reasoning_msg = await channel.send(embed=embed)

    display_sections = []
    failed_pages = set()
    tool_call_count = 0
    max_tools = 12
    has_planning = False
    has_synthesis = False
    is_research_query = False
    is_llama = "llama" in model_name.lower()

    async def update_ui(final=False):
        seen = set()
        unique_sections = []
        for section in display_sections:
            section_key = section[:100]
            if section_key not in seen:
                seen.add(section_key)
                unique_sections.append(section)
        if final: unique_sections = convert_to_past_tense(unique_sections)
        embed.description = "\n\n".join(unique_sections)[:4000]
        try: await reasoning_msg.edit(embed=embed)
        except: pass

    for iteration in range(30):
        messages = ctx.build_messages(iteration)

        # Stuck detection & urgency injection
        stuck_status = ctx.detect_stuck_loop()
        if stuck_status == "FORCE_ACTION":
            messages.append({"role": "user", "content": "URGENT: Stop planning. Either call a tool now or provide the final answer if you have enough information."})

        try:
            response = groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=get_tools(include_memory=(supermemory and supermemory.enabled)),
                tool_choice="auto",
                temperature=0.2,
                max_tokens=2000
            )
        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower() or "413" in error_msg or "too large" in error_msg.lower():
                # ContextManager should have handled this, but if not, emergency trim
                ctx.working_memory = ctx.working_memory[-5:]
                continue
            await channel.send(f"⚠️ API Error: {e}")
            return

        msg = response.choices[0].message
        content = msg.content or ""
        tool_calls = msg.tool_calls

        if tool_calls: is_research_query = True

        # Track reasoning
        think = extract_reasoning(content)
        if think:
            is_research_query = True
            header, body = parse_thinking_with_header(think)
            if header:
                if "planning" in header.lower(): has_planning = True
                elif "synthesiz" in header.lower(): has_synthesis = True

            # Extract facts from reasoning semantically (simple heuristic)
            if "fact" in think.lower() or "found" in think.lower():
                for line in think.split('\n'):
                    if line.strip().startswith(('-', '•', '*')) and len(line) > 20:
                        ctx.add_fact(line.strip())

            thinking_section = f"🧠 **Thought**\n\n> **{header or 'Thinking'}**\n\n{body or think[:500]}"
            display_sections.append(thinking_section)
            await update_ui()

        # Handle hallucinations
        hallucinated = re.search(r'<function[^>]*>|(?:search_wikipedia|get_wikipedia_page|search_memory)\s*\(|\{\s*"query":', content, re.IGNORECASE)
        if hallucinated and not tool_calls:
            ctx.add_message("assistant", content)
            ctx.add_message("user", "ERROR: Use native tool calls only. Do not simulate them.")
            continue

        if is_llama and think and tool_calls:
            ctx.add_message("assistant", content)
            ctx.add_message("user", "ERROR: NEVER combine <think> and tool calls.")
            continue

        if not has_planning and tool_calls and iteration == 0:
            ctx.add_message("assistant", content, tool_calls=[{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in tool_calls])
            ctx.add_message("user", "ERROR: Start with <think>**Planning**</think> FIRST.")
            continue

        if tool_calls:
            ctx.add_message("assistant", content, tool_calls=[{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in tool_calls])

            for tool_call in tool_calls:
                tool_call_count += 1
                if tool_call_count > max_tools:
                    ctx.add_message("tool", content="Maximum tools reached. Synthesize findings.", tool_call_id=tool_call.id, name=tool_call.function.name)
                    display_sections.append("⚠️ **Tool Limit Reached**")
                    await update_ui()
                    continue

                fn_name = tool_call.function.name
                try: fn_args = json.loads(tool_call.function.arguments)
                except:
                    ctx.add_message("tool", content="ERROR: Invalid JSON arguments", tool_call_id=tool_call.id, name=fn_name)
                    continue

                result = ""
                if fn_name == "search_memory":
                    if not (supermemory and supermemory.enabled): result = "Memory unavailable."
                    else:
                        query = fn_args.get('query', '')
                        display_sections.append(f"🧠 **Searching Memory...**\n\n> {query}")
                        await update_ui()
                        memories = await supermemory.search_memory(query, container_tag, limit=3)
                        result = "Memories:\n" + "\n".join([str(m) for m in memories]) if memories else "No memories found."

                elif fn_name == "search_wikipedia":
                    query = fn_args.get('query', '')
                    display_sections.append(f"🔍 **Searching Wikipedia...**\n\n> {query}")
                    await update_ui()
                    result = await search_wikipedia(query)

                elif fn_name == "get_wikipedia_page":
                    title = fn_args.get('title', '')
                    if title in failed_pages:
                        result = "Already checked."
                        display_sections.append(f"⚠️ **Skipped Duplicate**\n\n> {title}")
                    else:
                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        display_sections.append(f"📖 **Reading Article...**\n\n- [{title}]({wiki_url})")
                        await update_ui()
                        result = await get_wikipedia_page(title)
                        if "Failed" in result or "not found" in result: failed_pages.add(title)
                        else: ctx.add_source(title, wiki_url)

                ctx.add_message("tool", content=str(result)[:1800], tool_call_id=tool_call.id, name=fn_name)

        else:
            final_answer = clean_output(content)

            # Enforcement logic
            if is_research_query:
                if ctx.pages_read_count < 3 and not has_synthesis and iteration < 20:
                    ctx.add_message("assistant", content)
                    ctx.add_message("user", f"Read {3 - ctx.pages_read_count} more page(s) before answering.")
                    continue
                if not has_synthesis and final_answer.strip() and iteration < 25:
                    ctx.add_message("assistant", content)
                    ctx.add_message("user", "Briefly synthesize findings with <think> before final answer.")
                    continue

            if not final_answer.strip():
                if iteration < 28:
                    ctx.add_message("assistant", content)
                    ctx.add_message("user", "Please provide the final answer now.")
                    continue
                final_answer = "I couldn't find a definitive answer."

            if ctx.sources and is_research_query:
                final_answer += "\n\n📚 **Sources**\n" + "\n".join([f"{i+1}. [{t}]({u})" for i, (t, u) in enumerate(sorted(ctx.sources.items()), 1)])

            # Save to Memory
            if supermemory and supermemory.enabled and len(final_answer) > 50:
                asyncio.create_task(supermemory.add_memory(f"User: {prompt}\nAI: {final_answer[:1000]}", container_tag, {"type": "qa"}))

            # History management
            conversation_history[cid].append({"role": "user", "content": prompt})
            conversation_history[cid].append({"role": "assistant", "content": final_answer[:400]})
            if len(conversation_history[cid]) > 6: conversation_history[cid] = conversation_history[cid][-6:]

            embed.title = "✅ Reasoning Complete"
            embed.color = 0x57F287
            await update_ui(final=True)

            for chunk in [final_answer[i:i+2000] for i in range(0, len(final_answer), 2000)]:
                await channel.send(chunk)
            return

    await channel.send("⚠️ Max iterations reached.")

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN not set in .env file")
        exit(1)
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY not set in .env file")
        exit(1)
    
    print("🚀 Starting Discord bot...")
    bot.run(DISCORD_BOT_TOKEN)
