function hasUsableScore(profile = {}) {
  const score = Number(profile.score)
  return Number.isFinite(score) && score >= 0 && score <= 750
}

function classifyReportMode(profile = {}) {
  if ((profile.planning_mode === 'early' || profile.report_mode === 'planning') && !hasUsableScore(profile)) {
    return 'planning'
  }
  if (profile.score_type === 'estimated' || profile.report_mode === 'estimated') {
    return 'estimated'
  }
  if (hasUsableScore(profile)) return 'official'
  return 'planning'
}

function buildTimeAndModeSection(mode) {
  if (mode === 'planning') {
    return `【时间与数据背景】
当前是提前规划场景，用户可能是高一/高二家长，尚未掌握正式分数。报告重点是专业方向、孩子画像、能力差距、学习路径、目标分数段和家长行动。严禁输出精确冲稳保院校排序。`
  }
  if (mode === 'estimated') {
    return `【时间与数据背景】
当前使用的是预估分数。预估分数只作为粗定位参考，不是分数预测产品；允许合理误差。报告核心价值必须来自专业适配、孩子画像、家庭约束、风险判断和行动质量。可以给出大致院校层次参考，但不要把预估分建议写成录取承诺，也不要反复用校准提醒打断报告。`
  }
  return `【时间与数据背景】
当前时间背景是 2026 年 6 月至 7 月，正处于高考出分后、家长和考生集中填报志愿的关键阶段。2025 年录取分数线已经可作为核心历史参考；2023、2024 年数据可辅助判断波动趋势。报告读者是家长和孩子，必须把“能不能上、值不值得上、适不适合上、风险在哪里、下一步怎么核验”讲清楚。`
}

function buildCandidatePoolSection(mode, recText) {
  if (mode === 'planning') {
    return `【院校层次认知与后续校准策略资料】
当前没有正式分数和位次，结构化冲稳保候选池不作为本报告核心依据。Tab 5 应解释未来如何看院校层次、需要收集哪些分数/位次/专业组数据、什么时候回来校准。`
  }
  return `【2025 年结构化冲稳保候选池（Tab 5 院校研究核心依据，禁止编造列表外学校）】
${recText}`
}

function buildCandidatePoolRules(mode) {
  if (mode === 'planning') {
    return `【院校层次策略使用规则】
- 当前无正式分数，不能输出具体冲稳保学校排序，也不要把候选池为空当作报告弱点。
- Tab 5 必须转为“院校层次认知与后续校准策略”：说明家长未来要收集分数、位次、专业组、招生计划和城市约束，再回来做院校定位。
- 可以讲院校层次、城市选择、专业组风险的判断方法，但不要虚构学校、专业、分数线和位次。`
  }
  if (mode === 'estimated') {
    return `【预估分候选池使用规则】
- 预估分数只用于粗定位参考，不是分数预测产品；允许合理误差，核心价值仍是专业适配、孩子画像、家庭约束、风险判断和行动质量。
- Tab 5 可以结合候选池做大致院校层次参考，但必须使用“预估定位”口径，不要写成录取承诺。
- 只在关键位置提醒正式分数/位次出来后再校准，不要反复用校准提醒打断报告。
- 使用候选池时，优先引用 2025 年最低分、最低位次、分差和批次；不得把 2025 年历史录取线表述为 2026 年最终录取线。`
  }
  return `【冲稳保候选池使用规则】
- 冲稳保候选池只约束 Tab 5“大学深度研究”和 Tab 6 中涉及院校排序的部分；不要让冲稳保分数线挤占 Tab 1-4 的测评画像、专业适配和专业研究内容。
- Tab 5 可围绕候选池学校做院校定位，只能围绕上方候选池中的学校/专业组/专业做选择、排序和解释；候选池为空时，必须说明“当前结构化数据库召回不足”，不要凭空补学校。
- 使用候选池时，优先引用 2025 年最低分、最低位次、分差和批次；不得把 2025 年历史录取线表述为 2026 年最终录取线。
- 候选池是后端按考生分数/位次附近召回的小范围数据，不是全量数据库；你负责做家长能看懂的取舍解释，不负责扩写原始分数线表。`
}

