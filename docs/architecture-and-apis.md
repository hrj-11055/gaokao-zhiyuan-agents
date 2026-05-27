# 峰哥咨询参考——高考志愿智能填报系统软件架构与接口规范

本文件是「峰哥咨询参考（Gaokao advising MVP）」的系统架构设计、开发运行指南及跨组件 API 相互调用接口规范。

---

## 一、 软件系统整体架构 (Software Architecture)

### 1.1 核心拓扑与分层设计
系统整体由 **前端客户端**、**业务代理网关**、**数据与大模型智能体引擎**、**批处理评估系统** 四大部分组成。为应对高并发、保障 API 安全以及提供流式（SSE）无卡顿 AI 体验，系统采用代理中介拓扑，所有客户端请求不直接触达 Dify 智能体或数据库，而是由业务代理网关统一校验、限流、脱敏并代理。

```mermaid
flowchart TD
    subgraph ClientLayer["客户端层 (Client Layer)"]
        MP["微信小程序\n(UniApp Vue 3 / Pinia)\nAPI: https://gaokao.aicoming.cn"]
    end

    subgraph GatewayLayer["网关与代理层 (Gateway & Proxy Layer - Server 47)"]
        Nginx["Nginx 反向代理\n(Port 80/443)\n反代 /api/*, /reports/*"]
        Proxy["gaokao-proxy\n(Node.js Express / PM2 Port 3001)"]
        MemoryStore["内存/Redis 缓存\n(频率限制 & 报告生成冷却)"]
        ReportsDir["静态报告宿主目录\n(gaokao-proxy/reports/)"]
    end

    subgraph AIDataLayer["智能体与数据服务层 (AI & Data Layer - Server 159)"]
        Dify["Dify AI 智能体工作流\n(Docker Port 8080)\nDify 后台配置模型"]
        GaokaoApi["gaokao-api 分数接口\n(Docker Port 5001->5000)"]
        Postgres["PostgreSQL 数据库\n(表: majors, universities, stats_overview)"]
    end

    subgraph ExternalServices["外部依赖服务 (External Services)"]
        WxPay["微信支付 JSAPI\n(官方支付下单/通知接口)"]
        DeepSeekAPI["DeepSeek Chat Completions\n(综合报告模型: deepseek-v4-pro)"]
        WeChatAuth["微信登录授权 API\n(jscode2session)"]
    end

    %% 客户端到网关
    MP -->|HTTP/SSE 请求| Nginx
    Nginx -->|反向代理到 127.0.0.1:3001| Proxy

    %% 网关内部与本地缓存
    Proxy <-->|Rate Limit & Cooldown| MemoryStore
    Proxy -->|写入静态报告/PDF懒生成| ReportsDir

    %% 网关到外部依赖
    Proxy -->|微信静默登录| WeChatAuth
    Proxy -->|JSAPI 下单| WxPay
    Proxy -->|直接驱动生成报告| DeepSeekAPI

    %% 网关到 159 服务器
    Proxy -->|RAG 对话 DIFY_API_URL| Dify
    Proxy -.->|Gaokao 分数线查询\nSCORE_API_URL=/score-api| GaokaoApi
    Proxy -->|直接读取专业/院校评估数据| Postgres
```

### 1.2 关键组件角色说明
1. **微信小程序 (gaokao-miniprogram)**：基于 Vue 3 Composition API、Pinia 状态管理与 UniApp 框架构建。管理用户本地档案表单、MBTI/Holland 测评状态、与 Proxy 网关维持 SSE（Server-Sent Events）流式会话。
2. **业务代理网关 (gaokao-proxy)**：基于 Node.js Express 框架，部署于公网服务器 `47.113.125.147`。核心职责包括：
   - 微信登录 Code 换取 OpenID，分发受秘钥保护的 JWT `sessionToken`。
   - 微信支付 JSAPI 统一下单，签名分发，接收官方异步支付回调并更新会员状态。
   - 对接 Dify 智能体进行 SSE 流式数据管道转发，并实时**拦截、过滤并剔除 `<think>...</think>` 思维链**，保证极佳的用户阅读体验。
   - 实现用户测评档案收集与完整性强校验（当前 21 道有效问卷题 + MBTI + Holland），利用 Puppeteer 懒加载生成 PDF，并冷却频繁请求。
   - 直接读取 PostgreSQL 中的结构化专业/院校三级深度评估数据，对免费用户脱敏脱密，对付费用户完整呈现。
