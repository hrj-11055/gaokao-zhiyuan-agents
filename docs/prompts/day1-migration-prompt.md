# Day 1 综合提示词

> 用途：复制此提示词给 Claude Code，指导完成新服务器迁移 + Dify 验证 + 100 题测试框架搭建
> 前置条件：已购买新 8C16G 服务器，已配置 SSH 密钥登录

---

## 综合提示词（直接复制使用）

```
我需要你帮我完成高考志愿填报项目的服务器迁移和 Dify 验证工作。这是一个完整的 Day 1 任务，请严格按以下步骤执行，每一步验证通过后再进入下一步。

## 背景信息

- 老服务器：8.135.37.159（2C4G，阿里云），已配 SSH 密钥登录
- 新服务器：<填入新服务器 IP>（8C16G），已配 SSH 密钥登录
- Dify 版本：v1.13.3，必须保持不变
- 项目代码在本地：/Users/MarkHuang/Desktop/高考志愿填报项目/
- gaokao-proxy 代码在：/Users/MarkHuang/Desktop/高考志愿填报项目/gaokao-proxy/
- 只迁移志愿填报相关服务（Dify + gaokao-api + gaokao-proxy），其他项目不要动

## Step 1：新服务器基础环境

SSH 到新服务器，安装以下环境：

1. Docker + Docker Compose
2. Node.js 18+（用于 gaokao-proxy）
3. PM2（进程守护）
4. Python 3 + pip（用于脚本）
5. Nginx（反向代理）
6. git, htop, curl

验证：docker --version, node --version, pm2 --version 都有输出。

## Step 2：Dify 数据迁移

### 2.1 老机器打包

SSH 到 8.135.37.159，执行：
```bash
cd /opt/dify/docker
tar czf /tmp/dify-backup.tar.gz docker-compose.yaml docker-compose.middleware.yaml .env volumes/
ls -lh /tmp/dify-backup.tar.gz
```

### 2.2 传到新机器

用 scp 把 /tmp/dify-backup.tar.gz 从老机器传到新机器 /tmp/。

### 2.3 新机器解压启动

SSH 到新服务器：
```bash
mkdir -p /opt/dify/docker
cd /opt/dify/docker
tar xzf /tmp/dify-backup.tar.gz
docker compose up -d
```

等待所有容器启动（约 2-3 分钟），然后检查：
```bash
docker compose ps
```

预期看到 11 个容器全部 running/healthy：api, web, worker, worker_beat, db_postgres, redis, nginx, sandbox, plugin_daemon, pgvector, ssrf_proxy。

## Step 3：Dify 完整性验证

这一步非常关键，必须逐一验证以下所有项目。

### 3.1 控制台访问

curl http://<新IP>:8080 确认返回 HTML 页面。尝试登录（用老机器相同的账号密码）。

### 3.2 应用验证

通过 Dify API 检查所有应用是否迁移成功：
```bash
# 用 .env 中的 API key 或在控制台手动查看
# 预期看到 6 个应用：
# - 张雪峰高考志愿填报助手（advanced-chat）← 最重要
# - Jina Reader 总结网站内容（workflow）
# - 123（advanced-chat）
# - 文润 · 妙笔生花（workflow）
# - 判断是否需要消费（workflow）
# - 文件翻译（advanced-chat）
```

### 3.3 知识库验证

检查 6 个知识库是否完整：

| 知识库 | 检查方式 |
|--------|---------|
| KB-1 张雪峰语料库 | 在控制台查看文件数 |
| KB-2 录取分数线 | 应有 31 个省份文件 |
| KB-3 专业百科 | 数量应与老机器一致 |
| KB-4 院校研究 | 检查文件数 |
| KB-5 就业数据 | 检查文件数 |
| KB-6 张雪峰金句 | 应有 1 个文件 |

### 3.4 插件验证

在 Dify 控制台的「张雪峰高考志愿填报助手」应用中：
- 检查插件列表中是否有 deepseek 和 zhipuai
- 测试发送一条消息：「你好」，确认能正常回复

### 3.5 对话质量验证

在 Dify 控制台与「张雪峰助手」对话，逐一测试以下 5 个问题，记录回复质量：

1. 「广东物理类 600 分能上什么学校？」→ 应调用知识库返回具体院校
2. 「计算机科学与技术专业怎么样？」→ 应返回专业详情
3. 「女生适合学什么专业？」→ 应有张雪峰风格建议
4. 「2024 年广东一本线多少分？」→ 应返回真实分数线数据
5. 「我想学法学，但家人让我学金融，怎么办？」→ 应有追问和建议

每个回复检查：
- 是否编造了数据（准确性一票否决）
- 是否有具体的院校/专业推荐
- 是否有张雪峰风格（直白务实）
- 回复是否完整（没有中途截断）

如果以上任何一项验证失败，立即停止并报告问题。不要继续下一步。

## Step 4：gaokao-api 部署

### 4.1 部署代码

将本地 /Users/MarkHuang/Desktop/高考志愿填报项目/opt/gaokao/ 的代码部署到新服务器 /opt/gaokao/。

### 4.2 数据库

gaokao-api 依赖 PostgreSQL 中的分数线数据。有两种方式：

方式 A：连接 Dify 自带的 PostgreSQL（推荐，减少运维）
```bash
# 在新服务器上，gaokao-api 加入 Dify 的 Docker 网络
# DATABASE_URL 指向 docker-db_postgres-1
```

方式 B：独立 PostgreSQL 容器

选择方式 A 优先尝试。

### 4.3 导入分数数据

从老机器导出分数数据并导入新机器：
```bash
# 老机器导出
ssh root@8.135.37.159 "docker exec docker-db_postgres-1 pg_dump -U postgres dify" > /tmp/dify_dump.sql

