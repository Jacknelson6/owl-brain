# ChromaDB — Local Vector Database

ChromaDB is the "fast local search" layer. It runs entirely in-process with zero infrastructure — no servers, no cloud, no API keys (for the database itself). Just import and use.

## What Makes ChromaDB Special

Most vector databases require running a server or connecting to a cloud service. ChromaDB runs embedded in your Python process:

```python
import chromadb

# That's it. No server, no connection string, no API key.
client = chromadb.Client()
```

For persistent storage (survives restarts):
```python
client = chromadb.PersistentClient(path="./my_data")
```

## How It Works Under the Hood

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR DOCUMENTS                        │
│  "Jack prefers dark mode", "Meeting on Friday", etc.    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              EMBEDDING MODEL                             │
│  Converts text → 1536-dimensional vectors               │
│  (Uses Sentence Transformers by default, or OpenAI)     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              HNSW INDEX                                  │
│  Hierarchical Navigable Small World graph               │
│  Enables fast approximate nearest neighbor search       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              LOCAL STORAGE                               │
│  SQLite + Parquet files on disk                         │
│  No external database needed                            │
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install chromadb
```

That's all. No additional setup required.

## Basic Usage

### Creating a Client

```python
import chromadb

# In-memory (lost on restart) - good for testing
client = chromadb.Client()

# Persistent (saved to disk) - use this for production
client = chromadb.PersistentClient(path="/path/to/storage")
```

### Creating Collections

Collections are like tables — they group related documents:

```python
# Create or get existing collection
collection = client.get_or_create_collection(
    name="agent_memories",
    metadata={"description": "My agent's memory"}
)

# With custom distance metric
collection = client.get_or_create_collection(
    name="agent_memories",
    metadata={"hnsw:space": "cosine"}  # cosine, l2, or ip
)
```

### Adding Documents

```python
# Basic add
collection.add(
    documents=["Jack prefers dark mode", "Meeting scheduled for Friday"],
    ids=["doc1", "doc2"]
)

# With metadata (for filtering later)
collection.add(
    documents=[
        "Jack prefers dark mode",
        "Project deadline is Friday",
        "Use Python for backend"
    ],
    metadatas=[
        {"type": "preference", "user": "jack"},
        {"type": "task", "priority": "high"},
        {"type": "preference", "category": "tech"}
    ],
    ids=["pref_1", "task_1", "pref_2"]
)
```

### Searching (Querying)

```python
# Basic semantic search
results = collection.query(
    query_texts=["What does the user like?"],
    n_results=5
)

# Returns:
# {
#     'ids': [['pref_1', 'pref_2']],
#     'documents': [['Jack prefers dark mode', 'Use Python for backend']],
#     'metadatas': [[{'type': 'preference', ...}, {...}]],
#     'distances': [[0.234, 0.456]]
# }
```

### Filtering with Metadata

```python
# Filter by exact match
results = collection.query(
    query_texts=["preferences"],
    where={"type": "preference"},
    n_results=10
)

# Filter with operators
results = collection.query(
    query_texts=["tasks"],
    where={
        "$and": [
            {"type": {"$eq": "task"}},
            {"priority": {"$eq": "high"}}
        ]
    }
)

# Available operators: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
```

### Updating Documents

```python
# Update by ID
collection.update(
    ids=["doc1"],
    documents=["Jack NOW prefers light mode"],
    metadatas=[{"type": "preference", "updated": True}]
)

# Upsert (update or insert)
collection.upsert(
    ids=["doc1", "doc3"],
    documents=["Updated doc", "New doc"],
)
```

### Deleting Documents

```python
# Delete by ID
collection.delete(ids=["doc1", "doc2"])

# Delete by filter
collection.delete(where={"type": "temporary"})
```

### Getting Documents

```python
# Get specific documents
docs = collection.get(ids=["doc1", "doc2"])

# Get with filter
docs = collection.get(where={"type": "preference"})

# Get all (careful with large collections)
all_docs = collection.get()
```

## Chunking Strategy for Memory Files

When indexing markdown files, chunk them intelligently:

```python
def chunk_markdown(content: str, chunk_size: int = 1000) -> list:
    """Split markdown by headers and size"""
    chunks = []
    current_chunk = []
    current_headers = []
    current_size = 0
    
    for line in content.split('\n'):
        # Track headers for context
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            header = line.lstrip('#').strip()
            current_headers = current_headers[:level-1] + [header]
            
            # Flush chunk if substantial
            if current_size > 200:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'headers': ' > '.join(current_headers[:-1])
                })
                current_chunk = []
                current_size = 0
        
        current_chunk.append(line)
        current_size += len(line)
        
        # Flush if too large
        if current_size >= chunk_size:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'headers': ' > '.join(current_headers)
            })
            current_chunk = current_chunk[-3:]  # Keep overlap
            current_size = sum(len(l) for l in current_chunk)
    
    # Final chunk
    if current_chunk:
        chunks.append({
            'text': '\n'.join(current_chunk),
            'headers': ' > '.join(current_headers)
        })
    
    return chunks