3. **Dify 引擎 (Dify Engine)**：运行于 `159.75.110.157`，提供流式 RAG 问答及专业逻辑工作流。Dify 的具体对话模型以 Dify 后台配置为准；综合报告不走 Dify 模型，而是由 47 上的 `gaokao-proxy` 直连 DeepSeek Chat Completions，目标模型为 `deepseek-v4-pro`。
4. **数据引擎 (gaokao-api & Postgres)**：PostgreSQL 内含高价值数据表 `majors`（专业评估数据）、`universities`（院校评估数据）和 `stats_overview`（全盘评估数据统计）。`gaokao-api` 在 Dify 后端容器中运行，提供分数线与录取规则支持。

---

## 二、 系统使用与运行说明文档 (Usage & Operations Manual)

### 2.1 依赖环境要求
- **前端开发**：Node.js v18.x+，npm v9.x+，推荐微信开发者工具（最新稳定版）。
- **代理后端**：Node.js v18.x~v20.x，PM2 进程管理器，支持 PostgreSQL 15+、Redis 7+（可选，无 Redis 则自动降级至内存模式）。
- **数据跑批**：Python 3.10+，核心依赖包：`requests`, `pandas`, `psycopg2-binary`。

---

### 2.2 前端客户端开发与构建使用说明

#### 第一步：安装依赖
进入前端源码目录，使用 npm 安装所有构建与编译依赖：
```bash
cd gaokao-miniprogram
npm install
```

