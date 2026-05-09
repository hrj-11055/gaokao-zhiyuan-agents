# Phase 5.1 — 使用统计与分析看板

> 排期：Week 5（05/14 - 05/20）
> 前置依赖：Phase 4.2 微信小程序上线
> 阻塞任务：无

---

## 1. 如何完成

### 目标

收集用户使用数据，指导后续迭代优化方向。

### 需要采集的数据

| 数据项 | 采集方式 | 用途 |
|--------|---------|------|
| 用户问题原文 | 后端代理日志 | 分析高频问题类型 |
| 意图分类结果 | Dify Chatflow 节点输出 | 统计各意图占比 |
| 知识库命中率 | 知识检索节点返回 | 发现知识库盲区 |
| 对话轮数 | conversation_id 关联 | 判断单轮解决率 |
| 用户满意度 | 小程序内点赞/踩 | 量化回答质量 |

### 技术方案

#### 方案 A：后端代理日志（推荐）

在小程序后端代理层记录所有请求：

```python
# 简单的 Flask 代理 + 日志
@app.route("/chat", methods=["POST"])
def chat():
    query = request.json["query"]
    user_id = request.json["user"]

    # 调用 Dify API
    response = call_dify_api(query, user_id)

    # 记录日志
    log_entry = {
        "timestamp": datetime.now(),
        "user_id": user_id,
        "query": query,
        "answer_length": len(response["answer"]),
        "conversation_id": response["conversation_id"]
    }
    save_to_db(log_entry)

    return response
```

#### 方案 B：Dify 内置日志

Dify Console 自带日志查看功能：
- 打开 Dify → 应用 → 日志
- 可查看每条对话的输入输出、知识库命中情况

这是零成本的方案，但数据导出和分析不如方案 A 灵活。

#### 方案 C：简单看板

用 Dify 日志 + 手动导出 + Excel 分析即可，前期不需要复杂的实时看板。

### 实施步骤

1. 先用方案 B（Dify 内置日志）零成本启动
2. 在小程序后端代理中加入基本日志（方案 A）
3. 前期手动分析即可，不需要实时看板
4. 用户量上来后再考虑搭建分析看板

---

## 2. 验收标准

- [ ] Dify 日志可正常查看（方案 B）
- [ ] 后端代理已记录基本对话日志（用户ID、问题、时间）
- [ ] 能导出一周的对话数据做基本分析（问题类型分布、高频问题 Top 10）
- [ ] 知识库命中率可查看（Dify 知识检索节点日志）

---

## 3. 排期

| 日期 | 工作内容 |
|------|---------|
| 05/14 | 确认 Dify 内置日志可用 |
| 05/15 | 在后端代理中加入日志记录 |
| 05/16-05/17 | 导出一周数据，做基本分析 |
| 05/18-05/20 | 根据分析结果调整知识库或 prompt |
