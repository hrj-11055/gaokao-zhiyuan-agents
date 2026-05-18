# 张雪峰高考志愿填报 Agent - Dify 配置指南

## 当前配置状态

- Dify 地址：`http://159.75.110.157:8080`
- 应用类型：Chatflow
- 模型：DeepSeek / deepseek-chat
- 分数查询 API：`http://gaokao-api:5000`（Docker 内网直连，894K 条录取数据）
- 已配置工具：score_match、school_scores

---

## 一、创建 HTTP 工具

### 工具 1：score_match（冲稳保推荐）

路径：Dify 控制台 → 左侧「工具」→「自定义」→「创建自定义工具」

**OpenAPI Schema（直接复制）：**

```yaml
openapi: 3.0.0
info:
  title: 分数线查询 API
  version: 1.0.0
servers:
  - url: http://gaokao-api:5000
paths:
  /api/scores/match:
    get:
      operationId: score_match
      summary: 根据省份、分数和科类查询录取分数线，返回冲稳保三档学校推荐
      description: 当用户询问"我能上什么学校"、"XX分能报哪些学校"、"推荐学校"、"冲稳保"时调用此工具
      parameters:
        - name: province
          in: query
          required: true
          description: 省份名称，如"广东"、"河南"、"四川"
          schema:
            type: string
        - name: score
          in: query
          required: true
          description: 高考分数
          schema:
            type: integer
        - name: category
          in: query
          required: false
          description: 科类，"物理类"或"历史类"，无法判断时默认"物理类"
          schema:
            type: string
            default: 物理类
        - name: year
          in: query
          required: false
          description: 年份
          schema:
            type: integer
            default: 2024
        - name: limit
          in: query
          required: false
          description: 每档返回数量
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: 冲稳保推荐结果
```

### 工具 2：school_scores（学校专业分数线）

```yaml
openapi: 3.0.0
info:
  title: 学校分数线查询 API
  version: 1.0.0
servers:
  - url: http://gaokao-api:5000
paths:
  /api/scores/schools/{school_name}/provinces/{province}:
    get:
      operationId: school_scores
      summary: 查询某所学校在某省的专业录取分数线
      description: 当用户询问"XX大学在XX省录取线"、"中山大学在广东多少分"、"某大学专业分数线"时调用
      parameters:
        - name: school_name
          in: path
          required: true
          description: 大学名称，如"中山大学"、"清华大学"
          schema:
            type: string
        - name: province
          in: path
          required: true
          description: 省份名称
          schema:
            type: string
        - name: year
          in: query
          required: false
          description: 年份
          schema:
            type: integer
            default: 2024
      responses:
        '200':
          description: 学校专业分数线列表
```

创建完成后，点击「测试」验证工具可用：
- score_match 测试参数：`province=广东, score=600, category=物理类`
- school_scores 测试参数：`school_name=中山大学, province=广东`

---

## 二、更新 Chatflow LLM 节点

### 2.1 添加工具到 LLM 节点

在 Chatflow 编辑器中点击 LLM 节点：
1. 找到「工具」区域
2. 点击「+ 添加工具」
3. 选择刚创建的 `score_match` 和 `school_scores`
4. 两个工具都添加

### 2.2 更新系统提示词

将 LLM 节点的 SYSTEM PROMPT 替换为以下内容：

```
-
```

### 2.3 更新 LLM 参数

| 参数 | 旧值 | 新值 | 原因 |
|------|------|------|------|
| Max Tokens | 1024 | 2048 | 需要返回 API 查询结果 + 分析 |
| Temperature | 0.8 | 0.7 | 查询场景需要更稳定的输出 |
| Top P | 0.9 | 0.9 | 不变 |

---

## 三、发布测试

点击右上角「发布」，然后在调试面板中按顺序测试：

| # | 测试场景 | 输入 | 预期行为 |
|---|---------|------|---------|
| 1 | 纯打招呼 | "你好，我想咨询高考志愿" | 不调用工具，正常对话 |
| 2 | 缺信息 | "我考了580分，能上什么学校？" | 追问省份和科类 |
| 3 | 完整查询 | "广东600分物理类能上什么学校" | 调用 score_match，返回冲稳保 |
| 4 | 学校详情 | "中山大学在广东录取线是多少" | 调用 school_scores |
| 5 | 旧科类 | "四川530分理科能报什么" | 自动映射为物理类查询 |
| 6 | 纯专业咨询 | "张雪峰怎么看计算机专业" | 不调用工具，直接回答 |

### 验证要点

- [ ] 工具测试通过（Dify 工具页面的"测试"按钮）
- [ ] 场景 3 返回了包含 冲/稳/保 三档的推荐
- [ ] 场景 2 能正确追问而不是直接调用工具
- [ ] 场景 6 不误触发工具调用
- [ ] 对话风格保持"张雪峰"人设（直接、接地气）
