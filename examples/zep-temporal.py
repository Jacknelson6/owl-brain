#!/usr/bin/env python3
"""
Zep Temporal Memory for OpenClaw Agents
Time-aware memory that understands "before" and "after".
"""

import os
from zep_python import ZepClient
from zep_python.memory import Memory, Message

# Initialize client
# Cloud: ZepClient(api_key="z_...")
# Self-hosted: ZepClient(base_url="http://localhost:8000")

def get_zep_client():
    """Get Zep client based on available config."""
    api_key = os.environ.get("ZEP_API_KEY")
    base_url = os.environ.get("ZEP_API_URL")
    
    if api_key:
        return ZepClient(api_key=api_key)
    elif base_url:
        return ZepClient(base_url=base_url)
    else:
        raise ValueError("Set ZEP_API_KEY (cloud) or ZEP_API_URL (self-hosted)")


class TemporalMemory:
    """Wrapper for Zep's temporal memory capabilities."""
    
    def __init__(self):
        self.client = get_zep_client()
    
    async def add_session(self, session_id: str, user_id: str):
        """Create a new memory session."""
        await self.client.memory.add_session(
            session_id=session_id,
            user_id=user_id
        )
    
    async def add_messages(self, session_id: str, messages: list[dict]):
        """
        Add messages to a session.
        
        messages format: [{"role": "user", "content": "..."}, ...]
        """
        zep_messages = [
            Message(
                role=m["role"],
                content=m["content"],
                role_type="user" if m["role"] == "user" else "assistant"
            )
            for m in messages
        ]
        
        memory = Memory(messages=zep_messages)
        await self.client.memory.add(session_id, memory)
    
    async def search(self, session_id: str, query: str, limit: int = 5):
        """
        Search memory with temporal awareness.
        Zep understands time-based queries like "before the project started".
        """
        results = await self.client.memory.search(
            session_id,
            query,
            limit=limit
        )
        return results
    
    async def get_memory(self, session_id: str):
        """Get the synthesized memory for a session."""
        return await self.client.memory.get(session_id)


# Example usage (async)
if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("⏱️ Zep Temporal Memory Example")
        print("-" * 40)
        
        # Check if Zep is configured
        if not (os.environ.get("ZEP_API_KEY") or os.environ.get("ZEP_API_URL")):
            print("⚠️ Zep not configured.")
            print("Set ZEP_API_KEY for Zep Cloud")
            print("Or ZEP_API_URL for self-hosted (e.g., http://localhost:8000)")
            return
        
        tm = TemporalMemory()
        session_id = "night-crew-session-1"
        user_id = "jack"
        
        # Create session
        print(f"Creating session: {session_id}")
        await tm.add_session(session_id, user_id)
        
        # Add conversation
        messages = [
            {"role": "user", "content": "I'm starting a new project today"},
            {"role": "assistant", "content": "Exciting! What's the project?"},
            {"role": "user", "content": "It's called owl-brain, a memory stack for AI agents"},
        ]
        await tm.add_messages(session_id, messages)
        print("Added messages to session")
        
        # Search with temporal query
        results = await tm.search(session_id, "what project was started recently")
        print(f"Search results: {results}")
    
    asyncio.run(main())
