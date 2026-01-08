#!/usr/bin/env python3
"""
Wikipedia utilities for AskLab AI Bot
"""
import aiohttp
import asyncio
import os

# Import WIKI_HEADERS from config
try:
    from config import WIKI_HEADERS
except ImportError:
    # Fallback if import fails
    WIKI_HEADERS = {"User-Agent": "AskLabBot/2.0 (contact: admin@asklab.ai) aiohttp/3.8"}

async def fetch_wiki(params, retries=3):
    """Fetch data from Wikipedia API with retries."""
    url = "https://en.wikipedia.org/w/api.php"
    
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=WIKI_HEADERS) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Wikipedia API error: {response.status}")
                        if attempt < retries - 1:
                            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error fetching Wikipedia data (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1)
    
    return None

async def search_wikipedia(query):
    """Search Wikipedia for articles."""
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'search',
        'srsearch': query,
        'srlimit': 10,
        'srprop': 'snippet'
    }
    
    result = await fetch_wiki(params)
    
    if result and 'query' in result and 'search' in result['query']:
        search_results = result['query']['search']
        if search_results:
            return [f"{article['title']}" for article in search_results[:5]]
    
    return []

async def get_wikipedia_page(title):
    """Get the content of a Wikipedia page."""
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'extracts',
        'exintro': True,
        'explaintext': True,
        'titles': title,
        'redirects': 1
    }
    
    result = await fetch_wiki(params)
    
    if result and 'query' in result and 'pages' in result['query']:
        pages = result['query']['pages']
        for page_id, page_data in pages.items():
            if 'extract' in page_data and page_data['extract']:
                return page_data['extract']
            elif 'missing' in page_data:
                return f"Page '{title}' not found."
    
    return "Failed to retrieve Wikipedia page content."