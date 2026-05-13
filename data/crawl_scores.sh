#!/bin/bash
# 高考录取分数线爬取脚本（Shell + curl 版本）
# 数据源：掌上高考 api.zjzw.cn
# 爬取范围：河北(13) + 广东(44), 2023-2025年
# 输出：Dify 知识库格式的 Markdown 文件

set -euo pipefail

OUTPUT_DIR="/tmp/gaokao_scores"
mkdir -p "$OUTPUT_DIR"

# 学校ID列表（从linkage.json提取，取前500所本科院校）
# 先获取学校列表
echo "Fetching school list..."
SCHOOL_LIST=$(curl -s "https://static-data.gaokao.cn/www/2.0/info/linkage.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
schools = data.get('data', {}).get('school', [])
skip = ['职业', '专科', '民办', '独立学院', '中外合作', '艺术', '体育', '传媒', '音乐', '美术', '舞蹈', '影视', '戏剧']
count = 0
for s in schools:
    name = s['name']
    sid = s['school_id']
    if any(kw in name for kw in skip):
        continue
    count += 1
    if count <= 500:
        print(f'{sid}\t{name}')
")
TOTAL_SCHOOLS=$(echo "$SCHOOL_LIST" | wc -l | tr -d ' ')
echo "Schools to process: $TOTAL_SCHOOLS"

# 省份配置
declare -A PROV_NAMES
PROV_NAMES[13]="河北"
PROV_NAMES[44]="广东"

YEARS="2023 2024 2025"

for PROV_ID in 13 44; do
    PROV_NAME="${PROV_NAMES[$PROV_ID]}"
    OUTPUT_FILE="$OUTPUT_DIR/kb2-scores-${PROV_NAME}.md"

    echo ""
    echo "=========================================="
    echo "Processing: $PROV_NAME ($PROV_ID)"
    echo "=========================================="

    # Write header
    cat > "$OUTPUT_FILE" << EOF
# KB-2 ${PROV_NAME}省高考录取分数线数据

> 数据来源：掌上高考 | 覆盖年份：2023-2025年
> 包含各专业最低分、最低位次、平均分

EOF

    SUCCESS=0
    COUNT=0

    while IFS=$'\t' read -r SCHOOL_ID SCHOOL_NAME; do
        COUNT=$((COUNT + 1))

        for YEAR in $YEARS; do
            printf "  [%d/%d] %s - %d..." "$COUNT" "$TOTAL_SCHOOLS" "$SCHOOL_NAME" "$YEAR"

            # Fetch data
            DATA=$(curl -s "https://api.zjzw.cn/web/api/?local_province_id=${PROV_ID}&page=1&school_id=${SCHOOL_ID}&size=50&uri=apidata/api/gk/score/special&year=${YEAR}" \
              -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" 2>/dev/null || echo "")

            if [ -z "$DATA" ]; then
                echo " skip (empty)"
                continue
            fi

            # Parse data with Python
            RESULT=$(echo "$DATA" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
except:
    sys.exit(1)

d = data.get('data', {})
if not d:
    sys.exit(1)

items = d.get('item', []) if isinstance(d, dict) else d
if not items:
    sys.exit(1)

# Group by batch
batches = {}
for item in items:
    batch = item.get('local_batch_name', '未知')
    if batch not in batches:
        batches[batch] = []
    batches[batch].append({
        'spname': item.get('spname', '?'),
        'min': item.get('min', '-'),
        'min_section': item.get('min_section', '-'),
        'avg': item.get('average', '-'),
        'type_name': item.get('local_type_name', ''),
        'info': item.get('info', ''),
    })

# Output markdown
print(f'## $SCHOOL_NAME - {YEAR}年')
print()
for batch_name, majors in batches.items():
    print(f'### {batch_name}')
    print()
    print('| 专业名称 | 科类 | 最低分 | 最低位次 | 平均分 |')
    print('|---------|------|--------|---------|--------|')
    for m in sorted(majors, key=lambda x: int(str(x['min']).replace('-','999'))):
        name = m['spname']
        if m['info']:
            name += f'({m[\"info\"]})'
        print(f'| {name} | {m[\"type_name\"]} | {m[\"min\"]} | {m[\"min_section\"]} | {m[\"avg\"]} |')
    print()
" 2>/dev/null)

            if [ $? -eq 0 ] && [ -n "$RESULT" ]; then
                echo "$RESULT" >> "$OUTPUT_FILE"
                echo "---" >> "$OUTPUT_FILE"
                echo "" >> "$OUTPUT_FILE"
                SUCCESS=$((SUCCESS + 1))
                echo " OK ($(echo "$RESULT" | grep '^|' | wc -l | tr -d ' ') rows)"
            else
                echo " skip (no data)"
            fi

            # Rate limiting
            sleep 0.5
        done
    done <<< "$SCHOOL_LIST"

    SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo ""
    echo "Done: $PROV_NAME - $SUCCESS records, file size: $SIZE"
    echo "Output: $OUTPUT_FILE"
done

echo ""
echo "All done!"
ls -la "$OUTPUT_DIR/"*.md
