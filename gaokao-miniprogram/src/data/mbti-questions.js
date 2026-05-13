/**
 * MBTI 题库数据
 * 48 道题，覆盖 4 个维度（EI、SN、TF、JP），每个维度 12 题
 */

// MBTI 题目
export const MBTI_QUESTIONS = [
  // ========== E vs I (外向 vs 内向) ==========
  {
    id: 1,
    dimension: 'EI',
    text: '在社交场合中，你通常感觉如何？',
    options: [
      { text: '充满活力，从与人交流中获得能量', value: 'E' },
      { text: '有些疲惫，更喜欢独处或与少数人交流', value: 'I' }
    ]
  },
  {
    id: 2,
    dimension: 'EI',
    text: '周末你更倾向于：',
    options: [
      { text: '约朋友出去玩，参加聚会或活动', value: 'E' },
      { text: '待在家里，看书、追剧或做自己喜欢的事', value: 'I' }
    ]
  },
  {
    id: 3,
    dimension: 'EI',
    text: '遇到问题时，你更习惯：',
    options: [
      { text: '找人讨论，通过交流理清思路', value: 'E' },
      { text: '独自思考，在心里反复琢磨', value: 'I' }
    ]
  },
  {
    id: 4,
    dimension: 'EI',
    text: '在工作中，你更喜欢：',
    options: [
      { text: '团队协作，大家一起完成项目', value: 'E' },
      { text: '独立工作，自己掌控进度', value: 'I' }
    ]
  },
  {
    id: 5,
    dimension: 'EI',
    text: '当你需要放松时，你会：',
    options: [
      { text: '出去活动，见见朋友', value: 'E' },
      { text: '一个人静一静，做些安静的事情', value: 'I' }
    ]
  },
  {
    id: 6,
    dimension: 'EI',
    text: '在陌生环境中，你倾向于：',
    options: [
      { text: '主动与他人交流，建立联系', value: 'E' },
      { text: '先观察，慢慢熟悉后再交流', value: 'I' }
    ]
  },
  {
    id: 7,
    dimension: 'EI',
    text: '你认为自己更像是：',
    options: [
      { text: '开放外向，容易被他人了解', value: 'E' },
      { text: '深沉内敛，只有少数人真正了解你', value: 'I' }
    ]
  },
  {
    id: 8,
    dimension: 'EI',
    text: '在小组讨论中，你通常会：',
    options: [
      { text: '积极发言，分享自己的想法', value: 'E' },
      { text: '多听少说，思考后再发言', value: 'I' }
    ]
  },
  {
    id: 9,
    dimension: 'EI',
    text: '接到新任务时，你倾向于：',
    options: [
      { text: '立即行动，边做边调整', value: 'E' },
      { text: '先独自规划好再行动', value: 'I' }
    ]
  },
  {
    id: 10,
    dimension: 'EI',
    text: '你更喜欢的工作环境是：',
    options: [
      { text: '开放式办公，经常有互动', value: 'E' },
      { text: '独立办公室，可以专注工作', value: 'I' }
    ]
  },
  {
    id: 11,
    dimension: 'EI',
    text: '当你感到压力大时，你倾向于：',
    options: [
      { text: '找人倾诉，通过交流缓解', value: 'E' },
      { text: '独自消化，通过独处恢复', value: 'I' }
    ]
  },
  {
    id: 12,
    dimension: 'EI',
    text: '你认为自己更擅长：',
    options: [
      { text: '表达和沟通', value: 'E' },
      { text: '倾听和思考', value: 'I' }
    ]
  },

  // ========== S vs N (实感 vs 直觉) ==========
  {
    id: 13,
    dimension: 'SN',
    text: '你更关注：',
    options: [
      { text: '眼前现实的人和事', value: 'S' },
      { text: '未来的可能性和抽象概念', value: 'N' }
    ]
  },
  {
    id: 14,
    dimension: 'SN',
    text: '学习新知识时，你更喜欢：',
    options: [
      { text: '具体的例子和实践操作', value: 'S' },
      { text: '理论框架和概念理解', value: 'N' }
    ]
  },
  {
    id: 15,
    dimension: 'SN',
    text: '你更相信：',
    options: [
      { text: '过往经验和确凿的事实', value: 'S' },
      { text: '直觉预感和灵感', value: 'N' }
    ]
  },
  {
    id: 16,
    dimension: 'SN',
    text: '在阅读时，你更注意：',
    options: [
      { text: '具体的细节和描述', value: 'S' },
      { text: '整体的主题和寓意', value: 'N' }
    ]
  },
  {
    id: 17,
    dimension: 'SN',
    text: '你更喜欢：',
    options: [
      { text: '按部就班，处理具体事务', value: 'S' },
      { text: '天马行空，探索新的想法', value: 'N' }
    ]
  },
  {
    id: 18,
    dimension: 'SN',
    text: '你认为自己是：',
    options: [
      { text: '务实的人，注重实际效果', value: 'S' },
      { text: '理想主义者，追求意义', value: 'N' }
    ]
  },
  {
    id: 19,
    dimension: 'SN',
    text: '做决定时，你更看重：',
    options: [
      { text: '具体的数据和现实情况', value: 'S' },
      { text: '整体的趋势和潜在可能', value: 'N' }
    ]
  },
  {
    id: 20,
    dimension: 'SN',
    text: '你更喜欢的工作方式是：',
    options: [
      { text: '处理当下具体的问题', value: 'S' },
      { text: '规划未来的发展方向', value: 'N' }
    ]
  },
  {
    id: 21,
    dimension: 'SN',
    text: '在沟通中，你更习惯：',
    options: [
      { text: '说具体的事情和细节', value: 'S' },
      { text: '谈想法和概念', value: 'N' }
    ]
  },
  {
    id: 22,
    dimension: 'SN',
    text: '你对创新的看法是：',
    options: [
      { text: '在现有基础上改进更好', value: 'S' },
      { text: '彻底的创新更有价值', value: 'N' }
    ]
  },
  {
    id: 23,
    dimension: 'SN',
    text: '你更感兴趣的是：',
    options: [
      { text: '事物的本来面目', value: 'S' },
      { text: '事物背后的意义', value: 'N' }
    ]
  },
  {
    id: 24,
    dimension: 'SN',
    text: '在解决问题时，你倾向于：',
    options: [
      { text: '用已知的方法逐步解决', value: 'S' },
      { text: '寻找创新性的解决方案', value: 'N' }
    ]
  },

  // ========== T vs F (思考 vs 情感) ==========
  {
    id: 25,
    dimension: 'TF',
    text: '做决定时，你更看重：',
    options: [
      { text: '逻辑分析和客观标准', value: 'T' },
      { text: '个人价值观和他人感受', value: 'F' }
    ]
  },
  {
    id: 26,
    dimension: 'TF',
    text: '在争论中，你更注重：',
    options: [
      { text: '谁的观点更有道理', value: 'T' },
      { text: '维护彼此的关系和感受', value: 'F' }
    ]
  },
  {
    id: 27,
    dimension: 'TF',
    text: '你认为更重要是：',
    options: [
      { text: '公正和原则', value: 'T' },
      { text: '和谐与同情', value: 'F' }
    ]
  },
  {
    id: 28,
    dimension: 'TF',
    text: '评价他人时，你更看重：',
    options: [
      { text: '能力和表现', value: 'T' },
      { text: '态度和用心程度', value: 'F' }
    ]
  },
  {
    id: 29,
    dimension: 'TF',
    text: '面对冲突时，你倾向于：',
    options: [
      { text: '直接指出问题所在', value: 'T' },
      { text: '考虑对方感受，委婉表达', value: 'F' }
    ]
  },
  {
    id: 30,
    dimension: 'TF',
    text: '你更容易被什么打动？',
    options: [
      { text: '精妙的逻辑和论证', value: 'T' },
      { text: '真挚的情感和故事', value: 'F' }
    ]
  },
  {
    id: 31,
    dimension: 'TF',
    text: '在团队合作中，你更注重：',
    options: [
      { text: '效率和结果', value: 'T' },
      { text: '团队氛围和成员感受', value: 'F' }
    ]
  },
  {
    id: 32,
    dimension: 'TF',
    text: '你认为自己是：',
    options: [
      { text: '理性客观的人', value: 'T' },
      { text: '热情感性的人', value: 'F' }
    ]
  },
  {
    id: 33,
    dimension: 'TF',
    text: '给别人反馈时，你会：',
    options: [
      { text: '直接指出问题，不绕弯子', value: 'T' },
      { text: '先肯定优点，再委婉提出建议', value: 'F' }
    ]
  },
  {
    id: 34,
    dimension: 'TF',
    text: '你更欣赏：',
    options: [
      { text: '冷静理智的人', value: 'T' },
      { text: '善解人意的人', value: 'F' }
    ]
  },
  {
    id: 35,
    dimension: 'TF',
    text: '在做重要选择时，你倾向于：',
    options: [
      { text: '列出利弊，理性分析', value: 'T' },
      { text: '听从内心感受', value: 'F' }
    ]
  },
  {
    id: 36,
    dimension: 'TF',
    text: '你认为更好的领导风格是：',
    options: [
      { text: '公正严格，按规则办事', value: 'T' },
      { text: '关心下属，注重团队氛围', value: 'F' }
    ]
  },

  // ========== J vs P (判断 vs 感知) ==========
  {
    id: 37,
    dimension: 'JP',
    text: '你更喜欢：',
    options: [
      { text: '事先做好计划，按计划行事', value: 'J' },
      { text: '保持灵活，随遇而安', value: 'P' }
    ]
  },
  {
    id: 38,
    dimension: 'JP',
    text: '面对截止日期，你会：',
    options: [
      { text: '提前完成，留出缓冲时间', value: 'J' },
      { text: '在压力下最后冲刺', value: 'P' }
    ]
  },
  {
    id: 39,
    dimension: 'JP',
    text: '你的工作风格是：',
    options: [
      { text: '有条不紊，完成一件再开始下一件', value: 'J' },
      { text: '多任务并行，灵活切换', value: 'P' }
    ]
  },
  {
    id: 40,
    dimension: 'JP',
    text: '对于变化，你的态度是：',
    options: [
      { text: '希望提前知道，做好准备', value: 'J' },
      { text: '喜欢新鲜感，能随机应变', value: 'P' }
    ]
  },
  {
    id: 41,
    dimension: 'JP',
    text: '你的生活环境通常是：',
    options: [
      { text: '整洁有序，各归其位', value: 'J' },
      { text: '看似凌乱但心中有数', value: 'P' }
    ]
  },
  {
    id: 42,
    dimension: 'JP',
    text: '做决定时，你倾向于：',
    options: [
      { text: '尽快决定，不再纠结', value: 'J' },
      { text: '多收集信息，保持开放', value: 'P' }
    ]
  },
  {
    id: 43,
    dimension: 'JP',
    text: '你更喜欢的工作方式：',
    options: [
      { text: '任务明确，有清晰的里程碑', value: 'J' },
      { text: '自由探索，不受太多约束', value: 'P' }
    ]
  },
  {
    id: 44,
    dimension: 'JP',
    text: '面对未完成的事情，你会：',
    options: [
      { text: '感到不舒服，想尽快完成', value: 'J' },
      { text: '可以暂时放下，以后再说', value: 'P' }
    ]
  },
  {
    id: 45,
    dimension: 'JP',
    text: '你更喜欢：',
    options: [
      { text: '事情有定论，尘埃落定', value: 'J' },
      { text: '保持开放，等待更多可能性', value: 'P' }
    ]
  },
  {
    id: 46,
    dimension: 'JP',
    text: '旅行时，你会：',
    options: [
      { text: '详细规划行程', value: 'J' },
      { text: '到了再说，随心而动', value: 'P' }
    ]
  },
  {
    id: 47,
    dimension: 'JP',
    text: '你认为自己是：',
    options: [
      { text: '目标导向的人', value: 'J' },
      { text: '过程导向的人', value: 'P' }
    ]
  },
  {
    id: 48,
    dimension: 'JP',
    text: '你更喜欢的生活方式是：',
    options: [
      { text: '有规律、可预期的生活', value: 'J' },
      { text: '自由自在、充满惊喜的生活', value: 'P' }
    ]
  }
];

