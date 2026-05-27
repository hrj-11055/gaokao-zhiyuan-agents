// gaokao-miniprogram/src/composables/useHomeProgress.js
//
// Computes the 4-step progress state for the redesigned homepage.
// Pure-function composable: reads localStorage via storage utils, no side effects.

import { computed, ref } from 'vue'
import {
  loadUserProfile,
  loadAssessments,
  loadQuestionnaire,
  isProfileComplete,
  loadHistory,
  loadReport,
  QUESTIONNAIRE_REQUIRED_COUNT,
} from '../utils/storage.js'

// ---------------------------------------------------------------------------
// Step status enum
// ---------------------------------------------------------------------------

export const StepStatus = Object.freeze({
  DONE: 'done',
  ACTIVE: 'active',
  LOCKED: 'locked',
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Count user messages across chat history.
 * loadHistory() returns { conversationId, messages, updatedAt } for a single
 * conversation. We count messages where role === 'user'.
 */
function countUserMessages(history) {
  if (!history || !Array.isArray(history.messages)) return 0
  return history.messages.filter((m) => m.role === 'user').length
}

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useHomeProgress() {
  // ---- reactive source data (refreshed from localStorage) ----

  const profile = ref(loadUserProfile())
  const history = ref(loadHistory())
  const questionnaire = ref(loadQuestionnaire())
  const assessments = ref(loadAssessments())
  const report = ref(loadReport())

  // ---- re-read all storage ----

  function refresh() {
    profile.value = loadUserProfile()
    history.value = loadHistory()
    questionnaire.value = loadQuestionnaire()
    assessments.value = loadAssessments()
    report.value = loadReport()
  }

  // ---- step 1: profile ----

  const step1Done = computed(() => isProfileComplete(profile.value))

  // ---- step 2: chat ----

  const step2Done = computed(() => countUserMessages(history.value) >= 1)

  // ---- step 3: assessments ----

  const questionnaireDone = computed(
    () => questionnaire.value.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT,
  )

  const mbtiDone = computed(() => assessments.value.mbti.completed)

  const hollandDone = computed(() => assessments.value.holland.completed)

  const step3Count = computed(() => {
    let n = 0
    if (questionnaireDone.value) n++
    if (mbtiDone.value) n++
    if (hollandDone.value) n++
    return n
  })

  const step3Done = computed(() => step3Count.value >= 3)

  // ---- step 4: generated report ----

  const reportDone = computed(() => Boolean(report.value?.url))

  // ---- aggregate ----

  const completedSteps = computed(() => {
    let n = 0
    if (step1Done.value) n++
    if (step2Done.value) n++
    if (step3Done.value) n++
    if (reportDone.value) n++
    return n
  })

  /**
   * Which assessment should the user do next?
   * Priority: questionnaire > mbti > holland > null (all done)
   */
  const nextAssessment = computed(() => {
    if (!questionnaireDone.value) return 'questionnaire'
    if (!mbtiDone.value) return 'mbti'
    if (!hollandDone.value) return 'holland'
    return null
  })

  // ---- status per step (1-4) ----

  function statusFor(stepIndex) {
    switch (stepIndex) {
      case 1:
        return step1Done.value ? StepStatus.DONE : StepStatus.ACTIVE
      case 2:
        if (!step1Done.value) return StepStatus.LOCKED
        return step2Done.value ? StepStatus.DONE : StepStatus.ACTIVE
      case 3:
        if (!step2Done.value) return StepStatus.LOCKED
        return step3Done.value ? StepStatus.DONE : StepStatus.ACTIVE
      case 4:
        if (!step3Done.value) return StepStatus.LOCKED
        if (reportDone.value) return StepStatus.DONE
        return StepStatus.ACTIVE
      default:
        return StepStatus.LOCKED
    }
  }

  return {
    // reactive data
    profile,
    history,
    questionnaire,
    assessments,
    report,

    // step-level booleans
    step1Done,
    step2Done,
    step3Done,
    reportDone,

    // assessment-level booleans
    questionnaireDone,
    mbtiDone,
    hollandDone,

    // aggregates
    step3Count,
    completedSteps,
    nextAssessment,

    // helpers
    refresh,
    statusFor,
  }
}
