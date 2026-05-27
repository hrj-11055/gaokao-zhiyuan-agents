# 本地开发到服务器迁移规范

更新时间：2026-05-26

> 历史说明：本文保留 2026-05-09 本地开发阶段的迁移判断，用于追溯当时为什么没有直接使用未备案域名。当前线上链路已经改为 `https://gaokao.aicoming.cn` -> `47.113.125.147`，小程序备案、HTTPS、微信合法域名、PDF 下载和 1 元微信支付测试均已完成。当前不再推进旧域名备案路径；最新事实以 `docs/deployment/current-live-chain.md` 和 `docs/deployment/production-launch-todo.md` 为准。

## 当前决策

项目当时先回到本地开发，不急于上线服务器。小程序主体备案、微信审核类目和 AI 问答资质是上线前置条件，在这些问题没有解决前，不把 `aicoming.com.cn` 作为正式小程序接口域名。

当前可用的工程边界：

- 小程序前端：`gaokao-miniprogram/`
- 本地后端代理：`gaokao-proxy/`
- Dify 服务：开发期可以继续使用已有可访问实例
- 正式域名：历史阶段暂不启用；当前已使用 `https://gaokao.aicoming.cn`

## 备案与资质边界

### 小程序备案

微信小程序备案不在阿里云备案系统中办理。阿里云官方 FAQ 明确说明：阿里云备案只支持淘宝小程序备案，不支持微信小程序及其他平台小程序备案。

微信小程序备案应在微信公众平台办理。备案通过是发布上线的前置条件之一，但它和服务器部署不是同一件事。

### 网站 ICP 备案（历史判断）

当时的风险判断是：如果后期使用中国内地服务器，并用未完成备案或未完成接入的域名访问服务器接口，例如：

```text
https://www.aicoming.com.cn/api/health
```

则云厂商可能拦截 Host 请求，表现为：

```text
Non-compliance ICP Filing
```

当前项目已经切换为 `gaokao.aicoming.cn`，不再继续推进当时设想的 `aicoming.com.cn` 备案路径。

### AI 问答审核资质

当前产品包含 AI 问答能力。微信审核可能要求补充与 AI/深度合成/算法备案相关的服务类目和资质材料。若暂时无法提供第三方模型、算法备案或深度合成相关资质，不建议以“AI 问答”作为正式发布能力提交审核。

上线前需要决定：

- 继续做 AI 问答：准备平台要求的 AI 相关资质材料。
- 降级为非生成式咨询工具：去掉或隐藏自由 AI 问答能力，只保留静态内容检索、表单引导、规则化推荐等低风险功能。
- 仅内部测试：不提交公开发布，继续用开发版/体验版验证产品。

## 本地开发环境

### 目录

```text
gaokao-miniprogram/   UniApp 微信小程序
gaokao-proxy/         Express 本地 Dify 代理
data/                 研究数据、报告和知识库内容
docs/                 规格、计划、部署和测试文档
```

### 本地 proxy

在 `gaokao-proxy/.env` 中配置：

```env
DIFY_API_URL=http://127.0.0.1:8080
DIFY_API_KEY=app-xxxxxxxxxxxxxxxx
PORT=3001
JSON_BODY_LIMIT=32kb
REQUEST_TIMEOUT_MS=90000
STREAM_TIMEOUT_MS=120000
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX=30
MAX_QUERY_LENGTH=2000
```

如果 Dify 不在本机，把 `DIFY_API_URL` 改成可访问地址，例如：

```env
DIFY_API_URL=http://服务器IP:8080
```

启动：

```bash
cd gaokao-proxy
npm install
npm run dev
```

健康检查：

```bash
curl http://127.0.0.1:3001/api/health
```

期望返回：

```json
{"status":"ok"}
```

### 本地小程序

开发期小程序默认请求：

```text
http://localhost:3001
```

对应代码在：

```text
gaokao-miniprogram/src/api/dify.js
```

开发构建：

```bash
cd gaokao-miniprogram
npm install
npm run dev:mp-weixin
```

生产构建：

```bash
npm run build:mp-weixin
```

导入微信开发者工具的目录：

```text
gaokao-miniprogram/dist/build/mp-weixin
```

开发者工具里可以临时关闭合法域名校验，但这只适用于开发调试，不代表线上可用。

## 迁移到服务器前的准入条件

服务器迁移前至少满足以下条件：

- 小程序备案路径明确：微信公众平台备案能继续推进。
- AI 问答资质路径明确：能提交所需类目和资质，或决定先隐藏 AI 问答。
- 域名 ICP/接入备案明确：域名能被目标云厂商放行。
- Dify 部署位置明确：本机、同服务器、独立服务器或云服务。
- 生产环境密钥已准备：Dify App Key、数据库密码、JWT/Token 等。

## 服务器迁移目标结构

建议使用一台服务器承载 proxy，Dify 可按资源情况独立部署。

```text
/opt/gaokao-proxy
  .env
  package.json
  package-lock.json
  server.js
```

