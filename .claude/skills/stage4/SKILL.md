---
name: stage4
description: Findings - condition identification only
---

# /stage4

Findings (Condition Identification Only)

## Instructions

Read:
- ai_artifacts/stage1/services.csv
- ai_artifacts/stage2/entry_points.csv
- ai_artifacts/stage3/state_and_links.csv

Create ai_artifacts/stage4/findings.csv

Header:
id,svc_name,entry_point,condition_type,description,preconditions,reachable,state_touched,cross_svc,ext_dep,human_validation

condition_type:
MISSING_VALIDATION
TRUST_BOUNDARY_CROSSING
DANGEROUS_PRIMITIVE
STATE_MUTATION
CONFIG_DEPENDENT
EXTERNAL_CALL_INPUT
FILE_INTERACTION
SUBPROCESS_EXEC

Rules:
- Conditions only, not vulnerabilities.
- No severity/impact/likelihood/exploitability.
- No remediation.
- human_validation always = yes.
- Forbidden words: critical, high, medium, low, severe, exploitable, impact.
- CSV only.
- Overwrite.
- Stop.
