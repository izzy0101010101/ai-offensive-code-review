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

condition_type (use the most specific one):

| Type | Look for |
|------|----------|
| MISSING_VALIDATION | User input used without sanitization |
| TRUST_BOUNDARY_CROSSING | Data moves between trust zones |
| DANGEROUS_PRIMITIVE | eval(), SQL builders, deserializers |
| STATE_MUTATION | DB writes, cache updates, session changes |
| CONFIG_DEPENDENT | Behavior changes based on env/config |
| EXTERNAL_CALL_INPUT | User data sent to external APIs |
| FILE_INTERACTION | File read/write/delete from user input |
| SUBPROCESS_EXEC | Shell commands, process spawning |
| AUTH_BYPASS | Logic flaws in authentication |
| AUTHZ_BYPASS | Missing permission checks, IDOR |
| SESSION_HANDLING | Weak session management, fixation |
| SSRF | Server fetches URL from user input |
| OPEN_REDIRECT | Redirect URL from user input |
| PATH_TRAVERSAL | Directory traversal (../) patterns |
| TEMPLATE_INJECTION | User input in template engines |
| XML_PARSING | XXE patterns in XML parsers |
| MASS_ASSIGNMENT | Object binding without allowlist |
| HARDCODED_SECRET | API keys, passwords in code |
| WEAK_CRYPTO | MD5, SHA1, weak keys, ECB mode |
| SENSITIVE_LOGGING | PII, credentials in logs |
| INFO_DISCLOSURE | Stack traces, debug info exposed |
| RACE_CONDITION | TOCTOU, concurrent state access |

Rules:
- Conditions only, not vulnerabilities.
- No severity/impact/likelihood/exploitability.
- No remediation.
- human_validation always = yes.
- Forbidden words: critical, high, medium, low, severe, exploitable, impact.
- CSV only.
- Overwrite.
- Stop.
