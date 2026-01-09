#!/bin/bash
# CSV Validation Script - validates structure of generated CSVs

set -e

BASE_DIR="${1:-./ai_artifacts}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

validate_csv() {
    local file="$1"
    local expected="$2"
    local name="$3"

    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}[SKIP]${NC} $name - not found"
        return 0
    fi

    # Skip alias lines, get actual header
    header=$(grep -v '^#' "$file" | head -1)
    actual=$(echo "$header" | tr ',' '\n' | wc -l | xargs)
    expect=$(echo "$expected" | tr ',' '\n' | wc -l | xargs)

    if [ "$actual" -ne "$expect" ]; then
        echo -e "${RED}[FAIL]${NC} $name - expected $expect cols, got $actual"
        return 1
    fi

    lines=$(grep -v '^#' "$file" | wc -l | xargs)
    echo -e "${GREEN}[PASS]${NC} $name - $((lines - 1)) rows"
    return 0
}

echo "Validating: $BASE_DIR"
echo "========================"

errors=0

validate_csv "$BASE_DIR/stage1/services.csv" \
    "svc_name,repo_path,lang,runtime,build_artifact,build_cmd,run_cmd,entry_file,entry_func" \
    "services.csv" || ((errors++))

validate_csv "$BASE_DIR/stage1/dependencies.csv" \
    "svc_name,dep_name,version,src_file,scope,local_fork" \
    "dependencies.csv" || ((errors++))

validate_csv "$BASE_DIR/stage2/entry_points.csv" \
    "svc_name,entry_type,route,method,handler_file,handler_func,called_funcs,param_sources" \
    "entry_points.csv" || ((errors++))

validate_csv "$BASE_DIR/stage3/state_and_links.csv" \
    "svc_name,artifact_type,identifier,op,src_file,src_func,target_file,target_func,data_elements" \
    "state_and_links.csv" || ((errors++))

validate_csv "$BASE_DIR/stage4/findings.csv" \
    "id,svc_name,entry_point,condition_type,description,preconditions,reachable,state_touched,cross_svc,ext_dep,human_validation" \
    "findings.csv" || ((errors++))

echo "========================"
[ $errors -gt 0 ] && echo -e "${RED}$errors error(s)${NC}" && exit 1
echo -e "${GREEN}All valid${NC}"
