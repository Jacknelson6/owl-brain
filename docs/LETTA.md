# Letta — Self-Editing Hierarchical Memory

Letta (formerly MemGPT) is the "intelligent filing system" layer. Unlike other memory systems where you manage the data, Letta agents manage their own memory — deciding what to remember, what to forget, and how to organize information.

## What Makes Letta Special

Traditional memory is passive — you put things in, you get things out. Letta memory is active:

```
Traditional Memory:
  You → save("fact") → Memory → retrieve("query") → You

Letta Memory:
  You → conversation → Agent
                         ↓
                    Agent decides:
                    • What's important?
                    • Where should this go?
                    • Should I update existing memory?
                    • Is this core identity or trivia?
                         ↓
                    Memory (self-organized)
```

## The Three-Tier Memory Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     CORE MEMORY                              │
│  Always loaded in context. Limited size (~2000 tokens).      │
│  Agent's "working memory" - identity, key facts.             │
│                                                              │
│  Blocks:                                                     │
│  • persona: "I am Atlas, an AI assistant..."                │
│  • human: "My human is Jack. He prefers casual tone..."     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    RECALL MEMORY                             │
│  Recent conversation context. Automatically managed.         │
│  Searchable, summarized, paginated.                          │
│  Think: "What happened in our last few conversations?"       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   ARCHIVAL MEMORY                            │
│  Long-term storage. Unlimited size.                          │
│  Agent explicitly saves important information here.          │
│  Think: "Facts I want to remember forever."                  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

Letta runs as a server (Docker recommended):

```bash
# Create docker-compose.yml
mkdir letta-docker && cd letta-docker
```

```yaml
# docker-compose.yml
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

  letta-db:
    image: postgres:15
    container_name: letta-db
    environment:
      - POSTGRES_USER=letta
      - POSTGRES_PASSWORD=letta
      - POSTGRES_DB=letta
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  letta-data:
  postgres-data:
```

```bash
# Start Letta
export OPENAI_API_KEY="sk-your-key"
docker compose up -d

# Verify it's running
curl http://localhost:8283/v1/health/
# Returns: {"version":"0.x.x","status":"ok"}
```

## Web UI

Letta includes a web interface for managing agents:

```
http://localhost:8283
```

From here you can:
- Create and manage agents
- View conversation history
- Inspect memory contents
- Test conversations

## API Usage

### Check Health

```bash
curl http://localhost:8283/v1/health/
```

### List Agents

```bash
curl http://localhost:8283/v1/agents/
```

### Create an Agent

```bash
curl -X POST http://localhost:8283/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "atlas",
    "system": "You are Atlas, a helpful AI assistant with persistent memory.",
    "memory_blocks": [
      {
        "label": "human",
        "value": "The human I work with. I will learn about them over time."
      },
      {
        "label": "persona",
        "value": "I am Atlas. I have persistent memory across conversations."
      }
    ]
  }'
```

### Send a Message

```bash
curl -X POST http://localhost:8283/v1/agents/{agent_id}/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hi! My name is Jack and I work on AI projects."}
    ]
  }'
```

### Get Core Memory

```bash
curl http://localhost:8283/v1/agents/{agent_id}/memory/
```

### Update Core Memory

```bash
curl -X PATCH http://localhost:8283/v1/agents/{agent_id}/memory/ \
  -H "Content-Type: application/json" \
  -d '{
    "memory": {
      "human": "Jack Nelson, Chief Editing Officer. Prefers casual communication."
    }
  }'
```

### Add to Archival Memory

```bash
curl -X POST http://localhost:8283/v1/agents/{agent_id}/archival/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Important fact: Jack runs payroll on the 1st and 15th of each month."
  }'
```

### Search Archival Memory

```bash
curl "http://localhost:8283/v1/agents/{agent_id}/archival/?query=payroll&limit=5"
```

## Python Client

