#!/usr/bin/env python3
"""
Supermemory client for AskLab AI Bot
"""
import asyncio
import requests
import os

SUPERMEMORY_API_KEY = os.getenv('SUPERMEMORY_API_KEY')

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
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Memory added successfully: {result.get('id', 'Unknown ID')}")
                return result
            else:
                print(f"❌ Failed to add memory: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error adding memory: {e}")
            return None
    
    async def search_memory(self, query, container_tag=None, limit=3):
        """Search memories using the v4/search endpoint."""
        if not self.enabled:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            
            payload = {
                "q": query,
                "limit": limit
            }
            
            # Add container tag filter if provided
            if container_tag:
                payload["containerTag"] = container_tag
            
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
                result = response.json()
                return result.get("results", [])
            else:
                print(f"❌ Memory search failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching memory: {e}")
            return []