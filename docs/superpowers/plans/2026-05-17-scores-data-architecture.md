# 录取分数线数据架构规划

> 当前实现提示：这是分数线 API 规划快照。`gaokao-api` 容器在 159 内部暴露 `5001->5000`，但 47 当前通过 `SCORE_API_URL=http://159.75.110.157/score-api` 访问，不要把公开 `:5000` 当作线上入口。

## 一、当前状态

| 项目 | 状态 |
|------|------|
| 数据源 | 掌上高考 API (api.zjzw.cn) |
| 存储格式 | Markdown 文件 (`kb2-scores-*.md`) |
| 数据量 | 31 省 × ~600 校 × 3 年 ≈ 10 万条 |
| 年份 | 2023, 2024, 2025 |
| 已有服务 | Flask API (`gaokao-api`；47 当前通过 `http://159.75.110.157/score-api` 访问) |

## 二、使用场景分析

### 2.1 对话场景 (Dify RAG)

| 用户问题 | 查询需求 | 数据要求 |
|----------|----------|----------|
| "广东600分物理类能上什么学校？" | 省份+分数+选科 → 匹配学校 | 范围查询，按分数段筛选 |
| "中山大学在广东的分数线是多少？" | 学校+省份 → 查专业列表 | 精准匹配，返回完整专业列表 |
| "计算机专业哪些学校分数线在550-600之间？" | 专业+分数段 → 跨省查询 | 模糊匹配专业名，范围查询 |
| "我这个分数能冲哪些学校？" | 省份+分数 → 三档推荐 | 冲(30-50%)、稳(70-80%)、保(90%+) |

### 2.2 综合报告场景 (精准查询)

| 报告模块 | 查询需求 | 数据要求 |
|----------|----------|----------|
| Tab 5: 大学深度研究 | 按用户分数推荐 5-10 所目标院校 | 精准匹配，含历年数据 |
| 冲稳保分析 | 计算 2024 年该分数对应的位次区间 | 位次-分数转换 |
| 专业推荐 | 结合用户兴趣+分数，匹配专业 | 专业编码匹配 |

### 2.3 小程序直接查询场景

| 页面功能 | 查询需求 | 交互方式 |
|----------|----------|----------|
| 分数查询器 | 省份+选科+分数 → 可报学校列表 | 实时筛选，分页展示 |
| 学校详情 | 学校ID → 该校在用户省份的专业分数线 | 缓存优先 |
| 历年对比 | 学校+专业 → 2023-2025 分数趋势 | 图表展示 |

### 2.4 数据分析场景

| 分析需求 | 查询类型 |
|----------|----------|
| 某专业全国分数线分布 | 聚合统计 |
| 某省历年分数线变化趋势 | 时间序列 |
| 热门专业/学校排行 | 排序查询 |

## 三、查询方式设计

### 3.1 核心查询接口

```
1. 按分数匹配学校 (最常用)
   GET /api/scores/match?province=广东&score=600&category=物理类&year=2024
   → 返回: { 冲: [...], 稳: [...], 保: [...] }

2. 按学校查专业分数线
   GET /api/scores/schools/{school_id}/provinces/{province_id}
   → 返回: { school_name, majors: [{ name, min_score, min_rank, ... }] }

3. 按专业查学校分数线
   GET /api/scores/majors/{major_keyword}?province=广东&year=2024
   → 返回: [{ school, major, min_score, min_rank }]

4. 分数段统计
   GET /api/scores/stats?province=广东&score_min=550&score_max=600&category=物理类
   → 返回: { total_schools, avg_score, percentiles }

5. 位次转换
   GET /api/scores/rank-to-score?province=广东&rank=10000&category=物理类&year=2024
   → 返回: { score: 580, range: "575-585" }
```

### 3.2 Dify RAG 查询模式

| 查询模式 | 实现方式 | 适用场景 |
|----------|----------|----------|
| 向量检索 | Dify 知识库 (Embedding) | 自然语言问题 |
| 全文检索 | Dify 全文索引 | 专业名/学校名关键词 |
| 工具调用 | HTTP 工具节点调用 Flask API | 精准分数查询 |

