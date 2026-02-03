# TOOLS.md Snippet for OpenClaw Agents

Add this to your agent's `TOOLS.md` file to document the memory stack.

---

```markdown
## Advanced Memory Stack (.venv-memory)

Virtual environment: `~/your-workspace/.venv-memory` (Python 3.12)
Activate: `source ~/your-workspace/.venv-memory/bin/activate`

**Installed Packages:**
- ✅ **Mem0** (`from mem0 import Memory`) — Agentic memory with auto-extraction
- ✅ **ChromaDB** (`import chromadb`) — Local vector database
- ✅ **Zep** (`import zep_python`) — Temporal-aware memory
- ✅ **Letta** (`from letta import client`) — Self-editing hierarchical memory

**Quick Reference:**

```python
# Mem0 - Auto-extract memories from conversations
from mem0 import Memory
m = Memory()
m.add(messages, user_id="jack")
m.search("query", user_id="jack")

# ChromaDB - Fast local vector store
import chromadb
client = chromadb.PersistentClient(path="./memory_db")
collection = client.get_or_create_collection("memories")
collection.add(documents=["..."], ids=["id1"])
collection.query(query_texts=["search term"], n_results=5)

# Letta - Start server first: letta server
from letta import create_client
client = create_client()
# Then use web UI at http://localhost:8283
```

**Usage Notes:**
- Mem0 needs OpenAI key (uses their embeddings)
- ChromaDB is local, no API key needed
- Zep needs Zep Cloud account or self-hosted server
- Letta runs as a local server with web UI

**When to use what:**
- **Quick semantic search**: ChromaDB
- **Auto-extract from conversations**: Mem0
- **Time-aware queries ("before X happened")**: Zep
- **Agent-managed hierarchical memory**: Letta
```

---

## Integration Checklist

When wiring owl-brain into your agent:

1. **Create the venv**
   ```bash
   python3.12 -m venv .venv-memory
   source .venv-memory/bin/activate
   pip install mem0ai chromadb zep-python letta
   ```

2. **Set up OpenAI key** (for Mem0)
   ```bash
   mkdir -p ~/.config/openai
   echo "sk-your-key" > ~/.config/openai/api_key
   ```

3. **Add the TOOLS.md snippet** above

4. **Use the unified interface** from `examples/openclaw-integration.py`

5. **Decide your architecture:**
   - Minimal: ChromaDB only (zero config)
   - Standard: ChromaDB + Mem0 (good balance)
   - Full: All four systems (maximum capability)

---

*Part of [owl-brain](https://github.com/jacknelson/owl-brain) — memory that doesn't sleep.* 🦉
