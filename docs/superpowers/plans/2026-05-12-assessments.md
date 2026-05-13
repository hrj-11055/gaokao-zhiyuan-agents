# 测评模块实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 MBTI 性格测试和霍兰德职业兴趣测试，配合现有五环问卷，建立完整的测评体系，并基于测评结果推荐相关专业。

**架构:** 底部 Tab 导航（首页/测评/我的）+ 三个独立测评页 + 结果页（联动专业推荐）。数据本地存储，专业标签匹配算法。

**Tech Stack:** UniApp (Vue 3), Vite, SCSS, 小程序 API

---

## 文件结构

```
gaokao-miniprogram/
├── src/
│   ├── pages/
│   │   ├── index/
│   │   │   └── index.vue              # [修改] 添加测评卡片入口
│   │   ├── assessments/               # [新增] 测评 tab 页
│   │   │   └── assessments.vue
│   │   ├── mbti/                      # [新增] MBTI 测评
│   │   │   ├── mbti.vue               # 测评题目页
│   │   │   └── mbti-result.vue        # 结果页
│   │   ├── holland/                   # [新增] 霍兰德测评
│   │   │   ├── holland.vue            # 测评题目页
│   │   │   └── holland-result.vue     # 结果页
│   │   ├── profile/                   # [新增] 我的 tab 页
│   │   │   └── profile.vue
│   │   ├── questionnaire/
│   │   │   └── questionnaire.vue      # [保持] 五环问卷
│   │   ├── report/
│   │   │   └── report.vue             # [保持] 报告页
│   │   └── chat/
│   │       └── chat.vue               # [保持] 对话页
│   ├── data/                          # [新增] 测评题库
│   │   ├── mbti-questions.js
│   │   └── holland-questions.js
│   ├── utils/
│   │   └── storage.js                 # [修改] 扩展测评存储
│   ├── static/                        # [新增] Tab 图标
│   │   ├── tab-home.png
│   │   ├── tab-home-active.png
│   │   ├── tab-assess.png
│   │   ├── tab-assess-active.png
│   │   ├── tab-profile.png
│   │   └── tab-profile-active.png
│   └── pages.json                     # [修改] 添加 Tab Bar 配置
└── data/
    └── 专业标签映射.js                 # [新增] 专业推荐标签映射
```

---

## Task 1: 配置底部 Tab Bar

**Files:**
- Modify: `src/pages.json`

- [ ] **Step 1: 修改 pages.json 添加 Tab Bar 配置**

```json
{
  "pages": [
    { "path": "pages/index/index", "style": { "navigationBarTitleText": "峰哥咨询参考", "navigationStyle": "custom", "navigationStyle": "custom" } },
    { "path": "pages/assessments/assessments", "style": { "navigationBarTitleText": "测评", "navigationBarBackgroundColor": "#FFFFFF", "navigationBarTextStyle": "black" } },
    { "path": "pages/profile/profile", "style": { "navigationBarTitleText": "我的", "navigationBarBackgroundColor": "#FFFFFF", "navigationBarTextStyle": "black" } },
    // ... 其他页面保持
  ],
  "tabBar": {
    "color": "#9CA3AF",
    "selectedColor": "#F97316",
    "backgroundColor": "#FFFFFF",
    "borderStyle": "white",
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页",
        "iconPath": "static/tab-home.png",
        "selectedIconPath": "static/tab-home-active.png"
      },
      {
        "pagePath": "pages/assessments/assessments",
        "text": "测评",
        "iconPath": "static/tab-assess.png",
        "selectedIconPath": "static/tab-assess-active.png"
      },
      {
        "pagePath": "pages/profile/profile",
        "text": "我的",
        "iconPath": "static/tab-profile.png",
        "selectedIconPath": "static/tab-profile-active.png"
      }
    ]
  },
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "峰哥咨询参考",
    "navigationBarBackgroundColor": "#FFFFFF",
    "backgroundColor": "#F9FAFB"
  }
}
```

- [ ] **Step 2: 创建临时占位图标（64x64px）**

运行: 创建简单的 PNG 图标，或先用 emoji 文字占位
```bash
# 暂时使用文字图标，后续可替换为设计稿
cd src/static
# 创建占位说明文件
echo "Tab 图标占位 - 需设计稿: 64x64px PNG" > tab-icons-placeholder.txt
```

- [ ] **Step 3: 提交**

```bash
git add src/pages.json
git commit -m "feat: add tab bar configuration"
```

---

## Task 2: 扩展存储模块支持测评数据

**Files:**
- Modify: `src/utils/storage.js`

- [ ] **Step 1: 在 storage.js 末尾添加测评相关存储函数**

```javascript
// ============ 测评相关存储 ============

const ASSESSMENTS_KEY = 'assessments'

/**
 * 规范化测评数据
 */
function normalizeAssessments(data = {}) {
  return {
    mbti: normalizeMbti(data.mbti || {}),
    holland: normalizeHolland(data.holland || {}),
    questionnaire: data.questionnaire || { answers: {}, completedCount: 0 },
    updatedAt: data.updatedAt || 0
  }
}

function normalizeMbti(mbti) {
  return {
    completed: Boolean(mbti.completed),
    type: mbti.type || '',
    scores: mbti.scores || { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 },
    answers: mbti.answers || {},
    completedAt: mbti.completedAt || 0
  }
}

function normalizeHolland(holland) {
  return {
    completed: Boolean(holland.completed),
    code: holland.code || '',
    scores: holland.scores || { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 },
    answers: holland.answers || {},
    completedAt: holland.completedAt || 0
  }
}

/**
 * 保存测评数据
 */
export function saveAssessments(asessments) {
  const data = normalizeAssessments({ ...asessments, updatedAt: Date.now() })
  uni.setStorageSync(ASSESSMENTS_KEY, JSON.stringify(data))
  return data
}

/**
 * 读取测评数据
 */
export function loadAssessments() {
  const data = uni.getStorageSync(ASSESSMENTS_KEY)
  if (!data) return normalizeAssessments({})
  try {
    return normalizeAssessments(JSON.parse(data))
  } catch {
    return normalizeAssessments({})
  }
}

/**
 * 保存 MBTI 测评
 */
export function saveMbtiResult(result) {
  const assessments = loadAssessments()
  assessments.mbti = normalizeMbti({ ...result, completed: true, completedAt: Date.now() })
  return saveAssessments(assessments).mbti
}

/**
 * 保存霍兰德测评
 */
export function saveHollandResult(result) {
  const assessments = loadAssessments()
  assessments.holland = normalizeHolland({ ...result, completed: true, completedAt: Date.now() })
  return saveAssessments(assessments).holland
}

/**
 * 保存测评答题进度
 */
export function saveMbtiProgress(questionIndex, answers) {
  const assessments = loadAssessments()
  assessments.mbti.answers = answers
  assessments.mbti.lastIndex = questionIndex
  saveAssessments(assessments)
}

export function saveHollandProgress(questionIndex, answers) {
  const assessments = loadAssessments()
  assessments.holland.answers = answers
  assessments.holland.lastIndex = questionIndex
  saveAssessments(assessments)
}

/**
 * 计算测评完成数量（0-3）
 */
export function getCompletedAssessmentsCount() {
  const assessments = loadAssessments()
  let count = 0
  if (assessments.questionnaire.completedCount >= 22) count++
  if (assessments.mbti.completed) count++
  if (assessments.holland.completed) count++
  return count
}

/**
 * 检查所有测评是否完成
 */
export function isAllAssessmentsCompleted() {
  return getCompletedAssessmentsCount() === 3
}
```

- [ ] **Step 2: 提交**

```bash
git add src/utils/storage.js
git commit -m "feat: add assessment storage functions"
```

---

## Task 3: 创建 MBTI 题库数据

**Files:**
- Create: `src/data/mbti-questions.js`

- [ ] **Step 1: 创建 MBTI 题库文件（48题）**