# 新机器导入
cat /tmp/dify_dump.sql | ssh root@<新IP> "docker exec -i docker-db_postgres-1 psql -U postgres dify"
```

### 4.4 启动 gaokao-api

```bash
cd /opt/gaokao
docker build -t gaokao-api .
docker run -d --name gaokao-api \
  -p 5001:5000 \
  --network dify_default \
  gaokao-api
```

### 4.5 验证

```bash
curl http://<新IP>:5001/api/health  # → 200
curl "http://<新IP>:5001/api/recommend?province=广东&score=600&category=物理类&year=2024&limit=3"
curl "http://<新IP>:5001/api/stats"
```

## Step 5：gaokao-proxy 部署

### 5.1 部署代码

将 gaokao-proxy 代码部署到新服务器 /opt/gaokao-proxy/：
```bash
# 方式 1：从本地 scp
scp -r /Users/MarkHuang/Desktop/高考志愿填报项目/gaokao-proxy/ root@<新IP>:/opt/gaokao-proxy/

# 方式 2：从 GitHub 拉取
```

### 5.2 配置

```bash
cd /opt/gaokao-proxy
npm install
cp .env.example .env
```

编辑 .env：
```
DIFY_API_URL=http://docker-api-1:5001/v1
DIFY_API_KEY=<从老机器 Dify 控制台复制>
PORT=3001
STREAM_TIMEOUT_MS=120000
PROXY_API_TOKEN=<设置一个 token>
```

**注意**：DIFY_API_URL 要用 Docker 内网地址（docker-api-1），因为 proxy 和 Dify 在同一台机器上。但 proxy 不在 Docker 里，所以需要确认：
- 如果 gaokao-proxy 用 PM2 运行（非 Docker），DIFY_API_URL 应该是 http://127.0.0.1:5001（Dify API 容器映射的端口）或 http://<docker-network-ip>:5001
- 验证方法：先 curl http://127.0.0.1:5001/v1 parameters 看是否通

### 5.3 启动

```bash
pm2 start server.js --name gaokao-proxy
pm2 save
pm2 startup
```

### 5.4 验证

```bash
# 健康检查
curl http://localhost:3001/api/health

# SSE 流式测试
curl -N -X POST http://localhost:3001/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query":"广东物理类600分能上什么学校","user":"test-user-001"}'