```python
import httpx

class LettaClient:
    def __init__(self, base_url: str = "http://localhost:8283"):
        self.client = httpx.Client(
            base_url=base_url, 
            timeout=30.0,
            follow_redirects=True
        )
        self.agent_id = None
    
    def health_check(self) -> bool:
        """Check if Letta is running"""
        try:
            resp = self.client.get("/v1/health/")
            return resp.status_code == 200
        except:
            return False
    
    def create_agent(self, name: str, system: str = None) -> str:
        """Create a new agent, return agent_id"""
        payload = {
            "name": name,
            "system": system or f"You are {name}, an AI with persistent memory.",
            "memory_blocks": [
                {"label": "human", "value": "My human. I'll learn about them."},
                {"label": "persona", "value": f"I am {name}."}
            ]
        }
        resp = self.client.post("/v1/agents/", json=payload)
        self.agent_id = resp.json()["id"]
        return self.agent_id
    
    def get_or_create_agent(self, name: str) -> str:
        """Get existing agent or create new one"""
        resp = self.client.get("/v1/agents/")
        for agent in resp.json():
            if agent.get("name") == name:
                self.agent_id = agent["id"]
                return self.agent_id
        return self.create_agent(name)
    
    def send_message(self, message: str) -> str:
        """Send message and get response"""
        resp = self.client.post(
            f"/v1/agents/{self.agent_id}/messages/",
            json={"messages": [{"role": "user", "content": message}]}
        )
        messages = resp.json().get("messages", [])
        # Find assistant response
        for msg in messages:
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        return ""
    
    def get_core_memory(self) -> dict:
        """Get the always-loaded core memory"""
        resp = self.client.get(f"/v1/agents/{self.agent_id}/memory/")
        return resp.json()
    
    def update_core_memory(self, block: str, content: str) -> bool:
        """Update a core memory block"""
        resp = self.client.patch(
            f"/v1/agents/{self.agent_id}/memory/",
            json={"memory": {block: content}}
        )
        return resp.status_code == 200
    
    def add_to_archival(self, text: str) -> bool:
        """Add to long-term archival memory"""
        resp = self.client.post(
            f"/v1/agents/{self.agent_id}/archival/",
            json={"text": text}
        )
        return resp.status_code in [200, 201]
    
    def search_archival(self, query: str, limit: int = 5) -> list:
        """Search archival memory"""
        resp = self.client.get(
            f"/v1/agents/{self.agent_id}/archival/",
            params={"query": query, "limit": limit}
        )
        return resp.json() if resp.status_code == 200 else []


# Usage
letta = LettaClient()
if letta.health_check():
    letta.get_or_create_agent("atlas")
    
    # The agent will manage its own memory during conversation
    response = letta.send_message("Hi! I'm Jack, I work on AI projects.")
    print(response)
    
    # But you can also directly add to archival
    letta.add_to_archival("Jack's payroll runs on 1st and 15th of each month")
    
    # And search it
    results = letta.search_archival("payroll")
```

## How Agents Manage Memory

When you talk to a Letta agent, it has special "tools" for memory management:

### Core Memory Tools

```python
# The agent can call these internally:
core_memory_append(label="human", content="Loves coffee")
core_memory_replace(label="human", old="unknown", new="Jack Nelson")
```

### Archival Memory Tools

```python
# For long-term storage:
archival_memory_insert(content="Important meeting notes from Jan 15...")
archival_memory_search(query="meeting notes", page=0)
```

### Recall Memory Tools

```python
# For conversation history:
conversation_search(query="what did we discuss about the project?", page=0)
```

The agent decides when to use these based on the conversation.

## Core Memory Blocks

You define the structure of core memory when creating an agent:

```python
{
    "memory_blocks": [
        {
            "label": "persona",
            "value": "I am Atlas, an AI assistant. I'm helpful and concise."
        },
        {
            "label": "human", 
            "value": "My human's name is Jack. He prefers casual communication."
        },
        {
            "label": "project",  # Custom blocks allowed
            "value": "Current project: Toastique Content OS"
        }
    ]
}
```

Core memory is always in context — the agent "always knows" this information without searching.

## Storage

Letta stores data in:
- **PostgreSQL**: Agent configs, messages, metadata
- **Vector store**: Archival memory embeddings (configurable)

Data location with Docker:
- `letta-data` volume: Agent data, configs
- `postgres-data` volume: Database

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
LETTA_LLM_MODEL=gpt-4o              # Default LLM
LETTA_EMBEDDING_MODEL=text-embedding-3-small
LETTA_SERVER_HOST=0.0.0.0
LETTA_SERVER_PORT=8283
```

## Troubleshooting

### "Connection refused"

```bash
# Check if containers are running
docker ps | grep letta

# Check logs
docker logs letta-server

# Restart
docker compose restart
```

### "Agent not found"

```python
# List all agents to find the right ID
resp = client.get("/v1/agents/")
print(resp.json())
```

### Slow responses

Letta agents do more thinking than simple LLM calls. They:
1. Parse your message
2. Decide if memory operations are needed
3. Execute memory tools
4. Generate response

This takes 5-15 seconds typically. For faster responses, use simpler memory systems.

### API returns redirects

Letta's API requires trailing slashes:
```python
# ❌ Wrong
client.get("/v1/health")

# ✅ Correct
client.get("/v1/health/")
```

## When to Use Letta

✅ **Good for:**
- Agents that need to maintain their own knowledge
- Long-running relationships with users
- Complex memory hierarchies
- Agent self-reflection and learning

❌ **Not ideal for:**
- Simple fact storage (overkill, use ChromaDB)
- Auto-extraction from text (use Mem0)
- Time-based queries (use Zep)
- Low-latency applications (Letta is slower)

## Advanced: Custom Memory Tools

You can extend Letta agents with custom tools:

```python
# Define a custom tool
tool_def = {
    "name": "check_calendar",
    "description": "Check the user's calendar for upcoming events",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "Date to check (YYYY-MM-DD)"}
        }
    }
}

# Add to agent
curl -X POST http://localhost:8283/v1/agents/{agent_id}/tools/ \
  -H "Content-Type: application/json" \
  -d '{"tool": ...}'
```

The agent can then use this tool during conversations to augment its memory capabilities.
