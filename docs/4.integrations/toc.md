4.1 integrations/langgraph.md
Hook: Use mindBrain as a LangGraph checkpointer and projection node.

Blocks to develop:

Install: pip install mindbrain-langgraph

MindBrainCheckpointer: replaces MemorySaver, persists graph state in mindBrain

MindBrainProjectionNode: injects a projection as a named graph node

Full example: compliance graph with 3 nodes, mindBrain as checkpoint

Why this beats MemorySaver: typed, queryable, multi-agent shared state

→ Next: integrations/crewai.md

4.2 integrations/crewai.md
Hook: MindBrainMemoryTool gives CrewAI agents structured persistent memory.

Blocks to develop:

Install: pip install mindbrain-crewai

MindBrainMemoryTool: drop-in tool for any CrewAI agent

Example: 3-agent crew (researcher, analyst, writer) sharing a mindBrain schema

What each agent reads and writes

Why this beats CrewAI's built-in memory: schema-enforced, queryable by other agents

→ Next: integrations/ghostcrab-mcp.md

4.3 integrations/claude-code.md
Hook: Use GhostCrab MCP to give Claude Code persistent project memory.

Blocks to develop:

Prerequisites: GhostCrab MCP installed, Claude Desktop or claude CLI

Config block for .claude/settings.local.json

What Claude can now do: query tasks, update status, request projections — via natural language

Example conversation: Claude reads a blocked task projection, writes a fix, marks done

Personal schema suggestion for dev projects: Task + File + Dependency entities

→ Next: integrations/cursor.md (placeholder)

4.4 integrations/n8n.md
Hook: mindBrain Memory Node for n8n — persistent structured memory in any workflow.

Blocks to develop:

Install: community node @mindflight/n8n-nodes-mindbrain

Available nodes: MindBrain Query, MindBrain Insert, MindBrain Project, MindBrain Update

Example workflow: webhook → classify intent → query mindBrain → branch on status → update

Why this matters for the n8n community: replaces ad-hoc JSON storage with typed knowledge

Link to n8n community marketplace

→ Next: integrations/crewai.md