---
name: stage5
description: Attack path synthesis with code-specific POCs (project)
---

# /stage5

Attack Path Synthesis

## Purpose

You are an attacker. Your job is to find **real, exploitable attack paths** with working POCs based on the actual code. Not theoretical risks - actual attacks that would work against this specific codebase.

## Input

Read ALL previous artifacts:
- `ai_artifacts/stage0/overview.md` - Understand what the app does
- `ai_artifacts/stage1/services.csv` - Services and aliases
- `ai_artifacts/stage1/dependencies.csv` - Libraries in use
- `ai_artifacts/stage2/entry_points.csv` - All entry points
- `ai_artifacts/stage3/state_and_links.csv` - Data flows
- `ai_artifacts/stage4/findings.csv` - Identified conditions

Then READ THE ACTUAL SOURCE CODE for each finding to understand:
- What sanitization/validation exists
- What the bypass would be
- What the complete path looks like

## Output

Create `ai_artifacts/stage5/attack_paths.md`

## Process

### Step 1: Understand the Business Logic

Before attacking, understand:
- What is this application FOR?
- What are the valuable assets? (user data, money, admin access, etc.)
- What would an attacker actually want to achieve?
- What are the trust boundaries?

### Step 2: Trace Attack Paths

For each finding in stage4, attempt to build a complete attack:

```
ENTRY → [what attacker controls] → PROCESSING → [what code does] → SINK → [what happens]
```

You MUST read the actual source code to:
1. Verify the vulnerability exists
2. Understand what defenses are in place
3. Craft a payload that would actually work
4. Confirm the attack reaches a meaningful sink

### Step 3: Consider Chains

Look for attack combinations:
- Can A + B together achieve more than either alone?
- Does exploiting X give access to exploit Y?
- Can low-privilege actions chain to high-privilege outcomes?

Example chains:
- XSS → Session theft → Account takeover
- IDOR → Data leak → Password reset abuse
- SSRF → Internal service access → RCE
- Mass assignment → Privilege escalation → Admin access

### Step 4: Self-Validation (CRITICAL)

For EACH attack path, ask yourself:
1. Did I actually read the code that handles this?
2. Is there sanitization I missed?
3. Would the attacker get stuck somewhere?
4. Does this actually reach a meaningful impact?
5. Am I hallucinating or is this based on real code?
6. Did I verify ALL paths to this sink, not just one?

If ANY answer is uncertain → DELETE the attack path.

Before concluding "not exploitable due to validation":
- Confirm validation is applied on the SPECIFIC path being analyzed.
- Do not assume sibling implementations share the same controls.
- Incomplete implementations (TODO stubs) are findings, not assumptions of safety.

### Step 5: Write POCs

For validated attacks only, write:

```markdown
## A1: [Short Attack Name]

**Target:** [endpoint]
**Type:** [e.g., SQL Injection, XSS, IDOR]

### Attack Flow
1. Attacker does X at [entry point]
2. Input passes through [function] in [file:line]
3. No sanitization at [specific location]
4. Reaches sink at [function] in [file:line]
5. Result: [specific impact]

### POC

```http
POST /api/endpoint HTTP/1.1
Host: target.com
Content-Type: application/json

{"field": "payload-here"}
```

**Expected Result:** [what happens]

### Code Evidence
- [file:line] - [what the code shows]
- [file:line] - [why bypass works]

### Chain Potential
- Can chain with: A3, A5
- Enables: [what becomes possible after this]
```

## Rules

### DO:
- Read actual source code before claiming anything
- Craft payloads specific to the code's handling
- Consider the actual libraries/frameworks in use
- Think about business logic abuse
- Chain vulnerabilities where logical
- Be specific about file:line locations
- Delete anything you're not confident about

### DO NOT:
- Hallucinate vulnerabilities not in the code
- Use generic payloads without checking if they'd work
- Include "might be vulnerable" - either it is or delete it
- Add misconfigurations or theoretical issues
- Include severity ratings
- Pad the report - empty is fine if nothing is exploitable
- Assume vulnerabilities without reading the sink

### Output Nothing If:
- No complete attack paths can be traced
- All paths have blocking defenses
- You cannot verify with actual code
- Impact is negligible

Write: "No viable attack paths identified. All conditions from Stage 4 were analyzed but none could be traced to a complete, exploitable attack."

## Format

```markdown
# Attack Paths

**Application:** [name from overview]
**Analysis Date:** [date]
**Findings Analyzed:** [X from stage4]
**Viable Attacks:** [Y]

---

## A1: [Attack Name]
[full details as above]

---

## A2: [Attack Name]
[full details as above]

---

## Attack Chains

### Chain 1: [Name]
A1 → A3 → A5: [description of combined attack]

---

## Summary

| ID | Attack | Entry Point | Impact |
|----|--------|-------------|--------|
| A1 | ... | ... | ... |

## Not Exploitable

These Stage 4 findings were analyzed but no viable attack path exists:
- L3: [reason - e.g., "sanitization at line X blocks payload"]
- L7: [reason - e.g., "requires authentication as admin which defeats purpose"]
```

## Quality Check

Before finalizing, verify:
- [ ] Every POC has actual code evidence with file:line
- [ ] Every payload is specific to the code (not generic)
- [ ] Every attack path is complete (entry to impact)
- [ ] No "might", "could", "possibly" language
- [ ] Chains are logical and achievable
- [ ] Deleted anything uncertain

If the report has fewer attacks than Stage 4 findings, that's GOOD. It means you're being rigorous.
