#!/bin/bash
# update-task-progress.sh
# 在 Claude Code Stop 事件或 git post-commit 时自动调用
# 功能：检测项目变更，自动更新对应的 TASK-*.md 文件
#
# 用法：
#   ./scripts/update-task-progress.sh [TASK文件名]
#   如果不传参数，自动匹配变更文件对应的 TASK 文件

set -euo pipefail

PROJECT_DIR="/Users/MarkHuang/Desktop/高考志愿填报项目"
cd "$PROJECT_DIR"

# 找到目标 TASK 文件
TASK_FILE=""
if [ -n "${1:-}" ]; then
    TASK_FILE="$PROJECT_DIR/$1"
else
    # 自动查找：优先找"进行中"的 TASK
    for f in "$PROJECT_DIR"/TASK-*.md; do
        [ -f "$f" ] || continue
        [ "$(basename "$f")" = "TASK-TEMPLATE.md" ] && continue
        if grep -q "进行中" "$f" 2>/dev/null; then
            TASK_FILE="$f"
            break
        fi
    done
    # 如果没有"进行中"的，找第一个非模板的
    if [ -z "$TASK_FILE" ]; then
        for f in "$PROJECT_DIR"/TASK-*.md; do
            [ -f "$f" ] || continue
            [ "$(basename "$f")" = "TASK-TEMPLATE.md" ] && continue
            TASK_FILE="$f"
            break
        done
    fi
fi

if [ -z "$TASK_FILE" ] || [ ! -f "$TASK_FILE" ]; then
    echo "[task-update] 没有 TASK 文件需要更新"
    exit 0
fi

TASK_NAME=$(basename "$TASK_FILE" .md)
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

# 获取最近的变更
RECENT_COMMITS=$(git log --oneline -5 --since="30 minutes ago" 2>/dev/null | head -5 || true)
DIFF_STAT=$(git diff --stat 2>/dev/null | tail -3 || true)
CHANGED_FILES=$(git diff --name-only 2>/dev/null | head -20 || true)
UNSTAGED_FILES=$(git diff --name-only HEAD 2>/dev/null | head -10 || true)

# 如果没有任何变更，不更新
if [ -z "$RECENT_COMMITS" ] && [ -z "$DIFF_STAT" ]; then
    echo "[task-update] 无变更，跳过更新"
    exit 0
fi

# 构建变更摘要
SUMMARY=""
if [ -n "$RECENT_COMMITS" ]; then
    COMMIT_COUNT=$(echo "$RECENT_COMMITS" | wc -l | tr -d ' ')
    SUMMARY="最近 ${COMMIT_COUNT} 个 commit:\n$(echo "$RECENT_COMMITS" | sed 's/^/  /')"
fi
if [ -n "$CHANGED_FILES" ]; then
    FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
    SUMMARY="${SUMMARY}\n工作区变更 ${FILE_COUNT} 个文件:\n$(echo "$CHANGED_FILES" | head -5 | sed 's/^/  /')"
    [ "$FILE_COUNT" -gt 5 ] && SUMMARY="${SUMMARY}\n  ... 等 ${FILE_COUNT} 个"
fi

# 检查 TASK 文件是否已有今日记录，避免重复
TODAY=$(date "+%Y-%m-%d")
if grep -q "### ${TODAY}" "$TASK_FILE" 2>/dev/null; then
    # 已有今日记录，更新最后一条
    # 使用 python 来做精确的 markdown 操作
    :
fi

# 追加进度记录到 TASK 文件（在"下一步"之前插入）
PROGRESS_ENTRY="
### ${TIMESTAMP} 自动记录

${SUMMARY}

---

"

# 在 TASK 文件中找到"## 下一步"之前插入记录
# 如果没有"## 下一步"，就追加到文件末尾
if grep -q "^## 下一步" "$TASK_FILE"; then
    # 使用 sed 在"## 下一步"之前插入
    # 先写到临时文件
    TMP_FILE=$(mktemp)
    awk -v entry="$PROGRESS_ENTRY" '
        /^## 下一步/ { print entry }
        { print }
    ' "$TASK_FILE" > "$TMP_FILE"
    mv "$TMP_FILE" "$TASK_FILE"
else
    echo "$PROGRESS_ENTRY" >> "$TASK_FILE"
fi

echo "[task-update] 已更新 ${TASK_NAME} — ${TIMESTAMP}"
