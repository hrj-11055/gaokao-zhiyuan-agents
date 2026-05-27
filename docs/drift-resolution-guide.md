# 漂移问题解决流程

## 概述

本项目的"漂移"指数据、Schema、代码、文件管理在多轮迭代中产生的不一致问题。本文档定义漂移类型、检测方法、修复流程和预防措施。

当前执行口径：

- 线上链路、服务器角色和运行时环境变量以 `docs/deployment/current-live-chain.md` 为准。
- 上线待办和验收状态以 `docs/deployment/production-launch-todo.md` 与 `docs/deployment/mvp-next-todo-2026-05-28.md` 为准。
- `docs/superpowers/plans/*`、`docs/superpowers/specs/*`、旧迁移清单和旧提示词只作历史追溯；执行前必须先核对上述 source-of-truth 文档。

---

## 一、漂移类型定义

### 1. 数据漂移

**定义**：原始数据（Markdown）→ 结构化数据（JSON）→ 数据库（PostgreSQL）之间的内容不一致。

**典型表现**：
- JSON 文件中模块内容为空（解析失败）
- 加权分为 0（关键结构化字段未提取）
- 数据库 province 列大面积为空（提取逻辑与数据格式不匹配）
- 数据集遗漏记录（如缺少某所大学）

**本项目的实际案例**：

| 问题 | 根因 | 影响 |
|------|------|------|
| 185/956 院校所有模块为空 | 源 Markdown 格式与解析器正则不匹配 | 19.4% 院校数据完全无效 |
| 772/773 专业缺 module6/module7 | 解析器未覆盖这两个模块的变体标题 | 99.7% 专业缺趣味卡片内容 |
| 879/956 院校 province 为空 | location 字段格式不规范，简单字符串匹配失效 | 92% 院校无省份筛选能力 |

### 2. Schema 漂移

**定义**：数据库 Schema 定义与实际数据结构不一致。

**典型表现**：
- Schema 中定义了列但从未填充
- JSON 字段名与 Schema 列名不匹配
- 约束检查函数引用了错误的数据类型（如对 JSON 对象调用数组方法）

**本项目的实际案例**：

| 问题 | 根因 |
|------|------|
| name_pinyin, city 等 5 列从未填充 | Schema 设计时预留但导入脚本未实现提取逻辑 |
| check_data_quality() 使用 jsonb_array_length() | layer3_detail 是 JSON 对象而非数组 |

### 3. 代码漂移

**定义**：代码中的硬编码值、配置默认值与实际部署环境不一致。

**典型表现**：
- 硬编码的服务器 IP/端口与实际不符
- 凭证明文写在源码中
- 代码默认值与 .env.example 文档不一致
- 代码引用的文件/服务不存在

**本项目的实际案例**：

| 问题 | 文件 |
|------|------|
| SCORE_API_URL 曾被误判为端口 5000/5001；当前 47 应使用 159 Nginx 路由 `http://159.75.110.157/score-api` | `lib/data-api.js:3` |
| 47 服务器 `.env` 仍可能残留 `DEEPSEEK_MODEL=deepseek-chat` 或 `MEMBERSHIP_PRICE_CENTS=100`，而代码和 example 已更新为 `deepseek-v4-pro` / `1990` | `/opt/gaokao-proxy/.env` vs `gaokao-proxy/.env.example` |
| CLAUDE.md 引用 `run_univ_eval.py` 但该脚本已归档 | `CLAUDE.md` |

### 4. 文件管理漂移

**定义**：项目文件结构随迭代累积的冗余、重复、孤立文件。

**典型表现**：
- 旧版本目录与新版本并存（v1 vs v2）
- 已废弃脚本未归档
- 临时文件未被 gitignore
- 重复功能的文件（如两个 Flask 应用）

**本项目的实际案例**：

| 问题 | 说明 |
|------|------|
| `data/*_json/` 与 `data/*_json_v2/` 并存 | v1 已被 v2 替代，占 7.3MB |
| 7 个已废弃脚本仍在 `data/` | `scripts_archive/` 已用于其他废弃脚本 |
| `gaokao-api/app.py` 与 `data/gaokao_api.py` 重复 | 前者未部署，实际用的是后者 |
| `tmp/`, `logs/` 未 gitignore | 测试产物可能被提交 |

---

## 二、检测方法

### 数据漂移检测

```bash
# 1. 文件数量对比（MD vs JSON vs DB）
echo "Major MD: $(ls data/专业评估报告/*.md | wc -l)"
echo "Major JSON: $(ls data/专业评估报告_json_v2/*.json | grep -v '^_' | wc -l)"
PG_PASSWORD=xxx python3 scripts/import_reports_to_pg.py --check-only

# 2. 空模块检测
python3 scripts/data_quality_check.py --check-empty-modules

# 3. 零分报告检测
python3 scripts/data_quality_check.py --check-zero-scores

# 4. 大学类型验证
python3 scripts/data_quality_check.py --check-univ-types
```

### Schema 漂移检测

