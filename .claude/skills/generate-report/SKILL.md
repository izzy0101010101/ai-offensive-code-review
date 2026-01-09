---
name: generate-report
description: Generate HTML report from CSV artifacts
---

# /generate-report

Generate HTML report from CSV artifacts.

## Instructions

Run the pre-built report generator:

```bash
python3 scripts/generate_report.py
```

This reads:
- ai_artifacts/stage1/services.csv
- ai_artifacts/stage1/dependencies.csv
- ai_artifacts/stage2/entry_points.csv
- ai_artifacts/stage3/state_and_links.csv
- ai_artifacts/stage4/findings.csv

And outputs:
- ai_artifacts/report.html

The script handles:
- Path alias resolution
- Code snippet extraction
- HTML generation with navigation
- Search and sortable tables

No AI generation needed - just run the script.