服务端口：

```text
3001  gaokao-proxy
80    Nginx HTTP
443   Nginx HTTPS
8080  Dify，仅在本机或内网暴露
```

## 服务器环境变量

生产服务器 `/opt/gaokao-proxy/.env`：

```env
DIFY_API_URL=http://127.0.0.1:8080
DIFY_API_KEY=app-xxxxxxxxxxxxxxxx
PORT=3001
JSON_BODY_LIMIT=32kb
REQUEST_TIMEOUT_MS=90000
STREAM_TIMEOUT_MS=120000
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX=30
MAX_QUERY_LENGTH=2000
ALLOWED_ORIGINS=
PROXY_API_TOKEN=
```

注意：

- `.env` 不提交 Git。
- `DIFY_API_KEY` 不写进小程序。
- 如果 Dify 不在同一台服务器，`DIFY_API_URL` 必须换成可达地址。
- 如果启用 `PROXY_API_TOKEN`，小程序端也要增加 `x-proxy-token` 请求头；当前代码还没有加入该逻辑。

## Nginx 迁移配置

生产环境只让公网访问 Nginx，不直接暴露 Node 端口。

HTTP 基础配置：

```nginx
server {
    listen 80;
    server_name www.aicoming.com.cn aicoming.com.cn;

    client_max_body_size 50m;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
        default_type text/plain;
        try_files $uri =404;
    }

    location = /api/health {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/chat {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 180s;
        proxy_send_timeout 180s;
    }
}
```

HTTPS 证书申请前确认：

```bash
curl -H 'Host: www.aicoming.com.cn' http://服务器IP/.well-known/acme-challenge/ping
```

必须返回服务器自己的内容，不能返回云厂商备案拦截页。

证书申请：

```bash
certbot certonly --webroot -w /var/www/letsencrypt -d www.aicoming.com.cn
```

如根域名也要使用：

```bash
certbot certonly --webroot -w /var/www/letsencrypt -d aicoming.com.cn -d www.aicoming.com.cn
```

## 小程序正式环境调整

上线前新增或修改：

```text
gaokao-miniprogram/.env.production
```

内容：

```env
VITE_API_BASE=https://www.aicoming.com.cn
```

重新构建：

```bash
cd gaokao-miniprogram
npm run build:mp-weixin
```

微信公众平台需要配置：

```text
request 合法域名：https://www.aicoming.com.cn
```

微信开发者工具上传：

```text
gaokao-miniprogram/dist/build/mp-weixin
```

## 迁移步骤清单

1. 确认备案/资质可以继续。
2. 确认域名解析到目标服务器。
3. 确认 Host 请求不被云厂商备案拦截。
4. 安装服务器运行环境：Node.js、npm、pm2、Nginx、certbot。
5. 上传 `gaokao-proxy/` 到 `/opt/gaokao-proxy`。
6. 创建 `/opt/gaokao-proxy/.env`。
7. 执行 `npm install`。
8. 用 pm2 启动：

```bash
pm2 start server.js --name gaokao-proxy
pm2 save
pm2 startup
```

9. 配置 Nginx 反代。
10. 验证 HTTP：

```bash
curl http://服务器IP/api/health
```

11. 申请 HTTPS 证书。
12. 验证 HTTPS：

```bash
curl https://www.aicoming.com.cn/api/health
```

13. 修改 `VITE_API_BASE` 并重新编译小程序。
14. 微信公众平台配置 request 合法域名。
15. 微信开发者工具上传体验版。
16. 资质和备案通过后提交审核。

## 当前不建议做的事

- 不建议现在把小程序正式域名固定到未放行的域名。
- 不建议把 Dify API Key 写入小程序端。
- 不建议在资质未解决前公开发布 AI 问答功能。
- 不建议为了绕过审核而更换描述但保留自由 AI 问答入口。
- 不建议把 `data/`、`tmp/`、日志、`.env`、大文件输出一次性提交到 Git。

## 迁移验收标准

本地开发验收：

```bash
cd gaokao-proxy && npm run dev
curl http://127.0.0.1:3001/api/health
cd ../gaokao-miniprogram && npm run build:mp-weixin
```

服务器部署验收：

```bash
pm2 list
curl http://127.0.0.1:3001/api/health
curl http://服务器IP/api/health
curl https://www.aicoming.com.cn/api/health
```

小程序上线验收：

- 微信开发者工具预览可正常发送消息。
- 开发版/体验版可正常收流式回复。
- request 合法域名已配置。
- 小程序备案完成。
- AI 问答相关类目和资质审核通过，或相关功能已隐藏。

## 参考

- 阿里云备案 FAQ：阿里云备案只支持淘宝小程序备案，不支持微信小程序及其他平台小程序备案。
- 阿里云 ICP 备案流程：使用阿里云中国内地节点服务器托管网站/App 时，需要按备案流程处理。
- 微信小程序备案：在微信公众平台办理，小程序发布前需要完成备案。
