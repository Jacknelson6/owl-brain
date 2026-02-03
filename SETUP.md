# Complete Setup Guide

This guide walks you through setting up the entire owl-brain memory stack from scratch.

## Prerequisites

- **Python 3.12+** (3.10+ works, 3.12 recommended)
- **Docker** (for Letta)
- **OpenAI API key** (for Mem0 and Letta)
- **~500MB disk space** for dependencies and data

## Quick Start (5 minutes)

If you just want to get running fast:

```bash
# Clone and setup
git clone https://github.com/Jacknelson6/owl-brain.git
cd owl-brain
python3 -m venv .venv
source .venv/bin/activate
pip install mem0ai chromadb httpx

# Set your API key
export OPENAI_API_KEY="sk-your-key-here"

# Test it
python unified/atlas_recall.py --stats
```

That's the minimum. Read on for the full setup.

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/Jacknelson6/owl-brain.git
cd owl-brain
```

## Step 2: Create Python Virtual Environment

```bash
# Create venv
python3.12 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

Your prompt should now show `(.venv)`.

## Step 3: Install Dependencies

### Minimal (Mem0 + ChromaDB only)

```bash
pip install mem0ai chromadb httpx
```

This gives you:
- ✅ Mem0 (auto-extraction)
- ✅ ChromaDB (vector search)
- ❌ Letta (requires Docker)
- ❌ Zep (requires server)

### Full Stack

```bash
pip install mem0ai chromadb httpx zep-python letta
```

### From requirements.txt

```bash
pip install -r requirements.txt
```

## Step 4: Configure OpenAI API Key

Mem0 and Letta need an OpenAI key for embeddings and LLM calls.

### Option A: Environment Variable

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Add to your shell profile (`~/.bashrc`, `~/.zshrc`) to persist:

```bash
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Option B: Config File

```bash
mkdir -p ~/.config/openai
echo "sk-your-key-here" > ~/.config/openai/api_key
chmod 600 ~/.config/openai/api_key
```

The scripts will automatically read from this location.

### Verify

```bash
python -c "import os; print('Key set!' if os.getenv('OPENAI_API_KEY') or open(os.path.expanduser('~/.config/openai/api_key')).read().strip() else 'No key found')"
```

## Step 5: Set Up Letta (Optional but Recommended)

Letta provides hierarchical memory and runs as a Docker service.

### Install Docker

- **Mac**: `brew install --cask docker` or [Docker Desktop](https://docker.com/products/docker-desktop)
- **Linux**: `sudo apt install docker.io docker-compose`
- **Windows**: [Docker Desktop](https://docker.com/products/docker-desktop)

### Start Letta

```bash
# Navigate to letta config
cd owl-brain  # or wherever you cloned

# Create the docker-compose file if it doesn't exist
mkdir -p letta-docker
cat > letta-docker/docker-compose.yml << 'EOF'
services:
  letta-server:
    image: letta/letta:latest
    container_name: letta-server
    ports:
      - "8283:8283"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - letta-data:/root/.letta
    depends_on:
      - letta-db
    restart: unless-stopped

  letta-db:
    image: postgres:15
    container_name: letta-db
    environment:
      - POSTGRES_USER=letta
      - POSTGRES_PASSWORD=letta
      - POSTGRES_DB=letta
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  letta-data:
  postgres-data:
EOF

# Start it
cd letta-docker
docker compose up -d

# Verify
curl http://localhost:8283/v1/health/
# Should return: {"version":"0.x.x","status":"ok"}
```

### Check Letta Status

```bash
docker ps | grep letta
# Should show letta-server and letta-db running
```

### View Letta Logs

```bash
docker logs letta-server -f
```

### Stop Letta

```bash
cd letta-docker
docker compose down
```

### Letta Web UI

Once running, visit: http://localhost:8283

## Step 6: Configure Storage Paths

The unified recall system stores data in `~/.atlas/`:

```
~/.atlas/
├── chroma/           # ChromaDB document chunks
├── mem0_chroma/      # Mem0 extracted facts  
└── index_state.json  # Tracks indexed files
```

These are created automatically on first run.

### Custom Paths

Edit `unified/atlas_recall.py` to change paths:

```python
# Near the top of the file
CLAWD_DIR = Path.home() / "clawd"           # Your workspace
MEMORY_DIR = CLAWD_DIR / "memory"           # Daily memory files
MEMORY_FILE = CLAWD_DIR / "MEMORY.md"       # Main memory file
CHROMA_DIR = Path.home() / ".atlas" / "chroma"  # ChromaDB storage
```

## Step 7: Create Your Memory Files

The system indexes markdown files. Create the structure:

```bash
mkdir -p ~/clawd/memory

# Create main memory file
cat > ~/clawd/MEMORY.md << 'EOF'
# MEMORY.md - Long-Term Memory

