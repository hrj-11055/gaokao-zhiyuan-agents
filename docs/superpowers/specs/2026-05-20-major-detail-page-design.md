# 专业详情页设计

> 创建时间：2026-05-20

## 背景

MBTI 和 Holland 测评结果页有「专业推荐」卡片，点击后只弹 toast，没有跳转。需要新增专业详情页，补全这个交互。

## 范围

仅基于已有测评数据（MBTI/Holland type descriptions）展示，不调外部 API、不查数据库。

## 页面设计

### 路由

`/pages/major-detail/major-detail`

### 参数

| 参数 | 说明 |
|------|------|
| `name` | 专业名称（必填） |
| `source` | 来源：`mbti` 或 `holland`（必填） |
| `type` | MBTI 类型代码（如 INTJ）或 Holland 代码（如 RIA）（必填） |

### 页面内容

1. **顶部**：专业名称 + 简要描述
2. **推荐理由**：「基于你的 XX 类型，该专业与你的性格特征高度匹配」，列出 2-3 条匹配点（从该类型的 traits 中取）
3. **相关职业方向**：展示该类型推荐的全部 careers
4. **性格标签**：展示该类型的 tags
5. **底部**：「返回测评结果」按钮

### 数据来源

全部来自已有的 `mbti-questions.js` 和 `holland-questions.js` 中的 type descriptions 数据。描述文本复用各结果页已有的 `descMap`/`descs`。

## 改动清单

| 文件 | 改动 |
|------|------|
| `src/pages/major-detail/major-detail.vue` | 新增页面 |
| `src/pages.json` | 注册新路径 |
| `src/pages/mbti/mbti-result.vue` | `viewMajorDetail()` 改为 navigateTo |
| `src/pages/holland/holland-result.vue` | `viewMajorDetail()` 改为 navigateTo |

## 不做的事

- 不调 reports API 或数据库
- 不做专业搜索/列表
- 不加入 tabBar
