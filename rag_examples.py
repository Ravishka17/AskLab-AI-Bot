"""
RAG (Retrieval-Augmented Generation) module for few-shot examples.
Provides retrieval of reasoning patterns and examples based on query context.
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class RAGExampleStore:
    """
    Manages retrieval of few-shot examples for reasoning patterns.
    Uses simple keyword matching to find relevant examples.
    """
    
    def __init__(self, examples_file: str = None):
        """Initialize the RAG example store."""
        if examples_file is None:
            # Try to find rag_examples.json in multiple locations
            env_path = os.getenv('RAG_EXAMPLES_PATH')
            if env_path:
                examples_file = Path(env_path)
            else:
                # Look for rag_examples.json in the container root or data folder
                possible_paths = [
                    Path.cwd() / "rag_examples.json",  # Container root
                    Path.cwd() / "data" / "rag_examples.json",  # data folder
                    Path("/home/container/rag_examples.json"),  # fps.ms path
                    Path("/home/container/data/rag_examples.json"),  # fps.ms data path
                ]
                for path in possible_paths:
                    if path.exists():
                        examples_file = path
                        break
                else:
                    # Fallback
                    examples_file = Path.cwd() / "data" / "rag_examples.json"
        else:
            examples_file = Path(examples_file)
        
        self.examples_file = examples_file
        self.examples = self._load_examples()
        
    def _load_examples(self) -> Dict:
        """Load examples from JSON file."""
        try:
            with open(self.examples_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: RAG examples file not found at {self.examples_file}")
            return {"examples": [], "reasoning_rules": {}}
        except json.JSONDecodeError as e:
            print(f"Error parsing RAG examples file: {e}")
            return {"examples": [], "reasoning_rules": {}}
    
    def _calculate_relevance(self, query: str, example: Dict) -> float:
        """Calculate relevance score between query and example."""
        query_lower = query.lower()
        score = 0.0
        
        # Check for current leader patterns
        leader_keywords = [
            'president', 'prime minister', 'chancellor', 'monarch', 
            'king', 'queen', 'governor', 'mayor', 'leader', 'head of state'
        ]
        
        if any(kw in query_lower for kw in leader_keywords):
            example_id = example.get('id', '')
            if 'leader' in example_id.lower():
                score += 0.5
            if 'biography' in example_id.lower():
                score += 0.3
        
        # Check for country/entity names
        for keyword in query_lower.split():
            if len(keyword) > 3:
                if keyword in example.get('question', '').lower():
                    score += 0.2
        
        # Boost for current event patterns
        event_keywords = ['recent', 'current', 'latest', 'now', 'today', '2024', '2023']
        if any(kw in query_lower for kw in event_keywords):
            example_id = example.get('id', '')
            if 'current' in example_id.lower() or 'recent' in example_id.lower():
                score += 0.3
        
        # Boost for technology/product patterns
        tech_keywords = ['iphone', 'phone', 'laptop', 'computer', 'software', 'ai', 'model']
        if any(kw in query_lower for kw in tech_keywords):
            example_id = example.get('id', '')
            if 'technology' in example_id.lower() or 'product' in example_id.lower():
                score += 0.4
        
        return min(score, 1.0)
    
    def retrieve_examples(self, query: str, max_examples: int = 2) -> List[Dict]:
        """Retrieve the most relevant examples for a given query."""
        if not self.examples.get('examples'):
            return []
        
        scored_examples = []
        for example in self.examples['examples']:
            relevance = self._calculate_relevance(query, example)
            if relevance > 0:
                scored_examples.append((relevance, example))
        
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored_examples[:max_examples]]
    
    def get_system_prompt_additions(self, query: str) -> str:
        """Generate system prompt additions based on retrieved examples."""
        examples = self.retrieve_examples(query)
        
        if not examples:
            return ""
        
        prompt_additions = "\n\n📋 **EXAMPLE PATTERNS TO FOLLOW:**\n\n"
        
        for i, example in enumerate(examples, 1):
            prompt_additions += f"--- Example {i}: {example.get('id', 'Unknown')} ---\n"
            prompt_additions += f"Question: {example.get('question', '')}\n\n"
            
            for step in example.get('thinking_examples', []):
                prompt_additions += f"Step {step.get('step', '?')}:\n"
                prompt_additions += f"🧠 Thinking:\n{step.get('thinking', '')}\n\n"
                if step.get('action') == 'answer':
                    prompt_additions += f"✅ Final Answer: {step.get('content', '')}\n\n"
            
            prompt_additions += "---\n\n"
        
        return prompt_additions
    
    def check_research_completeness(self, query: str, pages_read: List[str]) -> Dict:
        """Check if the research is complete based on the example patterns."""
        examples = self.retrieve_examples(query)
        
        if not examples:
            return {"complete": True, "reason": "No example patterns to validate against"}
        
        example = examples[0]
        rules = self.examples.get('reasoning_rules', {}).get('required_sources', {})
        
        query_lower = query.lower()
        leader_keywords = ['president', 'prime minister', 'chancellor', 'leader']
        is_leader_research = any(kw in query_lower for kw in leader_keywords)
        
        if is_leader_research:
            required_count = rules.get('required_pages', 2)
            position_keywords = ['president of', 'prime minister of', 'list of']
            biography_keywords = ['biography', 'born', 'early life']
            
            def looks_like_name(title: str) -> bool:
                words = title.split()
                if len(words) >= 2:
                    return all(w[0].isupper() for w in words if w and len(w) > 1)
                return False
            
            has_position = any(kw in page.lower() for kw in position_keywords for page in pages_read)
            has_bio = any(
                kw in page.lower() for kw in biography_keywords 
                for page in pages_read
            ) or any(looks_like_name(page) for page in pages_read)
            
            if has_position and has_bio:
                return {"complete": True, "reason": "Both position and biography pages have been read"}
            elif not has_bio and has_position:
                return {"complete": False, "reason": "You have read the position page but NOT the biography page. For current leaders, you MUST read BOTH to provide a complete answer."}
            elif has_bio and not has_position:
                return {"complete": False, "reason": "You have read the biography page but NOT the position page. For current leaders, you MUST read BOTH to provide a complete answer."}
        
        if len(pages_read) >= rules.get('required_pages', 1):
            return {"complete": True, "reason": f"Required number of pages have been read"}
        
        return {"complete": False, "reason": f"You have only read {len(pages_read)} page(s). More research may be needed."}


# Singleton instance
_rag_store = None

def get_rag_store() -> RAGExampleStore:
    """Get or create the singleton RAG store instance."""
    global _rag_store
    if _rag_store is None:
        _rag_store = RAGExampleStore()
    return _rag_store

def initialize_rag(examples_file: str = None) -> RAGExampleStore:
    """Initialize the RAG store with optional custom examples file."""
    global _rag_store
    _rag_store = RAGExampleStore(examples_file)
    return _rag_store