## 四、数据架构设计

### 4.1 存储方案：混合存储

```
┌─────────────────────────────────────────────────────────┐
│                    应用层                                │
├─────────────────────────────────────────────────────────┤
│  Dify RAG (向量+全文)    │    Flask API (精准查询)      │
└──────────┬───────────────────────┬──────────────────────┘
           │                       │
           ▼                       ▼
┌──────────────────┐      ┌──────────────────────────────┐
│  Dify PostgreSQL │      │  专用 PostgreSQL (scores_db) │
│  - 知识库表       │      │  - scores_2023              │
│  - 文档块         │      │  - scores_2024              │
│  - 向量嵌入       │      │  - scores_2025              │
└──────────────────┘      │  - schools (学校元数据)      │
                          │  - majors (专业元数据)       │
                          └──────────────────────────────┘
```

### 4.2 数据库表结构

#### 主表：scores (分区表)

```sql
CREATE TABLE scores (
    id BIGSERIAL PRIMARY KEY,
    year INT NOT NULL,
    province_id VARCHAR(2) NOT NULL,
    province_name VARCHAR(20) NOT NULL,
    school_id VARCHAR(10) NOT NULL,
    school_name VARCHAR(100) NOT NULL,
    major_id VARCHAR(10),
    major_name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL,  -- 物理类/历史类/综合
    batch_name VARCHAR(50),          -- 本科批/提前批等
    min_score INT,                   -- 最低分
    min_rank INT,                    -- 最低位次
    avg_score INT,                   -- 平均分
    is_985 BOOLEAN,
    is_211 BOOLEAN,
    is_double_first BOOLEAN,         -- 双一流
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY LIST (year);

-- 索引
CREATE INDEX idx_province_score ON scores(province_id, category, min_score);
CREATE INDEX idx_school_province ON scores(school_id, province_id);
CREATE INDEX idx_major_name ON scores USING GIN(to_tsvector('chinese', major_name));
```

#### 辅助表：schools (学校元数据)

```sql
CREATE TABLE schools (
    school_id VARCHAR(10) PRIMARY KEY,
    school_name VARCHAR(100) NOT NULL,
    province_id VARCHAR(2),
    city VARCHAR(50),
    school_type VARCHAR(20),  -- 本科/专科
    school_level VARCHAR(50), -- 985/211/双一流/普通本科
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.3 Dify 知识库格式 (RAG 用)

为支持 Dify 向量检索，需要将数据格式化为更友好的文本块：

```markdown
## 广东-中山大学-2024-物理类

学校：中山大学 (985, 211, 双一流)
省份：广东
科目：物理类
批次：普通本科批

专业分数线：
| 专业名称 | 最低分 | 最低位次 | 平均分 |
|---------|--------|---------|--------|
| 计算机类 | 645 | 3200 | 650 |
| 临床医学 | 660 | 1500 | 665 |
| ...
```

**块大小控制**：每块 1-2 个学校，确保检索粒度合适。

## 五、实施计划

### Phase 1: 数据转换 (优先级最高)

**任务**：将 Markdown 转换为 JSON + 导入 PostgreSQL

```bash
# 新脚本：data/convert_scores_to_json.py
# 功能：
# 1. 解析所有 kb2-scores-*.md 文件
# 2. 提取结构化数据为 JSON
# 3. 生成 SQL 导入文件
# 4. 验证数据完整性

python3 data/convert_scores_to_json.py --input data/knowledge-base/kb2-scores-*.md --output data/scores.json
python3 data/convert_scores_to_json.py --import --db-host 159.75.110.157
```

**输出格式**：
```json
[
  {
    "year": 2024,
    "province_id": "44",
    "province_name": "广东",
    "school_id": "104",
    "school_name": "中山大学",
    "major_name": "计算机类",
    "category": "物理类",
    "batch": "普通本科批",
    "min_score": 645,
    "min_rank": 3200,
    "avg_score": 650,
    "tags": ["985", "211", "双一流"]
  }
]
```

### Phase 2: API 服务升级

**现有 gaokao-api 扩展**：

```python
# 新增端点
@app.route('/api/scores/match', methods=['GET'])
def match_schools():
    """按分数匹配学校（冲稳保）"""
    province = request.args.get('province')
    score = int(request.args.get('score'))
    category = request.args.get('category', '物理类')
    year = int(request.args.get('year', 2024))

    # 查询逻辑：分数 ±10 分为稳，+10~20 为冲，-10~-20 为保
    ...
    return jsonify({ 冲: [...], 稳: [...], 保: [...] })