// MBTI 16 种人格类型描述
export const MBTI_TYPE_DESCRIPTIONS = {
  INTJ: {
    name: '建筑师',
    tags: ['独立', '战略', '理性', '完美主义'],
    traits: [
      '富有想象力和战略性的思考者',
      '对一切皆有计划，追求卓越',
      '善于发现系统中的低效问题并改进',
      '独立自主，不随波逐流',
      '知识渊博，喜欢深入钻研'
    ],
    careers: ['软件架构师', '战略顾问', '科研人员', '数据科学家', '系统分析师', '投资分析师'],
    majors: ['计算机科学与技术', '数学', '物理学', '哲学', '经济学', '建筑学']
  },
  INTP: {
    name: '逻辑学家',
    tags: ['好奇', '分析', '创新', '独立'],
    traits: [
      '对理论和抽象概念充满好奇',
      '善于分析复杂问题，寻找本质',
      '思维灵活，富有创新精神',
      '重视智力和能力',
      '喜欢独立思考，不受束缚'
    ],
    careers: ['研究员', '程序员', '数据分析师', '大学教授', '科学作家', '产品设计师'],
    majors: ['计算机科学', '数学', '物理学', '化学', '生物学', '逻辑学']
  },
  ENTJ: {
    name: '指挥官',
    tags: ['领导', '果断', '自信', '战略'],
    traits: [
      '天生的领导者，善于组织协调',
      '目标明确，行动果断',
      '追求效率和成果',
      '具有战略眼光',
      '喜欢挑战，不畏困难'
    ],
    careers: ['企业高管', '管理咨询', '创业家', '项目经理', '律师', '投资银行家'],
    majors: ['工商管理', '法学', '经济学', '金融学', '国际关系', '市场营销']
  },
  ENTP: {
    name: '辩论家',
    tags: ['机智', '创新', '挑战', '灵活'],
    traits: [
      '思维敏捷，善于辩论',
      '喜欢挑战传统观念',
      '富有创新精神，点子多',
      '善于发现机会',
      '适应能力强，喜欢变化'
    ],
    careers: ['创业者', '咨询顾问', '记者', '广告创意', '投资经理', '产品经理'],
    majors: ['工商管理', '新闻传播', '市场营销', '法学', '心理学', '设计学']
  },
  INFJ: {
    name: '提倡者',
    tags: ['理想', '深刻', '有原则', '富有洞察力'],
    traits: [
      '富有理想主义色彩',
      '对人性和社会有深刻洞察',
      '坚持原则和价值观',
      '富有同理心，关心他人',
      '追求意义和使命感'
    ],
    careers: ['心理咨询师', '人力资源', '非营利组织', '教育工作者', '社会工作者', '作家'],
    majors: ['心理学', '社会学', '教育学', '文学', '社会工作', '公共管理']
  },
  INFP: {
    name: '调停者',
    tags: ['理想', '温和', '创造性', '真诚'],
    traits: [
      '内心世界丰富，富有想象力',
      '追求真善美',
      '温和友善，富有同理心',
      '重视个人价值观和真实性',
      '富有创造力和艺术天赋'
    ],
    careers: ['作家', '艺术家', '心理咨询师', '编辑', '教师', '非营利组织'],
    majors: ['文学', '心理学', '艺术设计', '新闻传播', '社会工作', '哲学']
  },
  ENFJ: {
    name: '主人公',
    tags: ['魅力', '利他', '领导', '热情'],
    traits: [
      '天生具有感染力和号召力',
      '关心他人成长，乐于助人',
      '善于发现他人优点',
      '富有激情和理想',
      '擅长组织和激励团队'
    ],
    careers: ['教师', '培训师', '人力资源总监', '公关经理', '政治家', '社会活动家'],
    majors: ['教育学', '心理学', '人力资源管理', '公共关系', '播音主持', '社会工作']
  },
  ENFP: {
    name: '竞选者',
    tags: ['热情', '创造', '自由', '社交'],
    traits: [
      '热情洋溢，充满活力',
      '富有想象力和创造力',
      '善于与人建立联系',
      '追求自由和多样性',
      '乐观积极，富有感染力'
    ],
    careers: ['媒体人', '活动策划', '销售经理', '公关', '心理咨询师', '创意总监'],
    majors: ['新闻传播', '市场营销', '艺术设计', '心理学', '表演艺术', '广告学']
  },
  ISTJ: {
    name: '物流师',
    tags: ['负责', '可靠', '传统', '有条理'],
    traits: [
      '认真负责，值得信赖',
      '做事有条不紊，注重细节',
      '尊重传统和规则',
      '意志坚定，说到做到',
      '稳重务实，踏实肯干'
    ],
    careers: ['会计师', '审计师', '律师', '医生', '工程师', '公务员'],
    majors: ['会计学', '法学', '医学', '土木工程', '计算机科学', '公共管理']
  },
  ISFJ: {
    name: '守卫者',
    tags: ['温暖', '尽责', '忠诚', '谦逊'],
    traits: [
      '温和友善，富有同情心',
      '尽职尽责，注重细节',
      '忠诚可靠，值得信赖',
      '谦虚低调，不喜张扬',
      '善于营造和谐氛围'
    ],
    careers: ['护士', '教师', '社工', '行政助理', '人力资源专员', '图书管理员'],
    majors: ['护理学', '教育学', '社会工作', '图书馆学', '行政管理', '医学技术']
  },
  ESTJ: {
    name: '总经理',
    tags: ['高效', '组织', '果断', '务实'],
    traits: [
      '出色的组织管理能力',
      '注重效率和结果',
      '决策果断，行动力强',
      '尊重规则和秩序',
      '务实导向，注重实际'
    ],
    careers: ['企业管理者', '项目经理', '军官', '警察', '运营总监', '酒店管理'],
    majors: ['工商管理', '项目管理', '法学', '行政管理', '物流管理', '军事学']
  },
  ESFJ: {
    name: '执政官',
    tags: ['热心', '合作', '传统', '周到'],
    traits: [
      '热心助人，富有同情心',
      '善于团队合作',
      '重视传统和和谐',
      '细心周到，体贴他人',
      '喜欢帮助他人解决问题'
    ],
    careers: ['教师', '护士', '销售代表', '公关', '活动策划', '客户服务'],
    majors: ['教育学', '护理学', '市场营销', '酒店管理', '旅游管理', '社会工作']
  },
  ISTP: {
    name: '鉴赏家',
    tags: ['冷静', '灵活', '实践', '独立'],
    traits: [
      '冷静理性，临危不乱',
      '动手能力强，善于实践',
      '灵活应变，适应力强',
      '独立自主，不喜被约束',
      '对机械和技术感兴趣'
    ],
    careers: ['工程师', '技师', '飞行员', '外科医生', '数据分析师', '运动员'],
    majors: ['机械工程', '计算机科学', '航空技术', '医学', '自动化', '体育教育']
  },
  ISFP: {
    name: '探险家',
    tags: ['温和', '艺术', '灵活', '低调'],
    traits: [
      '温和友善，不喜冲突',
      '富有艺术天赋和审美',
      '活在当下，享受生活',
      '灵活随性，不受拘束',
      '谦逊低调，不喜张扬'
    ],
    careers: ['设计师', '艺术家', '摄影师', '厨师', '心理咨询师', '兽医'],
    majors: ['艺术设计', '美术学', '音乐学', '服装设计', '园林设计', '烹饪艺术']
  },
  ESTP: {
    name: '企业家',
    tags: ['大胆', '务实', '直接', '灵活'],
    traits: [
      '大胆果断，敢于冒险',
      '务实导向，注重结果',
      '直截了当，不绕弯子',
      '适应力强，反应敏捷',
      '喜欢挑战和新鲜感'
    ],
    careers: ['创业者', '销售总监', '股票交易员', '公关', '房地产经纪人', '运动员'],
    majors: ['市场营销', '金融学', '体育教育', '新闻传播', '工商管理', '国际贸易']
  },
  ESFP: {
    name: '表演者',
    tags: ['热情', '活泼', '有趣', '社交'],
    traits: [
      '热情洋溢，充满活力',
      '乐观开朗，幽默风趣',
      '善于与人互动',
      '活在当下，享受生活',
      '喜欢成为关注焦点'
    ],
    careers: ['演员', '主持人', '销售', '活动策划', '旅游顾问', '时尚买手'],
    majors: ['表演艺术', '播音主持', '市场营销', '旅游管理', '服装设计', '音乐学']
  }
};

