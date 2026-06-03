import { MBTI_RESULT_REPORTS } from '../data/mbti-questions.js'
import {
  HOLLAND_DIMENSION_TRAITS,
  HOLLAND_RESULT_REPORTS,
  HOLLAND_TYPE_LABELS,
} from '../data/holland-questions.js'
import { loadAssessments } from './storage.js'

const HOLLAND_ORDER = ['R', 'I', 'A', 'S', 'E', 'C']

function pickReportFields(report = {}) {
  return {
    name: report.name || '',
    tags: Array.isArray(report.tags) ? report.tags : [],
    traits: Array.isArray(report.traits) ? report.traits : [],
    careers: Array.isArray(report.careers) ? report.careers : [],
    majors: Array.isArray(report.majors) ? report.majors : [],
  }
}

function buildHollandIndicators(scores = {}) {
  return HOLLAND_ORDER
    .map((type) => ({
      type,
      label: HOLLAND_TYPE_LABELS[type] || type,
      score: Number(scores[type]) || 0,
    }))
    .sort((a, b) => b.score - a.score)
}

function buildHollandDimensions(code = '') {
  return String(code)
    .split('')
    .map((type) => HOLLAND_DIMENSION_TRAITS[type])
    .filter(Boolean)
}

export function buildReportAssessmentPayload(source = loadAssessments()) {
  const mbti = source?.mbti || {}
  const holland = source?.holland || {}
  const mbtiReport = mbti.type ? MBTI_RESULT_REPORTS[mbti.type] : null
  const hollandReport = holland.code ? HOLLAND_RESULT_REPORTS[holland.code] : null

  return {
    mbti: {
      completed: Boolean(mbti.completed),
      version: mbti.version || '',
      type: mbti.type || '',
      report: pickReportFields(mbtiReport),
    },
    holland: {
      completed: Boolean(holland.completed),
      version: holland.version || '',
      code: holland.code || '',
      scores: holland.scores || {},
      indicators: buildHollandIndicators(holland.scores),
      dimensions: buildHollandDimensions(holland.code),
      report: pickReportFields(hollandReport),
    },
  }
}