#### 第二步：环境变量与基础配置
确保基础路径配置文件 [gaokao-miniprogram/src/config.js](file:///Users/MarkHuang/Desktop/高考志愿填报项目/gaokao-miniprogram/src/config.js) 和 `.env` 的域名指向业务网关：
```javascript
// 未显式配置时，默认指向已备案 HTTPS 网关
export const API_BASE = import.meta.env.VITE_API_BASE || 'https://gaokao.aicoming.cn'
```

#### 第三步：启动微信小程序本地开发构建
执行 UniApp 构建命令，它将监听文件修改并生成微信小程序专用的编译包：
```bash
npm run dev:mp-weixin
```
编译成功后，会生成开发版目录：`gaokao-miniprogram/dist/dev/mp-weixin/`。

#### 第四步：微信开发者工具预览与测试
1. 打开微信开发者工具，点击「导入项目」。
2. 选择目录 `gaokao-miniprogram/dist/dev/mp-weixin/`。
3. 输入你的微信小程序 AppID（或使用测试号）。
4. 在开发者工具的「详情」->「本地设置」中，勾选「**不校验合法域名、web-view（业务域名）、TLS版本以及HTTPS证书**」以支持本地 HTTP 接口调试。

#### 第五步：生产打包构建
当需要发布体验版或审核版时，执行生产压缩构建命令：
```bash
npm run build:mp-weixin
```
打包成功后，编译包在 `gaokao-miniprogram/dist/build/mp-weixin/`。用微信开发者工具导入该文件夹，点击「上传」即可。

---

### 2.3 代理后端网关（gaokao-proxy）运行与部署说明

#### 第一步：安装依赖
```bash
cd gaokao-proxy
npm install
```

#### 第二步：配置本地/生产环境变量
在 `gaokao-proxy/` 目录下创建并编辑私密环境变量文件 `.env`：
```env
# 核心智能体与大盘 API 配置
DIFY_API_URL=http://159.75.110.157
DIFY_API_KEY=app-YOUR_DIFY_API_KEY_HERE
SCORE_API_URL=http://159.75.110.157/score-api

# 业务数据库配置
PG_HOST=159.75.110.157
PG_PORT=5432
PG_DATABASE=gaokao_db
PG_USER=postgres
PG_PASSWORD=YOUR_DB_PASSWORD_HERE

# 微信授权及支付参数 (生产上线用)
WECHAT_APPID=wx_your_appid
WECHAT_MCH_ID=your_mch_id
WECHAT_PAY_API_V3_KEY=your_apiv3_secret_key
WECHAT_PAY_SERIAL_NO=your_mch_cert_serial_number
WECHAT_PAY_PUBLIC_KEY_ID=PUB_KEY_ID_xxxxxxxxx
WECHAT_PAY_PUBLIC_KEY_PATH=/opt/gaokao-proxy/certs/wechatpay_public_key.pem
WECHAT_PAY_PRIVATE_KEY_PATH=/opt/gaokao-proxy/certs/apiclient_key.pem

# 基础运行时配置
PORT=3001
JWT_SECRET=your-jwt-auth-session-secret-key
REPORT_BASE_URL=https://gaokao.aicoming.cn
WECHAT_PAY_NOTIFY_URL=https://gaokao.aicoming.cn/api/payment/wechat/notify
MEMBERSHIP_INVITE_REQUIRED=5
MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT=10
MEMBERSHIP_VIP_CODES=FENGGE2026
```

#### 第三步：运行后端网关
- **本地开发热更新运行**：
  ```bash
  npm run dev
  ```
- **生产环境持久化部署（PM2 启动与自启）**：
  ```bash
  # 启动并命名服务
  pm2 start server.js --name gaokao-proxy

  # 保存当前进程列表并配置开机自启
  pm2 save
  pm2 startup
  ```
- **查看与管理网关日志**：
  ```bash
  pm2 logs gaokao-proxy
  ```

---

### 2.4 数据评估批处理脚本（Python 3）使用说明
项目提供了全自动的专业评估和院校评估的跑批、校验与数据导入机制。

#### 1. 专业评估报告生成进度查看
```bash
# 查看全国专业分类门类的跑批情况与绿黄红灯评分比例
python3 run_major_eval.py --status
```

#### 2. 专业跑批测试与全量评估
```bash
# 对指定门类 (例如 06 历史学) 跑批 3 条样本数据进行快速校验
python3 run_major_eval.py 06 --limit 3

# 重试某门类所有生成失败的专业
python3 run_major_eval.py 06 --retry
```

#### 3. 院校 360 度深度评估跑批 (基于 Gemini 架构)
```bash
# 启动广东省所有本科院校评估
python3 run_univ_eval_gemini.py 广东省

# 仅对广东省的特定高校进行精准多线程评估
python3 run_univ_eval_gemini.py 广东省 --only 中山大学 华南理工大学
```

#### 4. 生成报告字数与合规性质量检测
```bash
# 自动递归检查 data/专业评估报告 文件夹下所有 MD，过滤低于 3000 字的不合规低质报告并列出名单
python3 check_reports.py --min-chars 3000
```

#### 5. 导入更新至 Dify 知识库
```bash
# 将最新生成的结构化评估 Markdown 上传并同步至 159 服务器的 Dify 向量库中
python3 data/upload_to_dify.py
```

---

## 三、 数据 API 相互调用的输入输出接口 (API & Interface Specifications)

> [!NOTE]
> 1. 所有需要微信用户身份校验的接口，均须在 HTTP Header 中附带 `Authorization: Bearer <sessionToken>`。
> 2. API 网关默认以 JSON 格式通信，响应异常时统一采用 HTTP Status Code 映射，且返回规范的错误包 `{ "error": "具体错误提示文字", "code": "ERR_CODE" }`。

---

### 3.1 用户与会员管理接口 (User & Membership Management)

#### ① 微信小程序静默登录
*   **请求路由**：`POST /api/auth/wechat-login`
*   **请求说明**：小程序通过 `uni.login` 换取微信临时 code，传给网关与微信官方通信，创建或更新系统本地用户，并分发 JWT 会员令牌。
*   **请求 Header**：`Content-Type: application/json`
*   **请求 Body 参数**：
    ```json
    {
      "code": "0c3sP1000mQxxxxxxxxx_your_wx_login_code",
      "inviterId": "1a7fd9bc238ef (可选：邀请人用户ID)"
    }
    ```
*   **成功响应 (200 OK)**：
    ```json
    {
      "userId": "usr_789abcde123456",
      "sessionToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ1c3JfNzg5YWJjZGUxMjM0NTYiLCJvcGVuaWQiOiJveHh4eHh4In0...",
      "membership": {
        "status": "inactive",
        "expiresAt": null,
        "invite": {
          "code": "usr_789abcde123456",
          "count": 0,
          "unlocked": false,
          "required": 5
        },
        "downloadQuota": {
          "limit": 10,
          "used": 0,
          "remaining": 10
        }
      },
      "invite": {
        "code": "usr_789abcde123456",
        "count": 0,
        "unlocked": false,
        "required": 5
      }
    }
    ```

#### ② 查询用户当前会员状态
*   **请求路由**：`GET /api/membership/status`
*   **请求 Header**：
    *   `Authorization: Bearer eyJhbGciOiJIUzI1Ni... (必需)`
*   **成功响应 (200 OK)**：
    *   **已激活会员（付费解锁、邀请满 5 人解锁或会员邀请码解锁）**：
        ```json
        {
          "status": "active",
          "expiresAt": "2027-05-20T08:11:59.000Z",
          "invite": {
            "code": "usr_789abcde123456",
            "count": 5,
            "unlocked": true,
            "required": 5
          },
          "downloadQuota": {
            "limit": 10,
            "used": 1,
            "remaining": 9
          }
        }
        ```
    *   **未激活普通用户**：
        ```json
        {
          "status": "inactive",
          "expiresAt": null,
          "invite": {
            "code": "usr_789abcde123456",
            "count": 1,
            "unlocked": false,
            "required": 5
          },
          "downloadQuota": {
            "limit": 10,
            "used": 0,
            "remaining": 10
          }
        }
        ```

#### ③ 保存/完成个人档案以记录推荐位次
*   **请求路由**：`POST /api/profile/complete`
*   **请求说明**：当考生填完高考省份、位次、分数档案后，触发此接口。若该用户是由他人邀请，此步骤将自动给邀请人贡献 1 个有效邀请名额。
*   **请求 Header**：
    *   `Authorization: Bearer <sessionToken> (必需)`
*   **请求 Body**：`{}` （自动基于 Header 解析的 Token 关联的用户来处理）
*   **成功响应 (200 OK)**：
    ```json
    {
      "status": "ok",
      "inviteCounted": true,
      "membership": {
        "status": "inactive",
        "expiresAt": null,
        "invite": {
          "code": "usr_789abcde123456",
          "count": 2,
          "unlocked": false,
          "required": 5
        },
        "downloadQuota": {
          "limit": 10,
          "used": 0,
          "remaining": 10
        }
      }
    }
    ```

#### ④ 兑换会员邀请码
*   **请求路由**：`POST /api/membership/redeem-code`
*   **请求说明**：用户在报告页输入后台配置的会员邀请码后，直接解锁 VIP 报告权益。邀请码大小写不敏感，后端会做去空格和大写归一化。
*   **请求 Header**：
    *   `Authorization: Bearer <sessionToken> (必需)`
    *   `Content-Type: application/json`
*   **请求 Body 参数**：
    ```json
    {
      "code": "FENGGE2026"
    }
    ```
*   **成功响应 (200 OK)**：
    ```json
    {
      "code": "VIP_CODE_REDEEMED",
      "membership": {
        "status": "active",
        "expiresAt": "2027-05-20T08:11:59.000Z",
        "invite": {
          "code": "usr_789abcde123456",
          "count": 0,
          "unlocked": false,
          "required": 5
        },
        "downloadQuota": {
          "limit": 10,
          "used": 0,
          "remaining": 10
        }
      }
    }
    ```
*   **邀请码无效或已兑换响应 (400 Bad Request)**：
    ```json
    {
      "error": "会员邀请码无效",
      "code": "VIP_CODE_INVALID"
    }
    ```
    重复兑换时当前实现同样返回 `400`，`error` 文案会说明“该会员邀请码已兑换”。

---

### 3.2 微信支付体系接口 (Payment Subsystem)

#### ① 发起支付并创建会员解锁订单
*   **请求路由**：`POST /api/payment/create`
*   **请求说明**：当用户在小程序端点击「付费解锁」时调用。网关在本地创建待支付订单，并调用微信 JSAPI 接口生成小程序拉起收银台所需要的二次签名对象。
*   **请求 Header**：
    *   `Authorization: Bearer <sessionToken> (必需)`
*   **成功响应 (200 OK - 成功生成微信支付拉起包)**：
    ```json
    {
      "orderId": "ORD20260520140228392",
      "payment": {
        "timeStamp": "1779237748",
        "nonceStr": "a4b893f4cd91837aef82bc19483012fc",
        "package": "prepay_id=wx2014022839281203ef9281a0e100329031",
        "signType": "RSA",
        "paySign": "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC..."
      }
    }
    ```
*   **成功响应 (200 OK - 用户已经解锁无须再次支付)**：
    ```json
    {
      "alreadyUnlocked": true,
      "membership": {
        "status": "active",
        "expiresAt": "2027-05-20T08:11:59.000Z"
      }
    }
    ```
*   **服务不可用响应 (503 Service Unavailable)**：
    ```json
    {
      "error": "微信支付商户未在网关配置，请稍后重试",
      "code": "WECHAT_PAY_NOT_CONFIGURED"
    }
    ```

#### ② 查询指定支付订单支付状态
*   **请求路由**：`GET /api/payment/order/:orderId`
*   **请求 Header**：
    *   `Authorization: Bearer <sessionToken> (必需)`
*   **成功响应 (200 OK)**：
    ```json
    {
      "order": {
        "orderId": "ORD20260520140228392",
        "userId": "usr_789abcde123456",
        "priceCents": 1990,
        "status": "paid",
        "prepayId": "wx2014022839281203ef9281a0e100329031",
        "transactionId": "4200000109202605203928120389",
        "createdAt": "2026-05-20T00:10:02.000Z",
        "paidAt": "2026-05-20T00:10:15.000Z"
      },
      "membership": {
        "status": "active",
        "expiresAt": "2027-05-20T08:11:59.000Z"
      }
    }
    ```

#### ③ 微信支付官方服务器回调异步通知网关 (WeChat Pay Server Callback)
*   **请求路由**：`POST /api/payment/wechat/notify`
*   **安全要求**：网关在底层会自动利用微信 V3 证书进行验签，防止回调欺诈与伪造订单。
*   **请求 Body**：(微信官方标准的 V3 回调加密 JSON 消息)
*   **网关成功应答 (200 OK)**：
    ```json
    {
      "code": "SUCCESS",
      "message": "成功"
    }
    ```
*   **网关失败应答 (400 / 500)**：
    ```json
    {
      "code": "FAIL",
      "message": "签名验证失败 / 内部处理错误"
    }
    ```

---

### 3.3 智能 AI 对话与交互接口 (AI Chat Subsystem)

#### ① 同步阻塞式 AI 问答接口
*   **请求路由**：`POST /api/chat`
*   **请求说明**：同步等待大模型思考并输出完整 Markdown 文本。
*   **请求 Header**：
    *   `Authorization: Bearer <sessionToken> (可选，用来绑定身份)`
    *   `x-proxy-token: your_internal_api_token (可选，用于后台组件防盗刷)`
*   **请求 Body 参数**：
    ```json
    {
      "query": "计算机科学与技术专业，女生学起来吃力吗？就业方向如何？",
      "conversation_id": "conv_a81f3d2e9c182b83 (新会话传入空字符串)",
      "user": "usr_789abcde123456",
      "inputs": {
        "province": "广东省",
        "subject": "物理类",
        "score": 620,
        "rank": 8500
      }
    }
    ```
*   **成功响应 (200 OK)**：
    ```json
    {
      "event": "message",
      "message_id": "msg_901e2f3a4b5c",
      "conversation_id": "conv_a81f3d2e9c182b83",
      "mode": "chat",
      "answer": "学计算机科学与技术专业，女生并不会有先天的智力吃力，关键在于对逻辑思维和编程实践的兴趣。...\n\n### 核心就业方向：\n1. **研发与软件开发**：各大型互联网公司的软件工程师。\n2. **产品与运营**：结合女生天然的细致特质，走产品经理方向。\n3. **金融科技/国企IT**：工作相对稳定，福利体系健全。",
      "created_at": 1779237902
    }
    ```

#### ② SSE 流式问答接口 (流式传输，实时脱敏)
*   **请求路由**：`POST /api/chat/stream`
*   **数据原理**：此接口以 `text/event-stream` 格式响应。网关会实时从流中检测并剥离 `<think>` 标签以剔除思考阶段，确保小程序接收到的全都是干净的正文。
*   **请求 Header**：
    *   `Authorization: Bearer <sessionToken>`
    *   `Accept: text/event-stream`
*   **请求 Body**：与同步接口一致。
*   **响应内容格式 (SSE 块流)**：
    ```text
    data: {"event": "message", "answer": "计", "conversation_id": "conv_a81f3d2e9c182b83", "message_id": "msg_901e2f3a4b5c"}

    data: {"event": "message", "answer": "算", "conversation_id": "conv_a81f3d2e9c182b83", "message_id": "msg_901e2f3a4b5c"}

    data: {"event": "message", "answer": "机", "conversation_id": "conv_a81f3d2e9c182b83", "message_id": "msg_901e2f3a4b5c"}

    ... (后续的文字流)

    data: {"event": "message_end", "conversation_id": "conv_a81f3d2e9c182b83", "message_id": "msg_901e2f3a4b5c"}
    ```

#### ③ 对话内容用户点赞/点踩反馈
*   **请求路由**：`POST /api/chat/feedback`
*   **请求 Body 参数**：
    ```json
    {
      "messageId": "msg_901e2f3a4b5c",
      "rating": 1,
      "query": "计算机科学与技术专业就业...",
      "answer": "学计算机科学与技术专业..."
    }
    ```
*   **成功响应 (200 OK)**：
    ```json
    {
      "status": "ok"
    }
    ```

### 3.4 测评数据查询与报告生成接口 (Evaluation & Report Generation)

#### ① 列表查询所有专业评估数据
*   **请求路由**：`GET /api/reports/majors`
*   **查询 URL 参数**：
    *   `search`：检索名称或代码 (e.g. `0809` 或 `计算机`)
    *   `category`：专业门类过滤 (e.g. `08` 工学)
    *   `level`：评级过滤 (`绿灯` / `黄灯` / `红灯`)
    *   `min_score`：加权评分下限 (0.0 ~ 100.0)
    *   `page`：当前页码（从 1 开始，默认 1）
    *   `page_size`：每页记录数（默认 20，最大 100）
*   **普通用户响应 (200 OK - 付费字段已被剔除与遮掩)**：
    ```json
    {
      "total": 526,
      "page": 1,
      "page_size": 2,
      "data": [
        {
          "code": "080901",
          "name": "计算机科学与技术",
          "category": "工学/计算机类",
          "overview": {
            "weighted_score": 92.5,
            "recommendation_level": "绿灯",
            "mbti_match": ["INTJ", "INTP", "ISTP"],
            "holland_code": "IRE"
          },
          "summary": "作为现代信息化产业的基石专业，社会需求极其旺盛，发展上限极高。"
        }
      ]
    }
    ```
*   **会员已激活响应 (200 OK - 包含核心完整评估 layer2_core 等全量数据)**：
    ```json
    {
      "total": 526,
      "page": 1,
      "page_size": 1,
      "data": [
        {
          "code": "080901",
          "name": "计算机科学与技术",
          "category": "工学/计算机类",
          "data": {
            "layer1_overview": {
              "weighted_score": 92.5,
              "recommendation_level": "绿灯",
              "mbti_match": ["INTJ", "INTP", "ISTP"],
              "holland_code": "IRE"
            },
            "layer2_core": {
              "summary": "作为现代信息化产业的基石专业，社会需求极其旺盛，发展上限极高。",
              "employment_rate": "94.2%",
              "salary_avg_3yr": "14500",
              "pros_cons": {
                "pros": ["发展天花板高", "岗位需求多元", "转行通道宽广"],
                "cons": ["加班情况普遍", "技术迭代要求极快", "中年面临转型压力"]
              }
            },
            "layer3_details": {
              "curriculum": ["数据结构", "计算机组成原理", "操作系统", "编译原理"],
              "industrial_demand": "极高",
              "gender_ratio": "男72% : 女28%"
            }
          }
        }
      ]
    }
    ```

#### ② 查询特定专业深度评估详情
*   **请求路由**：`GET /api/reports/majors/:code` (e.g. `/api/reports/majors/080901`)
*   **响应内容**：格式与上述 list 单条完全一致（若为会员，返回完整三级深度报告；普通用户自动脱敏只输出概要）。

#### ③ 列表查询所有院校深度评估数据
*   **请求路由**：`GET /api/reports/universities`
*   **查询 URL 参数**：`search`, `province` (省份), `type` (高校类型，例如 `综合类`, `理工类`), `level` (`绿灯`/`黄灯`/`红灯`), `page`, `page_size`
*   **普通用户响应 (200 OK)**：
    ```json
    {
      "total": 1240,
      "page": 1,
      "page_size": 1,
      "data": [
        {
          "name": "中山大学",
          "province": "广东省",
          "univ_type": "综合类",
          "overview": {
            "weighted_score": 89.2,
            "recommendation_level": "绿灯",
            "tags": ["双一流", "985", "211"]
          },
          "summary": "华南地区学科最齐全、科研实力最强的领头羊高校，综合保研率名列前茅。"
        }
      ]
    }
    ```
*   **激活会员响应 (200 OK)**：包含完整的 layer2 核心科研深度、就业明细分布以及历年投档线层级。

#### ④ 获取特定院校详细评估
*   **请求路由**：`GET /api/reports/universities/:name` (e.g. `/api/reports/universities/中山大学`)
*   **响应内容**：格式与列表高校单条一致。

#### ⑤ 生成志愿填报综合决策评估报告 (HTML/PDF)
*   **请求路由**：`POST /api/report/generate`
*   **业务前置限制**：
    1.  网关会严格检查 `questionnaire` 填答数量**不得少于 22 题**。
    2.  `assessments.mbti.completed` 与 `assessments.holland.completed` 必须均为 `true`。
    3.  系统限制同一用户 **10分钟内仅能生成一次** 报告以防刷爆。
*   **请求 Header**：
    *   `Authorization: Bearer <sessionToken> (必需)`
*   **请求 Body 参数**：
    ```json
    {
      "userId": "usr_789abcde123456",
      "profile": {
        "name": "张小明",
        "province": "广东省",
        "subject": "物理类",
        "score": 628,
        "rank": 7200
      },
      "questionnaire": {
        "q1": "A", "q2": "B", "q3": "A", "q4": "C", "q5": "B",
        "q6": "A", "q7": "A", "q8": "B", "q9": "C", "q10": "A",
        "q11": "B", "q12": "B", "q13": "A", "q14": "C", "q15": "B",
        "q16": "A", "q17": "A", "q18": "B", "q19": "C", "q20": "A",
        "q21": "A", "q22": "B"
      },
      "assessments": {
        "mbti": {
          "completed": true,
          "result": "INTJ",
          "details": "逻辑严密，追求系统化设计，偏向幕后统筹策划"
        },
        "holland": {
          "completed": true,
          "result": "IRE",
          "details": "具备强烈的探究特质、务实精神与进取态度"
        }
      },
      "conversationId": "conv_a81f3d2e9c182b83"
    }
    ```
*   **成功响应 (200 OK)**：
    ```json
    {
      "url": "https://gaokao.aicoming.cn/reports/usr_789abcde123456_20260520-17792377.html"
    }
    ```
*   **测评未做完响应 (400 Bad Request)**：
    ```json
    {
      "error": "请先完成全部 3 项测评后再生成综合报告"
    }
    ```
*   **报告冷却限制中 (429 Too Many Requests)**：
    ```json
    {
      "error": "请 580 秒后再试"
    }
    ```
*   **非会员阻拦响应 (402 Payment Required)**：
    ```json
    {
      "error": "请先解锁深度填报会员以开启个性化报告生成功能",
      "code": "MEMBERSHIP_REQUIRED",
      "priceCents": 1990,
      "invite": {
        "code": "usr_789abcde123456",
        "count": 1,
        "unlocked": false,
        "required": 5
      },
      "downloadQuota": {
        "limit": 10,
        "used": 0,
        "remaining": 10
      }
    }
    ```

---

### 3.5 学校/专业深度报告阅读与 PDF 下载接口 (Deep Report Reader & PDF Download)

#### ① 生成在线阅读短链
*   **请求路由**：`POST /api/reports/deep/view-token`
*   **请求说明**：小程序可免费换取 10 分钟有效的在线 HTML 阅读链接。在线阅读不消耗 PDF 下载额度；PDF 下载才需要会员并消耗额度。
*   **请求 Header**：
    *   `Content-Type: application/json`
*   **请求 Body 参数**：
    ```json
    {
      "type": "major",
      "id": "080901"
    }
    ```
*   **成功响应 (200 OK)**：
    ```json
    {
      "url": "https://gaokao.aicoming.cn/reports/deep/view/<signed-token>",
      "expiresIn": 600
    }
    ```
*   **在线阅读页**：`GET /reports/deep/view/<signed-token>` 返回已渲染 HTML，包含目录、摘要卡片、正文排版、页面内搜索、高亮和打印。

#### ② 下载学校或专业深度研究 PDF
*   **请求路由**：`GET /api/reports/deep/pdf?type=major&id=080901`
*   **请求说明**：会员可下载学校深度研究报告和专业研究报告，下载成功会消耗 1 次深度 PDF 下载额度。
*   **请求 Header**：
    *   `Authorization: Bearer <sessionToken> (必需)`
*   **成功响应 (200 OK)**：
    *   响应体为 `application/pdf`。
    *   Header `X-Deep-Report-Downloads-Remaining` 返回本次下载后的剩余次数。
*   **非会员阻拦响应 (402 Payment Required)**：
    ```json
    {
      "error": "请先解锁深度填报会员以下载深度研究报告",
      "code": "MEMBERSHIP_REQUIRED",
      "priceCents": 1990,
      "invite": {
        "code": "usr_789abcde123456",
        "count": 1,
        "unlocked": false,
        "required": 5
      },
      "downloadQuota": {
        "limit": 10,
        "used": 0,
        "remaining": 10
      }
    }
    ```
*   **下载次数耗尽响应 (429 Too Many Requests)**：
    ```json
    {
      "error": "深度报告下载次数已用完",
      "code": "DOWNLOAD_QUOTA_EXHAUSTED",
      "downloadQuota": {
        "limit": 10,
        "used": 10,
        "remaining": 0
      }
    }
    ```

---

### 3.6 全盘评估状态数据统计接口 (System Stats)

#### ① 获取当前系统评估绿黄红灯数量大盘指标
*   **请求路由**：`GET /api/reports/stats`
*   **说明**：从数据库 `stats_overview` 视图快速获取全盘统计，用于仪表盘渲染。
*   **成功响应 (200 OK)**：
    ```json
    {
      "majors": {
        "total": 526,
        "green": 128,
        "yellow": 310,
        "red": 88,
        "avg_score": "81.42"
      },
      "universities": {
        "total": 1240,
        "green": 294,
        "yellow": 782,
        "red": 164,
        "avg_score": "76.85"
      }
    }
    ```

#### ② 网关核心数据库连接健康体检
*   **请求路由**：`GET /api/reports/health`
*   **成功响应 (200 OK - 正常)**：
    ```json
    {
      "status": "ok",
      "postgres": "connected"
    }
    ```
*   **降级响应 (200 OK - 连接超时或中断)**：
    ```json
    {
      "status": "degraded",
      "postgres": "disconnected"
    }
    ```
