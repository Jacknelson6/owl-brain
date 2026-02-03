# Setup Guide

Getting your memory stack running. Grab some coffee (or energy drink, no judgment).

## Prerequisites

- **Python 3.12+** (we like living on the edge)
- **pip** (obviously)
- **OpenAI API key** (for Mem0's embeddings)

## Step 1: Create Your Environment

```bash
# Navigate to where you want the memory stack
cd ~/your-agent-workspace

# Create a dedicated venv (keeps things clean)
python3.12 -m venv .venv-memory

# Activate it
source .venv-memory/bin/activate

# Verify Python version
python --version  # Should show 3.12.x
```

## Step 2: Install the Stack

```bash
# All four packages
pip install mem0ai chromadb zep-python letta

# Or install from requirements.txt
pip install -r requirements.txt
```

### Package Breakdown

| Package | Size | Dependencies |
|---------|------|--------------|
| mem0ai | ~2MB | openai, chromadb |
| chromadb | ~50MB | numpy, onnxruntime |
| zep-python | ~1MB | httpx, pydantic |
| letta | ~10MB | openai, chromadb, uvicorn |

## Step 3: Configure API Keys

### OpenAI (Required for Mem0)

Mem0 uses OpenAI for embeddings. Set your key:

```bash
# Option A: Environment variable
export OPENAI_API_KEY="sk-..."

# Option B: Create a config file (recommended for persistence)
mkdir -p ~/.config/openai
echo "sk-your-key-here" > ~/.config/openai/api_key
chmod 600 ~/.config/openai/api_key
```

The test script checks both locations.

### Zep (Optional)

Zep has two modes:

**Zep Cloud (Easy)**
1. Sign up at [getzep.com](https://www.getzep.com/)
2. Get your project API key
3. Set it:
```bash
export ZEP_API_KEY="z_..."
```

**Self-Hosted (Full Control)**
```bash
# Docker compose (recommended)
git clone https://github.com/getzep/zep.git
cd zep
docker compose up -d

# Server runs at http://localhost:8000
export ZEP_API_URL="http://localhost:8000"
```

### Letta (Optional but Cool)

Letta runs as a local server with a web UI:

```bash
# Start the server
letta server

# Web UI available at http://localhost:8283
# API at http://localhost:8283/api
```

First run will prompt for OpenAI key configuration.

### ChromaDB (No Config Needed)

ChromaDB runs locally with zero config. It just works:

```python
import chromadb
client = chromadb.Client()  # In-memory
# or
client = chromadb.PersistentClient(path="./chroma_db")  # Persistent
```

## Step 4: Verify Installation

Run the test script:

```bash
python test/memory-stack-test.py
```

Expected output:

```
==================================================
🚀 Advanced Memory Stack Test
==================================================

🔷 Testing ChromaDB...
  ✅ ChromaDB working! Query returned 2 results

🧠 Testing Mem0...
  ✅ Mem0 initialized (OpenAI embeddings ready)

⏱️ Testing Zep...
  ✅ Zep client imported
  ℹ️ Zep requires either:
     - Zep Cloud account (https://www.getzep.com/)
     - Self-hosted Zep server

📚 Testing Letta...
  ✅ Letta client imported
  ℹ️ To start Letta server: letta server
     Web UI at http://localhost:8283

==================================================
📊 Results Summary
==================================================
  ✅ ChromaDB
  ✅ Mem0
  ✅ Zep
  ✅ Letta
```

## Troubleshooting

### "OPENAI_API_KEY not found"
- Check env variable: `echo $OPENAI_API_KEY`
- Check config file: `cat ~/.config/openai/api_key`
- Make sure key starts with `sk-`

### ChromaDB import errors
```bash
# Sometimes needs explicit sqlite
pip install pysqlite3-binary
```

### Letta won't start
```bash
# Check port isn't in use
lsof -i :8283

# Try different port
letta server --port 8284
```

### Zep connection refused
- Cloud: Check API key format (`z_...`)
- Self-hosted: Ensure Docker containers are running

## Directory Structure

After setup, your memory stack lives cleanly:

```
your-agent-workspace/
├── .venv-memory/          # Virtual environment
├── chroma_db/             # ChromaDB persistent storage (if used)
├── letta_data/            # Letta state (if used)
└── memory/                # Your agent's memory files
```

## Next Steps

- Check [examples/](examples/) for integration patterns
- Add the [TOOLS.md snippet](docs/TOOLS-snippet.md) to your agent
- Start building memory into your workflows

---

*Setup complete? You're ready to give your agent a brain.* 🦉