```javascript
/**
 * MBTI 性格测试题库
 * 48 题，每维度 12 题
 */

export const MBTI_QUESTIONS = [
  // E/I 维度 (外向/内向) - 12 题
  {
    id: 1,
    dimension: 'EI',
    text: '当你感到疲惫时，你更倾向于？',
    options: [
      { text: '独处静默恢复', value: 'I' },
      { text: '与朋友聊天放松', value: 'E' }
    ]
  },
  {
    id: 2,
    dimension: 'EI',
    text: '在社交场合中，你通常？',
    options: [
      { text: '主动认识新朋友', value: 'E' },
      { text: '只和熟悉的人交谈', value: 'I' }
    ]
  },
  {
    id: 3,
    dimension: 'EI',
    text: '你更喜欢的工作方式是？',
    options: [
      { text: '团队合作讨论', value: 'E' },
      { text: '独立专注完成', value: 'I' }
    ]
  },
  {
    id: 4,
    dimension: 'EI',
    text: '周末你更愿意？',
    options: [
      { text: '参加聚会活动', value: 'E' },
      { text: '在家休息看书', value: 'I' }
    ]
  },
  {
    id: 5,
    dimension: 'EI',
    text: '面对陌生人，你通常会？',
    options: [
      { text: '主动开启话题', value: 'E' },
      { text: '等待对方先说话', value: 'I' }
    ]
  },
  {
    id: 6,
    dimension: 'EI',
    text: '你更喜欢？',
    options: [
      { text: '热闹的环境', value: 'E' },
      { text: '安静的环境', value: 'I' }
    ]
  },
  {
    id: 7,
    dimension: 'EI',
    text: '在讨论中，你倾向于？',
    options: [
      { text: '边想边说', value: 'E' },
      { text: '想好再说', value: 'I' }
    ]
  },
  {
    id: 8,
    dimension: 'EI',
    text: '你的朋友圈是？',
    options: [
      { text: '广泛但不太深', value: 'E' },
      { text: '不多但很深入', value: 'I' }
    ]
  },
  {
    id: 9,
    dimension: 'EI',
    text: '遇到问题时，你首先会？',
    options: [
      { text: '找人讨论', value: 'E' },
      { text: '自己思考', value: 'I' }
    ]
  },
  {
    id: 10,
    dimension: 'EI',
    text: '你更喜欢？',
    options: [
      { text: '成为焦点', value: 'E' },
      { text: '低调观察', value: 'I' }
    ]
  },
  {
    id: 11,
    dimension: 'EI',
    text: '打电话时，你通常？',
    options: [
      { text: '喜欢长时间聊天', value: 'E' },
      { text: '简短说完挂断', value: 'I' }
    ]
  },
  {
    id: 12,
    dimension: 'EI',
    text: '你更倾向于？',
    options: [
      { text: '先行动后思考', value: 'E' },
      { text: '先思考后行动', value: 'I' }
    ]
  },

  // S/N 维度 (感觉/直觉) - 12 题
  {
    id: 13,
    dimension: 'SN',
    text: '你更关注？',
    options: [
      { text: '现实和细节', value: 'S' },
      { text: '可能性和含义', value: 'N' }
    ]
  },
  {
    id: 14,
    dimension: 'SN',
    text: '你更喜欢？',
    options: [
      { text: '具体的任务', value: 'S' },
      { text: '抽象的概念', value: 'N' }
    ]
  },
  {
    id: 15,
    dimension: 'SN',
    text: '你更相信？',
    options: [
      { text: '过往经验', value: 'S' },
      { text: '直觉预感', value: 'N' }
    ]
  },
  {
    id: 16,
    dimension: 'SN',
    text: '你更喜欢？',
    options: [
      { text: '按部就班', value: 'S' },
      { text: '随机应变', value: 'N' }
    ]
  },
  {
    id: 17,
    dimension: 'SN',
    text: '你更擅长？',
    options: [
      { text: '处理当下事务', value: 'S' },
      { text: '规划未来蓝图', value: 'N' }
    ]
  },
  {
    id: 18,
    dimension: 'SN',
    text: '你更喜欢？',
    options: [
      { text: '实用性强的事物', value: 'S' },
      { text: '有创意的事物', value: 'N' }
    ]
  },
  {
    id: 19,
    dimension: 'SN',
    text: '你更注重？',
    options: [
      { text: '事实本身', value: 'S' },
      { text: '事实背后的意义', value: 'N' }
    ]
  },
  {
    id: 20,
    dimension: 'SN',
    text: '你更喜欢？',
    options: [
      { text: '明确具体的信息', value: 'S' },
      { text: '宏观的描述', value: 'N' }
    ]
  },
  {
    id: 21,
    dimension: 'SN',
    text: '你更倾向于？',
    options: [
      { text: '传统可靠的方法', value: 'S' },
      { text: '创新的方法', value: 'N' }
    ]
  },
  {
    id: 22,
    dimension: 'SN',
    text: '你更喜欢？',
    options: [
      { text: '循序渐进', value: 'S' },
      { text: '跳跃式思考', value: 'N' }
    ]
  },
  {
    id: 23,
    dimension: 'SN',
    text: '你更擅长？',
    options: [
      { text: '观察细节', value: 'S' },
      { text: '发现规律', value: 'N' }
    ]
  },
  {
    id: 24,
    dimension: 'SN',
    text: '你更喜欢？',
    options: [
      { text: '实实在在的成果', value: 'S' },
      { text: '新的想法和理念', value: 'N' }
    ]
  },

  // T/F 维度 (思考/情感) - 12 题
  {
    id: 25,
    dimension: 'TF',
    text: '做决定时，你更看重？',
    options: [
      { text: '逻辑和原则', value: 'T' },
      { text: '人情和价值观', value: 'F' }
    ]
  },
  {
    id: 26,
    dimension: 'TF',
    text: '你更倾向于？',
    options: [
      { text: '客观分析问题', value: 'T' },
      { text: '考虑他人感受', value: 'F' }
    ]
  },
  {
    id: 27,
    dimension: 'TF',
    text: '你认为更重要的是？',
    options: [
      { text: '真理', value: 'T' },
      { text: '和谐', value: 'F' }
    ]
  },
  {
    id: 28,
    dimension: 'TF',
    text: '你更容易被什么说服？',
    options: [
      { text: '数据论证', value: 'T' },
      { text: '情感故事', value: 'F' }
    ]
  },
  {
    id: 29,
    dimension: 'TF',
    text: '评价他人时，你更看重？',
    options: [
      { text: '能力和效率', value: 'T' },
      { text: '态度和努力', value: 'F' }
    ]
  },
  {
    id: 30,
    dimension: 'TF',
    text: '你更擅长？',
    options: [
      { text: '指出问题', value: 'T' },
      { text: '鼓励他人', value: 'F' }
    ]
  },
  {
    id: 31,
    dimension: 'TF',
    text: '冲突中你倾向于？',
    options: [
      { text: '辩论解决', value: 'T' },
      { text: '妥协调和', value: 'F' }
    ]
  },
  {
    id: 32,
    dimension: 'TF',
    text: '你更注重？',
    options: [
      { text: '公平公正', value: 'T' },
      { text: '仁慈同情', value: 'F' }
    ]
  },
  {
    id: 33,
    dimension: 'TF',
    text: '你更喜欢？',
    options: [
      { text: '直接指出错误', value: 'T' },
      { text: '委婉表达建议', value: 'F' }
    ]
  },
  {
    id: 34,
    dimension: 'TF',
    text: '你认为更好的领导方式是？',
    options: [
      { text: '公正严明', value: 'T' },
      { text: '关怀体贴', value: 'F' }
    ]
  },
  {
    id: 35,
    dimension: 'TF',
    text: '你更看重？',
    options: [
      { text: '理性决策', value: 'T' },
      { text: '人际和谐', value: 'F' }
    ]
  },
  {
    id: 36,
    dimension: 'TF',
    text: '你更容易接受？',
    options: [
      { text: '批评建议', value: 'T' },
      { text: '赞美鼓励', value: 'F' }
    ]
  },

  // J/P 维度 (判断/感知) - 12 题
  {
    id: 37,
    dimension: 'JP',
    text: '你更喜欢？',
    options: [
      { text: '有计划地做事', value: 'J' },
      { text: '灵活应变', value: 'P' }
    ]
  },
  {
    id: 38,
    dimension: 'JP',
    text: '你的工作风格是？',
    options: [
      { text: '提前规划完成', value: 'J' },
      { text: '截止前冲刺', value: 'P' }
    ]
  },
  {
    id: 39,
    dimension: 'JP',
    text: '你更喜欢？',
    options: [
      { text: '事情确定下来', value: 'J' },
      { text: '保留选择余地', value: 'P' }
    ]
  },
  {
    id: 40,
    dimension: 'JP',
    text: '面对变化，你倾向于？',
    options: [
      { text: '希望能提前知道', value: 'J' },
      { text: '喜欢惊喜', value: 'P' }
    ]
  },
  {
    id: 41,
    dimension: 'JP',
    text: '你的日常习惯是？',
    options: [
      { text: '井井有条', value: 'J' },
      { text: '随性而为', value: 'P' }
    ]
  },
  {
    id: 42,
    dimension: 'JP',
    text: '你更喜欢？',
    options: [
      { text: '完成任务后再放松', value: 'J' },
      { text: '边工作边娱乐', value: 'P' }
    ]
  },
  {
    id: 43,
    dimension: 'JP',
    text: '面对多项任务，你会？',
    options: [
      { text: '列清单逐一完成', value: 'J' },
      { text: '看心情做哪个', value: 'P' }
    ]
  },
  {
    id: 44,
    dimension: 'JP',
    text: '你更倾向于？',
    options: [
      { text: '设定明确目标', value: 'J' },
      { text: '顺其自然', value: 'P' }
    ]
  },
  {
    id: 45,
    dimension: 'JP',
    text: '旅行时你喜欢？',
    options: [
      { text: '详细计划行程', value: 'J' },
      { text: '到了再说', value: 'P' }
    ]
  },
  {
    id: 46,
    dimension: 'JP',
    text: '你更喜欢？',
    options: [
      { text: '有条不紊的环境', value: 'J' },
      { text: '灵活多变的环境', value: 'P' }
    ]
  },
  {
    id: 47,
    dimension: 'JP',
    text: '面对截止日期，你通常会？',
    options: [
      { text: '提前完成', value: 'J' },
      { text: '最后时刻完成', value: 'P' }
    ]
  },
  {
    id: 48,
    dimension: 'JP',
    text: '你认为生活应该？',
    options: [
      { text: '有规划有节奏', value: 'J' },
      { text: '随性自由', value: 'P' }
    ]
  }
]

/**
 * MBTI 类型描述
 */
export const MBTI_TYPE_DESCRIPTIONS = {
  'INTJ': {
    name: '建筑师',
    tags: ['逻辑', '研究', '技术', '系统', '独立'],
    traits: ['战略思维强，追求独立', '善于发现系统中的问题', '喜欢深度思考，追求效率'],
    careers: ['软件开发', '数据分析', '科研工作', '系统架构'],
    majors: ['计算机科学与技术', '数学与应用数学', '软件工程', '数据科学']
  },
  'INTP': {
    name: '逻辑学家',
    tags: ['逻辑', '研究', '理论', '分析', '独立'],
    traits: ['好奇心强，热爱探索', '擅长抽象思维', '喜欢解决复杂问题'],
    careers: ['科学研究', '算法开发', '哲学研究', '数学研究'],
    majors: ['数学', '物理学', '哲学', '计算机科学']
  },
  'ENTJ': {
    name: '指挥官',
    tags: ['领导', '创新', '商业', '技术', '管理'],
    traits: ['天生的领导者', '目标导向，执行力强', '喜欢挑战和竞争'],
    careers: ['企业管理', '创业', '项目经理', '咨询顾问'],
    majors: ['工商管理', '经济学', '法学', '项目管理']
  },
  'ENTP': {
    name: '辩论家',
    tags: ['创新', '商业', '技术', '辩论', '灵活'],
    traits: ['思维敏捷，善于辩论', '喜欢尝试新事物', '创新能力强'],
    careers: ['创业', '产品经理', '市场营销', '咨询'],
    majors: ['市场营销', '创业管理', '产品设计', '传播学']
  },
  'INFJ': {
    name: '提倡者',
    tags: ['理想', '教育', '人文', '心理', '艺术'],
    traits: ['理想主义，富有同情心', '洞察力强', '追求意义和价值'],
    careers: ['心理咨询', '教育', '社会工作', '写作'],
    majors: ['心理学', '教育学', '社会学', '文学']
  },
  'INFP': {
    name: '调停者',
    tags: ['艺术', '人文', '写作', '理想', '创意'],
    traits: ['真诚友善，追求和谐', '丰富的内心世界', '富有创造力'],
    careers: ['写作', '艺术创作', '编辑', '心理咨询'],
    majors: ['汉语言文学', '艺术设计', '心理学', '新闻传播']
  },
  'ENFJ': {
    name: '主人公',
    tags: ['领导', '教育', '人际', '演讲', '激励'],
    traits: ['热情洋溢，善于激励', '关心他人成长', '天生的教育者'],
    careers: ['教育培训', '人力资源管理', '公关', '政治'],
    majors: ['教育学', '人力资源管理', '新闻学', '公共管理']
  },
  'ENFP': {
    name: '竞选者',
    tags: ['创意', '人际', '艺术', '媒体', '灵活'],
    traits: ['充满热情，富有想象力', '善于交际', '喜欢探索可能性'],
    careers: ['媒体传播', '创意策划', '市场营销', '演艺'],
    majors: ['新闻传播', '广告学', '表演艺术', '市场营销']
  },
  'ISTJ': {
    name: '物流师',
    tags: ['组织', '财务', '行政', '细节', '可靠'],
    traits: ['认真负责，注重细节', '喜欢有序的环境', '值得信赖'],
    careers: ['会计', '行政管理', '审计', '数据录入'],
    majors: ['会计学', '财务管理', '行政管理', '统计学']
  },
  'ISFJ': {
    name: '守卫者',
    tags: ['服务', '医疗', '教育', '细节', '关怀'],
    traits: ['温暖体贴，乐于助人', '注重细节', '默默奉献'],
    careers: ['护理', '教育', '行政支持', '客户服务'],
    majors: ['护理学', '教育学', '社会工作', '医学技术']
  },
  'ESTJ': {
    name: '总经理',
    tags: ['管理', '组织', '执行', '领导', '效率'],
    traits: ['高效务实，善于组织', '重视规则和秩序', '优秀的执行者'],
    careers: ['企业管理', '政府官员', '项目经理', '军官'],
    majors: ['工商管理', '公共管理', '法学', '工程管理']
  },
  'ESFJ': {
    name: '执政官',
    tags: ['服务', '教育', '医疗', '人际', '和谐'],
    traits: ['热心肠，喜欢帮助他人', '重视传统和规则', '团队合作者'],
    careers: ['护理', '教育', '销售', '客服'],
    majors: ['护理学', '教育学', '市场营销', '酒店管理']
  },
  'ISTP': {
    name: '鉴赏家',
    tags: ['技术', '动手', '工程', '实践', '灵活'],
    traits: ['冷静理性，动手能力强', '擅长解决实际问题', '喜欢独立工作'],
    careers: ['工程技术', '机械维修', '精密制造', '飞行员'],
    majors: ['机械工程', '自动化', '飞行技术', '土木工程']
  },
  'ISFP': {
    name: '探险家',
    tags: ['艺术', '设计', '动手', '灵活', '审美'],
    traits: ['温和友善，富有艺术感', '活在当下', '喜欢自由'],
    careers: ['艺术设计', '时尚设计', '摄影', '手工艺'],
    majors: ['艺术设计', '服装设计', '摄影', '景观设计']
  },
  'ESTP': {
    name: '企业家',
    tags: ['商业', '销售', '运动', '实践', '冒险'],
    traits: ['行动力强，敢于冒险', '擅长应对危机', '现实主义者'],
    careers: ['销售', '运动员', '创业', '急救'],
    majors: ['体育教育', '市场营销', '工商管理', '国际贸易']
  },
  'ESFP': {
    name: '表演者',
    tags: ['表演', '娱乐', '服务', '人际', '热情'],
    traits: ['热情开朗，喜欢社交', '活在当下', '带给他人快乐'],
    careers: ['演艺', '主持', '活动策划', '旅游服务'],
    majors: ['表演艺术', '播音主持', '旅游管理', ' event 管理']
  }
}

/**
 * 计算 MBTI 类型
 * @param {Object} answers - { questionId: optionValue }
 * @returns {{ type: string, scores: Object }}
 */
export function calculateMbtiType(answers) {
  const scores = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 }

  MBTI_QUESTIONS.forEach(q => {
    const answer = answers[q.id]
    if (answer) {
      scores[answer]++
    }
  })

  const type = [
    scores.E >= scores.I ? 'E' : 'I',
    scores.S >= scores.N ? 'S' : 'N',
    scores.T >= scores.F ? 'T' : 'F',
    scores.J >= scores.P ? 'J' : 'P'
  ].join('')

  return { type, scores }
}
```

- [ ] **Step 2: 提交**

```bash
git add src/data/mbti-questions.js
git commit -m "feat: add MBTI question bank (48 questions)"
```

---

## Task 4: 创建霍兰德题库数据

**Files:**
- Create: `src/data/holland-questions.js`

- [ ] **Step 1: 创建霍兰德题库文件（60题）**

