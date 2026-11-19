#!/usr/bin/env bash
# 部署后冒烟测试：首页、静态资源、登录页、未登录重定向
set -euo pipefail

BASE="${1:-http://127.0.0.1}"

check() {
  local path="$1" expect="$2" label="$3"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE$path")
  if [ "$code" = "$expect" ]; then
    echo "[PASS] $label ($path -> $code)"
  else
    echo "[FAIL] $label ($path -> $code, expected $expect)"
    exit 1
  fi
}

check "/login" 200 "登录页"
check "/static/style.css" 200 "静态样式"
check "/activities" 302 "未登录访问活动页应重定向"

echo "冒烟测试通过。"
