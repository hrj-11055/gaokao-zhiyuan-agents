import { defineStore } from 'pinia'

const ASSESSMENTS_KEY = 'assessments'
const QUESTIONNAIRE_KEY = 'questionnaire'
const QUESTIONNAIRE_REQUIRED_COUNT = 21
const QUESTIONNAIRE_ACTIVE_IDS = new Set([
  'q1', 'q2', 'q3', 'q4', 'q5',
  'q6', 'q7', 'q8',
  'q10', 'q11', 'q12', 'q13',
  'q14', 'q15', 'q16',
  'q17', 'q18', 'q19', 'q20', 'q21', 'q22'
])

function isFilledAnswer(value) {
  return value !== '' && value !== undefined && value !== null && !(Array.isArray(value) && value.length === 0)
}

function sanitizeQuestionnaireAnswers(answers = {}) {
  if (typeof answers !== 'object' || answers === null) {
    return {}
  }
  return Object.fromEntries(
    Object.entries(answers).filter(([id, value]) => QUESTIONNAIRE_ACTIVE_IDS.has(id) && isFilledAnswer(value))
  )
}

function normalizeQuestionnaire(questionnaire = {}) {
  const answers = sanitizeQuestionnaireAnswers(questionnaire.answers)
  return {
    answers,
    completedCount: Math.min(Object.keys(answers).length, QUESTIONNAIRE_REQUIRED_COUNT),
    updatedAt: questionnaire.updatedAt || 0
  }
}

function normalizeMbti(mbti = {}) {
  return {
    completed: Boolean(mbti.completed),
    type: typeof mbti.type === 'string' ? mbti.type : '',
    scores: {
      E: Number(mbti.scores?.E) || 0,
      I: Number(mbti.scores?.I) || 0,
      S: Number(mbti.scores?.S) || 0,
      N: Number(mbti.scores?.N) || 0,
      T: Number(mbti.scores?.T) || 0,
      F: Number(mbti.scores?.F) || 0,
      J: Number(mbti.scores?.J) || 0,
      P: Number(mbti.scores?.P) || 0
    },
    answers: Array.isArray(mbti.answers) ? mbti.answers : [],
    questionIndex: typeof mbti.questionIndex === 'number' ? mbti.questionIndex : 0,
    completedAt: mbti.completedAt || 0
  }
}

function normalizeHolland(holland = {}) {
  return {
    completed: Boolean(holland.completed),
    code: typeof holland.code === 'string' ? holland.code : '',
    scores: {
      R: Number(holland.scores?.R) || 0,
      I: Number(holland.scores?.I) || 0,
      A: Number(holland.scores?.A) || 0,
      S: Number(holland.scores?.S) || 0,
      E: Number(holland.scores?.E) || 0,
      C: Number(holland.scores?.C) || 0
    },
    answers: Array.isArray(holland.answers) ? holland.answers : [],
    questionIndex: typeof holland.questionIndex === 'number' ? holland.questionIndex : 0,
    completedAt: holland.completedAt || 0
  }
}

export const useAssessmentStore = defineStore('assessment', {
  state: () => ({
    mbti: normalizeMbti(),
    holland: normalizeHolland(),
    questionnaire: {
      answers: {},
      completedCount: 0,
      updatedAt: 0
    },
    updatedAt: 0
  }),

  getters: {
    completedCount(state) {
      let count = 0
      if (state.mbti.completed) count++
      if (state.holland.completed) count++
      if (state.questionnaire.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT) count++
      return count
    },
    isAllCompleted(state) {
      return this.completedCount >= 3
    }
  },

  actions: {
    loadAll() {
      // 兼容旧版的问卷数据
      const qData = uni.getStorageSync(QUESTIONNAIRE_KEY)
      if (qData) {
        try {
          this.questionnaire = normalizeQuestionnaire(JSON.parse(qData))
        } catch {}
      }

      const aData = uni.getStorageSync(ASSESSMENTS_KEY)
      if (aData) {
        try {
          const parsed = JSON.parse(aData)
          this.mbti = normalizeMbti(parsed.mbti)
          this.holland = normalizeHolland(parsed.holland)
          if (parsed.questionnaire) {
             this.questionnaire = normalizeQuestionnaire({ ...this.questionnaire, ...parsed.questionnaire })
          }
        } catch {}
      }
    },

    saveAssessments() {
      this.updatedAt = Date.now()
      uni.setStorageSync(ASSESSMENTS_KEY, JSON.stringify({
        mbti: this.mbti,
        holland: this.holland,
        questionnaire: this.questionnaire,
        updatedAt: this.updatedAt
      }))
    },

    saveQuestionnaire(answers) {
      const normalizedAnswers = sanitizeQuestionnaireAnswers(answers)
      this.questionnaire = {
        answers: normalizedAnswers,
        completedCount: Math.min(Object.keys(normalizedAnswers).length, QUESTIONNAIRE_REQUIRED_COUNT),
        updatedAt: Date.now()
      }
      uni.setStorageSync(QUESTIONNAIRE_KEY, JSON.stringify(this.questionnaire))
      this.saveAssessments()
    },

    saveMbtiResult(result) {
      this.mbti = normalizeMbti({
        ...result,
        completed: true,
        completedAt: Date.now()
      })
      this.saveAssessments()
    },

    saveHollandResult(result) {
      this.holland = normalizeHolland({
        ...result,
        completed: true,
        completedAt: Date.now()
      })
      this.saveAssessments()
    },

    saveMbtiProgress(questionIndex, answers = []) {
      this.mbti = normalizeMbti({
        ...this.mbti,
        completed: false,
        questionIndex,
        answers
      })
      this.saveAssessments()
    },

    saveHollandProgress(questionIndex, answers = []) {
      this.holland = normalizeHolland({
        ...this.holland,
        completed: false,
        questionIndex,
        answers
      })
      this.saveAssessments()
    }
  }
})
