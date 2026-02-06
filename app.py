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
    "GPT-OSS 120B": "openai/gpt-oss-120b",
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
def get_tools_for_model(model_name, include_memory=False):
    """Get tool definitions based on model type."""
    # GPT-OSS models use Groq's built-in tools (browser_search, code_interpreter)
    if "gpt-oss" in model_name.lower():
        tools = [
            {"type": "browser_search"},
            {"type": "code_interpreter"}
        ]
        
        # Add memory search for GPT-OSS if enabled
        if include_memory:
            tools.append({
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
        
        return tools
    
    # Kimi K2 uses custom Wikipedia tools
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
    
    if "gpt-oss" in model_name.lower():
        return base_prompt + (
            "### BUILT-IN TOOLS\n"
            "You have access to powerful built-in tools:\n"
            "- **browser_search**: Search the web for current information\n"
            "- **code_interpreter**: Execute Python code for calculations and analysis\n\n"
            "### RESEARCH WORKFLOW\n"
            "1. For factual questions: Use browser_search to find current information\n"
            "2. For calculations: Use code_interpreter to run Python code\n"
            "3. Synthesize findings into a clear answer with citations\n\n"
            "### CRITICAL RULES\n"
            "- Use browser_search for factual, current information\n"
            "- Use code_interpreter for math, data analysis, and computations\n"
            "- Cite sources from web search results\n"
            "- Provide clear, comprehensive answers\n"
        )
    else:
        # Kimi K2 Instruct system prompt
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
                label="GPT-OSS 120B",
                description="Advanced reasoning with web search",
                value="openai/gpt-oss-120b",
                emoji="🧠"
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

# --- SLASH COMMANDS ---
@bot.tree.command(name="model", description="Select AI model")
async def select_model(interaction: discord.Interaction):
    view = ModelSelectView(interaction.user.id)
    current_model = user_model_preferences.get(interaction.user.id, "openai/gpt-oss-120b")
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
            selected_model = user_model_preferences.get(user_id, "openai/gpt-oss-120b")
            await run_research(message.channel, prompt, selected_model, user_id)

# --- CONTEXT MANAGER ---
class ContextManager:
    """Manages dual-track context architecture to prevent instruction dilution."""
    
    def __init__(self, system_prompt, user_message, conversation_history=None, max_tokens=8000):
        self.system_prompt = system_prompt
        self.user_message = user_message
        self.conversation_history = conversation_history or []
        self.max_tokens = max_tokens
        
        # Separate working memory streams
        self.tool_results = []  # All tool results accumulated
        self.thinking_blocks = []  # All thinking blocks
        self.research_context = {}  # Sources, pages read, facts
        
        # Loop detection
        self.consecutive_thoughts_without_tools = 0
        self.last_thinking_themes = []  # Track thinking patterns
        self.iterations_without_new_facts = 0
        self.last_fact_count = 0
    
    def add_tool_result(self, tool_message):
        """Add a tool result to research context."""
        self.tool_results.append(tool_message)
        self.consecutive_thoughts_without_tools = 0
        
    def add_thinking(self, content, has_tool_calls=False):
        """Track thinking patterns for loop detection."""
        if not has_tool_calls:
            self.consecutive_thoughts_without_tools += 1
        else:
            self.consecutive_thoughts_without_tools = 0
            # Reset theme tracking when action is taken
            self.last_thinking_themes = []
        
        # Extract theme from thinking for pattern matching
        thinking = extract_reasoning(content)
        if thinking and not has_tool_calls:  # Only track themes when no action taken
            self.thinking_blocks.append({
                "iteration": len(self.thinking_blocks),
                "content": thinking[:200],  # Store snippet
                "theme": self._extract_theme(thinking)
            })
            self.last_thinking_themes.append(self._extract_theme(thinking))
            if len(self.last_thinking_themes) > 3:
                self.last_thinking_themes.pop(0)
    
    def _extract_theme(self, thinking):
        """Extract semantic theme from thinking block."""
        thinking_lower = thinking.lower()
        if any(word in thinking_lower for word in ["plan", "strategy", "approach", "need to"]):
            return "planning"
        elif any(word in thinking_lower for word in ["synthesiz", "combin", "overall", "summary"]):
            return "synthesis"
        elif any(word in thinking_lower for word in ["search", "find", "look for"]):
            return "search_intent"
        elif any(word in thinking_lower for word in ["read", "article", "page"]):
            return "read_intent"
        else:
            return "general"
    
    def detect_stuck_loop(self, iteration, is_llama=False):
        """Detect if AI is stuck in planning without action."""
        # Pattern 1: Same theme repeated 3+ times (check first - more specific)
        if len(self.last_thinking_themes) >= 3:
            if self.last_thinking_themes[-1] == self.last_thinking_themes[-2] == self.last_thinking_themes[-3]:
                if self.last_thinking_themes[-1] in ["planning", "search_intent"]:
                    return "theme_loop"
        
        # Pattern 2: Multiple consecutive thoughts without tool calls (general fallback)
        # For Llama, be more strict to force faster completion
        threshold = 3 if is_llama else 3
        if self.consecutive_thoughts_without_tools >= threshold:
            return "repeated_planning"
        
        # Pattern 3: No new facts accumulated - be stricter for Llama to force completion
        current_fact_count = len(self.tool_results)
        if iteration >= 6 and current_fact_count == self.last_fact_count:
            self.iterations_without_new_facts += 1
            # For Llama, be stricter to force completion sooner
            threshold = 4 if is_llama else 5
            if self.iterations_without_new_facts >= threshold:
                return "no_progress"
        else:
            self.iterations_without_new_facts = 0
            self.last_fact_count = current_fact_count
        
        # Pattern 4: Force completion after sufficient research for Llama
        if is_llama and iteration >= 12 and current_fact_count >= 3:
            return "sufficient_research"
        
        return None
    
    def should_trim_context(self, iteration, is_llama=False):
        """Progressive context trimming based on iteration."""
        # Llama needs more aggressive trimming due to the alternating pattern
        if is_llama:
            if iteration >= 12:
                return "emergency"  # Minimal context only
            elif iteration >= 8:
                return "aggressive"  # System + tool results + user message only
            elif iteration >= 5:
                return "moderate"  # Drop old thinking blocks
            else:
                return "light"  # Keep only recent thinking
        else:
            if iteration >= 20:
                return "emergency"  # Minimal context only
            elif iteration >= 15:
                return "aggressive"  # System + tool results + user message only
            elif iteration >= 10:
                return "moderate"  # Drop old thinking blocks
            else:
                return "none"
    
    def build_optimized_messages(self, current_messages, iteration, is_llama=False):
        """Build fresh message list from component streams."""
        trim_level = self.should_trim_context(iteration, is_llama)
        
        messages = []
        
        # System prompt always first and complete
        messages.append({"role": "system", "content": self.system_prompt})
        
        # Add progress markers to create urgency
        max_iter = 18 if is_llama else 30  # Match the max_iterations in run_research
        if iteration >= 5:
            progress_note = f"\n\n[PROGRESS: Iteration {iteration}/{max_iter}"
            if self.tool_results:
                progress_note += f" | {len(self.tool_results)} tools used"
            if self.research_context.get('pages_read', 0) > 0:
                progress_note += f" | {self.research_context['pages_read']} pages read"
            progress_note += "]"
            
            messages[0]["content"] += progress_note
        
        # Light trimming: keep only last 3 thinking blocks for Llama
        if trim_level == "light":
            # Minimal conversation history
            if self.conversation_history:
                messages.extend(self.conversation_history[-1:])
            
            # All tool results (they're compact)
            for tool_msg in self.tool_results:
                messages.append(tool_msg)
            
            # Only last 3 thinking messages from current_messages
            thinking_messages = [m for m in current_messages if m.get("role") == "assistant" and extract_reasoning(m.get("content", ""))]
            for think_msg in thinking_messages[-3:]:
                messages.append(think_msg)
            
            # Current user message
            messages.append({"role": "user", "content": self.user_message})
            
            return messages
        
        # Emergency mode: minimal context
        if trim_level == "emergency":
            # Only last 2 tool results for Llama (more aggressive)
            result_count = 2 if is_llama else 3
            if self.tool_results:
                for tool_msg in self.tool_results[-result_count:]:
                    messages.append(tool_msg)
            
            # Inject urgency
            messages.append({
                "role": "user",
                "content": f"[EMERGENCY: {30-iteration} iterations remaining. Synthesize and provide final answer NOW.]"
            })
            
            # Current user message
            messages.append({"role": "user", "content": self.user_message})
            
            return messages
        
        # Aggressive trimming: drop all thinking
        if trim_level == "aggressive":
            # All tool results (compact)
            for tool_msg in self.tool_results:
                messages.append(tool_msg)
            
            # Inject urgency
            messages.append({
                "role": "user", 
                "content": f"[{30-iteration} iterations left. Complete your answer with citations.]"
            })
            
            # Current user message
            messages.append({"role": "user", "content": self.user_message})
            
            return messages
        
        # Moderate trimming: keep only recent thinking
        if trim_level == "moderate":
            # Keep conversation history minimal
            if self.conversation_history:
                messages.extend(self.conversation_history[-2:])
            
            # All tool results
            for tool_msg in self.tool_results:
                messages.append(tool_msg)
            
            # Only last 2 thinking blocks from current_messages
            thinking_messages = [m for m in current_messages if m.get("role") == "assistant" and extract_reasoning(m.get("content", ""))]
            for think_msg in thinking_messages[-2:]:
                messages.append(think_msg)
            
            # Current user message
            messages.append({"role": "user", "content": self.user_message})
            
            return messages
        
        # No trimming: use current messages as-is but ensure system prompt is first
        # However, still truncate any overly long content
        cleaned_messages = []
        for msg in current_messages:
            if msg.get("role") == "system":
                cleaned_messages.append(msg)
            elif msg.get("role") == "tool":
                # Keep tool messages compact
                cleaned_msg = msg.copy()
                if isinstance(msg.get("content"), str) and len(msg["content"]) > 1800:
                    cleaned_msg["content"] = msg["content"][:1800]
                cleaned_messages.append(cleaned_msg)
            else:
                cleaned_messages.append(msg)
        
        return cleaned_messages
    
    def inject_urgency(self, iteration, stuck_type=None, max_iterations=30):
        """Generate urgency message based on situation."""
        if stuck_type == "repeated_planning":
            return "ERROR: Stop planning. Execute tool calls NOW. No more thinking without action."
        elif stuck_type == "theme_loop":
            return "ERROR: You're repeating yourself. Take action immediately - use tools or provide final answer."
        elif stuck_type == "no_progress":
            return "ERROR: No progress detected. Use tools to gather information or synthesize findings."
        elif stuck_type == "sufficient_research":
            return "COMPLETE: You have enough information. Provide final answer with citations NOW."
        elif iteration >= max_iterations * 0.67:  # 67% through iterations
            return f"CRITICAL: Only {max_iterations-iteration} iterations left. Provide final answer with citations immediately."
        elif iteration >= max_iterations * 0.5:  # 50% through iterations
            return f"URGENT: {max_iterations-iteration} iterations remaining. Complete synthesis and answer."
        else:
            return None

async def run_research(channel, prompt, model_name, user_id):
    cid = channel.id
    container_tag = str(user_id)  # Using user_id as container tag
    
    if cid not in conversation_history:
        conversation_history[cid] = []
    
    # Get user profile and search memory if Supermemory is enabled
    context_from_memory = ""
    if supermemory and supermemory.enabled:
        # Get profile with search in one call
        profile_data = await supermemory.get_profile(container_tag, query=prompt)
        
        if profile_data:
            profile = profile_data.get('profile', {})
            static_facts = profile.get('static', [])
            dynamic_context = profile.get('dynamic', [])
            
            # Build context from profile
            if static_facts or dynamic_context:
                context_parts = []
                if static_facts:
                    context_parts.append("**User Profile (Static):**\n" + "\n".join(f"- {fact}" for fact in static_facts[:5]))
                if dynamic_context:
                    context_parts.append("**Recent Context:**\n" + "\n".join(f"- {ctx}" for ctx in dynamic_context[:5]))
                
                context_from_memory = "\n\n".join(context_parts)
            
            # If search results were included
            search_results = profile_data.get('searchResults', {}).get('results', [])
            if search_results:
                memory_texts = []
                for result in search_results[:3]:
                    if 'memory' in result:
                        memory_texts.append(result['memory'][:200])
                    elif 'chunk' in result:
                        memory_texts.append(result['chunk'][:200])
                
                if memory_texts:
                    context_from_memory += "\n\n**Relevant Memories:**\n" + "\n".join(f"- {mem}" for mem in memory_texts)
    
    system_prompt = get_system_prompt(model_name, has_memory=(supermemory and supermemory.enabled))
    
    # Add memory context to system prompt if available
    if context_from_memory:
        system_prompt += f"\n\n### USER CONTEXT FROM MEMORY\n{context_from_memory}\n"
    
    recent_context = conversation_history[cid][-4:] if conversation_history[cid] else []
    
    # Initialize context manager
    context_mgr = ContextManager(
        system_prompt=system_prompt,
        user_message=prompt,
        conversation_history=recent_context
    )
    
    messages = [
        {"role": "system", "content": system_prompt}
    ] + recent_context + [
        {"role": "user", "content": prompt}
    ]
    
    embed = discord.Embed(title="Reasoning", color=0x5865F2)
    reasoning_msg = await channel.send(embed=embed)
    
    display_sections = []
    sources = {}
    failed_pages = set()
    tool_call_count = 0
    max_tools = 12
    
    has_planning = False
    has_synthesis = False
    pages_read = 0
    is_research_query = False
    is_llama = "llama" in model_name.lower()
    is_gpt_oss = "gpt-oss" in model_name.lower()

    async def update_ui(final=False):
        seen = set()
        unique_sections = []
        for section in display_sections:
            section_key = section[:100]
            if section_key not in seen:
                seen.add(section_key)
                unique_sections.append(section)
        
        if final:
            unique_sections = convert_to_past_tense(unique_sections)
        
        embed.description = "\n\n".join(unique_sections)[:4000]
        try:
            await reasoning_msg.edit(embed=embed)
        except:
            pass

    # Model-specific iteration limits
    max_iterations = 18 if is_llama else (25 if is_gpt_oss else 30)
    
    for iteration in range(max_iterations):
        # Check for stuck loops BEFORE API call
        stuck_type = context_mgr.detect_stuck_loop(iteration, is_llama=is_llama)
        if stuck_type:
            urgency_msg = context_mgr.inject_urgency(iteration, stuck_type, max_iterations)
            if urgency_msg:
                messages.append({"role": "user", "content": urgency_msg})
                print(f"🚨 Loop detected: {stuck_type} at iteration {iteration}")
        
        # Progressive context optimization - start earlier for Llama
        optimization_threshold = 4 if is_llama else 10
        if iteration >= optimization_threshold:
            messages = context_mgr.build_optimized_messages(messages, iteration, is_llama=is_llama)
            print(f"📊 Context optimized at iteration {iteration}: {len(str(messages))} chars")
        
        # Check context size and force emergency mode if needed
        context_size = len(str(messages))
        if context_size > 25000:  # Approximate token limit check
            print(f"⚠️ Large context detected ({context_size} chars), forcing emergency mode")
            messages = context_mgr.build_optimized_messages(messages, 20, is_llama=is_llama)
        
        try:
            # Build API parameters based on model type
            api_params = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 2000
            }
            
            # GPT-OSS models support reasoning and built-in tools
            if is_gpt_oss:
                # Use Groq's built-in tools
                api_params["tools"] = get_tools_for_model(model_name, include_memory=(supermemory and supermemory.enabled))
                # Enable reasoning for GPT-OSS (reasoning_format is NOT supported by GPT-OSS)
                # Only use include_reasoning parameter as per Groq documentation
                api_params["include_reasoning"] = True
                # Note: reasoning_format and include_reasoning are mutually exclusive
                # Note: cacheable property is not supported by openai/gpt-oss-120b
            else:
                # Kimi K2 uses custom tools and traditional format
                api_params["tools"] = get_tools_for_model(model_name, include_memory=(supermemory and supermemory.enabled))
                api_params["tool_choice"] = "auto"
            
            response = groq_client.chat.completions.create(**api_params)
        except Exception as e:
            error_msg = str(e)
            
            if "rate_limit" in error_msg.lower() or "413" in error_msg or "too large" in error_msg.lower():
                print(f"⚠️ Context too large error at iteration {iteration}")
                # Force emergency mode trimming with even more aggressive approach
                messages = context_mgr.build_optimized_messages(messages, 25, is_llama=is_llama)
                # Also inject urgency to force completion
                messages.append({
                    "role": "user",
                    "content": "CRITICAL: Context limit reached. Provide final answer NOW with available information."
                })
                continue
            else:
                await channel.send(f"⚠️ API Error: {e}")
                return

        msg = response.choices[0].message
        content = msg.content or ""
        
        # Handle reasoning content from GPT-OSS models
        # Per Groq docs, reasoning is in the 'reasoning' field when include_reasoning=True
        reasoning_content = None
        if is_gpt_oss and hasattr(msg, 'reasoning') and msg.reasoning:
            reasoning_content = msg.reasoning
            # Display reasoning in UI
            reasoning_section = f"🧠 **Reasoning**\n\n> {reasoning_content[:500]}"
            if len(reasoning_content) > 500:
                reasoning_section += "..."
            display_sections.append(reasoning_section)
            await update_ui()
        
        hallucinated = re.search(r'<function[^>]*>|(?:search_wikipedia|get_wikipedia_page|search_memory)\s*\(|\{\s*"query":', content, re.IGNORECASE)
        
        tool_calls = msg.tool_calls
        
        # Track in context manager for loop detection
        context_mgr.add_thinking(content, has_tool_calls=bool(tool_calls))
        
        # Handle thinking tags for Kimi K2 (not GPT-OSS which uses reasoning_content)
        if not is_gpt_oss:
            think = extract_reasoning(content)
            if think:
                is_research_query = True
                header, body = parse_thinking_with_header(think)
                
                if header:
                    if "Planning" in header or "planning" in header.lower():
                        has_planning = True
                    elif "Synthesiz" in header or "synthesiz" in header.lower():
                        has_synthesis = True
                
                # Truncate body for display and storage
                max_body_length = 500
                if body and len(body) > max_body_length:
                    body = body[:max_body_length] + "..."
                
                if header and body:
                    thinking_section = f"🧠 **Thought**\n\n> **{header}**\n\n{body}"
                elif body:
                    thinking_section = f"🧠 **Thought**\n\n> {think[:max_body_length]}"
                else:
                    thinking_section = f"🧠 **Thought**\n\n> {think[:max_body_length]}"
                
                display_sections.append(thinking_section)
                await update_ui()
        
        if tool_calls:
            is_research_query = True
        
        # Only check for hallucinated tools in Kimi K2 (not GPT-OSS which handles reasoning differently)
        if not is_gpt_oss and hallucinated and not tool_calls:
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": "ERROR: Use native API only."})
            continue
        
        if tool_calls:
            # Build assistant message with tool calls
            assistant_msg = {
                "role": "assistant",
                "content": content
            }
            
            # Add reasoning content if present (for GPT-OSS)
            if reasoning_content:
                assistant_msg["reasoning_content"] = reasoning_content
            
            # Add tool calls
            assistant_msg["tool_calls"] = [
                {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ]
            
            messages.append(assistant_msg)
            
            for tool_call in tool_calls:
                tool_call_count += 1
                
                if tool_call_count > max_tools:
                    error_msg = "⚠️ **Tool Limit Reached**"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": "Maximum tools. Synthesize and answer now."
                    })
                    display_sections.append(error_msg)
                    await update_ui()
                    continue
                
                # Check if this is a built-in tool (browser_search, code_interpreter)
                is_builtin_tool = tool_call.type in ["browser_search", "code_interpreter"]
                
                if is_builtin_tool:
                    # Built-in tools are handled automatically by Groq
                    # We just need to display them in the UI
                    tool_type = tool_call.type
                    
                    if tool_type == "browser_search":
                        # Extract query from tool call if available
                        query_display = "Searching the web..."
                        try:
                            if hasattr(tool_call, 'function') and tool_call.function.arguments:
                                fn_args = json.loads(tool_call.function.arguments)
                                query_display = f"Searching: {fn_args.get('query', 'the web')}"
                        except:
                            pass
                        
                        display_sections.append(f"🔍 **Web Search**\n\n> {query_display}")
                        await update_ui()
                    elif tool_type == "code_interpreter":
                        display_sections.append(f"💻 **Code Execution**\n\n> Running Python code...")
                        await update_ui()
                    
                    # Built-in tools don't need explicit handling - continue to next tool
                    continue
                
                # Handle custom function tools
                fn_name = tool_call.function.name
                
                try:
                    fn_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    result = "ERROR: Invalid arguments"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": result
                    })
                    continue
                
                if fn_name == "search_memory":
                    if not (supermemory and supermemory.enabled):
                        result = "Memory search unavailable. Enable Supermemory to use this feature."
                    else:
                        query = fn_args.get('query', '')
                        display_sections.append(f"🧠 **Searching Memory...**\n\n> {query}")
                        await update_ui()
                        
                        # Search memory with user filter
                        memories = await supermemory.search_memory(
                            query=query,
                            container_tag=container_tag,
                            limit=3
                        )
                        
                        if memories:
                            # Format memory results - handle both memory and chunk results
                            memory_texts = []
                            for mem in memories:
                                if isinstance(mem, dict):
                                    # Check if it's a memory result or chunk result
                                    if 'memory' in mem:
                                        content_text = mem['memory']
                                    elif 'chunk' in mem:
                                        content_text = mem['chunk']
                                    else:
                                        content_text = mem.get('content', str(mem))
                                    
                                    # Add metadata if available
                                    metadata = mem.get('metadata', {})
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
                        context_mgr.research_context['pages_read'] = pages_read
                else:
                    result = "ERROR: Unknown function"
                
                # Truncate tool results more aggressively for Llama
                max_tool_result = 800 if is_llama else 1800
                tool_result_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": str(result)[:max_tool_result]
                }
                messages.append(tool_result_msg)
                
                # Track in context manager
                context_mgr.add_tool_result(tool_result_msg)
        
        else:
            final_answer = clean_output(content)
            
            # For Kimi K2, check minimum pages (GPT-OSS uses browser_search instead)
            if is_research_query and not is_gpt_oss:
                min_pages = 3
                if pages_read < min_pages:
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"Read {min_pages - pages_read} more page(s) for comprehensive answer."
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
            
            # Save to Supermemory if enabled and it's a meaningful interaction
            if supermemory and supermemory.enabled and final_answer and len(final_answer) > 50:
                # Prepare memory content - store the conversation exchange
                memory_content = f"User: {prompt}\n\nAssistant: {final_answer[:1500]}"
                
                # Prepare metadata
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "model": model_name,
                    "type": "research_qa" if is_research_query else "conversation",
                    "channel_id": str(cid),
                    "sources_count": len(sources) if sources else 0
                }
                
                # Save asynchronously without blocking
                asyncio.create_task(supermemory.add_memory(
                    content=memory_content,
                    container_tag=container_tag,
                    metadata=metadata
                ))
                print(f"💾 Saving to memory for user {user_id}")
            
            # Update conversation history
            conversation_history[cid].append({"role": "user", "content": prompt})
            conversation_history[cid].append({"role": "assistant", "content": final_answer[:400]})
            
            # Trim conversation history
            if len(conversation_history[cid]) > 6:
                conversation_history[cid] = conversation_history[cid][-6:]
            
            # Update UI to show completion
            embed.title = "✅ Reasoning Complete"
            embed.color = 0x57F287
            await update_ui(final=True)
            
            # Send final answer
            if len(final_answer) > 2000:
                chunks = [final_answer[i:i+2000] for i in range(0, len(final_answer), 2000)]
                for chunk in chunks:
                    await channel.send(chunk)
            else:
                await channel.send(final_answer)
            
            return
    
    # If loop exhausted
    await channel.send("⚠️ Reasoning exceeded maximum iterations.")

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN not set in .env file")
        exit(1)
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY not set in .env file")
        exit(1)
    
    print("🚀 Starting Discord bot...")
    bot.run(DISCORD_BOT_TOKEN)
