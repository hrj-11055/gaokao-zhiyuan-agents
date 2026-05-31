// gaokao-miniprogram/src/composables/useHomeProgress.js
import { computed, ref } from 'vue'
import {
  loadUserProfile,
  loadAssessments,
  loadQuestionnaire,
  isProfileComplete,
  loadHistory,
  QUESTIONNAIRE_REQUIRED_COUNT,
} from '../utils/storage.js'

// 步骤状态枚举
export const StepStatus = {
  DONE: 'done',
  ACTIVE: 'active',
  LOCKED: 'locked',
}

// 步骤 2「已聊过」的阈值：用户至少有过 1 轮 user 提问
const CHAT_DONE_MIN_USER_MESSAGES = 1

export function useHomeProgress() {
  const profile = ref(loadUserProfile())
  const assessments = ref(loadAssessments())
  const questionnaire = ref(loadQuestionnaire())
  const chatRounds = ref(countUserMessages())

  function refresh() {
    profile.value = loadUserProfile()
    assessments.value = loadAssessments()
    questionnaire.value = loadQuestionnaire()
    chatRounds.value = countUserMessages()
  }

  function countUserMessages() {
    try {
      const history = loadHistory() || {}
      // history 结构：{ [conversationId]: messages[] }
      let total = 0
      Object.values(history).forEach((msgs) => {
        if (!Array.isArray(msgs)) return
        total += msgs.filter((m) => m && m.role === 'user').length
      })
      return total
    } catch {
      return 0
    }
  }

  const step1Done = computed(() => isProfileComplete(profile.value))
  const step2Done = computed(() => chatRounds.value >= CHAT_DONE_MIN_USER_MESSAGES)
  const questionnaireDone = computed(
    () => questionnaire.value.completedCount >= QUESTIONNAIRE_REQUIRED_COUNT
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
  const step3Done = computed(() => step3Count.value === 3)

  // 步骤 4 的「done」由 membership store 决定（此 composable 只算前 3 步）
  const completedSteps = computed(() => {
    let n = 0
    if (step1Done.value) n++
    if (step2Done.value) n++
    if (step3Done.value) n++
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
      return StepStatus.ACTIVE // 步骤 4 done 与否在调用方判断（结合 membership）
    }
    return StepStatus.LOCKED
  }

  // 提示下一项未完成的测评：questionnaire → mbti → holland
  const nextAssessment = computed(() => {
    if (!questionnaireDone.value) return 'questionnaire'
    if (!mbtiDone.value) return 'mbti'
    if (!hollandDone.value) return 'holland'
    return null
  })

  return {
    profile,
    assessments,
    questionnaire,
    chatRounds,
    refresh,
    statusFor,
    step1Done,
    step2Done,
    step3Done,
    questionnaireDone,
    mbtiDone,
    hollandDone,
    step3Count,
    completedSteps,
    nextAssessment,
  }
}
