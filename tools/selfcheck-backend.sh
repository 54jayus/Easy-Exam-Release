#!/usr/bin/env bash
# Easy Exam 后端自检（macOS / Linux）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

source "$SCRIPT_DIR/runtime-env.sh"
invoke_project_python -m backend.selfcheck "$@"