```bash
# 1. 检查数据库中未填充的列
PG_PASSWORD=xxx python3 -c "
import psycopg2
conn = psycopg2.connect(...)
cursor = conn.cursor()
# 检查 province 列空值率
cursor.execute(\"SELECT COUNT(*) FROM universities WHERE province IS NULL OR province = ''\")
print(f'Empty province: {cursor.fetchone()[0]}/956')
"

# 2. 检查 JSON 约束是否生效
# 通过 check_data_quality() 函数
```

### 代码漂移检测

```bash
# 1. 硬编码凭证扫描
grep -rn "|| ['\"]" gaokao-proxy/lib/ --include="*.js" | grep -v node_modules
grep -rn "password.*=" data/gaokao_api.py

# 2. CLAUDE.md 脚本存在性检查
grep -oE '[a-z_]+\.py' CLAUDE.md | sort -u | while read f; do
  [ ! -f "$f" ] && [ ! -f "scripts/$f" ] && [ ! -f "data/$f" ] && echo "MISSING: $f"
done

# 3. 环境变量一致性检查
# 对比 .env.example 中的变量与代码中实际使用的变量
grep -roh "process\.env\.\w*" gaokao-proxy/ --include="*.js" | sort -u > /tmp/code_envs.txt
grep -oE '^[A-Z_]+' gaokao-proxy/.env.example | sort -u > /tmp/example_envs.txt
comm -23 /tmp/code_envs.txt /tmp/example_envs.txt  # 代码中有但 example 中没有
```

### 文件管理漂移检测

```bash
# 1. 查找旧版本目录
ls -d data/*_json/ 2>/dev/null  # 如果 _json_v2/ 存在，这些是旧版

# 2. 查找根目录无文档脚本
ls *.py | while read f; do grep -q "$f" CLAUDE.md || echo "Undocumented: $f"; done

# 3. 查找未 gitignore 的临时目录
git status --short | grep -E "^?.*tmp/|^?.*logs/|^?.*test_json/"
```

---

## 三、修复流程

### 通用修复步骤

```
1. 检测 → 用上述命令发现漂移
2. 分类 → 确定是哪类漂移
3. 定位 → 找到根因（解析器正则？提取逻辑？硬编码？）
4. 修复 → 修改代码/数据/文档
5. 验证 → 重新运行检测，确认修复效果
6. 记录 → 在 CLAUDE.md 或本文档中记录变更
```

### 数据漂移修复流程

```
发现空模块/零分
  → 定位源 Markdown 文件
    → 检查源文件格式是否符合解析器预期
      → 是：修复解析器正则 → 重新生成 JSON → 重新导入 DB
      → 否（源文件确实缺失内容）：重新运行评估脚本生成源文件
```

### Schema 漂移修复流程

```
发现 Schema 列未填充
  → 评估：该列是否真正需要？
    → 是：在导入脚本中实现提取逻辑 → 重新导入
    → 否：从 Schema 中移除该列（或标注为"预留"）
```

### 代码漂移修复流程

```
发现硬编码或不一致
  → 将硬编码值改为环境变量
    → 更新 .env.example
      → 更新 CLAUDE.md
        → 在本地和服务器上验证
```

### 文件管理漂移修复流程

```
发现冗余文件
  → 确认是否真的不再需要
    → 是：移动到 scripts_archive/（保留历史）或删除（测试产物）
    → 不确定：添加 README 说明文件用途
```

---

## 四、预防措施

### 开发流程

1. **每次新增脚本**：同步更新 CLAUDE.md 关键脚本章节和 Python 依赖表
2. **每次新增 API 端点**：更新 CLAUDE.md 技术架构章节
3. **每次修改数据格式**：检查解析器、导入脚本、数据库 Schema 三者一致性
4. **每次部署变更**：更新 CLAUDE.md 的服务器连接和线上接口状态

### 代码规范

1. **禁止凭证硬编码**：所有凭证通过环境变量传入，不设明文默认值
2. **环境变量双保险**：每个新 env var 必须同步到 `.env.example` 和代码注释
3. **文件命名版本化**：新版本文件用 `_v2` 后缀，旧版归档到 `scripts_archive/`

### 定期检查

1. **每次大版本发布前**：运行 `scripts/data_quality_check.py --all`
2. **每月一次**：运行本文档"检测方法"章节的所有命令
3. **每次导入数据后**：运行 `python3 scripts/import_reports_to_pg.py --check-only`

---

## 五、检测脚本索引

| 脚本 | 用途 | 运行方式 |
|------|------|---------|
| `scripts/data_quality_check.py` | 全面数据质量检查 | `python3 scripts/data_quality_check.py --all` |
| `scripts/import_reports_to_pg.py --check-only` | 数据库层级完整性检查 | 需要 PG_PASSWORD |
| `scripts/test_report_api.sh` | API 端点功能测试 | `bash scripts/test_report_api.sh <URL>` |
| `check_reports.py` | Markdown 报告模块完整性 | `python3 check_reports.py` |