```javascript
/**
 * 霍兰德职业兴趣测试题库
 * 60 题，每类型 10 题
 * R=现实型 I=研究型 A=艺术型 S=社会型 E=企业型 C=常规型
 */

export const HOLLAND_QUESTIONS = [
  // R - 现实型 (10题)
  { id: 1, type: 'R', text: '我喜欢修理电器、机械', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 2, type: 'R', text: '我喜欢使用工具、机器工作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 3, type: 'R', text: '我喜欢户外活动', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 4, type: 'R', text: '我喜欢动手制作东西', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 5, type: 'R', text: '我喜欢种植花草或饲养动物', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 6, type: 'R', text: '我喜欢了解机械的运作原理', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 7, type: 'R', text: '我喜欢从事需要体力的工作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 8, type: 'R', text: '我喜欢操作精密仪器', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 9, type: 'R', text: '我喜欢组装模型或家具', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 10, type: 'R', text: '我不介意工作环境比较脏乱', options: ['非常像', '比较像', '不像', '完全不像'] },

  // I - 研究型 (10题)
  { id: 11, type: 'I', text: '我喜欢研究科学问题', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 12, type: 'I', text: '我喜欢阅读科学类书籍', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 13, type: 'I', text: '我喜欢解决复杂的数学问题', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 14, type: 'I', text: '我喜欢了解事物背后的原理', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 15, type: 'I', text: '我喜欢做实验', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 16, type: 'I', text: '我喜欢分析数据', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 17, type: 'I', text: '我喜欢独立思考', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 18, type: 'I', text: '我喜欢学习新知识', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 19, type: 'I', text: '我喜欢探索未知领域', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 20, type: 'I', text: '我不介意长时间专注研究', options: ['非常像', '比较像', '不像', '完全不像'] },

  // A - 艺术型 (10题)
  { id: 21, type: 'A', text: '我喜欢创作艺术作品', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 22, type: 'A', text: '我喜欢欣赏音乐、戏剧', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 23, type: 'A', text: '我喜欢从事创造性工作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 24, type: 'A', text: '我喜欢表达自己的想法', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 25, type: 'A', text: '我喜欢追求美感', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 26, type: 'A', text: '我喜欢设计东西', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 27, type: 'A', text: '我喜欢写作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 28, type: 'A', text: '我喜欢自由的工作方式', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 29, type: 'A', text: '我有丰富的想象力', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 30, type: 'A', text: '我不喜欢按部就班的工作', options: ['非常像', '比较像', '不像', '完全不像'] },

  // S - 社会型 (10题)
  { id: 31, type: 'S', text: '我喜欢帮助他人', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 32, type: 'S', text: '我喜欢与人交流', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 33, type: 'S', text: '我喜欢教育工作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 34, type: 'S', text: '我喜欢参加团体活动', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 35, type: 'S', text: '我关心社会问题', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 36, type: 'S', text: '我喜欢倾听他人的烦恼', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 37, type: 'S', text: '我愿意为他人牺牲自己的时间', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 38, type: 'S', text: '我喜欢团队合作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 39, type: 'S', text: '我善于理解他人的感受', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 40, type: 'S', text: '我从事服务性质的工作让我感到满足', options: ['非常像', '比较像', '不像', '完全不像'] },

  // E - 企业型 (10题)
  { id: 41, type: 'E', text: '我喜欢领导他人', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 42, type: 'E', text: '我喜欢影响别人的看法', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 43, type: 'E', text: '我喜欢销售工作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 44, type: 'E', text: '我喜欢竞争', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 45, type: 'E', text: '我喜欢追求财富和地位', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 46, type: 'E', text: '我喜欢演讲', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 47, type: 'E', text: '我喜欢创业', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 48, type: 'E', text: '我喜欢做决策', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 49, type: 'E', text: '我喜欢接受挑战', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 50, type: 'E', text: '我希望成为管理者', options: ['非常像', '比较像', '不像', '完全不像'] },

  // C - 常规型 (10题)
  { id: 51, type: 'C', text: '我喜欢按计划办事', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 52, type: 'C', text: '我喜欢处理数据', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 53, type: 'C', text: '我喜欢整理文件', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 54, type: 'C', text: '我喜欢有序的环境', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 55, type: 'C', text: '我喜欢准确的工作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 56, type: 'C', text: '我喜欢遵守规则', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 57, type: 'C', text: '我喜欢重复性工作', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 58, type: 'C', text: '我喜欢档案管理', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 59, type: 'C', text: '我注重细节', options: ['非常像', '比较像', '不像', '完全不像'] },
  { id: 60, type: 'C', text: '我不喜欢工作中有太多变数', options: ['非常像', '比较像', '不像', '完全不像'] }
]

/**
 * 霍兰德类型描述
 */
export const HOLLAND_TYPE_DESCRIPTIONS = {
  'RIA': {
    name: '现实+艺术+研究',
    tags: ['技术', '艺术', '动手', '设计', '创造'],
    traits: ['擅长动手操作', '有艺术创造力', '喜欢探索原理'],
    careers: ['工业设计', '建筑', '珠宝设计', '摄影'],
    majors: ['工业设计', '建筑学', '珠宝设计', '摄影']
  },
  'RIS': {
    name: '现实+研究+社会',
    tags: ['技术', '医疗', '动手', '研究', '服务'],
    traits: ['动手能力强', '喜欢钻研', '乐于助人'],
    careers: ['医生', '牙医', '物理治疗', '兽医'],
    majors: ['临床医学', '口腔医学', '康复治疗学', '动物医学']
  },
  'RIE': {
    name: '现实+研究+企业',
    tags: ['技术', '研究', '商业', '管理', '创新'],
    traits: ['技术背景', '商业思维', '创新能力'],
    careers: ['技术总监', '创业', '产品经理', '咨询'],
    majors: ['工程管理', '技术经济', '工商管理', '项目管理']
  },
  'RIC': {
    name: '现实+研究+常规',
    tags: ['技术', '数据', '分析', '系统', '精确'],
    traits: ['注重细节', '分析能力强', '有条理'],
    careers: ['数据分析师', '质量管理', '审计', '系统分析师'],
    majors: ['统计学', '信息管理与信息系统', '审计学', '质量管理工程']
  },
  'RAS': {
    name: '现实+艺术+社会',
    tags: ['动手', '艺术', '教育', '服务', '创意'],
    traits: ['动手能力强', '有艺术感', '善于沟通'],
    careers: ['美术老师', '职业治疗师', '室内设计', '手工艺'],
    majors: ['美术教育', '职业治疗学', '室内设计', '工艺美术']
  },
  'RAE': {
    name: '现实+艺术+企业',
    tags: ['技术', '艺术', '商业', '创意', '营销'],
    traits: ['有创意', '商业意识', '执行力强'],
    careers: ['创意总监', '广告创意', '品牌设计', '创业'],
    majors: ['广告学', '品牌管理', '产品设计', '市场营销']
  },
  'RAC': {
    name: '现实+艺术+常规',
    tags: ['技术', '艺术', '细节', '规范', '设计'],
    traits: ['注重细节', '有美感', '遵守规范'],
    careers: ['平面设计', '制图', '档案管理', '编辑'],
    majors: ['视觉传达设计', '制图工程', '档案学', '编辑出版学']
  },
  'RIS': {
    name: '现实+社会+研究',
    tags: ['医疗', '技术', '服务', '研究', '关怀'],
    traits: ['关怀他人', '技术能力', '研究精神'],
    careers: ['护理', '康复治疗', '医学技术', '健康教育'],
    majors: ['护理学', '康复治疗学', '医学检验技术', '健康服务与管理']
  },
  'RIE': {
    name: '现实+企业+研究',
    tags: ['技术', '商业', '创新', '领导', '执行'],
    traits: ['技术专长', '领导能力', '商业思维'],
    careers: ['工程经理', '技术创业', '销售工程师', '项目管理'],
    majors: ['工程管理', '市场营销', '技术经济', '项目管理']
  },
  'RSC': {
    name: '现实+社会+常规',
    tags: ['服务', '规范', '执行', '稳定', '协助'],
    traits: ['乐于助人', '遵守规则', '踏实可靠'],
    careers: ['行政', '客服', '银行柜员', '图书管理'],
    majors: ['行政管理', '公共事业管理', '金融服务', '信息资源管理']
  },
  'RSA': {
    name: '现实+社会+艺术',
    tags: ['教育', '艺术', '服务', '创意', '沟通'],
    traits: ['善于沟通', '有创意', '乐于助人'],
    careers: ['教师', '培训师', '社会工作者', '活动策划'],
    majors: ['教育学', '社会工作', '公共关系学', '会展经济与管理']
  },
  'RSE': {
    name: '现实+社会+企业',
    tags: ['服务', '管理', '销售', '人际', '领导'],
    traits: ['善于沟通', '领导能力', '服务意识'],
    careers: ['销售经理', '客户经理', '人力资源', '培训主管'],
    majors: ['人力资源管理', '市场营销', '工商管理', '公共事业管理']
  },
  'RES': {
    name: '现实+企业+社会',
    tags: ['商业', '服务', '人际', '销售', '管理'],
    traits: ['商业意识', '善于沟通', '执行力强'],
    careers: ['销售', '公关', '市场推广', '客户服务'],
    majors: ['市场营销', '公共关系学', '广告学', '工商管理']
  },
  'REC': {
    name: '现实+企业+常规',
    tags: ['管理', '规范', '执行', '组织', '效率'],
    traits: ['组织能力强', '注重效率', '遵守规则'],
    careers: ['项目经理', '生产管理', '运营主管', '办公室管理'],
    majors: ['工商管理', '管理科学', '工程管理', '行政管理']
  },
  'REI': {
    name: '现实+企业+研究',
    tags: ['技术', '商业', '创新', '分析', '领导'],
    traits: ['技术背景', '商业思维', '创新能力'],
    careers: ['技术总监', '产品经理', '创业', '咨询'],
    majors: ['工程管理', '技术经济', '工商管理', '信息管理']
  },
  'RCE': {
    name: '现实+常规+企业',
    tags: ['财务', '商业', '规范', '数据', '管理'],
    traits: ['注重细节', '商业意识', '有条理'],
    careers: ['会计', '财务分析', '审计', '银行'],
    majors: ['会计学', '财务管理', '审计学', '金融学']
  },
  'IAS': {
    name: '研究+艺术+社会',
    tags: ['研究', '艺术', '教育', '人文', '创意'],
    traits: ['有创意', '喜欢研究', '善于沟通'],
    careers: ['大学教授', '研究员', '艺术治疗', '文化研究'],
    majors: ['心理学', '艺术教育', '社会学', '文化产业管理']
  },
  'IAE': {
    name: '研究+艺术+企业',
    tags: ['创意', '商业', '研究', '设计', '营销'],
    traits: ['有创意', '商业思维', '研究能力'],
    careers: ['创意总监', '设计总监', '品牌策划', '市场研究'],
    majors: ['设计学', '品牌管理', '市场营销', '广告学']
  },
  'IAR': {
    name: '研究+艺术+现实',
    tags: ['技术', '艺术', '研究', '设计', '创新'],
    traits: ['动手能力强', '有创意', '喜欢研究'],
    careers: ['建筑', '工业设计', ' UX 设计', '游戏设计'],
    majors: ['建筑学', '工业设计', '数字媒体技术', '游戏设计']
  },
  'ISE': {
    name: '研究+社会+企业',
    tags: ['研究', '人际', '商业', '咨询', '教育'],
    traits: ['研究能力', '善于沟通', '商业思维'],
    careers: ['管理咨询', '市场研究', '大学教授', '培训师'],
    majors: ['工商管理', '心理学', '市场营销', '教育学']
  },
  'ISA': {
    name: '研究+社会+艺术',
    tags: ['人文', '教育', '艺术', '研究', '创意'],
    traits: ['有创意', '关心社会', '喜欢研究'],
    careers: ['社会学研究', '文化研究', '艺术教育', '心理咨询'],
    majors: ['社会学', '心理学', '艺术教育', '文化产业管理']
  },
  'ISC': {
    name: '研究+社会+常规',
    tags: ['数据', '研究', '服务', '规范', '分析'],
    traits: ['分析能力强', '乐于助人', '有条理'],
    careers: ['数据分析师', '教育统计', '心理咨询', '研究助理'],
    majors: ['统计学', '心理学', '应用心理学', '信息管理']
  },
  'IRA': {
    name: '研究+现实+艺术',
    tags: ['技术', '设计', '研究', '创新', '动手'],
    traits: ['动手能力强', '有创意', '喜欢研究'],
    careers: ['建筑', '工业设计', ' UX 设计', '游戏开发'],
    majors: ['建筑学', '工业设计', '人机交互', '数字媒体技术']
  },
  'IRE': {
    name: '研究+现实+企业',
    tags: ['技术', '商业', '研究', '创新', '管理'],
    traits: ['技术背景', '商业思维', '研究能力'],
    careers: ['技术总监', '产品经理', '研发管理', '技术顾问'],
    majors: ['工程管理', '技术经济', '信息管理', '项目管理']
  },
  'IRS': {
    name: '研究+现实+社会',
    tags: ['技术', '医疗', '研究', '服务', '关怀'],
    traits: ['技术能力', '关怀他人', '研究精神'],
    careers: ['医生', '医学研究', '康复治疗', '健康顾问'],
    majors: ['临床医学', '医学影像学', '康复治疗学', '公共卫生']
  },
  'IRC': {
    name: '研究+现实+常规',
    tags: ['技术', '数据', '分析', '规范', '系统'],
    traits: ['分析能力强', '注重细节', '有条理'],
    careers: ['数据分析师', '质量管理', '系统分析师', '统计'],
    majors: ['统计学', '信息管理与信息系统', '质量管理工程', '数据科学']
  },
  'ISE': {
    name: '研究+社会+企业',
    tags: ['教育', '商业', '研究', '咨询', '培训'],
    traits: ['善于沟通', '研究能力', '商业思维'],
    careers: ['大学教授', '管理咨询', '培训师', '教育科技'],
    majors: ['教育学', '工商管理', '心理学', '教育技术学']
  },
  'ISA': {
    name: '研究+社会+艺术',
    tags: ['人文', '艺术', '教育', '研究', '创意'],
    traits: ['有创意', '关心社会', '研究能力'],
    careers: ['社会学研究', '文化研究', '艺术教育', '媒体研究'],
    majors: ['社会学', '心理学', '艺术教育', '新闻传播学']
  },
  'ISC': {
    name: '研究+社会+常规',
    tags: ['数据', '服务', '研究', '规范', '分析'],
    traits: ['分析能力强', '乐于助人', '有条理'],
    careers: ['教育统计', '心理咨询', '社会研究', '数据分析'],
    majors: ['统计学', '心理学', '社会学', '信息管理']
  },
  'AIS': {
    name: '艺术+研究+社会',
    tags: ['艺术', '人文', '教育', '创意', '研究'],
    traits: ['有创意', '喜欢研究', '善于沟通'],
    careers: ['艺术教育', '文化研究', '创意写作', '媒体'],
    majors: ['艺术教育', '汉语言文学', '新闻学', '文化产业管理']
  },
  'AIE': {
    name: '艺术+研究+企业',
    tags: ['创意', '商业', '设计', '营销', '品牌'],
    traits: ['有创意', '商业思维', '研究能力'],
    careers: ['创意总监', '品牌策划', '设计总监', '广告'],
    majors: ['广告学', '品牌管理', '设计学', '市场营销']
  },
  'AIR': {
    name: '艺术+研究+现实',
    tags: ['设计', '技术', '艺术', '创新', '动手'],
    traits: ['有创意', '动手能力强', '喜欢研究'],
    careers: ['工业设计', '建筑', ' UX 设计', '游戏设计'],
    majors: ['工业设计', '建筑学', '数字媒体技术', '游戏设计']
  },
  'ASE': {
    name: '艺术+社会+企业',
    tags: ['媒体', '创意', '人际', '营销', '传播'],
    traits: ['有创意', '善于沟通', '商业意识'],
    careers: ['媒体策划', '公关', '活动策划', '内容营销'],
    majors: ['广告学', '公共关系学', '新闻传播', '市场营销']
  },
  'ASI': {
    name: '艺术+社会+研究',
    tags: ['人文', '艺术', '教育', '研究', '创意'],
    traits: ['有创意', '关心社会', '研究能力'],
    careers: ['艺术教育', '文化研究', '媒体评论', '创意研究'],
    majors: ['艺术教育', '汉语言文学', '新闻学', '文化产业管理']
  },
  'AER': {
    name: '艺术+企业+现实',
    tags: ['创意', '商业', '技术', '设计', '执行'],
    traits: ['有创意', '执行力强', '商业思维'],
    careers: ['产品设计师', '创意创业者', '设计总监', '广告创意'],
    majors: ['产品设计', '设计学', '广告学', '工商管理']
  },
  'AES': {
    name: '艺术+企业+社会',
    tags: ['媒体', '创意', '商业', '人际', '传播'],
    traits: ['有创意', '善于沟通', '商业意识'],
    careers: ['媒体人', '公关总监', '活动策划', '内容创作者'],
    majors: ['新闻传播', '广告学', '公共关系', '广播电视编导']
  },
  'AEC': {
    name: '艺术+企业+常规',
    tags: ['创意', '商业', '规范', '执行', '管理'],
    traits: ['有创意', '有条理', '商业思维'],
    careers: ['创意管理', '品牌管理', '广告公司管理', '项目管理'],
    majors: ['工商管理', '广告学', '品牌管理', '文化产业管理']
  },
  'ARE': {
    name: '艺术+现实+企业',
    tags: ['设计', '技术', '商业', '创意', '执行'],
    traits: ['有创意', '动手能力强', '商业意识'],
    careers: ['工业设计', '创意创业', '产品设计', '品牌设计'],
    majors: ['工业设计', '产品设计', '设计学', '广告学']
  },
  'ARS': {
    name: '艺术+现实+社会',
    tags: ['设计', '教育', '服务', '创意', '沟通'],
    traits: ['有创意', '善于沟通', '动手能力强'],
    careers: ['设计教师', '职业治疗师', '手工艺', '社会设计'],
    majors: ['设计教育', '职业治疗学', '工艺美术', '社会工作']
  },
  'ARC': {
    name: '艺术+现实+常规',
    tags: ['设计', '规范', '细节', '技术', '执行'],
    traits: ['有创意', '注重细节', '遵守规范'],
    careers: ['平面设计', '制图', '档案管理', '编辑'],
    majors: ['视觉传达设计', '编辑出版学', '档案学', '数字出版']
  },
  'ASC': {
    name: '艺术+社会+常规',
    tags: ['教育', '媒体', '规范', '服务', '传播'],
    traits: ['有创意', '善于沟通', '有条理'],
    careers: ['编辑', '教师', '媒体策划', '行政管理'],
    majors: ['新闻传播', '编辑出版', '教育学', '行政管理']
  },
  'SAE': {
    name: '社会+艺术+企业',
    tags: ['媒体', '创意', '人际', '商业', '传播'],
    traits: ['善于沟通', '有创意', '商业意识'],
    careers: ['媒体人', '公关', '活动策划', '内容营销'],
    majors: ['新闻传播', '广告学', '公共关系', '市场营销']
  },
  'SAC': {
    name: '社会+艺术+常规',
    tags: ['教育', '媒体', '服务', '规范', '创意'],
    traits: ['善于沟通', '有创意', '有条理'],
    careers: ['教师', '编辑', '媒体策划', '行政'],
    majors: ['教育学', '新闻传播', '编辑出版', '行政管理']
  },
  'SER': {
    name: '社会+企业+研究',
    tags: ['商业', '人际', '研究', '咨询', '培训'],
    traits: ['善于沟通', '研究能力', '商业思维'],
    careers: ['管理咨询', '培训师', '市场研究', '人力资源'],
    majors: ['工商管理', '心理学', '市场营销', '人力资源管理']
  },
  'SEI': {
    name: '社会+企业+研究',
    tags: ['商业', '研究', '人际', '分析', '咨询'],
    traits: ['善于沟通', '分析能力', '商业思维'],
    careers: ['管理咨询', '市场研究', '大学教授', '分析师'],
    majors: ['工商管理', '心理学', '市场营销', '应用统计学']
  },
  'SRC': {
    name: '社会+现实+常规',
    tags: ['服务', '规范', '执行', '稳定', '协助'],
    traits: ['乐于助人', '遵守规则', '踏实可靠'],
    careers: ['行政', '客服', '银行柜员', '图书管理'],
    majors: ['行政管理', '公共事业管理', '金融服务', '信息资源管理']
  },
  'SRE': {
    name: '社会+现实+企业',
    tags: ['服务', '商业', '人际', '销售', '管理'],
    traits: ['善于沟通', '商业意识', '执行力强'],
    careers: ['销售经理', '客户经理', '人力资源', '培训主管'],
    majors: ['市场营销', '人力资源管理', '工商管理', '公共事业管理']
  },
  'SRI': {
    name: '社会+研究+现实',
    tags: ['医疗', '技术', '服务', '研究', '关怀'],
    traits: ['关怀他人', '技术能力', '研究精神'],
    careers: ['医生', '康复治疗', '医学研究', '健康教育'],
    majors: ['临床医学', '康复治疗学', '医学检验技术', '公共卫生']
  },
  'SIC': {
    name: '社会+研究+常规',
    tags: ['数据', '服务', '研究', '规范', '分析'],
    traits: ['分析能力强', '乐于助人', '有条理'],
    careers: ['教育统计', '心理咨询', '研究助理', '数据分析'],
    majors: ['统计学', '心理学', '应用心理学', '信息管理']
  },
  'SAR': {
    name: '社会+艺术+现实',
    tags: ['教育', '艺术', '服务', '创意', '动手'],
    traits: ['善于沟通', '有创意', '动手能力强'],
    careers: ['美术老师', '职业治疗师', '活动策划', '手工艺'],
    majors: ['美术教育', '职业治疗学', '社会工作', '工艺美术']
  },
  'SCE': {
    name: '社会+常规+企业',
    tags: ['服务', '管理', '规范', '人际', '组织'],
    traits: ['善于沟通', '有条理', '组织能力'],
    careers: ['人力资源', '行政管理', '办公室管理', '客户服务'],
    majors: ['人力资源管理', '行政管理', '工商管理', '公共事业管理']
  },
  'EAS': {
    name: '企业+艺术+社会',
    tags: ['媒体', '创意', '商业', '人际', '传播'],
    traits: ['善于沟通', '有创意', '商业意识'],
    careers: ['媒体策划', '公关', '活动策划', '内容营销'],
    majors: ['广告学', '公共关系', '新闻传播', '市场营销']
  },
  'EAC': {
    name: '企业+艺术+常规',
    tags: ['创意', '商业', '规范', '管理', '执行'],
    traits: ['有创意', '有条理', '商业思维'],
    careers: ['创意管理', '品牌管理', '项目管理', '广告管理'],
    majors: ['工商管理', '广告学', '品牌管理', '文化产业管理']
  },
  'EAI': {
    name: '企业+艺术+研究',
    tags: ['创意', '商业', '研究', '设计', '分析'],
    traits: ['有创意', '商业思维', '研究能力'],
    careers: ['创意总监', '品牌策划', '设计总监', '市场研究'],
    majors: ['设计学', '品牌管理', '市场营销', '广告学']
  },
  'EAS': {
    name: '企业+艺术+社会',
    tags: ['媒体', '创意', '商业', '人际', '传播'],
    traits: ['善于沟通', '有创意', '商业意识'],
    careers: ['媒体人', '公关', '活动策划', '内容创作者'],
    majors: ['新闻传播', '广告学', '公共关系', '市场营销']
  },
  'ECI': {
    name: '企业+常规+研究',
    tags: ['商业', '数据', '分析', '规范', '财务'],
    traits: ['商业思维', '分析能力强', '有条理'],
    careers: ['财务分析', '投资分析', '审计', '数据分析师'],
    majors: ['财务管理', '会计学', '金融学', '统计学']
  },
  'ERA': {
    name: '企业+研究+艺术',
    tags: ['商业', '创意', '研究', '设计', '创新'],
    traits: ['商业思维', '有创意', '研究能力'],
    careers: ['产品经理', '创意总监', '品牌策划', '设计总监'],
    majors: ['工商管理', '设计学', '市场营销', '广告学']
  },
  'ERI': {
    name: '企业+研究+现实',
    tags: ['商业', '技术', '研究', '创新', '管理'],
    traits: ['商业思维', '技术背景', '研究能力'],
    careers: ['技术总监', '产品经理', '研发管理', '技术顾问'],
    majors: ['工程管理', '技术经济', '信息管理', '工商管理']
  },
  'ERS': {
    name: '企业+研究+社会',
    tags: ['商业', '研究', '人际', '咨询', '培训'],
    traits: ['商业思维', '研究能力', '善于沟通'],
    careers: ['管理咨询', '市场研究', '大学教授', '培训师'],
    majors: ['工商管理', '心理学', '市场营销', '教育学']
  },
  'ESC': {
    name: '企业+社会+常规',
    tags: ['商业', '服务', '规范', '管理', '组织'],
    traits: ['商业思维', '善于沟通', '有条理'],
    careers: ['人力资源', '行政管理', '办公室管理', '客户服务'],
    majors: ['人力资源管理', '行政管理', '工商管理', '公共事业管理']
  },
  'ESI': {
    name: '企业+社会+研究',
    tags: ['商业', '人际', '研究', '咨询', '培训'],
    traits: ['善于沟通', '研究能力', '商业思维'],
    careers: ['管理咨询', '培训师', '市场研究', '人力资源'],
    majors: ['工商管理', '心理学', '市场营销', '人力资源管理']
  },
  'ESA': {
    name: '企业+社会+艺术',
    tags: ['媒体', '创意', '商业', '人际', '传播'],
    traits: ['善于沟通', '有创意', '商业意识'],
    careers: ['媒体人', '公关', '活动策划', '内容创作者'],
    majors: ['新闻传播', '广告学', '公共关系', '市场营销']
  },
  'ECR': {
    name: '企业+常规+现实',
    tags: ['商业', '规范', '执行', '组织', '效率'],
    traits: ['商业思维', '有条理', '执行力强'],
    careers: ['项目经理', '生产管理', '运营主管', '办公室管理'],
    majors: ['工商管理', '管理科学', '工程管理', '行政管理']
  },
  'ECS': {
    name: '企业+常规+社会',
    tags: ['商业', '服务', '规范', '管理', '人际'],
    traits: ['商业思维', '善于沟通', '有条理'],
    careers: ['人力资源', '行政管理', '办公室管理', '客户服务'],
    majors: ['人力资源管理', '行政管理', '工商管理', '公共事业管理']
  },
  'EIR': {
    name: '企业+研究+现实',
    tags: ['商业', '技术', '研究', '创新', '管理'],
    traits: ['商业思维', '技术背景', '研究能力'],
    careers: ['技术总监', '产品经理', '研发管理', '技术顾问'],
    majors: ['工程管理', '技术经济', '信息管理', '项目管理']
  },
  'EIS': {
    name: '企业+研究+社会',
    tags: ['商业', '研究', '人际', '咨询', '培训'],
    traits: ['商业思维', '研究能力', '善于沟通'],
    careers: ['管理咨询', '大学教授', '培训师', '市场研究'],
    majors: ['工商管理', '心理学', '市场营销', '教育学']
  },
  'CER': {
    name: '常规+企业+现实',
    tags: ['财务', '商业', '规范', '执行', '组织'],
    traits: ['注重细节', '商业思维', '有条理'],
    careers: ['会计', '财务分析', '审计', '生产管理'],
    majors: ['会计学', '财务管理', '审计学', '金融学']
  },
  'CES': {
    name: '常规+企业+社会',
    tags: ['财务', '服务', '规范', '管理', '人际'],
    traits: ['注重细节', '善于沟通', '有条理'],
    careers: ['人力资源', '财务管理', '行政管理', '客户服务'],
    majors: ['人力资源管理', '财务管理', '行政管理', '公共事业管理']
  },
  'CEI': {
    name: '常规+企业+研究',
    tags: ['财务', '商业', '数据', '分析', '研究'],
    traits: ['注重细节', '商业思维', '分析能力强'],
    careers: ['财务分析', '投资分析', '审计', '数据分析师'],
    majors: ['财务管理', '会计学', '金融学', '统计学']
  },
  'CSE': {
    name: '常规+社会+企业',
    tags: ['服务', '管理', '规范', '人际', '组织'],
    traits: ['有条理', '善于沟通', '组织能力强'],
    careers: ['人力资源', '行政管理', '办公室管理', '客户服务'],
    majors: ['人力资源管理', '行政管理', '工商管理', '公共事业管理']
  },
  'CSR': {
    name: '常规+社会+现实',
    tags: ['服务', '规范', '执行', '稳定', '协助'],
    traits: ['有条理', '乐于助人', '踏实可靠'],
    careers: ['行政', '客服', '银行柜员', '图书管理'],
    majors: ['行政管理', '公共事业管理', '金融服务', '信息资源管理']
  },
  'CSA': {
    name: '常规+社会+艺术',
    tags: ['教育', '媒体', '规范', '服务', '创意'],
    traits: ['有条理', '善于沟通', '有创意'],
    careers: ['教师', '编辑', '媒体策划', '行政管理'],
    majors: ['教育学', '新闻传播', '编辑出版', '行政管理']
  },
  'CRI': {
    name: '常规+研究+现实',
    tags: ['数据', '技术', '分析', '规范', '系统'],
    traits: ['分析能力强', '注重细节', '有条理'],
    careers: ['数据分析师', '质量管理', '系统分析师', '统计'],
    majors: ['统计学', '信息管理与信息系统', '质量管理工程', '数据科学']
  },
  'CRE': {
    name: '常规+研究+企业',
    tags: ['财务', '商业', '数据', '分析', '研究'],
    traits: ['注重细节', '商业思维', '分析能力强'],
    careers: ['财务分析', '投资分析', '审计', '数据分析师'],
    majors: ['财务管理', '会计学', '金融学', '统计学']
  },
  'CRS': {
    name: '常规+研究+社会',
    tags: ['数据', '服务', '研究', '规范', '分析'],
    traits: ['分析能力强', '乐于助人', '有条理'],
    careers: ['教育统计', '心理咨询', '研究助理', '数据分析'],
    majors: ['统计学', '心理学', '应用心理学', '信息管理']
  },
  'CRA': {
    name: '常规+研究+艺术',
    tags: ['数据', '研究', '规范', '设计', '分析'],
    traits: ['分析能力强', '注重细节', '有创意'],
    careers: ['数据可视化', '信息设计', '研究分析', '编辑'],
    majors: ['信息管理', '设计学', '统计学', '编辑出版']
  },
  'CRS': {
    name: '常规+研究+社会',
    tags: ['数据', '服务', '研究', '规范', '分析'],
    traits: ['分析能力强', '乐于助人', '有条理'],
    careers: ['教育统计', '心理咨询', '研究助理', '数据分析'],
    majors: ['统计学', '心理学', '应用心理学', '信息管理']
  }
}

/**
 * 计算霍兰德代码
 * @param {Object} answers - { questionId: optionIndex } 0-3
 * @returns {{ code: string, scores: Object }}
 */
export function calculateHollandCode(answers) {
  const scores = { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 }

  HOLLAND_QUESTIONS.forEach(q => {
    const answer = answers[q.id]
    if (answer !== undefined && answer >= 0 && answer <= 3) {
      // 0-3 分制：0=完全不像(1分), 1=不像(2分), 2=比较像(3分), 3=非常像(4分)
      scores[q.type] += (answer + 1)
    }
  })

  // 按分数排序，取前三位
  const sortedTypes = Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(entry => entry[0])

  const code = sortedTypes.join('')

  return { code, scores }
}
```

