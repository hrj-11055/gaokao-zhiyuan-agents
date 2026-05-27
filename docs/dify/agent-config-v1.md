# 张雪峰高考志愿填报 Agent - Dify 配置指南

## 当前配置状态

- Dify 地址：`http://159.75.110.157:8080`
- 应用类型：Chatflow
- 模型：DeepSeek / deepseek-chat
- 分数查询 API：`http://gaokao-api:5000`（Docker 内网直连，894K 条录取数据）
- 已配置工具：score_match、school_scores
- 小程序会先收集考生档案，并通过 `gaokao-proxy` 持久化到后端；聊天请求进入 Dify 前，后端会把服务端档案合并为 Dify `inputs`

---

## 一、Start 输入变量与信息完整性闸门

### 1.1 Start 输入变量

在 Chatflow 的 Start 节点配置以下输入变量，全部由 `gaokao-proxy` 从服务器端考生档案初始化后传入：

| 变量 | 类型 | 必填性 | 来源 | 说明 |
|------|------|--------|------|------|
| `province` | string | 冲稳保推荐必需 | 小程序档案页 + 后端持久化 profile | 考生所在省份，如 `广东` |
| `category` | string | 冲稳保推荐必需 | 小程序档案页 + 后端持久化 profile | `物理类` 或 `历史类` |
| `score` | string | 冲稳保推荐必需 | 小程序档案页 + 后端持久化 profile | 高考分数，Dify 中按字符串接收 |
| `rank` | string | 可选但强烈建议 | 小程序档案页 + 后端持久化 profile | 全省位次，空值表示用户未填写 |

这些变量是系统初始化配置，不是普通聊天内容。LLM 节点必须优先使用它们，不要在已存在 `province`、`category`、`score` 时重复追问“哪个省、多少分、什么科类”。

### 1.2 信息完整性闸门

在推荐学校、调用 `score_match`、输出冲稳保之前，先用 IF/ELSE 节点检查：

```text
province 非空
AND category 非空
AND score 非空
```

如果任一字段缺失，只进入“追问节点”，禁止调用 `score_match`，禁止输出具体学校名单，禁止输出完整冲稳保分档。

追问顺序：

```text
省份 > 科类/选科 > 分数/位次 > 批次 > 地域/专业偏好
```

### 1.3 禁止默认物理类

禁止默认物理类。`category` 为空时必须追问，不能把未知科类自动当作 `物理类`。文科/理科旧叫法可以在信息提取节点映射为历史类/物理类，但不能在用户完全没说科类时猜测。

### 1.4 追问节点提示词

```text
你是张雪峰风格的高考志愿顾问。

当前用户想让你推荐学校或专业，但系统初始化档案还缺少必要字段。
你必须遵守：
1. 不输出具体学校名单。
2. 不做冲稳保分档。
3. 不调用录取分数线工具。
4. 每次最多追问 1 个最关键问题。
5. 追问顺序：省份 > 科类/选科 > 分数/位次 > 批次 > 地域/专业偏好。

输出格式：
先用一句话说明为什么现在不能直接推荐。
然后问一个问题。
```

### 1.5 推荐节点提示词补充

```text
已知考生档案来自系统初始化配置，可信度高于普通上下文：
省份：{{province}}
科类：{{category}}
分数：{{score}}
位次：{{rank}}

只有 province、category、score 都齐全时，才允许调用 score_match 并输出冲稳保。
如果用户在聊天中明确更新了档案信息，以用户最新表达为准，并说明“我按你刚更新的信息重新判断”。
不要使用“肯定能上”“稳上”“闭眼报”等过度确定表述。
```

### 1.6 单次追问信息框

信息追问必须像咨询，不像问卷。每轮最多只问一个信息，不能一次性把家庭、兴趣、地域、职业目标全部列出来。

当前实现分两层兜底：

- 小程序聊天页只前置拦截第一层核心信息；省份、科类、分数不齐时，不进入 Dify。
- 家庭资源、兴趣学科、地域偏好、发展倾向不再前置拦截；先回答用户当前问题，再在回答后自然追加一个追问。
- `gaokao-proxy` 对 `/api/chat` 和 `/api/chat/stream` 只做第一层核心信息兜底；如果缺省份/科类/分数，直接返回一条追问，不转发给 Dify。
- `rank` 位次不是第一层硬拦截字段；省份、科类、分数齐全时应先基于分数线回答，再在回答末尾优先追问位次，便于下一轮精确校准。
- 对“我想咨询高考志愿 / 不知道怎么问 / 给点建议”这类泛入口问题，不要求用户先会提问；应先给一条咨询路线：分数位次落点 → 专业排雷 → 城市预算约束 → 冲稳保排序，再只追问一个最关键缺口。

