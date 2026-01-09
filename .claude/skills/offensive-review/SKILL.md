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

1. Run `/stage1` on the target repository
2. Run `/stage2`
3. Run `/stage3`
4. Run `/stage4`
5. Run `python3 scripts/generate_report.py`

Verify each stage's CSV output before proceeding to the next.

All outputs go to `ai_artifacts/` directory.
