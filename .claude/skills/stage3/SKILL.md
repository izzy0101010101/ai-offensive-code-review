---
name: stage3
description: State and cross-service extraction
---

# /stage3

State and Cross-Service Extraction

## Instructions

Read:
- ai_artifacts/stage1/services.csv (with aliases)
- ai_artifacts/stage2/entry_points.csv

Create ai_artifacts/stage3/state_and_links.csv

Header:
svc_name,artifact_type,identifier,op,src_file,src_func,target_file,target_func,data_elements

artifact_type:
DATASTORE, FILE, QUEUE, HTTP_CALL, SDK_CALL

op:
READ, WRITE, EXECUTE, PUBLISH, CONSUME

Rules:
- One row per concrete operation.
- Use alias:path format for files.
- No security language.
- CSV only.
- Overwrite.
- Stop.