- [ ] **Step 2: 提交**

```bash
git add src/data/holland-questions.js
git commit -m "feat: add holland question bank (60 questions)"
```

---

## Task 5: 创建测评 Tab 页

**Files:**
- Create: `src/pages/assessments/assessments.vue`

- [ ] **Step 1: 创建测评 Tab 页**

```vue
<template>
  <view class="page">
    <!-- 五环问卷卡片 -->
    <view class="assessment-card" @click="goQuestionnaire">
      <view class="card-header">
        <view class="card-icon">📋</view>
        <view class="card-info">
          <text class="card-title">个人特质测评</text>
          <text class="card-subtitle">五环问卷 · 22 题</text>
        </view>
        <view class="card-status" :class="questionnaireCompleted ? 'completed' : ''">
          <text v-if="questionnaireCompleted">已完成 ✓</text>
          <text v-else>去测试</text>
        </view>
      </view>
      <view v-if="questionnaireCompleted" class="completed-time">
        <text>完成于 {{ formatDate(assessments.questionnaire.updatedAt) }}</text>
      </view>
    </view>

    <!-- MBTI 卡片 -->
    <view class="assessment-card" @click="goMbti">
      <view class="card-header">
        <view class="card-icon">🧠</view>
        <view class="card-info">
          <text class="card-title">MBTI 性格测试</text>
          <text class="card-subtitle">48 题 · 约 8 分钟</text>
        </view>
        <view class="card-status" :class="assessments.mbti.completed ? 'completed' : ''">
          <text v-if="assessments.mbti.completed">查看结果</text>
          <text v-else>去测试</text>
        </view>
      </view>
      <view v-if="assessments.mbti.completed" class="completed-time">
        <text>你是 {{ assessments.mbti.type }} · 完成于 {{ formatDate(assessments.mbti.completedAt) }}</text>
      </view>
    </view>

    <!-- 霍兰德卡片 -->
    <view class="assessment-card" @click="goHolland">
      <view class="card-header">
        <view class="card-icon">💼</view>
        <view class="card-info">
          <text class="card-title">霍兰德职业兴趣测试</text>
          <text class="card-subtitle">60 题 · 约 10 分钟</text>
        </view>
        <view class="card-status" :class="assessments.holland.completed ? 'completed' : ''">
          <text v-if="assessments.holland.completed">查看结果</text>
          <text v-else>去测试</text>
        </view>
      </view>
      <view v-if="assessments.holland.completed" class="completed-time">
        <text>你是 {{ assessments.holland.code }} 型 · 完成于 {{ formatDate(assessments.holland.completedAt) }}</text>
      </view>
    </view>

    <!-- 底部提示 -->
    <view class="footer-hint">
      <text>完成全部测评后，可生成更准确的个人志愿报告</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onShow } from 'vue'
import { loadAssessments, loadQuestionnaire } from '../../utils/storage.js'

const assessments = ref(loadAssessments())
const questionnaire = ref(loadQuestionnaire())

const questionnaireCompleted = computed(() => {
  return questionnaire.value.completedCount >= 22
})

onShow(() => {
  assessments.value = loadAssessments()
  questionnaire.value = loadQuestionnaire()
})

function formatDate(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  if (assessments.value.mbti.completed) {
    uni.navigateTo({ url: '/pages/mbti/mbti-result' })
  } else {
    uni.navigateTo({ url: '/pages/mbti/mbti' })
  }
}

function goHolland() {
  if (assessments.value.holland.completed) {
    uni.navigateTo({ url: '/pages/holland/holland-result' })
  } else {
    uni.navigateTo({ url: '/pages/holland/holland' })
  }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
  padding: 32rpx;
  box-sizing: border-box;
}

.assessment-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
}

.card-icon {
  width: 88rpx;
  height: 88rpx;
  background: linear-gradient(135deg, #FFF7ED, #FEF3C7);
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  margin-right: 24rpx;
}

.card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.card-subtitle {
  font-size: 24rpx;
  color: $text-muted;
}

.card-status {
  padding: 12rpx 24rpx;
  border-radius: $radius-full;
  font-size: 24rpx;
  font-weight: 600;
  background: $bg-input;
  color: $text-secondary;

  &.completed {
    background: linear-gradient(135deg, #F97316, #EA580C);
    color: #fff;
  }
}

.completed-time {
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 2rpx solid $border-light;
  font-size: 24rpx;
  color: $text-muted;
}

.footer-hint {
  margin-top: 48rpx;
  text-align: center;
  padding: 24rpx;
  font-size: 24rpx;
  color: $text-muted;
  line-height: 1.6;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/pages/assessments/
git commit -m "feat: add assessments tab page"
```

