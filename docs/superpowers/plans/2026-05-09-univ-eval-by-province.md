# 全国大学深度评估 — 按省份执行计划

> **For agentic workers:** 本计划为操作执行计划，不是代码实现计划。使用 `run_univ_eval_gemini.py` 脚本按省份批量跑 Gemini 评估。

**Goal:** 完成全国 29 个剩余省份共 ~1206 所本科院校的深度评估报告

**Architecture:** 使用现有 `run_univ_eval_gemini.py` 脚本，Gemini 3 Flash + Google Search，每所大学生成 9 模块 Markdown 报告 + JSON 数据文件

**Tech Stack:** Gemini API (`google-genai`), 提示词模板 v2, 5s 调用间隔

---

## 当前状态

| 指标 | 数据 |
|------|------|
| 已完成省份 | 广东（77 所）、江苏（82 所） |
| 已完成总数 | 159 / 1365（11.6%） |
| 待跑总数 | ~1206 所，29 个省份 |
| 报告目录 | `data/大学评估报告/` |

---

## 执行前准备（5 分钟）

### 1. 确认提示词版本

当前脚本使用 `跑大学提示词-v2.txt`。已有 v3（精简版，去掉搜索策略指引）和 v4（极简版，仅 47 行）。

**建议继续用 v2**。理由：
- v2 的搜索策略指引（7 组搜索）对 Gemini Search 更有引导性
- v2 的输出格式更严格，质检模块 `REQUIRED_MODULES` 与之匹配
- 广东、江苏已用 v2 跑完，保持一致性便于横向比较

### 2. 确认环境

```bash
# 确认 API Key 已设置
echo $GEMINI_API_KEY

# 确认依赖已安装
pip3 install google-genai

# 确认当前进度
python3 run_univ_eval_gemini.py --status
```

### 3. 可选：切换模型

当前默认 `gemini-3-flash-preview`。如需切换：

```bash
export GEMINI_MODEL="gemini-2.5-flash-preview-05-20"  # 如有更新模型
```

---

## 省份执行顺序

### 策略

1. **公办优先**：先跑 `--public-only`，民办大学对志愿填报价值较低，可后补
2. **教育大省先跑**：北京、上海、湖北、陕西等高校集中的省份优先
3. **志愿填报热点省份先跑**：山东、河南、河北、四川等考生大省

### 分批计划

#### 第一批：教育核心省份（6 省，~241 所公办）

这些省份集中了最多 985/211 高校，是志愿填报咨询的高频查询对象。

| 序号 | 省份 | 公办/总计 | 执行命令 | 预估时间 |
|------|------|----------|---------|---------|
| 1 | 北京市 | 63/69 | `python3 run_univ_eval_gemini.py 北京市 --public-only` | ~2.5h |
| 2 | 湖北省 | 37/70 | `python3 run_univ_eval_gemini.py 湖北省 --public-only` | ~1.5h |
| 3 | 陕西省 | 38/61 | `python3 run_univ_eval_gemini.py 陕西省 --public-only` | ~1.5h |
| 4 | 上海市 | 31/40 | `python3 run_univ_eval_gemini.py 上海市 --public-only` | ~1.2h |
| 5 | 湖南省 | 33/54 | `python3 run_univ_eval_gemini.py 湖南省 --public-only` | ~1.3h |
| 6 | 四川省 | 37/55 | `python3 run_univ_eval_gemini.py 四川省 --public-only` | ~1.5h |

**第一批小计**：~239 所公办，预估 ~9.5 小时

#### 第二批：考生大省（6 省，~229 所公办）

考生多、咨询需求大的省份。

| 序号 | 省份 | 公办/总计 | 执行命令 | 预估时间 |
|------|------|----------|---------|---------|
| 7 | 山东省 | 47/72 | `python3 run_univ_eval_gemini.py 山东省 --public-only` | ~1.9h |
| 8 | 河南省 | 40/62 | `python3 run_univ_eval_gemini.py 河南省 --public-only` | ~1.6h |
| 9 | 河北省 | 42/63 | `python3 run_univ_eval_gemini.py 河北省 --public-only` | ~1.7h |
| 10 | 浙江省 | 42/65 | `python3 run_univ_eval_gemini.py 浙江省 --public-only` | ~1.7h |
| 11 | 安徽省 | 36/50 | `python3 run_univ_eval_gemini.py 安徽省 --public-only` | ~1.4h |
| 12 | 辽宁省 | 42/64 | `python3 run_univ_eval_gemini.py 辽宁省 --public-only` | ~1.7h |

