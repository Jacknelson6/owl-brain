#!/usr/bin/env python3
"""
Atlas Unified Memory Recall

Replaces the old PageIndex system with Mem0 + ChromaDB + Letta stack.

Usage:
    python3 atlas_recall.py "your query here"
    python3 atlas_recall.py --index              # Index all memory files
    python3 atlas_recall.py --stats              # Show memory stats
    python3 atlas_recall.py --add "fact here"    # Add a fact manually

Searches:
    - Mem0: Auto-extracted facts from conversations
    - ChromaDB: Chunked memory files (MEMORY.md, memory/*.md)
    - Letta: Hierarchical archival memory (if available)
"""

import os
import sys
import json
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Paths
CLAWD_DIR = Path.home() / "clawd"
MEMORY_DIR = CLAWD_DIR / "memory"
MEMORY_FILE = CLAWD_DIR / "MEMORY.md"
CHROMA_DIR = Path.home() / ".atlas" / "chroma"
INDEX_STATE = Path.home() / ".atlas" / "index_state.json"

# Ensure directories exist
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_STATE.parent.mkdir(parents=True, exist_ok=True)


def load_openai_key():
    """Load OpenAI API key"""
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    
    key_path = Path.home() / ".config" / "openai" / "api_key"
    if key_path.exists():
        key = key_path.read_text().strip()
        os.environ["OPENAI_API_KEY"] = key
        return key
    
    raise ValueError("OPENAI_API_KEY not found")


def chunk_markdown(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict]:
    """
    Split markdown into semantic chunks based on headers and size.
    Returns list of {text, metadata} dicts.
    """
    chunks = []
    lines = content.split('\n')
    
    current_chunk = []
    current_headers = []
    current_size = 0
    
    for line in lines:
        # Track headers for context
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            header_text = line.lstrip('#').strip()
            
            # Flush current chunk if it's substantial
            if current_size > 200:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'headers': ' > '.join(current_headers),
                    'size': current_size
                })
                # Keep overlap
                overlap_lines = current_chunk[-3:] if len(current_chunk) > 3 else current_chunk
                current_chunk = overlap_lines
                current_size = sum(len(l) for l in current_chunk)
            
            # Update header stack
            current_headers = current_headers[:level-1] + [header_text]
        
        current_chunk.append(line)
        current_size += len(line)
        
        # Flush if chunk is large enough
        if current_size >= chunk_size:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'headers': ' > '.join(current_headers),
                'size': current_size
            })
            # Keep overlap
            overlap_lines = current_chunk[-3:] if len(current_chunk) > 3 else current_chunk
            current_chunk = overlap_lines
            current_size = sum(len(l) for l in current_chunk)
    
    # Final chunk
    if current_chunk:
        chunks.append({
            'text': '\n'.join(current_chunk),
            'headers': ' > '.join(current_headers),
            'size': current_size
        })
    
    return chunks


def get_file_hash(path: Path) -> str:
    """Get hash of file contents for change detection"""
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_index_state() -> Dict:
    """Load index state (tracks what's been indexed)"""
    if INDEX_STATE.exists():
        return json.loads(INDEX_STATE.read_text())
    return {"files": {}, "last_full_index": None}


def save_index_state(state: Dict):
    """Save index state"""
    INDEX_STATE.write_text(json.dumps(state, indent=2))


