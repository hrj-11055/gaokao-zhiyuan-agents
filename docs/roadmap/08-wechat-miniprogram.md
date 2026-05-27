# Phase 4.2 — 微信小程序接入

> 排期：Week 4-5（05/07 - 05/16）
> 前置依赖：Phase 3.2 多轮对话优化、Phase 3.3 安全护栏
> 阻塞任务：Phase 5.1 使用统计、Phase 5.2 省份扩展
> 状态：历史路线图。当前线上 API 入口、HTTPS、会员/PDF 事实以 `docs/deployment/current-live-chain.md` 为准。

---

## 1. 如何完成

### 架构

```
微信小程序 → gaokao-proxy（https://gaokao.aicoming.cn）→ Dify API（http://159.75.110.157）
```

### 技术选型

| 层 | 方案 | 说明 |
|----|------|------|
| 前端 | 微信小程序原生 / UniApp | 推荐 UniApp，方便后续扩展到 H5 |
| 后端 | Dify API 直连 | 小程序直接调用 Dify Chat API |
| 部署 | 小程序入口 `https://gaokao.aicoming.cn`；gaokao-proxy 服务器 47.113.125.147；Dify/gaokao-api 服务器 159.75.110.157 | 当前线上拆分部署 |

### 小程序核心页面

1. **首页/对话页**：核心交互界面，类似微信聊天
2. **快捷入口**：预设常见问题按钮（"查分数线""问专业""推荐学校"）
3. **关于页**：免责声明、使用说明

### Dify API 对接

```javascript
// 小程序中调用 Dify Chat API
const response = await wx.request({
  url: 'https://gaokao.aicoming.cn/api/chat/stream',
  method: 'POST',
  header: {
    'Authorization': 'Bearer app-xxx',
    'Content-Type': 'application/json'
  },
  data: {
    inputs: {},
    query: userMessage,
    response_mode: 'streaming', // 或 'blocking'
    conversation_id: conversationId, // 第二轮开始携带
    user: openId
  }
})
```

### 关键注意点

1. **域名备案**：小程序要求后端域名已备案。当前小程序后端入口是 `https://gaokao.aicoming.cn` 的 `gaokao-proxy`，需要：
   - 绑定已备案域名
   - 在小程序后台配置合法域名
   - 或使用微信云开发做中转

2. **流式响应**：Dify 支持 SSE 流式输出，小程序需要用 `requestTask` 或 `wx.connectSocket` 处理

3. **鉴权**：Dify App API Key 不能暴露在前端代码中，需要：
   - 搭建简单的后端代理（Node.js/Python），将 API Key 存在服务端
   - 或使用 Dify 的 Web App 嵌入方式

### 实施步骤

1. 注册微信小程序账号，获取 AppID
2. 确认域名备案方案（备案新域名 or 云开发中转）
3. 搭建后端代理（如需要）
4. 开发小程序对话页面
5. 对接 Dify API，实现对话功能
6. 添加快捷入口和关于页
7. 提交审核

---

## 2. 验收标准

- [ ] 微信小程序可正常打开，对话界面可用
- [ ] 发送消息后能收到 Agent 回复
- [ ] 多轮对话（上下文记忆）正常工作
- [ ] 快捷入口按钮功能正常
- [ ] 免责声明页面完整
- [ ] 通过微信小程序审核

---

## 3. 排期

| 日期 | 工作内容 |
|------|---------|
| 05/07-05/08 | 确认域名方案 + 搭建后端代理 |
| 05/09-05/11 | 开发小程序对话页 + API 对接 |
| 05/12 | 开发快捷入口 + 关于页 |
| 05/13-05/14 | 联调测试 + 修复 bug |
| 05/15 | 提交微信审核 |
| 05/16 | 处理审核反馈，上线 |