---

## Task 6: 创建"我的"Tab 页

**Files:**
- Create: `src/pages/profile/profile.vue`

- [ ] **Step 1: 创建"我的"页面**

```vue
<template>
  <view class="page">
    <!-- 头部 -->
    <view class="header">
      <view class="avatar">
        <text class="avatar-text">我</text>
      </view>
      <text class="header-title">我的</text>
    </view>

    <!-- 报告卡片 -->
    <view class="section">
      <text class="section-title">我的志愿报告</text>
      <view class="report-card">
        <view class="report-icon">📊</view>
        <view class="report-info">
          <text class="report-title">综合志愿报告</text>
          <text class="report-subtitle">基于测评结果生成的个性化分析</text>
        </view>
        <view class="report-action" @click="goReport">
          <text>{{ hasReport ? '查看报告' : '生成报告' }}</text>
        </view>
      </view>
    </view>

    <!-- 测评记录 -->
    <view class="section">
      <text class="section-title">测评记录</text>
      <view class="record-list">
        <view class="record-item" @click="goQuestionnaire">
          <view class="record-info">
            <text class="record-title">个人特质测评</text>
            <text class="record-time">{{ questionnaireRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>
        <view class="record-item" @click="goMbti">
          <view class="record-info">
            <text class="record-title">MBTI 性格测试</text>
            <text class="record-time">{{ mbtiRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>
        <view class="record-item" @click="goHolland">
          <view class="record-info">
            <text class="record-title">霍兰德职业兴趣测试</text>
            <text class="record-time">{{ hollandRecordText }}</text>
          </view>
          <text class="record-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 设置入口（预留） -->
    <view class="section">
      <text class="section-title">设置</text>
      <view class="setting-item">
        <text class="setting-title">清除数据</text>
        <text class="setting-arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onShow } from 'vue'
import { loadAssessments, loadQuestionnaire, getCompletedAssessmentsCount } from '../../utils/storage.js'

const assessments = ref(loadAssessments())
const questionnaire = ref(loadQuestionnaire())

const hasReport = ref(false)

onShow(() => {
  assessments.value = loadAssessments()
  questionnaire.value = loadQuestionnaire()
  // TODO: 检查是否已生成报告
})

const questionnaireRecordText = computed(() => {
  if (questionnaire.value.completedCount >= 22) {
    return `已完成 · ${formatDate(questionnaire.value.updatedAt)}`
  }
  return `未完成 · ${questionnaire.value.completedCount}/22 题`
})

const mbtiRecordText = computed(() => {
  if (assessments.value.mbti.completed) {
    return `你是 ${assessments.value.mbti.type} · ${formatDate(assessments.value.mbti.completedAt)}`
  }
  return '未完成'
})

const hollandRecordText = computed(() => {
  if (assessments.value.holland.completed) {
    return `你是 ${assessments.value.holland.code} 型 · ${formatDate(assessments.value.holland.completedAt)}`
  }
  return '未完成'
})

function formatDate(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function goReport() {
  const count = getCompletedAssessmentsCount()
  if (count < 3) {
    uni.showToast({
      title: `还有 ${3 - count} 个测评未完成`,
      icon: 'none'
    })
    return
  }
  uni.navigateTo({ url: '/pages/report/report' })
}

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  if (assessments.value.mbti.completed) {
    uni.navigateTo({ url: '/pages/mbti/mbti-result' })
  } else {
    uni.navigateTo({ url: '/pages/mbti/mbti' })
  }
}

function goHolland() {
  if (assessments.value.holland.completed) {
    uni.navigateTo({ url: '/pages/holland/holland-result' })
  } else {
    uni.navigateTo({ url: '/pages/holland/holland' })
  }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
}

.header {
  background: linear-gradient(135deg, #FFF7ED, #FEF3C7);
  padding: 48rpx 32rpx 32rpx;
  display: flex;
  align-items: center;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  background: $brand-primary;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
}

.avatar-text {
  color: #fff;
  font-size: 40rpx;
  font-weight: 600;
}

.header-title {
  font-size: 36rpx;
  font-weight: 600;
  color: $text-primary;
}

.section {
  margin-top: 24rpx;
  background: $bg-white;
  padding: 32rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
  margin-bottom: 24rpx;
  display: block;
}

.report-card {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: linear-gradient(135deg, #FFF7ED, #FEF3C7);
  border-radius: $radius-lg;
}

.report-icon {
  width: 72rpx;
  height: 72rpx;
  background: $brand-primary;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  margin-right: 20rpx;
}

.report-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.report-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.report-subtitle {
  font-size: 24rpx;
  color: $text-secondary;
}

.report-action {
  padding: 12rpx 24rpx;
  background: $brand-primary;
  border-radius: $radius-full;
  font-size: 24rpx;
  font-weight: 600;
  color: #fff;
}

.record-list {
  display: flex;
  flex-direction: column;
}

.record-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 0;
  border-bottom: 2rpx solid $border-light;

  &:last-child {
    border-bottom: none;
  }
}

.record-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.record-title {
  font-size: 28rpx;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.record-time {
  font-size: 24rpx;
  color: $text-muted;
}

.record-arrow {
  font-size: 40rpx;
  color: $text-muted;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 0;
}

.setting-title {
  font-size: 28rpx;
  color: $text-primary;
}

.setting-arrow {
  font-size: 40rpx;
  color: $text-muted;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/pages/profile/
git commit -m "feat: add profile tab page"
```

---

## Task 7: 改造首页添加测评卡片

**Files:**
- Modify: `src/pages/index/index.vue`

- [ ] **Step 1: 修改首页，添加测评卡片和完成进度**

