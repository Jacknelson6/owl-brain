#!/usr/bin/env python3
"""
owl-brain Memory Stack Test Script
Run: source .venv/bin/activate && python test/memory-stack-test.py
"""

import os
import sys

def test_chromadb():
    """Test ChromaDB - Local vector database"""
    print("\n🔷 Testing ChromaDB...")
    import chromadb
    
    # Create ephemeral client (in-memory)
    client = chromadb.Client()
    collection = client.create_collection("test_collection")
    
    # Add some test data
    collection.add(
        documents=[
            "The owl sees patterns others miss",
            "Memory is more than context stuffing", 
            "3am ideas hit different"
        ],
        ids=["doc1", "doc2", "doc3"]
    )
    
    # Query
    results = collection.query(query_texts=["What makes good memory?"], n_results=2)
    print(f"  ✅ ChromaDB working! Query returned {len(results['documents'][0])} results")
    return True

def test_mem0():
    """Test Mem0 - Agentic memory system"""
    print("\n🧠 Testing Mem0...")
    try:
        from mem0 import Memory
        
        # Check for OpenAI key
        if not os.environ.get("OPENAI_API_KEY"):
            # Try loading from config
            key_path = os.path.expanduser("~/.config/openai/api_key")
            if os.path.exists(key_path):
                with open(key_path) as f:
                    os.environ["OPENAI_API_KEY"] = f.read().strip()
        
        if not os.environ.get("OPENAI_API_KEY"):
            print("  ⚠️ Mem0 requires OPENAI_API_KEY - skipping live test")
            print("  Set env var or create ~/.config/openai/api_key")
            return False
            
        m = Memory()
        print("  ✅ Mem0 initialized (OpenAI embeddings ready)")
        return True
    except Exception as e:
        print(f"  ❌ Mem0 error: {e}")
        return False

def test_zep():
    """Test Zep - Temporal-aware memory"""
    print("\n⏱️ Testing Zep...")
    try:
        from zep_python import ZepClient
        print("  ✅ Zep client imported")
        print("  ℹ️ Zep requires either:")
        print("     - Zep Cloud account (https://www.getzep.com/)")
        print("     - Self-hosted Zep server")
        return True
    except Exception as e:
        print(f"  ❌ Zep error: {e}")
        return False

def test_letta():
    """Test Letta - Self-editing hierarchical memory"""
    print("\n📚 Testing Letta...")
    try:
        from letta import create_client
        print("  ✅ Letta client imported")
        print("  ℹ️ To start Letta server: letta server")
        print("     Web UI at http://localhost:8283")
        return True
    except Exception as e:
        print(f"  ❌ Letta error: {e}")
        return False

def main():
    print("=" * 50)
    print("🦉 owl-brain Memory Stack Test")
    print("=" * 50)
    
    results = {
        "ChromaDB": test_chromadb(),
        "Mem0": test_mem0(),
        "Zep": test_zep(),
        "Letta": test_letta()
    }
    
    print("\n" + "=" * 50)
    print("📊 Results Summary")
    print("=" * 50)
    for name, status in results.items():
        emoji = "✅" if status else "⚠️"
        print(f"  {emoji} {name}")
    
    print("\n💡 Next steps:")
    print("  1. Set OPENAI_API_KEY for Mem0")
    print("  2. Run 'letta server' for Letta web UI")
    print("  3. Set up Zep Cloud or self-hosted server")
    print("  4. Wire these into your OpenClaw agent")

if __name__ == "__main__":
    main()