# 阻塞式测试
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"计算机专业怎么样","user":"test-user-001"}'
```

两个接口都应该返回正常内容。

## Step 6：小程序端到端测试

1. 修改本地 `gaokao-miniprogram/.env`，将 VITE_API_BASE 改为新服务器地址：
   ```
   VITE_API_BASE=http://<新IP>:3001
   ```

2. 编译：
   ```bash
   cd gaokao-miniprogram && npm run dev:mp-weixin
   ```

3. 微信开发者工具导入 dist/dev/mp-weixin 目录

4. 测试清单：
   - [ ] 首页加载正常（品牌展示 + 免费咨询入口）
   - [ ] 点击「免费咨询」进入对话页
   - [ ] 发送消息，SSE 流式回复正常（逐字显示）
   - [ ] 点击 QuickQuestions（如「广东600分能上什么学校」），回复正常
   - [ ] 发送关于专业的问题，知识库检索有效
   - [ ] 退出重进，历史记录保留
   - [ ] 真机调试（非模拟器）确认以上全部正常

## Step 7：100 题测试框架搭建

### 7.1 测试集设计

基于以下 8 个意图类别，每类 12-13 题，共 100 题：

| # | 意图类别 | 题数 | 示例 |
|---|---------|------|------|
| 1 | 分数线查询 | 13 | 「2024 年广东物理类本科线多少分？」 |
| 2 | 院校推荐 | 13 | 「广东 580 分理科能上什么大学？」 |
| 3 | 专业咨询 | 13 | 「人工智能专业学什么？就业怎么样？」 |
| 4 | 志愿填报策略 | 12 | 「冲稳保怎么分配比例？」 |
| 5 | 选科指导 | 12 | 「想学医必须选化学吗？」 |
| 6 | 跨省对比 | 12 | 「广东和浙江的 985 录取率差多少？」 |
| 7 | 张雪峰风格问答 | 13 | 「女生学计算机好吗？」（测试风格一致性） |
| 8 | 边界/刁钻问题 | 12 | 「我考了 0 分怎么办？」（测试鲁棒性） |

请帮我生成这 100 题的完整列表，保存到 `data/test-runs/100q-test-set.md`。

### 7.2 质量评估方法

每个回复按以下 4 维度打分（满分 5 分）：

**准确性（40%，一票否决）**
- 5 分：所有数据（分数线、院校名、专业名）准确无误
- 4 分：个别非关键数据有微小偏差，但不影响决策
- 3 分：有 1-2 处数据错误，可能误导用户
- ≤2 分：编造数据 → 直接记为不合格
- **一票否决规则：编造不存在的院校/专业/分数线，整体直接判 0 分**

**实用性（30%）**
- 5 分：给出了具体可操作的建议（如具体院校名、专业名、填报策略）
- 4 分：建议较具体，但缺少部分细节
- 3 分：建议笼统，缺乏可操作性
- ≤2 分：没有实质建议

**风格一致性（20%）**
- 5 分：典型的张雪峰风格（直白、务实、有态度、接地气）
- 4 分：整体风格接近，偶尔偏正式
- 3 分：风格不明显，像普通 AI 助手
- ≤2 分：完全不像张雪峰

**追问能力（10%）**
- 5 分：主动追问关键信息（省份、分数、选科、家庭情况）
- 4 分：追问了部分信息
- 3 分：简单追问
- ≤2 分：不追问直接给建议

**合格线：加权总分 ≥ 4.0 分（满分 5 分）**

### 7.3 评分流程

1. 用 Dify API 逐条发送 100 题（通过 `run_test_20q.py` 的扩展版）
2. 每条回复由 LLM（Claude/Gemini）自动初评 4 维度分数
3. 自动初评后，我人工抽查 20 题（每类 2-3 题）校准
4. 输出：
   - `data/test-runs/100q-results.md` — 逐题评分明细
   - `data/test-runs/100q-summary.md` — 按类别的汇总统计

### 7.4 自动化脚本

请帮我编写 `data/run_test_100q.py`，功能：
- 读取 `data/test-runs/100q-test-set.md` 中的 100 题
- 逐题调用 Dify API（通过 gaokao-proxy 的 /api/chat 接口，阻塞模式）
- 每题间隔 3 秒（避免限流）
- 记录每题的 question、answer、耗时
- 保存到 `data/test-runs/100q-raw-results.json`

然后编写 `data/eval_100q.py`，功能：
- 读取 raw results
- 用 Claude API（或 Gemini API）对每条回复自动评分（4 维度）
- 输出评分明细和汇总统计
- 标记编造数据的回复（一票否决）

## 重要约束

1. **每一步验证通过再进入下一步**。如果验证失败，停下来分析原因，不要跳过。
2. **SSH 命令都要通过 `ssh root@<IP> "command"` 方式执行**，不要让我手动登录。
3. **新服务器上的关键路径**：Dify 在 /opt/dify/docker/，gaokao-api 在 /opt/gaokao/，gaokao-proxy 在 /opt/gaokao-proxy/。
4. **老机器不要动**，直到新机器全部验证通过。
5. **遇到问题先排查再问我**，不要直接跳过或猜。

## 最终验收标准

Day 1 完成的标志：
- [ ] 新服务器 Dify 控制台可访问，6 个应用全部正常
- [ ] 知识库 6 个 KB 完整，文件数与老机器一致
- [ ] Dify 对话测试 5 题全部通过（无编造、有数据、有风格）
- [ ] gaokao-api /api/health 返回 200，/api/recommend 返回正常
- [ ] gaokao-proxy SSE 流式接口返回正常
- [ ] 小程序真机对话流程跑通
- [ ] 100 题测试集已生成
- [ ] 自动化测试脚本 `run_test_100q.py` 已编写
```

---

## 使用方法

1. 把 `<填入新服务器 IP>` 替换为实际 IP
2. 把 `<从老机器 Dify 控制台复制>` 替换为实际的 Dify API Key
3. 复制整个代码块内容，粘贴到 Claude Code 会话中
4. Claude Code 会按步骤执行，每步验证后继续

## 注意事项

- 这个提示词涵盖了 Day 1 的全部核心工作
- 100 题测试集的自动跑批可能需要 1-2 小时（3s 间隔 × 100 题 ≈ 5 分钟纯等待 + API 响应时间）
- 评分脚本需要 Claude API 或 Gemini API 的 Key
- 如果新服务器 IP 还没拿到，可以先做 Step 7（测试框架是本地文件，不依赖服务器）