保留品牌 Header、考生信息卡、免费咨询入口，修改报告入口区域为测评卡片+生成报告按钮：

```vue
<template>
  <view class="page">
    <!-- 品牌 Header -->
    <view class="header">
      <view class="logo">
        <text class="logo-text">峰</text>
      </view>
      <text class="title">峰哥咨询参考</text>
      <text class="subtitle">AI 志愿填报助手，专业的高考志愿参考建议</text>
    </view>

    <!-- 考生信息填报 -->
    <view class="profile-card">
      <view class="card-header">
        <text class="card-title">2026 高考志愿模拟填报</text>
        <text class="save-status">{{ saveStatus }}</text>
      </view>

      <picker :range="provinces" :value="provinceIndex" @change="onProvinceChange">
        <view class="field-row">
          <text class="field-label">省份</text>
          <view class="field-value-wrap">
            <text class="field-value" :class="{ placeholder: !profile.province }">{{ profile.province || '请选择' }}</text>
            <text class="chevron">›</text>
          </view>
        </view>
      </picker>

      <picker :range="categories" :value="categoryIndex" @change="onCategoryChange">
        <view class="field-row">
          <text class="field-label">科目</text>
          <view class="field-value-wrap">
            <text class="field-value" :class="{ placeholder: !profile.category }">{{ profile.category || '请选择' }}</text>
            <text class="chevron">›</text>
          </view>
        </view>
      </picker>

      <view class="field-row">
        <text class="field-label">分数</text>
        <view class="field-value-wrap">
          <input
            class="field-input"
            type="number"
            maxlength="3"
            :value="profile.score"
            placeholder="请输入"
            placeholder-class="input-placeholder"
            @input="onScoreInput"
          />
          <text class="field-unit">分</text>
        </view>
      </view>

      <view class="field-row field-row-last">
        <text class="field-label">位次</text>
        <view class="field-value-wrap">
          <input
            class="field-input"
            type="number"
            maxlength="8"
            :value="profile.rank"
            placeholder="选填"
            placeholder-class="input-placeholder"
            @input="onRankInput"
          />
          <text class="field-unit">名</text>
        </view>
      </view>

      <view class="primary-btn" @click="onSmartFill">
        <text class="primary-btn-title">智能填报</text>
      </view>

      <text class="profile-hint">填写后，AI 咨询会自动带入你的省份、科目、分数和位次。</text>
    </view>

    <!-- 咨询入口 -->
    <view class="chat-entry" @click="goChat">
      <view class="chat-entry-content">
        <text class="chat-entry-title">免费咨询</text>
        <text class="chat-entry-sub">AI 实时对话 · 带着考生信息问更准</text>
      </view>
      <text class="chat-entry-arrow">›</text>
    </view>

    <!-- 测评卡片区 -->
    <view class="assessments-section">
      <text class="section-title">专业测评</text>

      <!-- 五环问卷卡片 -->
      <view class="assessment-card" @click="goQuestionnaire">
        <view class="assessment-icon">📋</view>
        <view class="assessment-info">
          <text class="assessment-title">个人特质测评</text>
          <text class="assessment-subtitle">22 题 · 五环框架</text>
        </view>
        <view class="assessment-status" :class="{ completed: questionnaireCompleted }">
          <text v-if="questionnaireCompleted">✓</text>
          <text v-else>›</text>
        </view>
      </view>

      <!-- MBTI 卡片 -->
      <view class="assessment-card" @click="goMbti">
        <view class="assessment-icon">🧠</view>
        <view class="assessment-info">
          <text class="assessment-title">MBTI 性格测试</text>
          <text class="assessment-subtitle">48 题 · 约 8 分钟</text>
        </view>
        <view class="assessment-status" :class="{ completed: assessments.mbti.completed }">
          <text v-if="assessments.mbti.completed">✓</text>
          <text v-else>›</text>
        </view>
      </view>

      <!-- 霍兰德卡片 -->
      <view class="assessment-card" @click="goHolland">
        <view class="assessment-icon">💼</view>
        <view class="assessment-info">
          <text class="assessment-title">霍兰德职业兴趣</text>
          <text class="assessment-subtitle">60 题 · 约 10 分钟</text>
        </view>
        <view class="assessment-status" :class="{ completed: assessments.holland.completed }">
          <text v-if="assessments.holland.completed">✓</text>
          <text v-else>›</text>
        </view>
      </view>
    </view>

    <!-- 报告生成入口 -->
    <view class="report-entry" :class="{ enabled: allAssessmentsCompleted }" @click="goReport">
      <view class="report-entry-content">
        <text class="report-entry-title">生成个人报告</text>
        <text class="report-entry-sub">{{ reportSubtitle }}</text>
      </view>
      <text class="report-entry-arrow">›</text>
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">
      <text class="disclaimer-text">⚠️ 数据仅供参考，请以各省考试院公布信息为准</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { loadUserProfile, saveUserProfile, isProfileComplete, loadAssessments, loadQuestionnaire, getCompletedAssessmentsCount } from '../../utils/storage.js'

const provinces = [
  '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
  '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
  '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆'
]
const categories = ['物理类', '历史类']

const profile = ref(loadUserProfile())
const saveStatus = ref('自动保存')
const assessments = ref(loadAssessments())
const questionnaire = ref(loadQuestionnaire())

const provinceIndex = computed(() => Math.max(0, provinces.indexOf(profile.value.province)))
const categoryIndex = computed(() => Math.max(0, categories.indexOf(profile.value.category)))

const questionnaireCompleted = computed(() => questionnaire.value.completedCount >= 22)
const allAssessmentsCompleted = computed(() => getCompletedAssessmentsCount() === 3)

const reportSubtitle = computed(() => {
  const count = getCompletedAssessmentsCount()
  if (count === 3) {
    return '全部测评完成，可生成报告'
  }
  return `完成 ${count}/3 个测评后生成`
})

onShow(() => {
  profile.value = loadUserProfile()
  assessments.value = loadAssessments()
  questionnaire.value = loadQuestionnaire()
})

function goQuestionnaire() {
  uni.navigateTo({ url: '/pages/questionnaire/questionnaire' })
}

function goMbti() {
  if (assessments.value.mbti.completed) {
    uni.navigateTo({ url: '/pages/mbti/mbti-result' })
  } else {
    uni.navigateTo({ url: '/pages/mbti/mbti' })
  }
}

function goHolland() {
  if (assessments.value.holland.completed) {
    uni.navigateTo({ url: '/pages/holland/holland-result' })
  } else {
    uni.navigateTo({ url: '/pages/holland/holland' })
  }
}

function goReport() {
  if (!allAssessmentsCompleted.value) {
    uni.showToast({
      title: `还有 ${3 - getCompletedAssessmentsCount()} 个测评未完成`,
      icon: 'none'
    })
    return
  }
  uni.navigateTo({ url: '/pages/report/report' })
}

function goChat() {
  uni.navigateTo({ url: '/pages/chat/chat' })
}

function persistProfile(nextProfile) {
  profile.value = saveUserProfile(nextProfile)
  saveStatus.value = '已自动保存'
}

function onProvinceChange(event) {
  const index = Number(event.detail.value)
  persistProfile({ ...profile.value, province: provinces[index] })
}

function onCategoryChange(event) {
  const index = Number(event.detail.value)
  persistProfile({ ...profile.value, category: categories[index] })
}

function onScoreInput(event) {
  persistProfile({ ...profile.value, score: event.detail.value })
}

function onRankInput(event) {
  persistProfile({ ...profile.value, rank: event.detail.value })
}

function onSmartFill() {
  if (!isProfileComplete(profile.value)) {
    uni.showToast({
      title: '请先填写省份、科目和分数',
      icon: 'none'
    })
    return
  }
  goChat()
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(135deg, $brand-gradient-start 0%, $brand-gradient-end 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 32rpx;
  padding-top: 104rpx;
  padding-bottom: 48rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.logo {
  width: 112rpx;
  height: 112rpx;
  background: $brand-primary;
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.logo-text {
  color: #fff;
  font-size: 50rpx;
  font-weight: bold;
}

.title {
  font-size: 40rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.subtitle {
  font-size: 26rpx;
  color: $text-secondary;
}

.profile-card {
  width: 100%;
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 42rpx 32rpx 32rpx;
  box-shadow: 0 16rpx 40rpx rgba(249, 115, 22, 0.12);
  box-sizing: border-box;
  margin-bottom: 24rpx;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 28rpx;
}

.card-title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
}

.save-status {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.field-row {
  height: 104rpx;
  border-bottom: 2rpx solid $border-light;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-row-last {
  border-bottom: none;
  margin-bottom: 28rpx;
}

.field-label {
  font-size: 30rpx;
  font-weight: 600;
  color: #111827;
}

.field-value-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 260rpx;
}

.field-value {
  font-size: 30rpx;
  color: $text-secondary;
}

.placeholder,
.input-placeholder {
  color: $text-muted;
}

.chevron {
  margin-left: 18rpx;
  font-size: 46rpx;
  line-height: 1;
  color: $text-muted;
}

.field-input {
  width: 180rpx;
  text-align: right;
  font-size: 34rpx;
  color: $text-secondary;
}

.field-unit {
  margin-left: 14rpx;
  font-size: 28rpx;
  color: $text-secondary;
}

.primary-btn {
  width: 100%;
  background: $brand-primary;
  border-radius: $radius-full;
  height: 84rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 22rpx;
}

.primary-btn-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}

.profile-hint {
  display: block;
  text-align: center;
  font-size: 23rpx;
  color: $text-muted;
  line-height: 1.6;
}

.chat-entry {
  width: 100%;
  background: rgba(255, 255, 255, 0.78);
  border: 2rpx solid rgba(249, 115, 22, 0.16);
  border-radius: $radius-lg;
  padding: 28rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
  box-sizing: border-box;
}

.chat-entry-content {
  display: flex;
  flex-direction: column;
}

.chat-entry-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.chat-entry-sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $text-secondary;
}

.chat-entry-arrow {
  font-size: 46rpx;
  color: $brand-primary;
}

.assessments-section {
  width: 100%;
  background: rgba(255, 255, 255, 0.9);
  border-radius: $radius-xl;
  padding: 24rpx 20rpx;
  margin-bottom: 24rpx;
  box-sizing: border-box;
}

.section-title {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-secondary;
  margin-bottom: 16rpx;
  display: block;
  padding-left: 12rpx;
}

.assessment-card {
  display: flex;
  align-items: center;
  padding: 20rpx 16rpx;
  background: $bg-white;
  border-radius: $radius-lg;
  margin-bottom: 12rpx;
  border: 2rpx solid transparent;
  transition: all 0.2s;

  &:active {
    background: $bg-page;
  }
}

.assessment-icon {
  width: 64rpx;
  height: 64rpx;
  background: linear-gradient(135deg, #FFF7ED, #FEF3C7);
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  margin-right: 20rpx;
}

.assessment-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.assessment-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 6rpx;
}

.assessment-subtitle {
  font-size: 22rpx;
  color: $text-muted;
}

.assessment-status {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: $bg-input;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  color: $text-muted;

  &.completed {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
  }
}

.report-entry {
  width: 100%;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border-radius: $radius-lg;
  padding: 28rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
  opacity: 0.5;
  box-sizing: border-box;

  &.enabled {
    opacity: 1;
  }
}

.report-entry-content {
  display: flex;
  flex-direction: column;
}

.report-entry-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #fff;
}

.report-entry-sub {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.report-entry-arrow {
  font-size: 46rpx;
  color: #fff;
}

.disclaimer {
  width: 100%;
  padding: 32rpx 0 0;
  text-align: center;
}

.disclaimer-text {
  font-size: 22rpx;
  color: $text-muted;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/pages/index/index.vue
git commit -m "feat: add assessment cards to home page"
```

---

## Task 8: 创建 MBTI 测评页面

**Files:**
- Create: `src/pages/mbti/mbti.vue`

- [ ] **Step 1: 创建 MBTI 测评题目页**

