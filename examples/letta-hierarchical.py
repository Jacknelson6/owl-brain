#!/usr/bin/env python3
"""
Letta Hierarchical Memory for OpenClaw Agents
Self-editing memory where the agent maintains its own memory structure.

Letta (formerly MemGPT) has three memory tiers:
1. Core Memory - Always in context (persona, key facts)
2. Recall Memory - Conversation history, searchable
3. Archival Memory - Long-term storage, searchable

The agent itself decides what to store where.
"""

from letta import create_client

def start_letta_server():
    """
    Start Letta server in a separate terminal:
    $ letta server
    
    Then access:
    - Web UI: http://localhost:8283
    - API: http://localhost:8283/api
    """
    print("Start Letta server with: letta server")
    print("Web UI at http://localhost:8283")


class LettaMemory:
    """Wrapper for Letta's hierarchical memory."""
    
    def __init__(self, base_url: str = "http://localhost:8283"):
        self.client = create_client(base_url=base_url)
    
    def create_agent(self, name: str, persona: str = None):
        """
        Create a new Letta agent with self-editing memory.
        """
        agent = self.client.create_agent(
            name=name,
            memory={
                "persona": persona or "I am a helpful AI assistant with persistent memory.",
                "human": "The user interacting with me."
            }
        )
        return agent
    
    def chat(self, agent_id: str, message: str):
        """
        Send a message to an agent.
        The agent may update its own memory based on the conversation.
        """
        response = self.client.send_message(
            agent_id=agent_id,
            message=message,
            role="user"
        )
        return response
    
    def get_memory(self, agent_id: str):
        """Get the agent's current memory state."""
        return self.client.get_agent_memory(agent_id)
    
    def search_archival(self, agent_id: str, query: str):
        """Search the agent's archival memory."""
        return self.client.get_archival_memory(
            agent_id=agent_id,
            query=query
        )
    
    def add_to_archival(self, agent_id: str, content: str):
        """Manually add something to archival memory."""
        return self.client.insert_archival_memory(
            agent_id=agent_id,
            content=content
        )


# Example usage
if __name__ == "__main__":
    print("📚 Letta Hierarchical Memory Example")
    print("-" * 40)
    print()
    print("Letta runs as a server with a web UI.")
    print()
    print("To get started:")
    print("  1. Run: letta server")
    print("  2. Open: http://localhost:8283")
    print("  3. Create an agent in the UI")
    print("  4. Chat and watch it manage its own memory!")
    print()
    print("Or use the API:")
    print()
    print("```python")
    print("from letta import create_client")
    print()
    print("client = create_client()")
    print("agent = client.create_agent(name='owl-agent')")
    print("response = client.send_message(")
    print("    agent_id=agent.id,")
    print("    message='Remember that I prefer dark mode',")
    print("    role='user'")
    print(")")
    print("```")
    print()
    print("The agent will decide if this goes in core memory, recall, or archival.")
    print("That's the magic - it self-manages. 🦉")
