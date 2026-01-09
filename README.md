

<h1 align="center">AI Offensive Code Review Pipeline</h1>

<p align="center">
Automated security code review powered by Claude. Point it at a codebase and get:
</p>

<p align="center">
<b>Service inventory</b> · <b>Attack surface map</b> · <b>Data flow analysis</b> · <b>Security conditions</b>
</p>

<p align="center">
  <img src="screenshots/report.png" width="950px" style="border: 1px solid #30363d; border-radius: 8px;" />
</p>

---

## Why This Exists

I believe in manual security testing - AI should help map what's there so nothing gets missed. Traditional scanners give you severity labels and verdicts without evidence, flooding you with noise to triage. This pipeline takes a different approach: map the attack surface, trace data flows, and identify conditions worth looking at - then give you file paths, line numbers, and preconditions to validate yourself. Leads, not verdicts. You spend time on real issues instead of dismissing false ones.

---

## Requirements

- [Claude Code CLI](https://github.com/anthropics/claude-code)
- Python 3.x (standard library only, no pip install needed)
- Target repository cloned locally

---

## Supported Projects

Works on any language Claude can read - JavaScript, TypeScript, Python, Go, Java, Rust, C#, Ruby, PHP, and more. No language-specific configuration needed.

**Best suited for:**
- Web applications with HTTP entry points
- Microservices and backend APIs
- Anything with identifiable attack surface (routes, handlers, data flows)

**Token usage:** This pipeline reads code. Large codebases = more tokens. To reduce costs, run on specific subdirectories or use individual stages instead of the full pipeline.

---

## Quick Start

```bash
git clone https://github.com/izzy0101010101/ai-offensive-code-review.git
cd ai-offensive-code-review
claude
```

```
run /offensive-review /path/to/target/repo
```

That's it. Wait for the pipeline to complete and open `ai_artifacts/report.html`.

---

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    run /offensive-review                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Stage 0   │───▶│   Stage 1   │───▶│   Stage 2   │───▶│   Stage 3   │───▶│   Stage 4   │
│  Overview   │    │  Services   │    │   Entry     │    │   State &   │    │  Findings   │
│ & Diagram   │    │   & Deps    │    │   Points    │    │   Flows     │    │  (Leads)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                               │
                                               ▼
                                     ┌─────────────────┐
                                     │  report.html    │
                                     └─────────────────┘
```

---

## Run Stages Individually

| Command | What it does |
|---------|--------------|
| `run /stage0` | Application overview and architecture diagram |
| `run /stage1` | Inventory services and dependencies |
| `run /stage2` | Extract entry points (HTTP, queues, SDK) |
| `run /stage3` | Map state mutations and cross-service calls |
| `run /stage4` | Identify conditions requiring validation |
| `run /generate-report` | Generate HTML report from CSVs |

---

## Output Structure

```
ai_artifacts/
├── stage0/
│   └── overview.md         # Application overview & architecture
├── stage1/
│   ├── services.csv        # Service inventory with path aliases
│   └── dependencies.csv    # External dependencies
├── stage2/
│   └── entry_points.csv    # All entry surfaces
├── stage3/
│   └── state_and_links.csv # State operations & cross-service links
├── stage4/
│   └── findings.csv        # Conditions for human validation
└── report.html             # Interactive HTML report
```

---

## Project Structure

```
.claude/skills/       # Pipeline commands (stage1-4, offensive-review, generate-report)
scripts/
├── generate_report.py   # Builds HTML report from CSVs
├── validate-csv.sh      # Validates CSV structure
└── init-review.sh       # Creates ai_artifacts directories
ai_artifacts/         # Output directory (gitignored)
```

---

## Condition Types

Findings use these condition types (not severity labels):

| Type | Description |
|------|-------------|
| `MISSING_VALIDATION` | Input used without validation |
| `TRUST_BOUNDARY_CROSSING` | Data crosses trust boundaries |
| `DANGEROUS_PRIMITIVE` | Use of inherently risky functions |
| `STATE_MUTATION` | State change worth examining |
| `CONFIG_DEPENDENT` | Behavior depends on configuration |
| `EXTERNAL_CALL_INPUT` | User input in external calls |
| `FILE_INTERACTION` | File system operations |
| `SUBPROCESS_EXEC` | Process/command execution |

---

## Example Finding

![Example Finding](screenshots/finding.png)


---

## Permissions

This repo includes pre-configured permissions in `.claude/settings.local.json` so the pipeline runs without constant approval prompts.

Included permissions:
- All pipeline skills (stage1-4, offensive-review, generate-report)
- `python3` for report generation
- `git clone` for cloning target repos

To customize, edit `.claude/settings.local.json` or see the [Claude Code documentation](https://github.com/anthropics/claude-code).

---

## Philosophy

- **Leads, not verdicts** - AI identifies conditions, humans validate
- **No security theater** - No "CRITICAL" labels or impact scores
- **Evidence-based** - Every finding links to specific code locations
- **Transparent** - CSV outputs are auditable, not black-box

---

## Disclaimer

For authorized security testing and educational purposes only. Do not use on systems without permission. The authors are not responsible for misuse.
