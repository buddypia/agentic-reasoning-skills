#!/bin/bash
# Multi-LLM Recursive Meta-Cognition 실행 래퍼 스크립트
# venv를 활성화하고 main.py를 실행합니다.

set -e

# 스크립트 디렉토리 경로 (심볼릭 링크 해결)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# venv 활성화 (없으면 생성)
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
else
    echo "venv not found. Creating at $SCRIPT_DIR/.venv ..." >&2
    python3 -m venv "$SCRIPT_DIR/.venv"
    source "$SCRIPT_DIR/.venv/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# main.py 실행 (모든 인자 전달)
exec python "$SCRIPT_DIR/main.py" "$@"
