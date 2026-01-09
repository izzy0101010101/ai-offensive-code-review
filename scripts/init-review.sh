#!/bin/bash
# Initialize ai_artifacts directory structure

set -e

BASE_DIR="${1:-./ai_artifacts}"

echo "Initializing review artifacts directory..."

mkdir -p "$BASE_DIR/stage1"
mkdir -p "$BASE_DIR/stage2"
mkdir -p "$BASE_DIR/stage3"
mkdir -p "$BASE_DIR/stage4"

echo "Created: $BASE_DIR/stage1"
echo "Created: $BASE_DIR/stage2"
echo "Created: $BASE_DIR/stage3"
echo "Created: $BASE_DIR/stage4"
echo ""
echo "Ready. Run '/offensive-review <target_path>' to start."
