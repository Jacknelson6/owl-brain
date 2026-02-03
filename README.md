# 🦉 owl-brain

**Advanced memory stack for OpenClaw agents**

*Built at 3am by the night crew. Because the best ideas come when everyone else is sleeping.*

---

## What is this?

owl-brain is a curated memory stack that gives your OpenClaw agents **actual memory** — not just context stuffing, but real, persistent, intelligent recall.

We're combining four powerful memory systems:

| Package | What it does | Vibe |
|---------|--------------|------|
| **Mem0** | Agentic memory with auto-extraction | "I remember you mentioned that last week" |
| **ChromaDB** | Local vector database | Fast, embedded, no server needed |
| **Zep** | Temporal-aware memory | "That was before you changed jobs" |
| **Letta** | Self-editing hierarchical memory | The agent *maintains its own memory* |

Each tool has strengths. Use one, use all, mix and match. Your agent, your rules.

## Quick Start

```bash
# Clone it
git clone https://github.com/jacknelson/owl-brain.git
cd owl-brain

# Create your venv (Python 3.12+)
python3.12 -m venv .venv
source .venv/bin/activate

# Install the stack
pip install mem0ai chromadb zep-python letta

# Run the test
python test/memory-stack-test.py
```

See [SETUP.md](SETUP.md) for the full guide.

## Why these four?

We tested a lot of memory solutions. These survived the 3am gauntlet:

### 🧠 Mem0
The "just works" option. Point it at conversations, it extracts memories automatically. Uses OpenAI embeddings under the hood.

### 🔷 ChromaDB
When you need vectors but don't want to spin up infrastructure. Runs in-process, stores to disk, surprisingly fast.

### ⏱️ Zep
Temporal awareness is underrated. "What did they say about X before the project pivot?" Zep handles time-aware recall.

### 📚 Letta (f.k.a. MemGPT)
The wild one. Self-editing memory where the agent maintains its own memory hierarchy. Core memory, archival memory, recall memory. It's like giving your agent a filing system it actually uses.

## For OpenClaw Agents

Add the [TOOLS.md snippet](docs/TOOLS-snippet.md) to your agent's workspace and you're ready to integrate.

Check [examples/](examples/) for integration patterns.

## Philosophy

Most "memory" in AI is just cramming more tokens into context. That doesn't scale and it doesn't feel like memory.

Real memory is:
- **Selective** — not everything matters
- **Temporal** — when things happened changes their meaning
- **Hierarchical** — some memories are core, others are trivia
- **Self-maintaining** — you don't manually index your brain

owl-brain gives you tools that actually think about memory this way.

## Contributing

PRs welcome. Especially if you're also up at 3am.

## License

MIT — use it, fork it, make it better.

---

*"The owl sees what others miss in the dark."*

🦉 Night Crew
