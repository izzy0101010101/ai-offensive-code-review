---
name: stage0
description: Application overview and architecture (uses Haiku)
---

# /stage0

Generate application overview and architecture diagram.

**Model:** Use Haiku for this stage.

## Input
- Target repository path (from previous context or argument)

## Output
- `ai_artifacts/stage0/overview.md`

## Instructions

Analyze the codebase and generate a markdown file with:

### 1. Purpose (2-3 sentences)
What does this application do? Who is it for?

### 2. Tech Stack
- Language/runtime
- Framework (if any)
- Database (if any)
- Key dependencies

### 3. Architecture Diagram (ASCII)
Draw a simple flowchart showing main components and how data flows between them.

Use this format:
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│  input  │───▶│  core   │───▶│ output  │
└─────────┘    └─────────┘    └─────────┘
```

Keep it simple - 3-6 boxes max. Show:
- Entry points (HTTP, CLI, stdin)
- Core processing
- Data stores
- External calls

### 4. Key Components (bullet list)
List main modules/packages and what they do (one line each).

## Format

Write directly to `ai_artifacts/stage0/overview.md`:

```markdown
# Application Overview

## Purpose
[2-3 sentences]

## Tech Stack
- **Language:** [lang]
- **Framework:** [framework or "none"]
- **Database:** [db or "none"]
- **Key deps:** [list]

## Architecture

```
[ASCII diagram]
```

## Key Components
- **[module]** - [what it does]
- **[module]** - [what it does]
```

## Rules
- Keep it brief - this is context, not documentation
- ASCII diagram only (no mermaid)
- No security analysis here - that's for later stages
- Create `ai_artifacts/stage0/` directory if needed