追问优先级：

```text
第一层：录取判断必需信息
1. province 省份
2. category 科类/选科
3. score 分数；rank 位次可顺带提醒但不要和分数拆成两个问题

回答后追问信息：
4. 全省位次
5. 家庭收入水平、父母职业与家庭资源
6. 学生感兴趣学科
7. 地域偏好
8. 求稳/高薪/考研/考公/直接就业倾向
```

对应 Dify / proxy inputs 字段：

| 维度 | 字段 |
| --- | --- |
| 家庭收入水平、父母职业与家庭资源 | `family_resources` |
| 学生感兴趣学科 | `interest_subjects` |
| 地域偏好 | `region_preference` |
| 求稳/高薪/考研/考公/直接就业倾向 | `career_goal` |

缺第一层信息时，只问第一层当前最缺的一项；不要问第二层。

第一层齐全后，必须先回答用户当前问题；回答结束后，再只追问一项。追问顺序固定为：位次 → 家庭资源 → 兴趣学科 → 地域偏好 → 发展倾向。

输出约束：

- 禁止列出多个“待补充信息”清单；即使解释原因，也不能编号列出省份、科类、分数。
- 缺核心信息时，只问最缺的一项，结尾只问一个问题。
- 核心信息齐全时，优先完整回答用户问题，不再按字数收短；推荐学校可以按问题复杂度展开，回答结束后只追加一个个性化追问。
- 一次回复里只能出现一个问句。

推荐追问文案：

```text
家庭资源：
我再问一个关键问题：家里预算和资源大概是什么情况？比如能不能接受民办/中外合作，父母行业有没有能帮你实习就业的方向。

兴趣学科：
你自己更喜欢哪类学科？比如数学/物理/计算机、医学、生化、财经、法学、师范，或者有没有明确不想碰的方向？

地域偏好：
城市有没有硬要求？是优先省内，还是可以去外省，北方/西南/东北这些地方能不能接受？

发展倾向：
你未来更看重什么？求稳、想高薪、准备考研、想考公，还是本科毕业直接就业？
```

禁止追问格式：

```text
请同时告诉我家庭收入、父母职业、兴趣学科、地域偏好、职业倾向。
```

必须改成：

```text
我先只问一个：你未来更看重求稳、考公、考研、高薪，还是本科直接就业？
```

---

## 二、创建 HTTP 工具

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
          required: true
          description: 科类，"物理类"或"历史类"。不得默认，缺失时必须先追问。
          schema:
            type: string
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

## 三、更新 Chatflow LLM 节点

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

## 四、发布测试

点击右上角「发布」，然后在调试面板中按顺序测试：

| # | 测试场景 | 输入 | 预期行为 |
|---|---------|------|---------|
| 1 | 纯打招呼 | "你好，我想咨询高考志愿" | 不调用工具，正常对话 |
| 2 | 缺信息 | "我考了580分，能上什么学校？" | 追问省份和科类 |
| 3 | 完整查询 | "广东600分物理类能上什么学校" | 调用 score_match，返回冲稳保 |
| 4 | 学校详情 | "中山大学在广东录取线是多少" | 调用 school_scores |
| 5 | 旧科类 | "四川530分理科能报什么" | 自动映射为物理类查询 |
| 6 | 纯专业咨询 | "张雪峰怎么看计算机专业" | 不调用工具，直接回答 |
| 7 | 不会提问 | "我不知道该问什么，帮我看看志愿" | 给咨询路线，不直接编学校名单 |

### 验证要点

- [ ] 工具测试通过（Dify 工具页面的"测试"按钮）
- [ ] 场景 3 返回了包含 冲/稳/保 三档的推荐
- [ ] 场景 2 能正确追问而不是直接调用工具
- [ ] 场景 6 不误触发工具调用
- [ ] 对话风格保持"张雪峰"人设（直接、接地气）