/**
 * 计算 MBTI 类型
 * @param {Object} answers - 答案对象，key 为 questionId，value 为 选项索引 (0 或 1)
 * @returns {Object} - { type: 'INTJ', scores: { E: 5, I: 7, S: 6, N: 6, T: 8, F: 4, J: 7, P: 5 } }
 */
export function calculateMbtiType(answers) {
  const scores = {
    E: 0, I: 0,
    S: 0, N: 0,
    T: 0, F: 0,
    J: 0, P: 0
  };

  // 遍历答案，统计各维度得分
  Object.entries(answers).forEach(([questionId, answerIndex]) => {
    const question = MBTI_QUESTIONS.find(q => q.id === parseInt(questionId));
    if (question && question.options[answerIndex]) {
      const value = question.options[answerIndex].value;
      scores[value] = (scores[value] || 0) + 1;
    }
  });

  // 确定每个维度的类型
  const type = [
    scores.E >= scores.I ? 'E' : 'I',
    scores.S >= scores.N ? 'S' : 'N',
    scores.T >= scores.F ? 'T' : 'F',
    scores.J >= scores.P ? 'J' : 'P'
  ].join('');

  return {
    type,
    scores
  };
}

/**
 * 根据 MBTI 类型获取推荐专业和职业
 * @param {string} type - MBTI 类型，如 'INTJ'
 * @returns {Object} - { careers: [], majors: [], ...typeInfo }
 */
export function getMbtiRecommendations(type) {
  return MBTI_TYPE_DESCRIPTIONS[type] || null;
}
