#!/usr/bin/env python3
"""
Configuration and setup for AskLab AI Bot
"""
import os
import discord
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
SUPERMEMORY_API_KEY = os.getenv('SUPERMEMORY_API_KEY')

# --- CLIENTS ---
groq_client = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True

# --- BOT SETUP ---
bot = commands.Bot(command_prefix='!', intents=intents)

# --- CONSTANTS ---
WIKI_HEADERS = {"User-Agent": "AskLabBot/2.0 (contact: admin@asklab.ai) aiohttp/3.8"}

AVAILABLE_MODELS = {
    "Llama 3.3 70B": "llama-3.3-70b-versatile",
    "Kimi K2 Instruct": "moonshotai/kimi-k2-instruct-0905"
}

# --- GLOBAL STATE ---
conversation_history = {}
user_model_preferences = {}