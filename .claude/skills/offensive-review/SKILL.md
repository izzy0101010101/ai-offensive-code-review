---
name: offensive-review
description: Full offensive code review pipeline - runs all stages
---

# /offensive-review

Full offensive code review pipeline.

## Usage
```
/offensive-review /path/to/target/repository
```

## Instructions

Run the complete pipeline sequentially:

1. Run `/stage0` on the target repository (application overview)
2. Run `/stage1` (services and dependencies)
3. Run `/stage2` (entry points)
4. Run `/stage3` (state and flows)
5. Run `/stage4` (findings)
6. Run `python3 scripts/generate_report.py`

Verify each stage's output before proceeding to the next.

All outputs go to `ai_artifacts/` directory.