**第二批小计**：~249 所公办，预估 ~10 小时

#### 第三批：中部及西南省份（8 省，~190 所公办）

| 序号 | 省份 | 公办/总计 | 执行命令 | 预估时间 |
|------|------|----------|---------|---------|
| 13 | 江西省 | 30/49 | `python3 run_univ_eval_gemini.py 江西省 --public-only` | ~1.2h |
| 14 | 山西省 | 29/36 | `python3 run_univ_eval_gemini.py 山西省 --public-only` | ~1.2h |
| 15 | 福建省 | 24/41 | `python3 run_univ_eval_gemini.py 福建省 --public-only` | ~1.0h |
| 16 | 广西 | 29/41 | `python3 run_univ_eval_gemini.py 广西 --public-only` | ~1.2h |
| 17 | 云南省 | 26/35 | `python3 run_univ_eval_gemini.py 云南省 --public-only` | ~1.0h |
| 18 | 贵州省 | 24/32 | `python3 run_univ_eval_gemini.py 贵州省 --public-only` | ~1.0h |
| 19 | 吉林省 | 28/40 | `python3 run_univ_eval_gemini.py 吉林省 --public-only` | ~1.1h |
| 20 | 黑龙江省 | 28/40 | `python3 run_univ_eval_gemini.py 黑龙江省 --public-only` | ~1.1h |

**第三批小计**：~218 所公办，预估 ~8.8 小时

#### 第四批：其余省份（7 省，~113 所公办）

| 序号 | 省份 | 公办/总计 | 执行命令 | 预估时间 |
|------|------|----------|---------|---------|
| 21 | 天津市 | 20/31 | `python3 run_univ_eval_gemini.py 天津市 --public-only` | ~0.8h |
| 22 | 重庆市 | 20/29 | `python3 run_univ_eval_gemini.py 重庆市 --public-only` | ~0.8h |
| 23 | 甘肃省 | 25/28 | `python3 run_univ_eval_gemini.py 甘肃省 --public-only` | ~1.0h |
| 24 | 内蒙古 | 19/21 | `python3 run_univ_eval_gemini.py 内蒙古 --public-only` | ~0.8h |
| 25 | 新疆 | 23/26 | `python3 run_univ_eval_gemini.py 新疆 --public-only` | ~0.9h |
| 26 | 海南省 | 8/11 | `python3 run_univ_eval_gemini.py 海南省 --public-only` | ~0.3h |
| 27 | 宁夏 | 6/10 | `python3 run_univ_eval_gemini.py 宁夏 --public-only` | ~0.2h |
| 28 | 西藏 | 5/5 | `python3 run_univ_eval_gemini.py 西藏 --public-only` | ~0.2h |
| 29 | 青海省 | 5/6 | `python3 run_univ_eval_gemini.py 青海省 --public-only` | ~0.2h |

**第四批小计**：~131 所公办，预估 ~5.2 小时

#### 第五批（可选）：补齐民办

跑完公办后，根据需要决定是否补齐民办院校。民办数量大（~350 所），优先级低。

```bash
# 逐省补齐民办（去掉 --public-only 即跑全部）
python3 run_univ_eval_gemini.py 北京市  # 会跳过已完成的公办
```

---

## 总量预估

| 类别 | 数量 | 预估总时间 |
|------|------|-----------|
| 公办（29 省剩余） | ~837 所 | ~33 小时 |
| 民办（全部省份） | ~368 所 | ~15 小时 |
| **合计** | **~1205 所** | **~48 小时** |

> 注意：这里的"时间"是挂钟时间（含 API 调用等待），不是需要人盯着的时间。脚本全自动运行，每个省份跑完会有汇总输出。

---

## 执行操作指南

### 每个省份的标准操作

```bash
# 1. 跑公办（推荐）
python3 run_univ_eval_gemini.py <省份> --public-only

# 2. 如果有失败，重跑
python3 run_univ_eval_gemini.py <省份> --public-only --retry

# 3. 查看进度
python3 run_univ_eval_gemini.py --status
```