function buildTab5ModeRules(mode) {
  if (mode === 'planning') {
    return `- Tab 5 标题和内容应转为“院校层次认知与后续校准策略”，解释未来如何看院校层次、需要收集哪些分数/位次/专业组数据、什么时候回来校准；严禁输出精确冲稳保院校排序。`
  }
  if (mode === 'estimated') {
    return `- Tab 5 可以结合候选池做粗定位和层次参考，但必须用“预估定位”口径表达；只需要在关键位置提示正式分数/位次出来后再校准，不要让校准提醒压过专业和行动分析。`
  }
  return `- Tab 5 必须基于“2025 年结构化冲稳保候选池”中的学校，严禁虚构学校、专业、分数线和位次；每个候选解释都要说明“历史数据参考，不等于 2026 年录取承诺”。`
}

function buildPrompt(profile, messages, majorReports, univData, assessments = {}) {
  const arr = v => (Array.isArray(v) ? v.join('、') : v || '未作答')
  const reportMode = classifyReportMode(profile)
  const studentScore = Number(profile.score) || 0
  const mbti = assessments.mbti || {}
  const holland = assessments.holland || {}
  const mbtiReport = mbti.report || {}
  const hollandReport = holland.report || {}
  const hollandIndicators = Array.isArray(holland.indicators) ? holland.indicators : []

  const mbtiText = mbti.completed
    ? [
        `MBTI 测评结果：${mbti.type || '未知'} 型${mbtiReport.name ? `（${mbtiReport.name}）` : ''}`,
        `核心标签：${arr(mbtiReport.tags)}`,
        `主要特质：${arr(mbtiReport.traits)}`,
        `参考职业：${arr(mbtiReport.careers)}`,
        `参考专业：${arr(mbtiReport.majors)}`,
      ].join('\n')
    : 'MBTI 测评结果：未完成'

  const hollandScoreText = hollandIndicators.length > 0
    ? hollandIndicators.map(item => `${item.type || ''}${item.label || ''}=${item.score ?? 0}`).join(' | ')
    : Object.entries(holland.scores || {}).map(([key, value]) => `${key}=${value}`).join(' | ') || '未提供'

  const hollandText = holland.completed
    ? [
        `霍兰德职业兴趣：${holland.code || '未知'} 型${hollandReport.name ? `（${hollandReport.name}）` : ''}`,
        `六维指标：${hollandScoreText}`,
        `核心标签：${arr(hollandReport.tags)}`,
        `主要特质：${arr(hollandReport.traits)}`,
        `参考职业：${arr(hollandReport.careers)}`,
        `参考专业：${arr(hollandReport.majors)}`,
      ].join('\n')
    : '霍兰德职业兴趣：未完成'

  const msgText = messages.length > 0
    ? messages.slice(-20).map(m => `${m.role}：${m.content}`).join('\n')
    : '（暂无对话记录）'

  const majorText = majorReports.length > 0
    ? majorReports.join('\n\n')
    : '（该专业深度评估报告正在测算中，目前仅提供基础大模型分析）'

  const { recommendations = [], reports = [] } = univData || {}
  
  const recText = recommendations.length > 0
    ? recommendations.slice(0, 18).map(r => {
        const year = r.year || 2025
        const school = r.school_name || r.name || r.school || '未命名院校'
        const major = r.major_name || r.major || r.group_name || r.special_group || '专业组/专业未标注'
        const batch = r.batch || r.batch_name || '批次未标注'
        const minScore = r.min_score ?? '---'
        const minRank = r.min_rank ?? '---'
        const bucket = r.bucket || r.risk || r.level || '候选'
        const scoreGap = Number.isFinite(Number(minScore)) && studentScore
          ? Number(minScore) - studentScore
          : null
        const gapText = scoreGap === null ? '分差未知' : `分差${scoreGap >= 0 ? '+' : ''}${scoreGap}`
        return `- ${bucket} | ${school} | ${major} | ${batch} | ${year}年最低${minScore}分 | 位次${minRank} | ${gapText}`
      }).join('\n')
    : '（暂无结构化推荐数据）'

  const univText = reports.length > 0
    ? reports.join('\n\n')
    : '（该大学深度评估报告正在测算中，目前仅提供基础大模型分析）'

  return `你是一位专业的高考志愿填报顾问，风格参考资深规划专家：直接、专业、给具体可操作的建议。根据以下考生完整信息，生成一份个人化的综合测评参考报告。

${buildTimeAndModeSection(reportMode)}

【考生基本信息】
省份：${profile.province || '未填写'} | 科目：${profile.category || '未填写'} | 分数：${profile.score || '未填写'} | 位次：${profile.rank || '未填写'} | 规划模式：${profile.planning_mode || 'score'} | 分数类型：${profile.score_type || (reportMode === 'official' ? 'official' : '未填写')} | 年级/身份：${[profile.grade, profile.identity].filter(Boolean).join('/') || '未填写'} | 预估分段：${profile.score_range || '未填写'}

【测评结果摘要】
${mbtiText}
${hollandText}

【AI 对话记录（最近 20 条）】
${msgText}

${buildCandidatePoolSection(reportMode, recText)}

${buildCandidatePoolRules(reportMode)}

【专业深度研究资料（Tab 4 直接引用，不得编造数据）】
${majorText}

【院校深度研究资料（Tab 5 补充参考，不得编造数据）】
${univText}

输出要求：
- 服务端已经有固定 HTML 模板，并且服务端已经固定 HTML 页面格式和打印/PDF版式；你只负责填充内容 JSON，不要生成 HTML、CSS、JS、Markdown 排版或模板代码。
- 请严格输出合法的 JSON 对象，不要包含任何 Markdown 格式或多余说明，不要用 \`\`\`json 围栏。
- JSON 必须符合以下结构（不要输出 HTML 标签，只输出纯文本内容）：
{
  "conclusions": [
    "家长先看结论的第1条...",
    "家长先看结论的第2条..."
  ],
  "modules": [
    {
      "id": "tab1",
      "title": "自我评估总结",
      "summary": "模块的核心总结或顾问寄语...",
      "blocks": [
        {
          "type": "text",
          "title": "小节标题",
          "content": "小节正文内容..."
        },
        {
          "type": "list",
          "title": "列表标题（可选）",
          "items": ["列表项1", "列表项2"]
        },
        {
          "type": "alert",
          "level": "warning", // 必须是 info, warning, danger, success 之一
          "title": "提醒或核验动作标题",
          "content": "提示正文...",
          "items": ["动作1", "动作2"] // 可选动作列表
        },
        {
          "type": "quote",
          "author": "首席顾问点评",
          "content": "引用的金句或犀利点评..."
        },
        {
          "type": "table",
          "title": "表格标题（可选）",
          "headers": ["列1", "列2"],
          "rows": [["行1数据1", "行1数据2"], ["行2数据1", "行2数据2"]]
        }
      ]
    }
  ]
}
- \`conclusions\` 是一个字符串数组，每条是一句话，说明适合方向、必须避坑点、下一步动作等。
- \`modules\` 必须包含6个对象，对应：tab1(自我评估总结)、tab2(个人特质分析)、tab3(专业匹配分析)、tab4(专业深度研究)、tab5(大学深度研究)、tab6(综合决策报告)。
- 综合报告正文目标写到 9000-12000 字；硬性要求是 tab1-tab6 每个模块的中文正文内容都必须不少于 1000 字，字数不包含标题、表头和短标签。
- 每个模块至少包含 4 个实质分析 blocks，其中至少 2 个 text block 各不少于 250 字；用“结论 + 原因 + 对考生的影响 + 家长核验动作”的方式展开，禁止空泛重复和注水。
- 必须包含“志愿执行清单”：使用 list 或 alert 形式，每条建议必须包含动作、原因、核验材料。
- 每个模块至少包含 1 个 level 为 "warning" 或 "danger" 的 alert 块，作为“家长核验动作”。
- Tab 4 专业深度研究和 Tab 5 大学深度研究是综合报告正文的一部分，也必须各写不少于 1000 字：先基于资料做长篇决策分析，再在该模块最后一个 block 中添加 text，内容提示“完整 5000 字以上 PDF 已入库，需要到小程序‘深度报告下载页’付费后选择对应专业/学校下载”。
${buildTab5ModeRules(reportMode)}
- 不要生成额外的目录页、Table 页或单独的表格页；表格只能作为正文中的辅助 block，核心价值必须来自顾问式文字分析。
- 不要使用“AI 总评”“大模型认为”等词汇，统一改成“顾问结论”。`
}

module.exports = Object.assign(buildPrompt, {
  classifyReportMode,
})
