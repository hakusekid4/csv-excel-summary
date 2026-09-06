#!/usr/bin/env bash
# Lint とテストを 1 コマンドでまとめて実行する
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== ruff (Lint) =="
ruff check .
echo "== pytest (テスト) =="
pytest -q
echo "== すべて通りました =="
