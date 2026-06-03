// gaokao-miniprogram/src/composables/useHomeProgress.js
import { computed, ref } from 'vue'
import {
  loadUserProfile,
  loadAssessments,
  loadReport,
  isProfileComplete,
  loadHistory,
} from '../utils/storage.js'

// 步骤状态枚举
export const StepStatus = {
  DONE: 'done',
  ACTIVE: 'active',
  LOCKED: 'locked',
}

// 步骤 2「已聊过」的阈值：用户至少有过 1 轮 user 提问
const CHAT_DONE_MIN_USER_MESSAGES = 1
const ASSESSMENT_REQUIRED_COUNT = 2

export function useHomeProgress() {
  const profile = ref(loadUserProfile())
  const assessments = ref(loadAssessments())
  const report = ref(loadReport())
  const chatRounds = ref(countUserMessages())

  function refresh() {
    profile.value = loadUserProfile()
    assessments.value = loadAssessments()
    report.value = loadReport()
    chatRounds.value = countUserMessages()
  }

  function countUserMessages() {
    try {
      const history = loadHistory() || {}
      const messages = Array.isArray(history.messages) ? history.messages : []
      return messages.filter((m) => m && m.role === 'user').length
    } catch {
      return 0
    }
  }

  const step1Done = computed(() => isProfileComplete(profile.value))
  const step2Done = computed(() => chatRounds.value >= CHAT_DONE_MIN_USER_MESSAGES)
  const mbtiDone = computed(() => assessments.value.mbti.completed)
  const hollandDone = computed(() => assessments.value.holland.completed)
  const step3Count = computed(() => {
    let n = 0
    if (mbtiDone.value) n++
    if (hollandDone.value) n++
    return n
  })
  const step3Done = computed(() => step3Count.value === ASSESSMENT_REQUIRED_COUNT)
  const reportDone = computed(() => Boolean(report.value?.url))

  const completedSteps = computed(() => {
    let n = 0
    if (step1Done.value) n++
    if (step2Done.value) n++
    if (step3Done.value) n++
    if (reportDone.value) n++
    return n
  })

  function statusFor(stepIndex) {
    // 锁定逻辑：只要上一步未完成，本步即 locked
    if (stepIndex === 1) {
      return step1Done.value ? StepStatus.DONE : StepStatus.ACTIVE
    }
    if (stepIndex === 2) {
      if (!step1Done.value) return StepStatus.LOCKED
      return step2Done.value ? StepStatus.DONE : StepStatus.ACTIVE
    }
    if (stepIndex === 3) {
      if (!step2Done.value) return StepStatus.LOCKED
      return step3Done.value ? StepStatus.DONE : StepStatus.ACTIVE
    }
    if (stepIndex === 4) {
      if (!step3Done.value) return StepStatus.LOCKED
      if (reportDone.value) return StepStatus.DONE
      return StepStatus.ACTIVE
    }
    return StepStatus.LOCKED
  }

  // 提示下一项未完成的测评：mbti → holland
  const nextAssessment = computed(() => {
    if (!mbtiDone.value) return 'mbti'
    if (!hollandDone.value) return 'holland'
    return null
  })

  return {
    profile,
    assessments,
    report,
    chatRounds,
    refresh,
    statusFor,
    step1Done,
    step2Done,
    step3Done,
    mbtiDone,
    hollandDone,
    step3Count,
    reportDone,
    completedSteps,
    nextAssessment,
  }
}