## Key Facts
- Your name and basic info here
- Important preferences
- Key projects

## Preferences
- Communication style notes
- Tool preferences
- Working hours

## Projects
- Active project 1
- Active project 2
EOF

# Create a daily memory file
cat > ~/clawd/memory/$(date +%Y-%m-%d).md << 'EOF'
# $(date +%Y-%m-%d)

## Today
- What happened today
- Decisions made
- Things learned
EOF
```

## Step 8: Index Your Memory Files

```bash
cd owl-brain
source .venv/bin/activate

# Index all memory files
python unified/atlas_recall.py --index

# Output:
# 🧠 Initializing Atlas Memory Stack...
#   ✅ Letta connected
#   ✅ Ready!
# 📚 Indexing all memory files...
#   📄 MEMORY.md: 5 chunks
#   📄 2024-01-15.md: 3 chunks
# ✅ Indexed 2 files, 8 chunks
```

## Step 9: Test the System

### Check Stats

```bash
python unified/atlas_recall.py --stats

# Output:
# 📊 Atlas Memory Stats
#   ChromaDB documents: 8
#   Mem0 memories: 0
#   Letta available: True
#   Last full index: 2024-01-15T10:30:00
```

### Run a Search

```bash
python unified/atlas_recall.py "What are my preferences?"

# Output:
# 🔍 Query: What are my preferences?
# 📝 Found 3 results:
# 
# [1] chroma:MEMORY.md (score: 0.85)
#     Section: MEMORY.md > Preferences
#     - Communication style notes...
```

### Add a Fact

```bash
python unified/atlas_recall.py --add "I prefer dark mode for all applications"

# Output:
# ✅ Added to Mem0: {'results': [{'memory': 'Prefers dark mode for all applications', ...}]}
```

## Step 10: Set Up Daily Indexing (Optional)

Keep memory fresh with a cron job:

```bash
# Edit crontab
crontab -e

# Add this line (indexes at midnight daily)
0 0 * * * cd /path/to/owl-brain && /path/to/.venv/bin/python unified/atlas_recall.py --index >> /var/log/atlas-index.log 2>&1
```

---

## Verification Checklist

Run through this to confirm everything works:

```bash
# 1. Python environment
source .venv/bin/activate
python --version  # Should be 3.10+

# 2. Dependencies
python -c "import mem0; import chromadb; import httpx; print('✅ Core deps OK')"

# 3. OpenAI key
python -c "import os; assert os.getenv('OPENAI_API_KEY') or open(os.path.expanduser('~/.config/openai/api_key')).read().strip(); print('✅ OpenAI key OK')"

# 4. Letta (if using)
curl -s http://localhost:8283/v1/health/ | grep -q "ok" && echo "✅ Letta OK" || echo "❌ Letta not running"

# 5. Storage directories
ls -la ~/.atlas/ && echo "✅ Storage OK"

# 6. Full test
python unified/atlas_recall.py --stats && echo "✅ Full system OK"
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'mem0'"

```bash
source .venv/bin/activate  # Make sure venv is active
pip install mem0ai
```

### "OPENAI_API_KEY not found"

```bash
export OPENAI_API_KEY="sk-..."
# Or create ~/.config/openai/api_key
```

### "Letta not available"

```bash
# Check if Docker is running
docker ps

# Start Letta
cd letta-docker && docker compose up -d

# Check logs for errors
docker logs letta-server
```

### "ChromaDB: instance already exists"

Only one process can access ChromaDB at a time. Kill other Python processes:

```bash
pkill -f atlas_recall
```

### "Connection refused on localhost:8283"

Letta server isn't running:

```bash
cd letta-docker
docker compose up -d
docker logs letta-server  # Check for errors
```

### Slow indexing

First run downloads embedding models. Subsequent runs are faster. 

For very large files, increase chunk size:

```python
# In atlas_recall.py, change:
chunks = chunk_markdown(content, chunk_size=2000)  # Larger chunks
```

---

## Next Steps

1. **Read the individual guides:**
   - [Mem0 Deep Dive](docs/MEM0.md)
   - [ChromaDB Deep Dive](docs/CHROMADB.md)
   - [Letta Deep Dive](docs/LETTA.md)

2. **Explore examples:**
   - `examples/mem0-basic.py`
   - `examples/chromadb-basic.py`
   - `examples/letta-basic.py`
   - `examples/openclaw-integration.py`

3. **Integrate with your agent:**
   - Copy [docs/TOOLS-snippet.md](docs/TOOLS-snippet.md) to your agent's TOOLS.md
   - Use `unified/atlas_recall.py` as your recall system

---

## Uninstall

If you need to remove everything:

```bash
# Stop Letta
cd letta-docker && docker compose down -v

# Remove data
rm -rf ~/.atlas
rm -rf ~/.mem0

# Remove venv
rm -rf .venv
```
