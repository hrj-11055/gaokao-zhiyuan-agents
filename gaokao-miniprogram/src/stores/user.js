import { defineStore } from 'pinia'
import { normalizeUserProfile } from '../utils/storage.js'

const USER_ID_KEY = 'user_id'
const USER_PROFILE_KEY = 'user_profile'

export const useUserStore = defineStore('user', {
  state: () => ({
    userId: '',
    profile: normalizeUserProfile({ updatedAt: 0 })
  }),

  getters: {
    isProfileComplete(state) {
      const p = state.profile
      return Boolean(
        p.province &&
        (p.category === '物理类' || p.category === '历史类') &&
        typeof p.score === 'number' &&
        p.score >= 0 &&
        p.score <= 750
      )
    },
    
    profileInputs(state) {
      const p = state.profile
      const inputs = {}
      if (p.province) inputs.province = p.province
      if (p.category) inputs.category = p.category
      if (typeof p.score === 'number') inputs.score = String(p.score)
      if (typeof p.rank === 'number' && p.rank > 0) inputs.rank = String(p.rank)
      if (p.family_resources) inputs.family_resources = p.family_resources
      if (p.interest_subjects) inputs.interest_subjects = p.interest_subjects
      if (p.region_preference) inputs.region_preference = p.region_preference
      if (p.career_goal) inputs.career_goal = p.career_goal
      return inputs
    }
  },

  actions: {
    initUserId() {
      let id = uni.getStorageSync(USER_ID_KEY)
      if (!id) {
        id = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 11)
        uni.setStorageSync(USER_ID_KEY, id)
      }
      this.userId = id
    },

    loadProfile() {
      const data = uni.getStorageSync(USER_PROFILE_KEY)
      if (data) {
        try {
          this.profile = normalizeUserProfile(JSON.parse(data))
        } catch {
          this.profile = normalizeUserProfile({ updatedAt: 0 })
        }
      }
    },

    saveProfile(newProfile) {
      this.profile = normalizeUserProfile({ ...newProfile, updatedAt: Date.now() })
      uni.setStorageSync(USER_PROFILE_KEY, JSON.stringify(this.profile))
    }
  }
})
