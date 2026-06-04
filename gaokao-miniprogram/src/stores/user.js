import { defineStore } from 'pinia'
import {
  buildProfileInputs,
  isProfileComplete,
  normalizeUserProfile,
} from '../utils/storage.js'

const USER_ID_KEY = 'user_id'
const USER_PROFILE_KEY = 'user_profile'

export const useUserStore = defineStore('user', {
  state: () => ({
    userId: '',
    profile: normalizeUserProfile({ updatedAt: 0 })
  }),

  getters: {
    isProfileComplete(state) {
      return isProfileComplete(state.profile)
    },
    
    profileInputs(state) {
      return buildProfileInputs(state.profile)
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
