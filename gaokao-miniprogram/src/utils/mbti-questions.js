// MBTI 48 题测评题库
// 每题有两个选项，分别对应不同的维度倾向
// dimensions: E/I (外向/内向), S/N (实感/直觉), T/F (思考/情感), J/P (判断/感知)

export const MBTI_QUESTIONS = [
  // E/I 维度题目 (1-12)
  {
    id: 1,
    dimension: 'EI',
    text: '在社交聚会中，你通常会...',
    optionA: '主动与很多人交谈，包括陌生人',
    optionB: '只与少数熟悉的人交谈',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 2,
    dimension: 'EI',
    text: '当你需要充电时，你更倾向于...',
    optionA: '和朋友一起活动',
    optionB: '独自休息或做自己的事',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 3,
    dimension: 'EI',
    text: '在团队工作中，你通常...',
    optionA: '喜欢讨论和 brainstorm',
    optionB: '喜欢先独立思考再分享',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 4,
    dimension: 'EI',
    text: '遇到问题时，你更倾向于...',
    optionA: '找别人讨论解决',
    optionB: '自己琢磨解决',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 5,
    dimension: 'EI',
    text: '你觉得自己更像是...',
    optionA: '开放外向的人',
    optionB: '安静内敛的人',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 6,
    dimension: 'EI',
    text: '在空闲时间，你更喜欢...',
    optionA: '和朋友一起出去玩',
    optionB: '在家做自己喜欢的事',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 7,
    dimension: 'EI',
    text: '在陌生环境中，你通常会...',
    optionA: '主动结识新朋友',
    optionB: '观察等待，慢慢适应',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 8,
    dimension: 'EI',
    text: '你更容易被...吸引',
    optionA: '热闹的活动和场合',
    optionB: '安静的环境和氛围',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 9,
    dimension: 'EI',
    text: '说话时，你通常...',
    optionA: '边想边说，反应很快',
    optionB: '想好再说，比较谨慎',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 10,
    dimension: 'EI',
    text: '你更喜欢...',
    optionA: '成为关注的焦点',
    optionB: '在幕后默默工作',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 11,
    dimension: 'EI',
    text: '在学习新知识时，你更喜欢...',
    optionA: '与他人讨论交流',
    optionB: '独立思考和消化',
    valueA: 'E',
    valueB: 'I'
  },
  {
    id: 12,
    dimension: 'EI',
    text: '你认为自己是...',
    optionA: '容易被了解的人',
    optionB: '比较深藏不露的人',
    valueA: 'E',
    valueB: 'I'
  },
  // S/N 维度题目 (13-24)
  {
    id: 13,
    dimension: 'SN',
    text: '你更注重...',
    optionA: '现实和具体的细节',
    optionB: '可能性和整体图景',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 14,
    dimension: 'SN',
    text: '在做决定时，你更依赖...',
    optionA: '过往的经验和事实',
    optionB: '直觉和预感',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 15,
    dimension: 'SN',
    text: '你更喜欢...',
    optionA: '按部就班地做事',
    optionB: '随心所欲地尝试',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 16,
    dimension: 'SN',
    text: '你更擅长...',
    optionA: '处理当下的具体问题',
    optionB: '规划未来的发展方向',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 17,
    dimension: 'SN',
    text: '你认为自己是...',
    optionA: '务实的人',
    optionB: '有想象力的人',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 18,
    dimension: 'SN',
    text: '在学习中，你更关注...',
    optionA: '具体的事实和数据',
    optionB: '概念和理论',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 19,
    dimension: 'SN',
    text: '你更喜欢...',
    optionA: '确定和可靠的信息',
    optionB: '新奇和有趣的想法',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 20,
    dimension: 'SN',
    text: '在描述事物时，你倾向于...',
    optionA: '用具体的例子说明',
    optionB: '用比喻和类比',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 21,
    dimension: 'SN',
    text: '你对...更感兴趣',
    optionA: '现在正在发生的事',
    optionB: '未来可能发生的事',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 22,
    dimension: 'SN',
    text: '你更相信...',
    optionA: '确凿的证据',
    optionB: '灵感和洞察力',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 23,
    dimension: 'SN',
    text: '面对复杂问题时，你倾向于...',
    optionA: '分解成具体步骤逐步解决',
    optionB: '寻找背后的模式和规律',
    valueA: 'S',
    valueB: 'N'
  },
  {
    id: 24,
    dimension: 'SN',
    text: '你更喜欢...',
    optionA: '实践和动手操作',
    optionB: '思考和理论探讨',
    valueA: 'S',
    valueB: 'N'
  },
  // T/F 维度题目 (25-36)
  {
    id: 25,
    dimension: 'TF',
    text: '在做决定时，你更看重...',
    optionA: '逻辑和客观分析',
    optionB: '个人价值观和感受',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 26,
    dimension: 'TF',
    text: '你认为更重要...',
    optionA: '真理和公正',
    optionB: '和谐和同情',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 27,
    dimension: 'TF',
    text: '在争论中，你倾向于...',
    optionA: '坚持自己的观点',
    optionB: '顾及对方的感受',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 28,
    dimension: 'TF',
    text: '你更容易被...说服',
    optionA: '有理有据的论证',
    optionB: '真诚的情感表达',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 29,
    dimension: 'TF',
    text: '在评价他人时，你更看重...',
    optionA: '能力和表现',
    optionB: '态度和用心',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 30,
    dimension: 'TF',
    text: '你更倾向于...',
    optionA: '直接指出问题所在',
    optionB: '委婉地表达意见',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 31,
    dimension: 'TF',
    text: '在处理冲突时，你更注重...',
    optionA: '找出问题的根源',
    optionB: '维护各方的关系',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 32,
    dimension: 'TF',
    text: '你认为自己是...',
    optionA: '理性客观的人',
    optionB: '感性温暖的人',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 33,
    dimension: 'TF',
    text: '在团队中，你更愿意...',
    optionA: '承担批评和指正的任务',
    optionB: '负责鼓励和支持他人',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 34,
    dimension: 'TF',
    text: '你做决定时更倾向于...',
    optionA: '不被情感左右',
    optionB: '考虑对他人的影响',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 35,
    dimension: 'TF',
    text: '你认为更好的赞美是...',
    optionA: '夸奖某人的能力',
    optionB: '表达对某人的欣赏',
    valueA: 'T',
    valueB: 'F'
  },
  {
    id: 36,
    dimension: 'TF',
    text: '面对困难决定，你会...',
    optionA: '理性分析利弊',
    optionB: '考虑各方的感受',
    valueA: 'T',
    valueB: 'F'
  },
  // J/P 维度题目 (37-48)
  {
    id: 37,
    dimension: 'JP',
    text: '在日常生活中，你更喜欢...',
    optionA: '有计划地安排',
    optionB: '灵活随机地应对',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 38,
    dimension: 'JP',
    text: '你更倾向于...',
    optionA: '提前完成任务',
    optionB: '在截止日期前完成',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 39,
    dimension: 'JP',
    text: '面对变化，你通常...',
    optionA: '感到不适，希望有预知',
    optionB: '能够适应，甚至享受变化',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 40,
    dimension: 'JP',
    text: '你喜欢...',
    optionA: '事情有定论和结果',
    optionB: '保持选择的开放性',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 41,
    dimension: 'JP',
    text: '在工作中，你更喜欢...',
    optionA: '明确的目标和计划',
    optionB: '自由度和灵活性',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 42,
    dimension: 'JP',
    text: '你认为自己是...',
    optionA: '有条理、守时的人',
    optionB: '随性、灵活的人',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 43,
    dimension: 'JP',
    text: '在处理任务时，你倾向于...',
    optionA: '一次只做一件事',
    optionB: '同时处理多项任务',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 44,
    dimension: 'JP',
    text: '你更喜欢...',
    optionA: '列清单和做计划',
    optionB: '见机行事',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 45,
    dimension: 'JP',
    text: '面对最后期限的压力，你倾向于...',
    optionA: '提前规划，避免压力',
    optionB: '在压力下更有动力',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 46,
    dimension: 'JP',
    text: '你更喜欢...的环境',
    optionA: '有序和可预测',
    optionB: '充满新鲜感',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 47,
    dimension: 'JP',
    text: '在开始新项目时，你会...',
    optionA: '先制定详细计划',
    optionB: '边做边调整',
    valueA: 'J',
    valueB: 'P'
  },
  {
    id: 48,
    dimension: 'JP',
    text: '你认为更好的工作方式是...',
    optionA: '按计划推进',
    optionB: '根据情况随时调整',
    valueA: 'J',
    valueB: 'P'
  }
]

