# Web Project Ontology Example

This example adapts the starterkit templates to a website creation project.

Goal:
- keep the model small enough to start
- separate stable knowledge from operational tracking
- support both retrieval and later ingestion from an Obsidian vault

Recommended workspace:
- `website-delivery-template`

Recommended ontology families:
- `project-brief` — business goals, scope, constraints, stakeholders
- `information-architecture` — pages, navigation, page hierarchy
- `site-content` — content items, copy blocks, SEO targets, assets
- `design-system` — components, style tokens, UX decisions
- `technical-delivery` — integrations, environments, backlog tasks, milestones
- `quality-launch` — QA findings, launch checks, risks

Recommended shared entity types:
- `stakeholder`
- `objective`
- `requirement`
- `decision`
- `task`
- `risk`

Retrieval jobs this model supports:
- find the pages impacted by a client requirement
- retrieve all launch blockers and open QA findings
- trace a design or technical decision back to a requirement or objective
- rebuild current project status from tasks, milestones, and risks
