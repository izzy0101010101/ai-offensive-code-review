---
name: stage1
description: Service and dependency inventory (uses Haiku)
---

# /stage1

Service and Dependency Inventory

**Model: Use Haiku for this stage.**

## Instructions

Identify all services in the repository set.

First, define path aliases in this format at the top of services.csv:
```
#alias,svc_name,base_path
#alias,auth-svc,/full/path/to/auth-service
#alias,api-svc,/full/path/to/api-service
```

For each service, extract:
- svc_name
- repo_path (full path, used for alias)
- lang
- runtime (version only)
- build_artifact
- build_cmd
- run_cmd
- entry_file (use alias:relative/path format after aliases defined)
- entry_func

Write output to:
ai_artifacts/stage1/services.csv

Then extract dependencies.

For each dependency:
- svc_name
- dep_name
- version
- src_file (use alias:path format)
- scope (direct, indirect, dev)
- local_fork (yes/no)

Write output to:
ai_artifacts/stage1/dependencies.csv

Rules:
- CSV only.
- No analysis.
- No security language.
- Overwrite files.
- Stop after writing.
