#!/usr/bin/env python3
"""
Full OpenClaw Integration Example
Combining multiple memory systems for a complete agent memory solution.
"""

import os
from typing import Optional
from dataclasses import dataclass

# Import the memory systems
from mem0 import Memory
import chromadb


@dataclass
class MemoryResult:
    """Unified memory result format."""
    content: str
    source: str  # "mem0", "chroma", "zep", "letta"
    metadata: dict
    score: Optional[float] = None


class OpenClawMemory:
    """
    Unified memory interface for OpenClaw agents.
    
    Architecture:
    - ChromaDB: Fast local vector store for all memories (primary)
    - Mem0: Auto-extraction of memories from conversations
    - Zep: Temporal queries (optional, needs server)
    - Letta: Self-editing hierarchical memory (optional, needs server)
    
    This example uses ChromaDB + Mem0 as the core stack (zero infrastructure).
    """
    
    def __init__(self, persist_path: str = "./agent_memory"):
        # ChromaDB for fast local search
        self.chroma = chromadb.PersistentClient(path=persist_path)
        self.collection = self.chroma.get_or_create_collection(
            name="agent_memories",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Mem0 for automatic memory extraction
        self.mem0 = Memory()
        
        # User tracking
        self.current_user: Optional[str] = None
    
    def set_user(self, user_id: str):
        """Set the current user context."""
        self.current_user = user_id
    
    def remember_conversation(self, messages: list[dict], user_id: str = None):
        """
        Process a conversation and extract memories.
        Uses Mem0 for extraction, stores in both Mem0 and ChromaDB.
        """
        user_id = user_id or self.current_user or "default"
        
        # Mem0 auto-extracts memories
        result = self.mem0.add(messages, user_id=user_id)
        
        # Also store in ChromaDB for fast local search
        for i, msg in enumerate(messages):
            self.collection.add(
                documents=[msg["content"]],
                metadatas=[{
                    "role": msg["role"],
                    "user_id": user_id,
                    "source": "conversation"
                }],
                ids=[f"{user_id}_{self.collection.count()}_{i}"]
            )
        
        return result
    
    def remember(self, content: str, metadata: dict = None, user_id: str = None):
        """
        Store a single memory.
        """
        user_id = user_id or self.current_user or "default"
        metadata = metadata or {}
        metadata["user_id"] = user_id
        
        doc_id = f"{user_id}_{self.collection.count()}"
        
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def recall(self, query: str, n_results: int = 5, user_id: str = None) -> list[MemoryResult]:
        """
        Search memories.
        Queries both ChromaDB (fast, local) and Mem0 (semantic extraction).
        """
        user_id = user_id or self.current_user
        results = []
        
        # ChromaDB search
        where_filter = {"user_id": user_id} if user_id else None
        chroma_results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        for i, doc in enumerate(chroma_results["documents"][0]):
            results.append(MemoryResult(
                content=doc,
                source="chroma",
                metadata=chroma_results["metadatas"][0][i],
                score=chroma_results["distances"][0][i] if "distances" in chroma_results else None
            ))
        
        # Mem0 search
        mem0_results = self.mem0.search(query, user_id=user_id, limit=n_results)
        for mem in mem0_results.get("results", []):
            results.append(MemoryResult(
                content=mem.get("memory", str(mem)),
                source="mem0",
                metadata=mem.get("metadata", {})
            ))
        
        return results
    
    def get_context(self, user_id: str = None, max_memories: int = 10) -> str:
        """
        Get a formatted context string for injection into prompts.
        """
        user_id = user_id or self.current_user or "default"
        
        # Get all memories for user
        all_mems = self.mem0.get_all(user_id=user_id)
        
        if not all_mems.get("results"):
            return "No stored memories for this user."
        
        context_parts = ["## Relevant Memories"]
        for mem in all_mems["results"][:max_memories]:
            content = mem.get("memory", str(mem))
            context_parts.append(f"- {content}")
        
        return "\n".join(context_parts)


# Example usage
if __name__ == "__main__":
    print("🦉 OpenClaw Memory Integration Example")
    print("=" * 50)
    
    # Initialize
    memory = OpenClawMemory(persist_path="./demo_memory")
    memory.set_user("jack")
    
    # Store some memories
    print("\n📝 Storing memories...")
    memory.remember(
        "Jack is building owl-brain, a memory stack for AI agents",
        metadata={"type": "project", "topic": "ai"}
    )
    memory.remember(
        "Jack prefers working late night, 11pm-3am",
        metadata={"type": "preference", "topic": "schedule"}
    )
    memory.remember(
        "Tech stack preferences: Next.js, Supabase, Python",
        metadata={"type": "preference", "topic": "tech"}
    )
    
    # Process a conversation
    print("\n💬 Processing conversation...")
    conversation = [
        {"role": "user", "content": "I just finished the ChromaDB integration"},
        {"role": "assistant", "content": "Nice! How's it performing?"},
        {"role": "user", "content": "Super fast. Zero config needed, just works."}
    ]
    memory.remember_conversation(conversation)
    
    # Recall
    print("\n🔍 Searching for 'what database does Jack use'...")
    results = memory.recall("what database does Jack use", n_results=3)
    for r in results:
        print(f"  [{r.source}] {r.content}")
    
    # Get context for prompt injection
    print("\n📋 Context for prompt:")
    print(memory.get_context())
