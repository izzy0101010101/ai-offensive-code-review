# AI Offensive Code Review Pipeline

## Quick Start
```
run /offensive-review /path/to/target/repo
```

Or run stages individually:
```
run /stage0 → run /stage1 → run /stage2 → run /stage3 → run /stage4 → run /stage5 → run /generate-report
```

## Commands

| Command | Model | Description |
|---------|-------|-------------|
| `run /stage0` | Haiku | Application overview & architecture |
| `run /stage1` | Haiku | Service & dependency inventory |
| `run /stage2` | Haiku | Entry surface extraction |
| `run /stage3` | - | State & cross-service mapping |
| `run /stage4` | - | Condition identification |
| `run /stage5` | - | Attack paths with POCs |
| `run /generate-report` | - | Run `python3 scripts/generate_report.py` |

## Output

```
ai_artifacts/
├── stage0/overview.md       # application overview
├── stage1/services.csv      # with path aliases
├── stage1/dependencies.csv
├── stage2/entry_points.csv
├── stage3/state_and_links.csv
├── stage4/findings.csv
├── stage5/attack_paths.md   # POCs and attack chains
└── report.html
```

## CSV Columns (shortened)

**services.csv:**
`svc_name,repo_path,lang,runtime,build_artifact,build_cmd,run_cmd,entry_file,entry_func`

**dependencies.csv:**
`svc_name,dep_name,version,src_file,scope,local_fork`

**entry_points.csv:**
`svc_name,entry_type,route,method,handler_file,handler_func,called_funcs,param_sources`

Entry types: HTTP, QUEUE, SDK, WEBSOCKET, GRPC, CRON, FILE, STDIN, EVENT, IPC

**state_and_links.csv:**
`svc_name,artifact_type,identifier,op,src_file,src_func,target_file,target_func,data_elements`

**findings.csv:**
`id,svc_name,entry_point,condition_type,description,preconditions,reachable,state_touched,cross_svc,ext_dep,human_validation`

## Path Aliases

Stage 1 defines aliases at top of services.csv:
```
#alias,auth-svc,/full/path/to/auth-service
#alias,api-svc,/full/path/to/api-service
```

Then use: `auth-svc:handlers/auth.go` instead of full paths.

## Rules

- CSV only, no commentary
- No security language
- No severity labels
- Human validation required
- Overwrite files each run

## Scripts

```bash
./scripts/validate-csv.sh        # Check CSV structure
python3 scripts/generate_report.py  # Generate HTML report
```
