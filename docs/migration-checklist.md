# Dify 迁移清单（Day 1）

> 目标：从老服务器 8.135.37.159（2C4G）迁移到新服务器 8C16G
> 原则：保持 Dify v1.13.3 不变，只迁志愿填报相关服务

---

## Phase 0：新服务器准备

- [ ] 购买 8C16G 云服务器（推荐同区域，降低迁移带宽成本）
- [ ] 配置安全组：开放 22（SSH）、80（HTTP）、443（HTTPS）、3001（gaokao-proxy 临时）、5001（gaokao-api 临时）、8080（Dify 控制台）
- [ ] SSH 密钥登录配置
- [ ] 基础环境安装：
  ```bash
  # Docker
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker && systemctl start docker

  # Docker Compose（如未随 Docker 安装）
  apt install docker-compose-plugin  # 或 docker-compose

  # Node.js 18+
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
  apt install -y nodejs

  # PM2
  npm install -g pm2

  # Python 3 + pip
  apt install -y python3 python3-pip

  # Nginx
  apt install -y nginx

  # 常用工具
  apt install -y git htop curl wget
  ```

---

## Phase 1：Dify 数据迁移

### 1.1 老机器上打包

```bash
# SSH 到老机器
ssh root@8.135.37.159

# 打包 Dify 全部数据（docker-compose + volumes + .env）
cd /opt/dify/docker
tar czf /tmp/dify-backup.tar.gz \
  docker-compose.yaml \
  docker-compose.middleware.yaml \
  .env \
  volumes/

# 查看包大小（预计 ~1.1GB）
ls -lh /tmp/dify-backup.tar.gz
```

### 1.2 传输到新服务器

```bash
# 从老机器直接传到新服务器
scp /tmp/dify-backup.tar.gz root@<NEW_SERVER_IP>:/tmp/

# 或者在本地中转
scp root@8.135.37.159:/tmp/dify-backup.tar.gz /tmp/
scp /tmp/dify-backup.tar.gz root@<NEW_SERVER_IP>:/tmp/
```

### 1.3 新服务器上解压启动

```bash
# SSH 到新服务器
ssh root@<NEW_SERVER_IP>

# 解压
mkdir -p /opt/dify/docker
cd /opt/dify/docker
tar xzf /tmp/dify-backup.tar.gz

# 启动 Dify
docker compose up -d

# 检查所有容器状态
docker compose ps
# 预期：api, web, worker, worker_beat, db_postgres, redis, nginx, sandbox, plugin_daemon, pgvector 全部 running/healthy
```

### 1.4 验证清单

- [ ] Dify 控制台可访问：`http://<NEW_IP>:8080`
- [ ] 登录正常（用老机器的账号密码）
- [ ] 6 个应用全部可见：
  - 张雪峰高考志愿填报助手（advanced-chat）← 最重要
  - Jina Reader 总结网站内容（workflow）
  - 123（advanced-chat）
  - 文润 · 妙笔生花（workflow）
  - 判断是否需要消费（workflow）
  - 文件翻译（advanced-chat）
- [ ] 知识库完整（6 个 KB 全部可见，文件数一致）
  - KB-1 张雪峰语料库
  - KB-2 录取分数线（31 省份）
  - KB-3 专业百科
  - KB-4 院校研究
  - KB-5 就业数据
  - KB-6 张雪峰金句
- [ ] 插件正常：deepseek、zhipuai 可调用
- [ ] 对话测试：在 Dify 控制台与「张雪峰助手」对话，验证：
  - 能正常回复
  - 知识库检索有效（问分数线、专业相关问题）
  - SSE 流式输出正常

---

## Phase 2：gaokao-api 迁移

### 2.1 迁移 PostgreSQL 分数数据

