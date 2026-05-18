#!/bin/bash
# 报告 API 接口测试脚本
# 用法: bash scripts/test_report_api.sh [BASE_URL]
# 示例: bash scripts/test_report_api.sh http://127.0.0.1:3099

set -e

BASE="${1:-http://127.0.0.1:3099}"
PASS=0
FAIL=0

check() {
  local name="$1" url="$2" expect="$3"
  local status body
  body=$(curl -s "$BASE$url")
  status=$?

  if [ $status -ne 0 ]; then
    echo "FAIL [$name] curl failed"
    FAIL=$((FAIL+1))
    return
  fi

  if echo "$body" | python3 -c "import json,sys; d=json.load(sys.stdin); $expect" 2>/dev/null; then
    echo "PASS [$name]"
    PASS=$((PASS+1))
  else
    echo "FAIL [$name] assertion failed"
    echo "  Response: $(echo "$body" | head -c 200)"
    FAIL=$((FAIL+1))
  fi
}

echo "=== 报告 API 接口测试 ==="
echo "Target: $BASE"
echo ""

# 1. Health check
check "Health" "/api/reports/health" "exit(0 if d.get('status') in ('ok','degraded') else 1)"

# 2. Stats
check "Stats" "/api/reports/stats" "exit(0 if d.get('majors',{}).get('total',0) > 0 and d.get('universities',{}).get('total',0) > 0 else 1)"

# 3. List majors
check "List Majors" "/api/reports/majors?page_size=3" "exit(0 if d.get('total',0) > 700 and len(d.get('data',[])) == 3 else 1)"

# 4. Get single major
check "Get Major" "/api/reports/majors/080701" "exit(0 if d.get('code') == '080701' and d.get('name') == '电子信息工程' else 1)"

# 5. Search major
check "Search Major" "/api/reports/majors?search=%E8%AE%A1%E7%AE%97%E6%9C%BA&page_size=3" "exit(0 if d.get('total',0) >= 1 else 1)"

# 6. Filter by level
check "Filter Green" "/api/reports/majors?level=green&page_size=3" "exit(0 if d.get('total',0) >= 50 else 1)"

# 7. Filter by category
check "Filter Category" "/api/reports/majors?category=%E5%B7%A5%E5%AD%A6&page_size=2" "exit(0 if d.get('total',0) > 100 else 1)"

# 8. List universities
check "List Universities" "/api/reports/universities?page_size=3" "exit(0 if d.get('total',0) > 900 and len(d.get('data',[])) == 3 else 1)"

# 9. Get single university
check "Get University" "/api/reports/universities/%E6%B8%85%E5%8D%8E%E5%A4%A7%E5%AD%A6" "exit(0 if d.get('name') == '清华大学' and d.get('univ_type') == '985' else 1)"

# 10. Search university
check "Search University" "/api/reports/universities?search=%E5%8C%97%E4%BA%AC&page_size=5" "exit(0 if d.get('total',0) >= 5 else 1)"

# 11. Filter by type
check "Filter Type 985" "/api/reports/universities?type=985&page_size=3" "exit(0 if d.get('total',0) >= 20 else 1)"

# 12. 404 for non-existent major
check "Major 404" "/api/reports/majors/999999" "exit(0 if d.get('error') == '专业不存在' else 1)"

# 13. Pagination page 2
check "Pagination" "/api/reports/majors?page=2&page_size=10" "exit(0 if d.get('page') == 2 and len(d.get('data',[])) == 10 else 1)"

# 14. Min score filter
check "Min Score" "/api/reports/majors?min_score=4.0&page_size=5" "exit(0 if d.get('total',0) >= 50 else 1)"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ $FAIL -eq 0 ] && exit 0 || exit 1