```vue
<template>
  <view class="page">
    <!-- 进度条 -->
    <view class="progress-bar-wrap">
      <view class="progress-info">
        <text class="progress-text">第 {{ currentIndex + 1 }}/{{ QUESTIONS.length }} 题</text>
        <text class="progress-pct">{{ Math.round((currentIndex + 1) / QUESTIONS.length * 100) }}%</text>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: ((currentIndex + 1) / QUESTIONS.length * 100) + '%' }" />
      </view>
    </view>

    <!-- 当前题目 -->
    <view class="question-card">
      <text class="question-text">{{ currentQuestion.text }}</text>

      <!-- 选项列表 -->
      <view class="options-list">
        <view
          v-for="(opt, idx) in currentQuestion.options"
          :key="idx"
          class="option-item"
          :class="{ 'option-selected': answers[currentQuestion.id] === opt.value }"
          @click="selectOption(opt.value)"
        >
          <view class="option-radio">
            <text v-if="answers[currentQuestion.id] === opt.value" class="radio-dot">●</text>
          </view>
          <text class="option-text">{{ opt.text }}</text>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <view class="nav-btn prev-btn" :class="{ disabled: currentIndex === 0 }" @click="prev">上一题</view>
      <view v-if="currentIndex < QUESTIONS.length - 1" class="nav-btn next-btn" @click="next">下一题</view>
      <view v-else class="nav-btn next-btn" @click="finish">查看结果</view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onShow } from 'vue'
import { MBTI_QUESTIONS, calculateMbtiType, MBTI_TYPE_DESCRIPTIONS } from '../../data/mbti-questions.js'
import { loadAssessments, saveMbtiProgress, saveMbtiResult } from '../../utils/storage.js'

const currentIndex = ref(0)
const answers = ref({})

onShow(() => {
  const assessments = loadAssessments()
  if (assessments.mbti.completed) {
    uni.navigateBack()
  }
  // 恢复进度
  if (assessments.mbti.answers) {
    answers.value = assessments.mbti.answers
  }
  if (assessments.mbti.lastIndex !== undefined && assessments.mbti.lastIndex < MBTI_QUESTIONS.length) {
    currentIndex.value = assessments.mbti.lastIndex
  }
})

const currentQuestion = computed(() => MBTI_QUESTIONS[currentIndex.value])

function selectOption(value) {
  answers.value[currentQuestion.value.id] = value
  // 自动跳下一题
  if (currentIndex.value < MBTI_QUESTIONS.length - 1) {
    setTimeout(() => {
      next()
    }, 200)
  }
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

function next() {
  // 保存进度
  saveMbtiProgress(currentIndex.value, answers.value)

  if (currentIndex.value < MBTI_QUESTIONS.length - 1) {
    currentIndex.value++
  }
}

function finish() {
  const result = calculateMbtiType(answers.value)
  saveMbtiResult({
    type: result.type,
    scores: result.scores,
    answers: answers.value
  })
  uni.navigateTo({ url: '/pages/mbti/mbti-result' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
  padding: 24rpx 32rpx 200rpx;
  box-sizing: border-box;
}

.progress-bar-wrap {
  margin-bottom: 24rpx;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.progress-text, .progress-pct {
  font-size: 24rpx;
  color: $text-muted;
}

.progress-track {
  background: $border-light;
  border-radius: $radius-full;
  height: 8rpx;
}

.progress-fill {
  background: #F97316;
  border-radius: $radius-full;
  height: 8rpx;
  transition: width 0.3s;
}

.question-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.question-text {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
  display: block;
  line-height: 1.5;
  margin-bottom: 32rpx;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx;
  border-radius: $radius-lg;
  border: 2rpx solid $border-light;
  background: $bg-page;
  transition: all 0.2s;
}

.option-selected {
  border-color: #F97316;
  background: #FFF7ED;
}

.option-radio {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 2rpx solid $border-light;
  background: $bg-white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .option-selected & {
    border-color: #F97316;
  }
}

.radio-dot {
  color: #F97316;
  font-size: 20rpx;
}

.option-text {
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.4;
}

.footer {
  position: fixed;
  bottom: calc(120rpx + env(safe-area-inset-bottom));
  left: 32rpx;
  right: 32rpx;
  display: flex;
  gap: 16rpx;
}

.nav-btn {
  flex: 1;
  height: 80rpx;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 600;
}

.prev-btn {
  background: $bg-white;
  color: $text-secondary;
  border: 2rpx solid $border-light;
}

.next-btn {
  background: #F97316;
  color: #fff;
}

.disabled {
  opacity: 0.4;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/pages/mbti/mbti.vue
git commit -m "feat: add MBTI assessment page"
```

---

## Task 9: 创建 MBTI 结果页

**Files:**
- Create: `src/pages/mbti/mbti-result.vue`

- [ ] **Step 1: 创建 MBTI 结果页**

```vue
<template>
  <view class="page">
    <!-- 结果头部 -->
    <view class="result-header">
      <text class="result-type">{{ result.type }}</text>
      <text class="result-name">{{ typeInfo.name }}</text>
    </view>

    <!-- 维度得分 -->
    <view class="section">
      <text class="section-title">维度得分</text>
      <view class="scores-list">
        <view class="score-item" v-for="(dim, key) in dimensions" :key="key">
          <text class="score-label">{{ dim.label }}</text>
          <view class="score-bar-wrap">
            <view class="score-bar">
              <view
                class="score-fill-left"
                :style="{ width: getLeftPercent(result.scores[dim.left], result.scores[dim.right]) + '%' }"
              />
              <view class="score-divider" />
              <view
                class="score-fill-right"
                :style="{ width: getRightPercent(result.scores[dim.left], result.scores[dim.right]) + '%' }"
              />
            </view>
          </view>
          <view class="score-values">
            <text class="score-value">{{ result.scores[dim.left] }}</text>
            <text class="score-value">{{ result.scores[dim.right] }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 性格特征 -->
    <view class="section">
      <text class="section-title">性格特征</text>
      <view class="traits-list">
        <view class="trait-item" v-for="trait in typeInfo.traits" :key="trait">
          <text class="trait-dot">●</text>
          <text class="trait-text">{{ trait }}</text>
        </view>
      </view>
    </view>

    <!-- 适合职业 -->
    <view class="section">
      <text class="section-title">适合职业方向</text>
      <view class="careers-list">
        <view class="career-tag" v-for="career in typeInfo.careers" :key="career">
          {{ career }}
        </view>
      </view>
    </view>

    <!-- 专业推荐 -->
    <view class="section">
      <text class="section-title">基于你的性格，推荐专业</text>
      <view class="majors-list">
        <view
          class="major-card"
          v-for="(major, idx) in typeInfo.majors"
          :key="major"
          @click="viewMajorDetail(major, idx)"
        >
          <view class="major-header">
            <text class="major-name">{{ major }}</text>
            <text class="major-stars">{{ getStars(typeInfo.majors.length - idx) }}</text>
          </view>
          <text class="major-desc">{{ getMajorDesc(major) }}</text>
          <view class="major-action">
            <text>查看深度报告</text>
            <text>›</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <view class="retry-btn" @click="retry">
        <text>重新测试</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onShow } from 'vue'
import { MBTI_TYPE_DESCRIPTIONS } from '../../data/mbti-questions.js'
import { loadAssessments } from '../../utils/storage.js'

const result = ref({ type: '', scores: {} })

const dimensions = {
  EI: { left: 'E', right: 'I', label: '外向 / 内向' },
  SN: { left: 'S', right: 'N', label: '感觉 / 直觉' },
  TF: { left: 'T', right: 'F', label: '思考 / 情感' },
  JP: { left: 'J', right: 'P', label: '判断 / 感知' }
}

const typeInfo = computed(() => {
  return MBTI_TYPE_DESCRIPTIONS[result.value.type] || {
    name: '未知',
    traits: [],
    careers: [],
    majors: []
  }
})

onShow(() => {
  const assessments = loadAssessments()
  if (!assessments.mbti.completed) {
    uni.navigateBack()
    return
  }
  result.value = {
    type: assessments.mbti.type,
    scores: assessments.mbti.scores
  }
})

function getLeftPercent(left, right) {
  const total = left + right
  if (total === 0) return 50
  return Math.round(left / total * 100)
}

function getRightPercent(left, right) {
  const total = left + right
  if (total === 0) return 50
  return Math.round(right / total * 100)
}

function getStars(count) {
  return '★'.repeat(Math.min(count, 5)) + '☆'.repeat(Math.max(5 - count, 0))
}

function getMajorDesc(major) {
  const descs = {
    '计算机科学与技术': '逻辑性强，适合系统思维和分析',
    '数学与应用数学': '抽象思维强，喜欢理论研究',
    '软件工程': '逻辑清晰，善于解决问题',
    '数据科学': '分析能力强，对数据敏感'
  }
  return descs[major] || '与你的性格特点高度匹配'
}

function viewMajorDetail(major, idx) {
  // TODO: 跳转到专业深度报告页
  uni.showToast({
    title: '专业报告功能开发中',
    icon: 'none'
  })
}

function retry() {
  uni.showModal({
    title: '重新测试',
    content: '重新测试将覆盖当前结果，确定继续吗？',
    success: (res) => {
      if (res.confirm) {
        uni.navigateTo({ url: '/pages/mbti/mbti' })
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
  padding: 32rpx;
  padding-bottom: 200rpx;
  box-sizing: border-box;
}

.result-header {
  background: linear-gradient(135deg, #F97316, #EA580C);
  border-radius: $radius-xl;
  padding: 48rpx;
  text-align: center;
  margin-bottom: 32rpx;
}

.result-type {
  font-size: 72rpx;
  font-weight: 700;
  color: #fff;
  display: block;
  margin-bottom: 16rpx;
}

.result-name {
  font-size: 32rpx;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.section {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
  margin-bottom: 24rpx;
  display: block;
}

.scores-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.score-label {
  font-size: 26rpx;
  color: $text-secondary;
}

.score-bar-wrap {
  display: flex;
  justify-content: center;
}

.score-bar {
  width: 100%;
  height: 24rpx;
  background: $bg-input;
  border-radius: $radius-full;
  display: flex;
  overflow: hidden;
  position: relative;
}

.score-fill-left {
  background: linear-gradient(90deg, #F97316, #FB923C);
  height: 100%;
}

.score-divider {
  width: 4rpx;
  background: #fff;
  height: 100%;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.score-fill-right {
  background: linear-gradient(90deg, #93C5FD, #60A5FA);
  height: 100%;
  margin-left: auto;
}

.score-values {
  display: flex;
  justify-content: space-between;
}

.score-value {
  font-size: 24rpx;
  color: $text-muted;
}

.traits-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.trait-item {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.trait-dot {
  color: #F97316;
  font-size: 12rpx;
  margin-top: 6rpx;
}

.trait-text {
  flex: 1;
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.6;
}

.careers-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.career-tag {
  padding: 12rpx 24rpx;
  background: $bg-page;
  border-radius: $radius-full;
  font-size: 26rpx;
  color: $text-secondary;
}

.majors-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.major-card {
  background: $bg-page;
  border-radius: $radius-lg;
  padding: 24rpx;
}

.major-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.major-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.major-stars {
  font-size: 24rpx;
  color: #F97316;
}

.major-desc {
  font-size: 24rpx;
  color: $text-muted;
  line-height: 1.5;
  margin-bottom: 16rpx;
  display: block;
}

.major-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16rpx;
  border-top: 2rpx solid $border-light;
  font-size: 24rpx;
  color: #F97316;
}

.footer {
  position: fixed;
  bottom: calc(32rpx + env(safe-area-inset-bottom));
  left: 32rpx;
  right: 32rpx;
}

.retry-btn {
  width: 100%;
  height: 88rpx;
  background: $bg-white;
  border: 2rpx solid $border-light;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 600;
  color: $text-secondary;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/pages/mbti/mbti-result.vue
git commit -m "feat: add MBTI result page"
```

---

## Task 10: 创建霍兰德测评页面

**Files:**
- Create: `src/pages/holland/holland.vue`

- [ ] **Step 1: 创建霍兰德测评题目页**

```vue
<template>
  <view class="page">
    <!-- 进度条 -->
    <view class="progress-bar-wrap">
      <view class="progress-info">
        <text class="progress-text">第 {{ currentIndex + 1 }}/{{ QUESTIONS.length }} 题</text>
        <text class="progress-pct">{{ Math.round((currentIndex + 1) / QUESTIONS.length * 100) }}%</text>
      </view>
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: ((currentIndex + 1) / QUESTIONS.length * 100) + '%' }" />
      </view>
    </view>

    <!-- 当前题目 -->
    <view class="question-card">
      <text class="question-text">{{ currentQuestion.text }}</text>

      <!-- 选项列表 - 4分制 -->
      <view class="options-list">
        <view
          v-for="(opt, idx) in currentQuestion.options"
          :key="idx"
          class="option-item"
          :class="{ 'option-selected': answers[currentQuestion.id] === idx }"
          @click="selectOption(idx)"
        >
          <view class="option-check">
            <text v-if="answers[currentQuestion.id] === idx" class="check-icon">✓</text>
          </view>
          <text class="option-text">{{ opt }}</text>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <view class="nav-btn prev-btn" :class="{ disabled: currentIndex === 0 }" @click="prev">上一题</view>
      <view v-if="currentIndex < QUESTIONS.length - 1" class="nav-btn next-btn" @click="next">下一题</view>
      <view v-else class="nav-btn next-btn" @click="finish">查看结果</view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onShow } from 'vue'
import { HOLLAND_QUESTIONS, calculateHollandCode } from '../../data/holland-questions.js'
import { loadAssessments, saveHollandProgress, saveHollandResult } from '../../utils/storage.js'

const currentIndex = ref(0)
const answers = ref({})

onShow(() => {
  const assessments = loadAssessments()
  if (assessments.holland.completed) {
    uni.navigateBack()
  }
  // 恢复进度
  if (assessments.holland.answers) {
    answers.value = assessments.holland.answers
  }
  if (assessments.holland.lastIndex !== undefined && assessments.holland.lastIndex < HOLLAND_QUESTIONS.length) {
    currentIndex.value = assessments.holland.lastIndex
  }
})

const currentQuestion = computed(() => HOLLAND_QUESTIONS[currentIndex.value])

function selectOption(value) {
  answers.value[currentQuestion.value.id] = value
  // 自动跳下一题
  if (currentIndex.value < HOLLAND_QUESTIONS.length - 1) {
    setTimeout(() => {
      next()
    }, 200)
  }
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

function next() {
  // 保存进度
  saveHollandProgress(currentIndex.value, answers.value)

  if (currentIndex.value < HOLLAND_QUESTIONS.length - 1) {
    currentIndex.value++
  }
}

function finish() {
  const result = calculateHollandCode(answers.value)
  saveHollandResult({
    code: result.code,
    scores: result.scores,
    answers: answers.value
  })
  uni.navigateTo({ url: '/pages/holland/holland-result' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
  padding: 24rpx 32rpx 200rpx;
  box-sizing: border-box;
}

.progress-bar-wrap {
  margin-bottom: 24rpx;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.progress-text, .progress-pct {
  font-size: 24rpx;
  color: $text-muted;
}

.progress-track {
  background: $border-light;
  border-radius: $radius-full;
  height: 8rpx;
}

.progress-fill {
  background: #7c3aed;
  border-radius: $radius-full;
  height: 8rpx;
  transition: width 0.3s;
}

.question-card {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 40rpx 32rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.question-text {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
  display: block;
  line-height: 1.5;
  margin-bottom: 32rpx;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  border-radius: $radius-lg;
  border: 2rpx solid $border-light;
  background: $bg-page;
}

.option-selected {
  border-color: #7c3aed;
  background: #F5F3FF;
}

.option-check {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 2rpx solid $border-light;
  background: $bg-white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .option-selected & {
    background: #7c3aed;
    border-color: #7c3aed;
  }
}

.check-icon {
  color: #fff;
  font-size: 20rpx;
}

.option-text {
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.4;
}

.footer {
  position: fixed;
  bottom: calc(120rpx + env(safe-area-inset-bottom));
  left: 32rpx;
  right: 32rpx;
  display: flex;
  gap: 16rpx;
}

.nav-btn {
  flex: 1;
  height: 80rpx;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 600;
}

.prev-btn {
  background: $bg-white;
  color: $text-secondary;
  border: 2rpx solid $border-light;
}

.next-btn {
  background: #7c3aed;
  color: #fff;
}

.disabled {
  opacity: 0.4;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/pages/holland/holland.vue
git commit -m "feat: add holland assessment page"
```

