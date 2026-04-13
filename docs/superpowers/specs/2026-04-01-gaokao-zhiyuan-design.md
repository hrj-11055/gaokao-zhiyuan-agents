# 高考志愿填报助手 - MVP设计文档

## 概述

微信小程序，帮助高考生和家长通过智能推荐和专业测评做出志愿填报决策。

- **前端**：微信原生小程序（WXML/WXSS/JS）
- **后端**：微信云开发（云函数 + 云数据库）
- **用户**：高考生 + 家长，无需登录
- **商业模式**：Freemium（MVP阶段仅免费功能）
- **时间线**：2026年高考季前上线

## 用户流程

### 入口A：智能推荐

1. 首页点击"智能推荐"
2. 填写：省份、高考分数、全省位次（选填）、科类
3. 科类说明：
   - 老高考省份：文科/理科
   - 新高考省份：物理类/历史类
4. 点击"开始推荐"→ 结果页
5. 结果页分三个Tab：冲 / 稳 / 保
6. 点击院校卡片 → 院校详情页（含专业组及各专业分数线）

### 入口B：专业测评

1. 首页点击"专业测评"
2. 完成 MBTI 性格测试（约20题）+ Holland 职业兴趣测试（约20题）
3. 查看测评结果：性格类型 + 解读 + 推荐专业方向
4. 点击"查看匹配院校"→ 跳转智能推荐，优先展示相关专业的院校

### 推荐算法

基于位次优先、分数辅助的策略：

1. 用户输入位次（优先）或分数
2. 查询近3年同省份同学科组别的录取数据
3. 按位次差距分三档：
   - **冲**：位次在院校录取位次前10%-30%（有希望但不确定）
   - **稳**：位次在院校录取位次±10%以内
   - **保**：位次在院校录取位次后20%以上

新高考省份推荐精确到**院校专业组**级别。

## 技术架构

```
┌─────────────────────────────────────┐
│         微信小程序（原生）            │
│                                     │
│  pages/                             │
│  ├── home/        首页（两个入口）    │
│  ├── recommend/   智能推荐输入+结果   │
│  ├── school/      院校详情页         │
│  └── assess/      专业测评           │
│       ├── test/    答题页            │
│       └── result/  测评结果页        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      微信云开发                      │
│                                     │
│  云函数：                            │
│  ├── getRecommendations  推荐算法    │
│  ├── getSchoolDetail     院校详情    │
│  └── getAssessmentResult 测评计算    │
│                                     │
│  云数据库：                          │
│  ├── schools          院校信息       │
│  ├── school_groups    院校专业组     │
│  ├── majors           专业信息       │
│  ├── admission_scores 院校录取分数   │
│  ├── group_scores     专业组录取分数  │
│  ├── major_scores     专业录取分数   │
│  └── assessment_qs    测评题库       │
└─────────────────────────────────────┘
```

## 数据模型

### schools（院校信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | string | 主键 |
| name | string | 院校名称 |
| province | string | 所在省份 |
| city | string | 所在城市 |
| level | array | 标签：["985","211","双一流","普通"] |
| type | string | 院校类型：综合/理工/师范/医药等 |
| intro | string | 院校简介 |
| rankings.ruankao | number | 软科排名 |
| rankings.alumni | number | 校友会排名 |
| rankings.qs | number | QS排名（如有） |
| ranking_year | number | 排名年份 |

### school_groups（院校专业组）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | string | 主键 |
| school_id | string | 关联 schools._id |
| group_code | string | 专业组代码：如 "01" |
| group_name | string | 专业组名称：如 "物理+化学组" |
| subject_requirement | array | 选科要求：["物理","化学"] |
| requirement_type | string | 必选/任选 |
| description | string | 专业组说明 |

### majors（专业信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | string | 主键 |
| name | string | 专业名称 |
| category | string | 学科门类：工学/理学/文学等 |
| description | string | 专业描述 |
| suitable_types | array | MBTI匹配类型：["INTJ","ENTJ","INTP"] |
| subject_requirement | array | 选科要求（新高考） |
| requirement_type | string | 必选/任选 |

### group_majors（专业组内的专业）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | string | 主键 |
| group_id | string | 关联 school_groups._id |
| major_id | string | 关联 majors._id |
| major_name | string | 专业名称 |

### admission_scores（院校录取分数）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | string | 主键 |
| school_id | string | 关联 schools._id |
| year | number | 录取年份 |
| province | string | 招生省份 |
| subject_group | string | 学科组别：文科/理科/物理类/历史类 |
| min_score | number | 最低录取分 |
| min_rank | number | 最低录取位次 |
| avg_score | number | 平均录取分 |

### group_scores（专业组录取分数）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | string | 主键 |
| group_id | string | 关联 school_groups._id |
| school_id | string | 关联 schools._id |
| year | number | 录取年份 |
| province | string | 招生省份 |
| min_score | number | 最低录取分 |
| min_rank | number | 最低录取位次 |
| avg_score | number | 平均录取分 |

### major_scores（专业录取分数）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | string | 主键 |
| school_id | string | 关联 schools._id |
| major_id | string | 关联 majors._id |
| year | number | 录取年份 |
| province | string | 招生省份 |
| subject_group | string | 学科组别 |
| min_score | number | 最低录取分 |
| min_rank | number | 最低录取位次 |

### assessment_questions（测评题库）

| 字段 | 类型 | 说明 |
|------|------|------|
| _id | string | 主键 |
| type | string | "mbti" 或 "holland" |
| question | string | 题目文本 |
| options | array | [{text, value}] 选项及对应值 |
| dimension | string | 维度：E/I, S/N, T/F, J/P 或 Holland维度 |

## 页面清单

| # | 页面 | 路径 | 功能 |
|---|------|------|------|
| 1 | 首页 | pages/home/index | 两个入口：智能推荐 + 专业测评 |
| 2 | 推荐输入页 | pages/recommend/index | 省份、分数、位次、科类输入 |
| 3 | 推荐结果页 | pages/recommend/result | 冲/稳/保 Tab + 院校卡片列表 |
| 4 | 院校详情页 | pages/school/detail | 院校信息 + 专业组 + 历年分数线 |
| 5 | 测评答题页 | pages/assess/test | MBTI + Holland 答题 |
| 6 | 测评结果页 | pages/assess/result | 性格类型 + 推荐专业 + 跳转推荐 |

## 数据来源

院校录取数据需从外部爬取或购买。MVP阶段覆盖：
- 全国主要本科院校（约1000所）
- 近3年录取数据（2023-2025）
- 覆盖全部省份的新老高考数据

## 不在MVP范围内的功能

以下功能留待后续迭代：
- 用户登录 / 微信授权
- 院校收藏 / 对比
- 高级筛选（地域、类型、排名等）
- 付费深度分析报告
- 一对一咨询入口
- 院校/专业搜索
- 志愿表生成与导出
