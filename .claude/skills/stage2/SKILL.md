---
name: stage2
description: Entry surface extraction (uses Haiku)
---

# /stage2

Entry Surface Extraction

**Model: Use Haiku for this stage.**

## Instructions

Read ai_artifacts/stage1/services.csv (including path aliases).

Create ai_artifacts/stage2/entry_points.csv

Header:
svc_name,entry_type,route,method,handler_file,handler_func,called_funcs,param_sources

Rules:
- One row per concrete handler.
- Expand routers into final handlers only.
- entry_type: HTTP, QUEUE, SDK
- HTTP verbs uppercase.
- QUEUE uses MESSAGE.
- Use alias:path format for files.
- param_sources: path, query, body, headers, message.
- No auth labels.
- No security language.

CSV only.
Overwrite.
Stop.