```bash
# 老机器：导出 scores 数据库
ssh root@8.135.37.159
docker exec docker-db_postgres-1 pg_dump -U postgres dify > /tmp/dify_db_dump.sql
# 如果分数数据在独立库中：
docker exec docker-db_postgres-1 psql -U postgres -c "\l"  # 查看所有数据库

# 传输到新服务器
scp /tmp/dify_db_dump.sql root@<NEW_SERVER_IP>:/tmp/
```

### 2.2 部署 gaokao-api

```bash
# 新服务器
mkdir -p /opt/gaokao
# 从本地或 Git 拉取代码

# 启动 gaokao-api Docker 容器
# （使用老机器上相同的 Dockerfile 和配置）
cd /opt/gaokao
docker build -t gaokao-api .
docker run -d --name gaokao-api \
  -p 5001:5000 \
  --network dify_default \
  -e DATABASE_URL=postgresql://postgres:...@db_postgres:5432/dify \
  gaokao-api
```

### 2.3 验证

- [ ] `curl http://<NEW_IP>:5001/api/health` → 200
- [ ] `curl "http://<NEW_IP>:5001/api/recommend?province=广东&score=600&category=物理类&year=2024&limit=3"` → 返回院校列表
- [ ] `curl "http://<NEW_IP>:5001/api/stats"` → 数据统计

---

## Phase 3：gaokao-proxy 部署

```bash
# 新服务器
cd /opt
git clone <你的 gaokao-proxy 仓库> gaokao-proxy
cd gaokao-proxy
npm install

# 配置 .env
cp .env.example .env
# 编辑 .env：
#   DIFY_API_URL=http://docker-api-1:5001/v1  （Docker 内网）
#   DIFY_API_KEY=app-xxxxxxxx
#   PORT=3001
#   STREAM_TIMEOUT_MS=120000
#   PROXY_API_TOKEN=你的token

# PM2 启动
pm2 start server.js --name gaokao-proxy
pm2 save
pm2 startup
```

### 验证

- [ ] `curl http://localhost:3001/api/health` → 200
- [ ] `curl -X POST http://localhost:3001/api/chat/stream -H "Content-Type: application/json" -d '{"query":"广东600分能上什么学校","user":"test"}'` → SSE 流式响应

---

## Phase 4：Nginx 配置（可选，先用 IP 直连测试）

```nginx
# /etc/nginx/sites-available/gaokao
server {
    listen 80;
    server_name <NEW_IP>;

    # Dify 控制台
    location /console/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
    }

    # gaokao-proxy
    location /api/ {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
        proxy_buffering off;  # SSE 必须
    }
}
```

---

## Phase 5：小程序连接测试

1. 修改本地 `gaokao-miniprogram/.env`：
   ```
   VITE_API_BASE=http://<NEW_SERVER_IP>:3001
   ```
2. `npm run dev:mp-weixin`
3. 微信开发者工具真机调试
4. 测试点：
   - [ ] 首页加载正常
   - [ ] 进入对话页，发送消息，SSE 流式回复正常
   - [ ] QuickQuestions 点击正常
   - [ ] 历史记录保存/读取正常
   - [ ] 知识库检索有效（问具体分数线/专业问题）

---

## Phase 6：清理老机器

**确认新服务器全部正常后再执行！**

- [ ] 老机器停止 Dify：`cd /opt/dify/docker && docker compose down`
- [ ] 释放老机器（退订/释放）
- [ ] 更新 CLAUDE.md 中的服务器 IP

---

## 关键数据清单（必须迁移的内容）

| 数据 | 位置 | 大小 | 重要性 |
|------|------|------|--------|
| Dify volumes | `/opt/dify/docker/volumes/` | ~1.1GB | 核心 |
| docker-compose.yaml | `/opt/dify/docker/` | <1MB | 核心 |
| .env | `/opt/dify/docker/.env` | <1KB | 核心 |
| gaokao-api 代码 | `/opt/gaokao/` | ~5MB | 重要 |
| PostgreSQL 数据 | Docker volume 内 | ~217MB | 核心 |