@app.route('/api/scores/schools/<school_name>/provinces/<province>', methods=['GET'])
def get_school_scores(school_name, province):
    """查学校在某省的专业分数线"""
    ...
```

### Phase 3: Dify 集成

**配置 Dify Chatflow**：

```
用户输入 → LLM (意图识别) → 分支：
  ├─ 分数查询类 → HTTP 工具 → Flask API → 返回结构化数据
  ├─ 学校对比类 → HTTP 工具 → Flask API → 返回对比结果
  └─ 咨询建议类 → 知识检索 (RAG) → 综合回答
```

### Phase 4: 综合报告集成

**修改 report-builder.js**：

```javascript
// 当前：直接读本地 Markdown 文件
// 改进：调用 Flask API 获取精准匹配数据

async function matchSchoolsForReport(profile) {
  const { province, score, category } = profile
  const url = `${SCORE_API_URL}/api/scores/match?province=${province}&score=${score}&category=${category}&limit=10`
  const res = await fetch(url)
  return res.json()  // { 冲: [...], 稳: [...], 保: [...] }
}
```

## 六、数据流图

```
┌─────────────────┐
│  Markdown 文件   │ (kb2-scores-*.md)
└────────┬────────┘
         │
         ▼ convert_scores_to_json.py
┌─────────────────┐
│   JSON 中间文件  │ (scores.json)
└────────┬────────┘
         │
         ├─────────────────┐
         ▼                 ▼
┌──────────────────┐  ┌─────────────────────────┐
│ PostgreSQL 导入  │  │ Dify 知识库上传         │
│ (结构化查询)      │  │ (向量+全文检索)         │
└────────┬─────────┘  └──────────┬──────────────┘
         │                       │
         ▼                       ▼
┌──────────────────┐  ┌─────────────────────────┐
│  Flask API       │  │  Dify RAG               │
│  /api/scores/*   │  │  知识检索               │
└────────┬─────────┘  └──────────┬──────────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌─────────────────────────┐
         │  应用层                 │
         │  - 综合报告生成          │
         │  - 小程序查询            │
         │  - Dify 对话            │
         └─────────────────────────┘
```

## 七、优先级建议

| 优先级 | 任务 | 预计耗时 | 价值 |
|--------|------|----------|------|
| P0 | Markdown → JSON 转换脚本 | 2-3h | 基础数据 |
| P0 | PostgreSQL 表结构+导入 | 2h | 结构化查询 |
| P1 | Flask API 扩展 (/api/scores/match) | 3h | 核心查询 |
| P1 | report-builder.js 改用 API | 2h | 报告质量 |
| P2 | Dify 知识库重新格式化上传 | 2h | RAG 检索 |
| P2 | Dify Chatflow 配置工具调用 | 2h | 对话体验 |
| P3 | 小程序直接查询页面 | 4h | 用户功能 |

## 八、风险与备选方案

| 风险 | 影响 | 备选方案 |
|------|------|----------|
| PostgreSQL 容量不足 | 数据无法存储 | 使用分区表 + 按需加载 |
| API 响应慢 | 用户体验差 | 添加 Redis 缓存层 |
| Dify 知识库容量超限 | 无法上传 | 按省份/年份拆分多个知识库 |
| 数据格式不一致 | 转换失败 | 添加数据校验+清洗逻辑 |

## 九、后续扩展

1. **缓存层**：Redis 缓存热门查询 (省份+分数)
2. **异步任务**：大查询用 Celery 异步处理
3. **监控**：记录查询日志，分析热点专业/学校
4. **预测**：基于历史数据预测 2025 年分数线趋势
