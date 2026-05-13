#!/usr/bin/env bash
# 第二批大学评估省份运行脚本

# 确保环境变量存在
if [ -f "gaokao-proxy/.env" ]; then
    export $(grep -v '^#' gaokao-proxy/.env | xargs)
fi

PROVINCES=(
    "浙江省"
    "山东省"
    "河南省"
    "安徽省"
    "河北省"
    "辽宁省"
    "福建省"
    "重庆市"
)

echo "开始运行第二批大学评估..."
for prov in "${PROVINCES[@]}"; do
    echo "============================="
    echo "正在启动 $prov 的评估"
    echo "============================="
    python3 run_univ_eval_gemini.py "$prov"
done

echo "第二批全部省份已完成或已处理！"