```

Usage:
```python
content = open("MEMORY.md").read()
chunks = chunk_markdown(content)

for i, chunk in enumerate(chunks):
    collection.add(
        documents=[chunk['text']],
        metadatas=[{
            'source': 'MEMORY.md',
            'headers': chunk['headers'],
            'chunk_index': i
        }],
        ids=[f"memory_chunk_{i}"]
    )
```

## Embedding Models

### Default (Sentence Transformers)

ChromaDB uses `all-MiniLM-L6-v2` by default — free, fast, runs locally:

```python
# This just works, no API key needed
collection = client.get_or_create_collection("my_collection")
```

### OpenAI Embeddings

For better quality (costs money):

```python
from chromadb.utils import embedding_functions

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="sk-your-key",
    model_name="text-embedding-3-small"
)

collection = client.get_or_create_collection(
    name="my_collection",
    embedding_function=openai_ef
)
```

### Comparison

| Model | Quality | Speed | Cost |
|-------|---------|-------|------|
| all-MiniLM-L6-v2 (default) | Good | Fast | Free |
| text-embedding-3-small | Better | Medium | ~$0.02/1M tokens |
| text-embedding-3-large | Best | Slower | ~$0.13/1M tokens |

## Storage Location

```
/path/to/storage/
├── chroma.sqlite3      # Metadata and IDs
└── [uuid]/             # Collection data
    ├── data_level0.bin # HNSW index
    ├── header.bin
    ├── index_metadata.json
    └── length.bin
```

Typical size: ~1KB per document (varies with embedding dimension).

## Performance Tips

### Batch Operations

```python
# ❌ Slow - many small operations
for doc in documents:
    collection.add(documents=[doc], ids=[generate_id()])

# ✅ Fast - one batch operation
collection.add(
    documents=documents,
    ids=[generate_id() for _ in documents]
)
```

### Index Settings

For large collections (100K+ documents):

```python
collection = client.get_or_create_collection(
    name="large_collection",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:M": 32,              # More connections = better recall, more memory
        "hnsw:ef_construction": 200 # Higher = better index, slower build
    }
)
```

### Query Settings

```python
# Adjust search accuracy vs speed
results = collection.query(
    query_texts=["search term"],
    n_results=10,
    include=["documents", "metadatas", "distances"]  # Only request what you need
)
```

## Common Patterns

### Deduplication

```python
import hashlib

def get_doc_id(text: str) -> str:
    """Generate consistent ID from content"""
    return hashlib.md5(text.encode()).hexdigest()

# Now duplicates automatically update instead of duplicating
collection.upsert(
    documents=[text],
    ids=[get_doc_id(text)]
)
```

### Incremental Updates

```python
def index_file_if_changed(filepath: str, collection):
    """Only re-index if file changed"""
    content = open(filepath).read()
    file_hash = hashlib.md5(content.encode()).hexdigest()
    
    # Check if already indexed with same hash
    existing = collection.get(where={"source": filepath, "hash": file_hash})
    if existing['ids']:
        return  # Already indexed
    
    # Delete old chunks for this file
    collection.delete(where={"source": filepath})
    
    # Add new chunks
    chunks = chunk_markdown(content)
    collection.add(
        documents=[c['text'] for c in chunks],
        metadatas=[{"source": filepath, "hash": file_hash, **c} for c in chunks],
        ids=[f"{filepath}_{i}" for i in range(len(chunks))]
    )
```

## Troubleshooting

### "Collection already exists with different settings"

```python
# Delete and recreate
client.delete_collection("my_collection")
collection = client.create_collection("my_collection", ...)
```

### "An instance already exists for this path"

Only one `PersistentClient` can access a path at a time:

```python
# ❌ This will fail
client1 = chromadb.PersistentClient(path="./data")
client2 = chromadb.PersistentClient(path="./data")  # Error!

# ✅ Reuse the same client
client = chromadb.PersistentClient(path="./data")
collection1 = client.get_or_create_collection("col1")
collection2 = client.get_or_create_collection("col2")
```

### Slow queries on large collections

1. Use metadata filters to reduce search space
2. Reduce `n_results` if you don't need many
3. Consider using `hnsw:ef` parameter for speed/accuracy tradeoff

## When to Use ChromaDB

✅ **Good for:**
- Document/knowledge base search
- Fast local semantic search
- Chunked file indexing
- No-infrastructure deployments

❌ **Not ideal for:**
- Auto-extracting facts (use Mem0)
- Time-aware queries (use Zep)
- Agent self-editing memory (use Letta)
- Multi-process access (use a proper database)
