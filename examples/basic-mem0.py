#!/usr/bin/env python3
"""
Basic Mem0 Integration for OpenClaw Agents
Mem0 auto-extracts memories from conversations.
"""

import os
from mem0 import Memory

# Initialize
m = Memory()

# Store memories from a conversation
def remember_conversation(user_id: str, messages: list[dict]):
    """
    Process a conversation and extract memories.
    
    messages format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    result = m.add(messages, user_id=user_id)
    print(f"Extracted {len(result.get('results', []))} memories")
    return result

# Search memories
def recall(user_id: str, query: str, limit: int = 5):
    """
    Search memories for a user.
    """
    results = m.search(query, user_id=user_id, limit=limit)
    return results

# Get all memories for a user
def get_all_memories(user_id: str):
    """
    Retrieve all stored memories for a user.
    """
    return m.get_all(user_id=user_id)


# Example usage
if __name__ == "__main__":
    USER_ID = "jack"
    
    # Simulate a conversation
    conversation = [
        {"role": "user", "content": "I'm working on a project called Toastique"},
        {"role": "assistant", "content": "Tell me more about Toastique!"},
        {"role": "user", "content": "It's a content management system for social media. Built with Next.js and Supabase."},
        {"role": "assistant", "content": "Nice stack! Next.js for the frontend and Supabase for backend/auth?"},
        {"role": "user", "content": "Exactly. I prefer Supabase over Firebase these days."}
    ]
    
    # Store memories
    print("📝 Storing conversation memories...")
    remember_conversation(USER_ID, conversation)
    
    # Recall
    print("\n🔍 Searching for 'tech stack preferences'...")
    results = recall(USER_ID, "tech stack preferences")
    for r in results.get("results", []):
        print(f"  - {r.get('memory', r)}")
    
    # Get all
    print("\n📚 All memories for user:")
    all_mems = get_all_memories(USER_ID)
    for mem in all_mems.get("results", []):
        print(f"  - {mem.get('memory', mem)}")
