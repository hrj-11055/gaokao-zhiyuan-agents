// gaokao-miniprogram/src/composables/useReportPregen.js
import { triggerPregenerate } from '../api/pregenerate.js'
import { useHomeProgress } from './useHomeProgress.js'
import pinia from '../stores'
import { useMembershipStore } from '../stores/membership.js'
import { buildReportAssessmentPayload } from '../utils/report-assessments.js'
import {
  loadUserProfile,
  loadHistory
} from '../utils/storage.js'

export function useReportPregen() {
  const { step3Done, refresh } = useHomeProgress()
  const membershipStore = useMembershipStore(pinia)

  async function tryTriggerPregenerate({ force = false } = {}) {
    refresh()
    if (!step3Done.value) {
      console.log('[Pregen] 2 assessments not yet complete.')
      return { status: 'not_ready' }
    }

    const profile = loadUserProfile()
    const assessments = buildReportAssessmentPayload()
    const chatHistory = loadHistory()

    // Construct fingerprint to prevent duplicate pre-generation requests
    const fingerprintObj = {
      profile: {
        province: profile?.province || '',
        category: profile?.category || '',
        score: profile?.score || '',
        rank: profile?.rank || '',
      },
      assessments: {
        mbti: assessments?.mbti || {},
        holland: assessments?.holland || {},
      },
    }
    const fingerprint = JSON.stringify(fingerprintObj)
    const lastFingerprint = uni.getStorageSync('pregen_fingerprint')

    if (!force && lastFingerprint === fingerprint) {
      console.log('[Pregen] Assessments unchanged. Skipping pre-generation.')
      return { status: 'skipped' }
    }

    try {
      await membershipStore.ensureLogin()
      const res = await triggerPregenerate({
        profile,
        assessments,
        conversationId: chatHistory.conversationId || '',
        userId: membershipStore.userId,
        sessionToken: membershipStore.sessionToken,
      })
      console.log('[Pregen] Pre-generation triggered successfully:', res)
      uni.setStorageSync('pregen_fingerprint', fingerprint)
      return res
    } catch (err) {
      console.error('[Pregen] Pre-generation failed to trigger:', err)
      return { status: 'failed', error: err.message || err }
    }
  }

  return {
    tryTriggerPregenerate,
  }
}
