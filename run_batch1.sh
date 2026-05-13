#!/bin/bash
# 第一批：教育核心省份（公办优先）
cd "$(dirname "$0")"
mkdir -p logs

for province in "北京市" "湖北省" "陕西省" "上海市" "湖南省" "四川省"; do
  echo "=== $(date "+%Y-%m-%d %H:%M:%S") 开始跑 $province ==="
  python3 run_univ_eval_gemini.py "$province" --public-only
  echo "=== $(date "+%Y-%m-%d %H:%M:%S") $province 完成 ==="
  sleep 10
done

echo "=== $(date "+%Y-%m-%d %H:%M:%S") 第一批全部完成 ==="