class AtlasRecall:
    """Unified memory recall system"""
    
    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        load_openai_key()
        
        if not quiet:
            print("🧠 Initializing Atlas Memory Stack...")
        
        # Initialize ChromaDB first (shared client)
        import chromadb
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        
        # Document storage collection
        self.chroma = self.chroma_client.get_or_create_collection(
            name="atlas_memory",
            metadata={"description": "Atlas agent memory files"}
        )
        
        # Mem0 - uses separate ChromaDB path to avoid conflicts
        from mem0 import Memory
        mem0_dir = CHROMA_DIR.parent / "mem0_chroma"
        mem0_dir.mkdir(parents=True, exist_ok=True)
        mem0_config = {
            'vector_store': {
                'provider': 'chroma',
                'config': {
                    'collection_name': 'mem0_facts',
                    'path': str(mem0_dir)
                }
            }
        }
        self.mem0 = Memory.from_config(mem0_config)
        self.user_id = "atlas"
        
        # Letta (optional)
        self.letta = None
        self.letta_agent_id = None
        try:
            import httpx
            self.letta_client = httpx.Client(base_url="http://localhost:8283", timeout=10.0, follow_redirects=True)
            # Check if Letta is running
            resp = self.letta_client.get("/v1/health/")
            if resp.status_code == 200:
                self.letta = self.letta_client
                self._ensure_letta_agent()
                if not quiet:
                    print("  ✅ Letta connected")
        except Exception as e:
            if not quiet:
                print(f"  ⚠️ Letta not available: {e}")
        
        if not quiet:
            print("  ✅ Ready!")
    
    def _ensure_letta_agent(self):
        """Create or get the Atlas agent in Letta"""
        try:
            resp = self.letta.get("/v1/agents")
            if resp.status_code == 200:
                for agent in resp.json():
                    if agent.get("name") == "atlas":
                        self.letta_agent_id = agent["id"]
                        return
            
            # Create new agent
            payload = {
                "name": "atlas",
                "system": "You are Atlas, an AI assistant with persistent memory.",
                "memory_blocks": [
                    {"label": "human", "value": "My human is Jack Nelson."},
                    {"label": "persona", "value": "I am Atlas, running on Clawdbot/OpenClaw."}
                ]
            }
            resp = self.letta.post("/v1/agents", json=payload)
            if resp.status_code in [200, 201]:
                self.letta_agent_id = resp.json()["id"]
        except Exception:
            pass
    
    def index_file(self, path: Path, force: bool = False) -> int:
        """Index a single file into ChromaDB + Letta"""
        if not path.exists():
            return 0
        
        state = load_index_state()
        file_hash = get_file_hash(path)
        file_key = str(path)
        
        # Skip if unchanged
        if not force and state["files"].get(file_key) == file_hash:
            return 0
        
        content = path.read_text()
        chunks = chunk_markdown(content)
        
        # Delete old chunks for this file
        try:
            existing = self.chroma.get(where={"source_file": str(path)})
            if existing["ids"]:
                self.chroma.delete(ids=existing["ids"])
        except Exception:
            pass
        
        # Add new chunks to ChromaDB
        for i, chunk in enumerate(chunks):
            doc_id = f"{path.stem}_{i}_{datetime.now().timestamp()}"
            self.chroma.add(
                documents=[chunk["text"]],
                ids=[doc_id],
                metadatas=[{
                    "source_file": str(path),
                    "headers": chunk["headers"],
                    "chunk_index": i,
                    "indexed_at": datetime.now().isoformat()
                }]
            )
        
        # Also add to Letta archival if available
        if self.letta and self.letta_agent_id:
            try:
                # Store summary in archival
                summary = f"File: {path.name}\n\n" + content[:2000]
                self.letta.post(
                    f"/v1/agents/{self.letta_agent_id}/archival",
                    json={"text": summary}
                )
            except Exception:
                pass
        
        # Update state
        state["files"][file_key] = file_hash
        save_index_state(state)
        
        return len(chunks)
    
    def index_all(self, force: bool = False) -> Dict:
        """Index all memory files"""
        results = {"files": 0, "chunks": 0, "errors": []}
        
        # Index MEMORY.md
        if MEMORY_FILE.exists():
            try:
                chunks = self.index_file(MEMORY_FILE, force)
                results["files"] += 1
                results["chunks"] += chunks
                print(f"  📄 MEMORY.md: {chunks} chunks")
            except Exception as e:
                results["errors"].append(f"MEMORY.md: {e}")
        
        # Index memory/*.md
        if MEMORY_DIR.exists():
            for md_file in sorted(MEMORY_DIR.glob("*.md")):
                try:
                    chunks = self.index_file(md_file, force)
                    if chunks > 0:
                        results["files"] += 1
                        results["chunks"] += chunks
                        print(f"  📄 {md_file.name}: {chunks} chunks")
                except Exception as e:
                    results["errors"].append(f"{md_file.name}: {e}")
        
        # Update last full index time
        state = load_index_state()
        state["last_full_index"] = datetime.now().isoformat()
        save_index_state(state)
        
        return results
    
    def add_fact(self, text: str) -> Dict:
        """Add a fact to Mem0 (auto-extraction)"""
        result = self.mem0.add(text, user_id=self.user_id)
        return {"source": "mem0", "result": result}
    
    def recall(self, query: str, limit: int = 5) -> Dict:
        """
        Search all memory systems and return unified results.
        """
        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "mem0": [],
            "chroma": [],
            "letta": []
        }
        
        # Mem0 search
        try:
            mem0_raw = self.mem0.search(query, user_id=self.user_id, limit=limit)
            # Mem0 returns {'results': [...]}
            mem0_list = mem0_raw.get("results", []) if isinstance(mem0_raw, dict) else mem0_raw
            results["mem0"] = [
                {
                    "text": r.get("memory", r.get("text", str(r))),
                    "score": r.get("score", 0),
                    "source": "mem0"
                }
                for r in mem0_list
            ]
        except Exception as e:
            results["mem0_error"] = str(e)
        
        # ChromaDB search
        try:
            chroma_results = self.chroma.query(
                query_texts=[query],
                n_results=limit
            )
            
            for i, doc in enumerate(chroma_results["documents"][0]):
                meta = chroma_results["metadatas"][0][i]
                dist = chroma_results["distances"][0][i] if chroma_results.get("distances") else 0
                results["chroma"].append({
                    "text": doc,
                    "file": meta.get("source_file", "unknown"),
                    "headers": meta.get("headers", ""),
                    "distance": dist,
                    "source": "chroma"
                })
        except Exception as e:
            results["chroma_error"] = str(e)
        
        # Letta archival search
        if self.letta and self.letta_agent_id:
            try:
                resp = self.letta.get(
                    f"/v1/agents/{self.letta_agent_id}/archival",
                    params={"query": query, "limit": limit}
                )
                if resp.status_code == 200:
                    for item in resp.json():
                        results["letta"].append({
                            "text": item.get("text", ""),
                            "source": "letta"
                        })
            except Exception as e:
                results["letta_error"] = str(e)
        
        return results
    
    def recall_unified(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search and return a single ranked list of results.
        """
        raw = self.recall(query, limit=limit * 2)
        
        all_results = []
        
        # Normalize and combine
        for item in raw.get("mem0", []):
            all_results.append({
                "text": item["text"],
                "source": "mem0",
                "score": item.get("score", 0.5)
            })
        
        for item in raw.get("chroma", []):
            # Convert distance to score (lower distance = higher score)
            score = 1 - min(item.get("distance", 0.5), 1)
            all_results.append({
                "text": item["text"][:500],
                "source": f"chroma:{Path(item.get('file', '')).name}",
                "headers": item.get("headers", ""),
                "score": score
            })
        
        for item in raw.get("letta", []):
            all_results.append({
                "text": item["text"][:500],
                "source": "letta",
                "score": 0.7  # Letta results are pre-filtered
            })
        
        # Sort by score and dedupe
        seen = set()
        unique = []
        for item in sorted(all_results, key=lambda x: x.get("score", 0), reverse=True):
            text_hash = hashlib.md5(item["text"][:100].encode()).hexdigest()
            if text_hash not in seen:
                seen.add(text_hash)
                unique.append(item)
        
        return unique[:limit]
    
    def stats(self) -> Dict:
        """Get memory system statistics"""
        mem0_all = self.mem0.get_all(user_id=self.user_id)
        mem0_count = len(mem0_all.get("results", [])) if isinstance(mem0_all, dict) else len(mem0_all)
        stats = {
            "chroma_docs": self.chroma.count(),
            "mem0_memories": mem0_count,
            "letta_available": self.letta is not None,
            "index_state": load_index_state()
        }
        
        if self.letta and self.letta_agent_id:
            try:
                resp = self.letta.get(f"/v1/agents/{self.letta_agent_id}/memory")
                if resp.status_code == 200:
                    stats["letta_core_memory"] = resp.json()
            except Exception:
                pass
        
        return stats


def main():
    parser = argparse.ArgumentParser(description="Atlas Unified Memory Recall")
    parser.add_argument("query", nargs="*", help="Search query")
    parser.add_argument("--index", action="store_true", help="Index all memory files")
    parser.add_argument("--force", action="store_true", help="Force re-index even if unchanged")
    parser.add_argument("--stats", action="store_true", help="Show memory stats")
    parser.add_argument("--add", type=str, help="Add a fact to memory")
    parser.add_argument("--limit", type=int, default=5, help="Number of results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    
    args = parser.parse_args()
    
    recall = AtlasRecall(quiet=args.quiet or args.json)
    
    if args.index:
        print("\n📚 Indexing all memory files...")
        results = recall.index_all(force=args.force)
        print(f"\n✅ Indexed {results['files']} files, {results['chunks']} chunks")
        if results["errors"]:
            print(f"⚠️ Errors: {results['errors']}")
        return
    
    if args.stats:
        stats = recall.stats()
        if args.json:
            print(json.dumps(stats, indent=2, default=str))
        else:
            print("\n📊 Atlas Memory Stats")
            print(f"  ChromaDB documents: {stats['chroma_docs']}")
            print(f"  Mem0 memories: {stats['mem0_memories']}")
            print(f"  Letta available: {stats['letta_available']}")
            if stats.get("index_state", {}).get("last_full_index"):
                print(f"  Last full index: {stats['index_state']['last_full_index']}")
        return
    
    if args.add:
        result = recall.add_fact(args.add)
        print(f"✅ Added to Mem0: {result}")
        return
    
    if not args.query:
        parser.print_help()
        return
    
    query = " ".join(args.query)
    
    if args.json:
        results = recall.recall(query, limit=args.limit)
        print(json.dumps(results, indent=2, default=str))
    else:
        results = recall.recall_unified(query, limit=args.limit)
        
        print(f"\n🔍 Query: {query}")
        print(f"📝 Found {len(results)} results:\n")
        
        for i, item in enumerate(results, 1):
            source = item.get("source", "unknown")
            headers = item.get("headers", "")
            score = item.get("score", 0)
            text = item.get("text", "")[:300]
            
            print(f"[{i}] {source} (score: {score:.2f})")
            if headers:
                print(f"    Section: {headers}")
            print(f"    {text}...")
            print()


if __name__ == "__main__":
    main()