### 后台运行（推荐）

由于每个省份要跑 1-3 小时，建议用 `nohup` 或 `tmux` 后台运行：

```bash
# 方式一：nohup
nohup python3 run_univ_eval_gemini.py 北京市 --public-only > logs/北京.log 2>&1 &

# 方式二：tmux（可随时查看输出）
tmux new -s univ
python3 run_univ_eval_gemini.py 北京市 --public-only
# Ctrl+B, D 分离
# tmux attach -t univ 重新连接
```

### 连续跑多个省份

脚本不支持 `--all` 参数，但可以用 shell 循环：

```bash
# 第一批：教育核心省份（公办）
for province in "北京市" "湖北省" "陕西省" "上海市" "湖南省" "四川省"; do
  echo "=== 开始跑 $province ==="
  python3 run_univ_eval_gemini.py "$province" --public-only
  echo "=== $province 完成 ==="
  sleep 10
done

# 第二批：考生大省
for province in "山东省" "河南省" "河北省" "浙江省" "安徽省" "辽宁省"; do
  echo "=== 开始跑 $province ==="
  python3 run_univ_eval_gemini.py "$province" --public-only
  echo "=== $province 完成 ==="
  sleep 10
done

# 第三批：中部及西南
for province in "江西省" "山西省" "福建省" "广西壮族自治区" "云南省" "贵州省" "吉林省" "黑龙江省"; do
  echo "=== 开始跑 $province ==="
  python3 run_univ_eval_gemini.py "$province" --public-only
  echo "=== $province 完成 ==="
  sleep 10
done

# 第四批：其余省份
for province in "天津市" "重庆市" "甘肃省" "内蒙古自治区" "新疆维吾尔自治区" "海南省" "宁夏回族自治区" "西藏自治区" "青海省"; do
  echo "=== 开始跑 $province ==="
  python3 run_univ_eval_gemini.py "$province" --public-only
  echo "=== $province 完成 ==="
  sleep 10
done
```

---

## 质量控制

### 自动质检（已内置）

脚本内置 3 层质量控制：
1. **模块完整性检查**：9 个模块必须全部出现
2. **字数检查**：中文正文 ≥ 3000 字
3. **自动扩写修复**：质检失败时自动重试 1 次（`GEMINI_QUALITY_RETRIES=1`）

### 跑完后统一质检

```bash
# 批量质检所有报告
python3 check_reports.py  # 检查 data/大学评估报告/（如支持）
```

### 失败报告归档

质检未通过的报告自动移至 `data/大学评估报告/_failed_gemini/`，可用 `--retry` 重跑。

---

## 费用估算

| 模型 | 输出 Token | 单价（约） | 每所大学 | 1205 所总计 |
|------|-----------|-----------|---------|-----------|
| Gemini 3 Flash + Search | ~30K tokens | ~$0.02 | ~$0.03 | ~$36 |
| 含自动修复（~20% 触发） | +6K tokens | — | +$0.005 | +$6 |
| **合计** | — | — | **~$0.035** | **~$42** |

> Gemini Flash 价格低廉，Search 无额外费用。总费用预计 $40-50。

---

## 注意事项

1. **API 限流**：Gemini 免费层有 RPM 限制。如遇 429 错误，增大 `DELAY_SECONDS`：
   ```bash
   # 修改脚本中 DELAY_SECONDS = 5 为更大值，或用环境变量
   ```
2. **断点续跑**：脚本支持断点续跑。每个省份有独立进度文件 `_progress_gemini_{省份}.json`，中断后重新运行同一命令即可跳过已完成的。
3. **磁盘空间**：每份报告约 10-20KB Markdown + JSON，1205 所约 15-25MB，无压力。
4. **网络**：需稳定网络访问 Gemini API。如在国内服务器跑，需确认能访问 `generativelanguage.googleapis.com`。

---

## 脚本可能的优化（可选，非必须）

如需要，可以做以下改进，但不影响当前执行：

1. **添加 `--all` 参数**：一次性按优先级顺序跑所有剩余省份
2. **环境变量控制 DELAY_SECONDS**：目前硬编码为 5s，改为 `os.environ.get()` 可调
3. **切换提示词到 v3**：更精简，节省 Token（但需更新 `REQUIRED_MODULES` 匹配）