/**
 * 计算 MBTI 类型
 * @param {Object} answers - 答案对象 { questionId: 'A' | 'B' }
 * @returns {Object} { type: 'INTJ', scores: { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 } }
 */
export function calculateMbtiType(answers) {
  const scores = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 }

  MBTI_QUESTIONS.forEach(q => {
    const answer = answers[q.id]
    if (answer === 'A') {
      scores[q.valueA]++
    } else if (answer === 'B') {
      scores[q.valueB]++
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

/**
 * 获取 MBTI 类型描述
 * @param {string} type - MBTI 类型，如 'INTJ'
 * @returns {Object} { name, description, strengths, careers }
 */
export function getMbtiDescription(type) {
  const descriptions = {
    ISTJ: {
      name: '物流师',
      description: '安静、严肃，通过全面性和可靠性获得成功。实际，实事求是，注重事实。有责任感，负责，坚定不移。重视传统和忠诚。',
      strengths: ['专注', '可靠', '有条理', '诚实', '务实'],
      careers: ['会计', '审计', '计算机编程', '工程师', '医生']
    },
    ISFJ: {
      name: '守卫者',
      description: '安静、友好、有责任感和良知。坚定地致力于完成他们的义务。忠诚、体贴，关注对他人的细节，努力创造有序和谐的环境。',
      strengths: ['支持性', '可靠', '耐心', '观察力强', '善良'],
      careers: ['护士', '教师', '社会工作者', '行政人员', '图书管理员']
    },
    INFJ: {
      name: '提倡者',
      description: '寻求思想、关系、物质等之间的意义和联系。想了解什么能激励人，对人有很强的洞察力。有责任心，坚持自己的价值观。对于如何为共同利益服务有清晰的远景。',
      strengths: ['有洞察力', '有原则', '有爱心', '有远见', '有条理'],
      careers: ['心理咨询师', '作家', '人力资源', '非营利组织', '艺术家']
    },
    INTJ: {
      name: '建筑师',
      description: '有独创性的思想，对实现自己的想法和目标有强烈的动力。能很快看到外部事件的规律，形成长远的解释性远景。当承诺做一件事时，会组织好并坚持到底。怀疑、批判、独立、决断。',
      strengths: ['战略性', '独立', '分析性', '有条理', '有创造力'],
      careers: ['科学家', '工程师', '建筑师', '战略规划', '大学教授']
    },
    ISTP: {
      name: '鉴赏家',
      description: '灵活、忍耐力强，是个安静的观察者直到有问题发生，就会马上行动。分析事物运作的原理，从大量数据中找到核心问题的所在。对于原因和结果感兴趣，用逻辑的方式处理问题。',
      strengths: ['适应力强', '务实', '分析性', '冷静', '动手能力强'],
      careers: ['工程师', '技术员', '飞行员', '警察', '机械师']
    },
    ISFP: {
      name: '探险家',
      description: '安静、友好、敏感、和善。享受当下。喜欢有自己的空间，按照自己的时间表工作。忠诚于自己的价值观和对自己重要的人。不喜欢争论和冲突，不会把自己的观念和价值观强加于人。',
      strengths: ['富有创造力', '友善', '敏感', '灵活', '艺术性'],
      careers: ['艺术家', '设计师', '兽医', '护士', '治疗师']
    },
    INFP: {
      name: '调停者',
      description: '理想主义，对于自己的价值观和自己觉得重要的人非常忠诚。希望外部生活与内心价值观相符。好奇心重，能看到可能存在的各种可能性。作为实现想法的催化剂，适应力强，灵活，包容。',
      strengths: ['理想主义', '有同理心', '有创造力', '开放', '忠诚'],
      careers: ['作家', '艺术家', '心理咨询师', '教师', '社会工作者']
    },
    INTP: {
      name: '逻辑学家',
      description: '对于自己感兴趣的任何事物都寻求找到合理的解释。喜欢理论和抽象的事情，热衷于观念而非社交。安静、内向、灵活、适应力强。对于解决在他们感兴趣的范畴内的问题有非凡的能力。',
      strengths: ['逻辑性强', '分析性', '有创造力', '独立', '好奇'],
      careers: ['科学家', '程序员', '数学家', '哲学家', '研究员']
    },
    ESTP: {
      name: '企业家',
      description: '灵活、忍耐力强，实际，注重结果。觉得理论和抽象的解释非常无聊。喜欢积极地采取行动解决问题。注重当下，自然不做作，享受和他人在一起的时刻。',
      strengths: ['大胆', '务实', '直接', '善于观察', '有魅力'],
      careers: ['企业家', '销售', '警官', '消防员', '股票经纪人']
    },
    ESFP: {
      name: '表演者',
      description: '外向、友好、接受力强。热爱生活、人类和物质上的享受。喜欢和别人一起将事情做成功。在工作中讲究常识和实用性，并使工作变得有趣。灵活、自然，适应力强，对于新的人和环境都很包容。',
      strengths: ['热情', '有创造力', '友善', '灵活', '表演力强'],
      careers: ['演员', '销售', '活动策划', '教师', '公关']
    },
    ENFP: {
      name: '竞选者',
      description: '热情洋溢、富有想象力。认为人生充满了很多可能性。能很快地将事情和信息联系起来，然后很自信地根据自己的判断解决问题。总是需要得到别人的认可，也总是准备着给与他人赏识和支持。',
      strengths: ['热情', '有创造力', '社交性强', '有同理心', '有沟通能力'],
      careers: ['记者', '广告创意', '咨询师', '政治家', '活动家']
    },
    ENTP: {
      name: '辩论家',
      description: '反应快、睿智，有激励别人的能力，警觉性强，直言不讳。在解决新的、有挑战性的问题时机智而有策略。善于找出概念上的可能性，然后分析它们。善于读出别人的意图。对日常例行事务感到厌倦。',
      strengths: ['机智', '知识渊博', '有创造力', '善于辩论', '有魅力'],
      careers: ['企业家', '律师', '顾问', '政治家', '投资银行家']
    },
    ESTJ: {
      name: '总经理',
      description: '实际、现实主义。果断，一旦下决心就会马上行动。善于将项目和人组织起来将事情完成，并尽可能用最有效率的方法得到结果。注重日常的细节。有一套清晰的逻辑标准，系统性地遵循，并希望他人也同样遵循。',
      strengths: ['专注', '有条理', '可靠', '务实', '直接'],
      careers: ['高管', '军官', '法官', '教师', '会计师']
    },
    ESFJ: {
      name: '执政官',
      description: '热心肠、有责任心、合作。希望周边的环境温馨而和谐，并为此果断地执行。喜欢和他人一起精确并及时地完成任务。事无巨细都会保持忠诚。能体察到他在日常生活中的所需并竭尽全力帮助。',
      strengths: ['有爱心', '可靠', '有组织能力', '友善', '传统'],
      careers: ['教师', '护士', '社会工作者', '公关', '办公室主任']
    },
    ENFJ: {
      name: '主人公',
      description: '热情、为他人着想、反应敏捷、有责任感。非常关注他人的情感、需求和动机。善于发现他人的潜能，并希望能帮助他们实现。在团体中能很好地促进并充当催化剂。对于赞扬和批评都会积极响应。',
      strengths: ['有魅力', '有同理心', '有领导力', '可靠', '有说服力'],
      careers: ['教师', '培训师', '人力资源', '非营利组织', '咨询师']
    },
    ENTJ: {
      name: '指挥官',
      description: '坦诚、果断，是天生的领导者。能很快看到公司/组织程序和政策中的不合理性和低效能，发展并实施有效和全面的系统来解决问题。喜好长期的规划和目标的设定。通常见多识广，博览群书，喜欢拓广自己的知识面并将此分享给他人。',
      strengths: ['有战略眼光', '有领导力', '自信', '有条理', '有魅力'],
      careers: ['CEO', '管理顾问', '律师', '企业家', '政治家']
    }
  }

  return descriptions[type] || {
    name: '未知类型',
    description: '暂无该类型的描述',
    strengths: [],
    careers: []
  }
}
