#!/usr/bin/env python3
"""
ChromaDB Local Vector Store for OpenClaw Agents
Zero config, runs in-process, fast semantic search.
"""

import chromadb
from chromadb.config import Settings

# Ephemeral (in-memory, lost on restart)
def get_ephemeral_client():
    return chromadb.Client()

# Persistent (survives restarts)
def get_persistent_client(path: str = "./chroma_db"):
    return chromadb.PersistentClient(path=path)


class MemoryStore:
    """Simple wrapper for agent memory using ChromaDB."""
    
    def __init__(self, persist_path: str = None):
        if persist_path:
            self.client = chromadb.PersistentClient(path=persist_path)
        else:
            self.client = chromadb.Client()
        
        # Create or get the memories collection
        self.collection = self.client.get_or_create_collection(
            name="agent_memories",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
    
    def add(self, text: str, metadata: dict = None, doc_id: str = None):
        """Add a memory."""
        if doc_id is None:
            doc_id = f"mem_{self.collection.count()}"
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return doc_id
    
    def search(self, query: str, n_results: int = 5):
        """Search memories by semantic similarity."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    
    def get_all(self):
        """Get all memories."""
        return self.collection.get()
    
    def delete(self, doc_id: str):
        """Delete a memory by ID."""
        self.collection.delete(ids=[doc_id])


# Example usage
if __name__ == "__main__":
    # Create persistent store
    store = MemoryStore(persist_path="./test_memories")
    
    # Add some memories
    print("📝 Adding memories...")
    store.add(
        "Jack prefers Supabase over Firebase for backend",
        metadata={"type": "preference", "topic": "tech"}
    )
    store.add(
        "Current project is Toastique - a social media CMS",
        metadata={"type": "project", "topic": "work"}
    )
    store.add(
        "Best working hours are late night, 11pm-3am",
        metadata={"type": "preference", "topic": "schedule"}
    )
    
    # Search
    print("\n🔍 Searching for 'database preferences'...")
    results = store.search("database preferences", n_results=2)
    
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        print(f"  - {doc}")
        print(f"    metadata: {meta}")
    
    # Get all
    print(f"\n📚 Total memories stored: {store.collection.count()}")