---

## Task 11: 创建霍兰德结果页

**Files:**
- Create: `src/pages/holland/holland-result.vue`

- [ ] **Step 1: 创建霍兰德结果页**

```vue
<template>
  <view class="page">
    <!-- 结果头部 -->
    <view class="result-header">
      <text class="result-code">{{ result.code }}</text>
      <text class="result-name">{{ typeInfo.name }}</text>
    </view>

    <!-- 维度得分 -->
    <view class="section">
      <text class="section-title">各维度得分</text>
      <view class="scores-grid">
        <view class="score-item" v-for="(label, key) in hollandTypes" :key="key">
          <text class="score-type">{{ key }}</text>
          <view class="score-bar-wrap">
            <view class="score-bar-bg">
              <view class="score-bar-fill" :style="{ width: getPercent(result.scores[key]) + '%' }" />
            </view>
          </view>
          <text class="score-value">{{ result.scores[key] }}</text>
        </view>
      </view>
    </view>

    <!-- 性格特征 -->
    <view class="section">
      <text class="section-title">性格特征</text>
      <view class="traits-list">
        <view class="trait-item" v-for="trait in typeInfo.traits" :key="trait">
          <text class="trait-dot">●</text>
          <text class="trait-text">{{ trait }}</text>
        </view>
      </view>
    </view>

    <!-- 适合职业 -->
    <view class="section">
      <text class="section-title">适合职业方向</text>
      <view class="careers-list">
        <view class="career-tag" v-for="career in typeInfo.careers" :key="career">
          {{ career }}
        </view>
      </view>
    </view>

    <!-- 专业推荐 -->
    <view class="section">
      <text class="section-title">基于你的兴趣，推荐专业</text>
      <view class="majors-list">
        <view
          class="major-card"
          v-for="(major, idx) in typeInfo.majors"
          :key="major"
          @click="viewMajorDetail(major)"
        >
          <view class="major-header">
            <text class="major-name">{{ major }}</text>
            <text class="major-stars">{{ getStars(typeInfo.majors.length - idx) }}</text>
          </view>
          <text class="major-desc">{{ getMajorDesc(major) }}</text>
          <view class="major-action">
            <text>查看深度报告</text>
            <text>›</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <view class="retry-btn" @click="retry">
        <text>重新测试</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onShow } from 'vue'
import { HOLLAND_TYPE_DESCRIPTIONS } from '../../data/holland-questions.js'
import { loadAssessments } from '../../utils/storage.js'

const result = ref({ code: '', scores: {} })

const hollandTypes = {
  R: '现实型',
  I: '研究型',
  A: '艺术型',
  S: '社会型',
  E: '企业型',
  C: '常规型'
}

const typeInfo = computed(() => {
  return HOLLAND_TYPE_DESCRIPTIONS[result.value.code] || {
    name: '未知',
    traits: [],
    careers: [],
    majors: []
  }
})

onShow(() => {
  const assessments = loadAssessments()
  if (!assessments.holland.completed) {
    uni.navigateBack()
    return
  }
  result.value = {
    code: assessments.holland.code,
    scores: assessments.holland.scores
  }
})

function getPercent(score) {
  const maxScore = 40 // 10题 x 4分
  return Math.min(100, Math.round(score / maxScore * 100))
}

function getStars(count) {
  return '★'.repeat(Math.min(count, 5)) + '☆'.repeat(Math.max(5 - count, 0))
}

function getMajorDesc(major) {
  const descs = {
    '计算机科学与技术': '技术+研究型，适合逻辑分析和创新',
    '机械工程': '现实型，喜欢动手操作和技术研究',
    '建筑学': '现实+艺术型，兼具技术和创造力',
    '工商管理': '企业型，善于组织和管理'
  }
  return descs[major] || '与你的兴趣类型高度匹配'
}

function viewMajorDetail(major) {
  // TODO: 跳转到专业深度报告页
  uni.showToast({
    title: '专业报告功能开发中',
    icon: 'none'
  })
}

function retry() {
  uni.showModal({
    title: '重新测试',
    content: '重新测试将覆盖当前结果，确定继续吗？',
    success: (res) => {
      if (res.confirm) {
        uni.navigateTo({ url: '/pages/holland/holland' })
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-page;
  padding: 32rpx;
  padding-bottom: 200rpx;
  box-sizing: border-box;
}

.result-header {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border-radius: $radius-xl;
  padding: 48rpx;
  text-align: center;
  margin-bottom: 32rpx;
}

.result-code {
  font-size: 72rpx;
  font-weight: 700;
  color: #fff;
  display: block;
  margin-bottom: 16rpx;
}

.result-name {
  font-size: 28rpx;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.section {
  background: $bg-white;
  border-radius: $radius-xl;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
  margin-bottom: 24rpx;
  display: block;
}

.scores-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24rpx;
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.score-type {
  font-size: 32rpx;
  font-weight: 700;
  color: #7c3aed;
}

.score-bar-wrap {
  width: 100%;
}

.score-bar-bg {
  width: 100%;
  height: 12rpx;
  background: $bg-input;
  border-radius: $radius-full;
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #7c3aed, #A78BFA);
  border-radius: $radius-full;
}

.score-value {
  font-size: 24rpx;
  color: $text-muted;
}

.traits-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.trait-item {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.trait-dot {
  color: #7c3aed;
  font-size: 12rpx;
  margin-top: 6rpx;
}

.trait-text {
  flex: 1;
  font-size: 28rpx;
  color: $text-primary;
  line-height: 1.6;
}

.careers-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.career-tag {
  padding: 12rpx 24rpx;
  background: $bg-page;
  border-radius: $radius-full;
  font-size: 26rpx;
  color: $text-secondary;
}

.majors-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.major-card {
  background: $bg-page;
  border-radius: $radius-lg;
  padding: 24rpx;
}

.major-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.major-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.major-stars {
  font-size: 24rpx;
  color: #7c3aed;
}

.major-desc {
  font-size: 24rpx;
  color: $text-muted;
  line-height: 1.5;
  margin-bottom: 16rpx;
  display: block;
}

.major-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16rpx;
  border-top: 2rpx solid $border-light;
  font-size: 24rpx;
  color: #7c3aed;
}

.footer {
  position: fixed;
  bottom: calc(32rpx + env(safe-area-inset-bottom));
  left: 32rpx;
  right: 32rpx;
}

.retry-btn {
  width: 100%;
  height: 88rpx;
  background: $bg-white;
  border: 2rpx solid $border-light;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 600;
  color: $text-secondary;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/pages/holland/holland-result.vue
git commit -m "feat: add holland result page"
```

---

## Task 12: 添加 Tab 图标资源

**Files:**
- Create: `src/static/tab-home.png`, `src/static/tab-home-active.png`, `src/static/tab-assess.png`, `src/static/tab-assess-active.png`, `src/static/tab-profile.png`, `src/static/tab-profile-active.png`

- [ ] **Step 1: 创建占位图标说明文件**

由于设计稿未提供，先创建占位说明：

```bash
cd src/static
cat > tab-icons-placeholder.md << 'EOF'
# Tab 图标占位

需要设计稿提供以下图标（64x64px PNG）：

- tab-home.png: 首页图标（未选中）- 灰色
- tab-home-active.png: 首页图标（选中）- 橙色 #F97316
- tab-assess.png: 测评图标（未选中）- 灰色
- tab-assess-active.png: 测评图标（选中）- 橙色 #F97316
- tab-profile.png: 我的图标（未选中）- 灰色
- tab-profile-active.png: 我的图标（选中）- 橙色 #F97316

设计风格：线性图标，2px 描边

临时方案：可使用 iconfont 或 iconpark 在线图标库下载
EOF
```

- [ ] **Step 2: 使用在线图标作为临时方案**

从 iconfont 或 iconpark 下载 64x64px PNG 图标，放入 `src/static/` 目录。

建议图标：
- 首页：home 图标
- 测评：clipboard 或 document 图标
- 我的：user 或 profile 图标

- [ ] **Step 3: 提交**

```bash
git add src/static/
git commit -m "feat: add tab bar icons"
```

---

## Task 13: 更新 pages.json 配置

**Files:**
- Modify: `src/pages.json`

- [ ] **Step 1: 更新 pages.json，添加新页面路由**

```json
{
  "pages": [
    {
      "path": "pages/index/index",
      "style": {
        "navigationBarTitleText": "峰哥咨询参考",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/assessments/assessments",
      "style": {
        "navigationBarTitleText": "测评",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/profile/profile",
      "style": {
        "navigationBarTitleText": "我的",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/mbti/mbti",
      "style": {
        "navigationBarTitleText": "MBTI 性格测试",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/mbti/mbti-result",
      "style": {
        "navigationBarTitleText": "MBTI 测试结果",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/holland/holland",
      "style": {
        "navigationBarTitleText": "霍兰德职业兴趣测试",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/holland/holland-result",
      "style": {
        "navigationBarTitleText": "霍兰德测试结果",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/chat/chat",
      "style": {
        "navigationBarTitleText": "AI 咨询",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/questionnaire/questionnaire",
      "style": {
        "navigationBarTitleText": "个人特质问卷",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/report/report",
      "style": {
        "navigationBarTitleText": "我的志愿报告",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    },
    {
      "path": "pages/report-view/report-view",
      "style": {
        "navigationBarTitleText": "报告查看",
        "navigationBarBackgroundColor": "#FFFFFF",
        "navigationBarTextStyle": "black"
      }
    }
  ],
  "tabBar": {
    "color": "#9CA3AF",
    "selectedColor": "#F97316",
    "backgroundColor": "#FFFFFF",
    "borderStyle": "white",
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页",
        "iconPath": "static/tab-home.png",
        "selectedIconPath": "static/tab-home-active.png"
      },
      {
        "pagePath": "pages/assessments/assessments",
        "text": "测评",
        "iconPath": "static/tab-assess.png",
        "selectedIconPath": "static/tab-assess-active.png"
      },
      {
        "pagePath": "pages/profile/profile",
        "text": "我的",
        "iconPath": "static/tab-profile.png",
        "selectedIconPath": "static/tab-profile-active.png"
      }
    ]
  },
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "峰哥咨询参考",
    "navigationBarBackgroundColor": "#FFFFFF",
    "backgroundColor": "#F9FAFB"
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add src/pages.json
git commit -m "feat: update pages.json with new routes and tab bar"
```

---

## Task 14: 测试与验收

- [ ] **Step 1: 编译小程序**

```bash
cd gaokao-miniprogram
npm run dev:mp-weixin
```

- [ ] **Step 2: 在微信开发者工具中测试**

检查清单：
- [ ] 底部导航栏显示正确，可切换
- [ ] 首页显示三个测评卡片，状态正确
- [ ] 点击五环问卷卡片可跳转
- [ ] 点击 MBTI 卡片可跳转测评/结果页
- [ ] 点击霍兰德卡片可跳转测评/结果页
- [ ] MBTI 测评 48 题可正常作答
- [ ] MBTI 结果页显示正确
- [ ] 霍兰德测评 60 题可正常作答
- [ ] 霍兰德结果页显示正确
- [ ] 测评 tab 页显示正确状态
- [ ] 我的 tab 页显示测评记录
- [ ] 生成报告按钮在 3/3 完成后可点击

- [ ] **Step 3: 提交最终版本**

```bash
git add .
git commit -m "feat: complete assessment module implementation"
```

---

## 总结

本计划创建了完整的测评模块，包括：

1. **底部 Tab 导航**：首页、测评、我的
2. **首页改造**：新增测评卡片入口
3. **测评 Tab 页**：三个测评的卡片列表
4. **我的 Tab 页**：报告查看 + 测评记录
5. **MBTI 测评**：48 题 + 结果页 + 专业推荐
6. **霍兰德测评**：60 题 + 结果页 + 专业推荐
7. **存储扩展**：支持测评数据存储和进度保存

**总计 14 个任务**，预计 2-3 天完成开发。
