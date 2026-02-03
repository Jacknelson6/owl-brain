# Mem0 — Auto-Extracting Agentic Memory

Mem0 is the "passive learning" layer. You feed it conversations or text, and it automatically extracts the important facts without you having to tag or categorize anything.

## What Makes Mem0 Special

Traditional memory systems require you to explicitly save things:
```python
# Traditional approach - you decide what to save
memory.save("user_preference", "dark mode")
memory.save("user_name", "Jack")
```

Mem0 flips this:
```python
# Mem0 approach - it figures out what matters
mem0.add("Hey, I'm Jack. I really prefer dark mode for everything.")
# Mem0 automatically extracts:
# - "User's name is Jack"
# - "User prefers dark mode"
```

## How It Works Under the Hood

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR TEXT INPUT                       │
│  "I'm Jack, working on Toastique. I prefer Supabase."   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              MEM0 EXTRACTION ENGINE                      │
│  Uses LLM to identify facts, preferences, entities      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              EXTRACTED MEMORIES                          │
│  • "User's name is Jack"                                │
│  • "Working on project called Toastique"                │
│  • "Prefers Supabase"                                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              VECTOR STORE (ChromaDB/Qdrant)             │
│  Embeddings for semantic search                         │
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install mem0ai
```

## Configuration

Mem0 requires an OpenAI API key for:
1. **Extraction** — Uses GPT to identify facts in text
2. **Embeddings** — Uses text-embedding models for semantic search

### Set Your API Key

```bash
# Option 1: Environment variable
export OPENAI_API_KEY="sk-your-key-here"

# Option 2: Create a config file
mkdir -p ~/.config/openai
echo "sk-your-key-here" > ~/.config/openai/api_key
chmod 600 ~/.config/openai/api_key
```

### Vector Store Backend

By default, Mem0 uses Qdrant (embedded). You can also use ChromaDB:

```python
from mem0 import Memory

# Default (Qdrant embedded)
m = Memory()

# With ChromaDB backend
config = {
    'vector_store': {
        'provider': 'chroma',
        'config': {
            'collection_name': 'my_memories',
            'path': '/path/to/storage'
        }
    }
}
m = Memory.from_config(config)
```

## Basic Usage

### Adding Memories

```python
from mem0 import Memory

m = Memory()

# Add from plain text
m.add("Jack is building an AI agent. He prefers Python over JavaScript.", user_id="atlas")

# Add from conversation format
conversation = [
    {"role": "user", "content": "My name is Jack"},
    {"role": "assistant", "content": "Nice to meet you, Jack!"},
    {"role": "user", "content": "I work at Nativz as Chief Editing Officer"}
]
m.add(conversation, user_id="atlas")
```

**What gets extracted:**
```python
# From the above, Mem0 extracts:
# - "Name is Jack"
# - "Building an AI agent"  
# - "Prefers Python over JavaScript"
# - "Works at Nativz"
# - "Job title is Chief Editing Officer"
```

### Searching Memories

```python
# Semantic search
results = m.search("What programming language does the user prefer?", user_id="atlas")

# Returns:
# [{'memory': 'Prefers Python over JavaScript', 'score': 0.89, ...}]
```

### Getting All Memories

```python
all_memories = m.get_all(user_id="atlas")
# Returns: {'results': [{'id': '...', 'memory': '...', ...}, ...]}
```

### Deleting Memories

```python
# Delete specific memory
m.delete(memory_id="abc123")

# Delete all for a user
m.delete_all(user_id="atlas")
```

## Memory Tiers

Mem0 supports three scopes:

| Scope | Parameter | Use Case |
|-------|-----------|----------|
| **User** | `user_id="jack"` | Persistent facts about a specific user |
| **Session** | `session_id="chat_123"` | Context within a single conversation |
| **Agent** | `agent_id="atlas"` | Knowledge shared across all users |

```python
# User-level (most common)
m.add("Jack prefers dark mode", user_id="jack")

# Session-level (conversation context)
m.add("User asked about pricing", session_id="chat_abc123")

# Agent-level (shared knowledge)
m.add("Our company policy is...", agent_id="atlas")
```

## Advanced Configuration

### Custom Extraction Prompt

You can customize how Mem0 extracts facts:

```python
config = {
    'llm': {
        'provider': 'openai',
        'config': {
            'model': 'gpt-4o-mini',  # Cheaper model for extraction
            'temperature': 0
        }
    },
    'embedder': {
        'provider': 'openai',
        'config': {
            'model': 'text-embedding-3-small'  # Cheaper embeddings
        }
    }
}
m = Memory.from_config(config)
```

### Using Different LLM Providers

```python
# Anthropic
config = {
    'llm': {
        'provider': 'anthropic',
        'config': {
            'model': 'claude-3-haiku-20240307',
            'api_key': 'your-anthropic-key'
        }
    }
}

# Local LLM via Ollama
config = {
    'llm': {
        'provider': 'ollama',
        'config': {
            'model': 'llama2',
            'base_url': 'http://localhost:11434'
        }
    }
}
```

## Integration with OpenClaw/Clawdbot

### After Each Conversation

```python
def on_conversation_end(messages):
    """Process conversation through Mem0 after it ends"""
    conversation_text = "\n".join([
        f"{m['role']}: {m['content']}" 
        for m in messages
    ])
    m.add(conversation_text, user_id="atlas")
```

### Before Generating Response

```python
def get_context_for_query(query):
    """Search memories before responding"""
    memories = m.search(query, user_id="atlas", limit=5)
    context = "\n".join([mem['memory'] for mem in memories.get('results', [])])
    return f"Relevant memories:\n{context}"
```

## Storage Locations

| Backend | Default Location |
|---------|-----------------|
| Qdrant (default) | `~/.mem0/migrations_qdrant/` |
| ChromaDB | Custom path in config |
| History DB | `~/.mem0/history.db` |

## Troubleshooting

### "OPENAI_API_KEY not found"
```bash
export OPENAI_API_KEY="sk-..."
```

### Memories not persisting
Make sure you're using the same `user_id` across sessions:
```python
# Always use consistent user_id
m.add(..., user_id="atlas")  # ✓
m.search(..., user_id="atlas")  # ✓
```

### Slow extraction
Use a faster/cheaper model:
```python
config = {
    'llm': {
        'provider': 'openai',
        'config': {'model': 'gpt-4o-mini'}  # Fast and cheap
    }
}
```

## Cost Considerations

Mem0 uses OpenAI for both extraction and embeddings:

| Operation | API Calls | Approximate Cost |
|-----------|-----------|------------------|
| `add()` | 1 LLM + 1 embedding | ~$0.001-0.01 |
| `search()` | 1 embedding | ~$0.0001 |
| `get_all()` | None | Free |

**Tips to reduce costs:**
- Use `gpt-4o-mini` for extraction
- Use `text-embedding-3-small` for embeddings
- Batch additions when possible

## When to Use Mem0

✅ **Good for:**
- Learning user preferences over time
- Extracting facts from conversations automatically
- Building relationship context ("remembers you mentioned X")

❌ **Not ideal for:**
- Large document storage (use ChromaDB)
- Time-sensitive queries (use Zep)
- Agent self-reflection (use Letta)
