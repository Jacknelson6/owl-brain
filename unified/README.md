# Atlas Unified Recall System

The production-ready memory recall system that combines all three backends (Mem0 + ChromaDB + Letta) into a single CLI.

## What It Does

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR QUERY                                │
│                        ↓                                     │
│   ┌─────────┐    ┌──────────┐    ┌──────────┐              │
│   │  Mem0   │    │ ChromaDB │    │  Letta   │              │
│   │ (facts) │    │ (chunks) │    │(archival)│              │
│   └────┬────┘    └────┬─────┘    └────┬─────┘              │
│        │              │               │                      │
│        └──────────────┼───────────────┘                      │
│                       ↓                                      │
│              UNIFIED RESULTS                                 │
│         (ranked, deduplicated)                              │
└─────────────────────────────────────────────────────────────┘
```

- **Mem0**: Auto-extracted facts from conversations ("Jack prefers informal communication")
- **ChromaDB**: Chunked documents with semantic search (memory files, docs, notes)
- **Letta**: Hierarchical archival memory (optional, needs Docker)

## Quick Start

```bash
# Install dependencies
pip install mem0ai chromadb httpx

# Set OpenAI API key
export OPENAI_API_KEY="your-key"

# Run a search
python atlas_recall.py "What does the user prefer?"

# Index your memory files
python atlas_recall.py --index

# Add a fact manually
python atlas_recall.py --add "User prefers dark mode"

# Check stats
python atlas_recall.py --stats
```

## CLI Reference

```bash
# Search (default)
python atlas_recall.py "query here"
python atlas_recall.py "query" --limit 10
python atlas_recall.py "query" --json  # Raw output

# Index memory files
python atlas_recall.py --index          # Incremental (skips unchanged)
python atlas_recall.py --index --force  # Full re-index

# Manage facts
python atlas_recall.py --add "fact text"  # Add to Mem0

# Statistics
python atlas_recall.py --stats
```

## Configuration

The system stores data in `~/.atlas/`:

```
~/.atlas/
├── chroma/           # ChromaDB documents (chunked files)
├── mem0_chroma/      # Mem0 facts (auto-extracted)
└── index_state.json  # Tracks what's been indexed
```

### Memory File Paths

By default, it indexes:
- `~/clawd/MEMORY.md` — Main memory file
- `~/clawd/memory/*.md` — Daily logs and notes

Edit the `CLAWD_DIR`, `MEMORY_DIR`, and `MEMORY_FILE` constants at the top of `atlas_recall.py` to customize paths.

### Letta (Optional)

If Letta is running on `localhost:8283`, results will include archival memory. Start Letta with:

```bash
docker compose -f letta-docker/docker-compose.yml up -d
```

## How Indexing Works

1. **Reads** each markdown file
2. **Chunks** by headers + size (1000 chars, 100 overlap)
3. **Stores** chunks in ChromaDB with metadata (file path, headers)
4. **Tracks** file hashes to skip unchanged files on re-index

### Chunk Example

A file like:
```markdown
# User Preferences
## Communication
- Prefers casual tone
- No em-dashes
```

Becomes a chunk with:
- `text`: The content
- `headers`: "User Preferences > Communication"
- `file`: Original file path

## How Search Works

1. **Mem0**: Searches auto-extracted facts (returns `memory` field)
2. **ChromaDB**: Semantic search over document chunks (returns `text` + `headers`)
3. **Letta**: Searches archival memory (if available)
4. **Unified**: Combines, scores, and deduplicates results

### Scoring

- Lower distance = better match
- Results sorted by relevance
- Duplicates (same text hash) removed

## Integration with Clawdbot/OpenClaw

Add to your agent's workflow:

```python
# In your agent code
import subprocess
import json

def recall(query: str, limit: int = 5) -> list:
    """Search agent memory"""
    result = subprocess.run(
        ["python3", "atlas_recall.py", query, "--limit", str(limit), "--json"],
        capture_output=True, text=True, cwd="/path/to/unified"
    )
    data = json.loads(result.stdout)
    return data.get("chroma", []) + data.get("mem0", [])
```

Or use the shell wrapper:
```bash
./recall "What meetings are scheduled?"
```

## Cron Job Setup

Index daily to keep memory fresh:

```bash
# crontab -e
0 0 * * * cd /path/to/unified && /path/to/python atlas_recall.py --index >> /var/log/atlas-index.log 2>&1
```

Or with Clawdbot cron:
```json
{
  "name": "Atlas Memory Daily Index",
  "schedule": "0 0 * * *",
  "payload": {
    "kind": "agentTurn",
    "message": "Run: python3 atlas_recall.py --index"
  }
}
```

## Why Three Backends?

| Backend | Strength | Use Case |
|---------|----------|----------|
| **Mem0** | Auto-extracts facts from prose | "User mentioned they hate meetings" → extracts "User hates meetings" |
| **ChromaDB** | Fast local vector search | Documents, notes, knowledge base |
| **Letta** | Hierarchical + self-editing | Agent-curated memory, core facts |

Together they cover:
- **Passive learning** (Mem0 extracts facts you didn't explicitly save)
- **Document search** (ChromaDB finds relevant chunks)
- **Agent memory** (Letta maintains structured knowledge)

## Troubleshooting

### "OPENAI_API_KEY not found"
```bash
export OPENAI_API_KEY="sk-..."
# Or create ~/.config/openai/api_key
```

### "Letta not available"
Letta is optional. If you want it:
```bash
docker compose -f letta-docker/docker-compose.yml up -d
```

### "ChromaDB conflict"
If you see "instance already exists" errors, ensure only one process accesses `~/.atlas/chroma/` at a time.

### Mem0 returning empty
Mem0 needs facts added first. Use `--add` to seed it:
```bash
python atlas_recall.py --add "Key facts about the project..."
```
