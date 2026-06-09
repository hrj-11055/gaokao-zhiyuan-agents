<template>
  <view class="chat-page">
    <view class="chat-glow chat-glow-blue" />
    <view class="chat-glow chat-glow-purple" />

    <scroll-view
      class="chat-scroll"
      scroll-y
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
    >
      <view class="scroll-content">
        <ChatBubble type="ai" :content="welcomeMsg" :show-actions="false" />

        <view v-if="!isProfileReady" class="profile-gate">
          <text class="profile-gate-title">先补充基础资料</text>
          <text class="profile-gate-desc">基础资料可以先不填正式分数；有预估分就按预估定位，没有分数也能先做专业规划。</text>
          <view class="profile-gate-btn" @click="goCompleteProfile">
            <text class="profile-gate-btn-text">去填写资料</text>
          </view>
        </view>

        <view v-if="showWelcomeSuggestions" class="suggestion-panel">
          <text class="suggestion-title">从关键决策开始</text>
          <view class="suggestion-list">
            <view
              v-for="chip in quickQuestions"
              :key="chip"
              class="suggestion-chip"
              @click="onQuickSelect(chip)"
            >
              <text class="suggestion-chip-text">{{ chip }}</text>
            </view>
          </view>
        </view>

        <template v-for="(msg, index) in messages" :key="index">
          <view :id="`message-${index}`" class="message-anchor">
            <ChatBubble
              :type="msg.role"
              :content="msg.content"
              :messageId="msg.messageId"
              :canRegenerate="canRegenerateMessage(msg, index)"
              :isStreaming="isStreaming && index === messages.length - 1 && msg.role === 'ai'"
              @regenerate="handleRetry"
            />

            <view
              v-if="msg.role === 'ai' && msg.truncated && index === messages.length - 1"
              class="retry-bar"
            >
              <text class="retry-hint">这次回复不完整</text>
              <view class="retry-btn" @click="handleRetry">
                <text class="retry-btn-text">重新生成</text>
              </view>
            </view>

            <PersonalityAssessmentGuide
              v-if="index === personalityGuideMessageIndex"
              :started="hasStartedPersonalityTest"
              @start="goPersonalityTest"
              @dismiss="dismissPersonalityGuideCard"
            />
          </view>
        </template>

        <view class="scroll-bottom-space" />
      </view>
    </scroll-view>

    <view class="input-bar">
      <input
        class="input-field"
        v-model="inputText"
        :placeholder="inputPlaceholder"
        placeholder-class="input-placeholder"
        :disabled="isStreaming || !isProfileReady"
        confirm-type="send"
        @confirm="handleSend"
      />
      <view
        class="send-btn"
        :class="{ active: inputText.trim() && !isStreaming && isProfileReady }"
        @click="handleSend"
      >
        <text class="send-icon">↑</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import ChatBubble from '../../components/ChatBubble.vue'
import PersonalityAssessmentGuide from '../../components/PersonalityAssessmentGuide.vue'
import { useChat } from './useChat.js'
import {
  dismissPersonalityGuide,
  getProfileReportMode,
  isPersonalityGuideDismissed,
  isProfileComplete,
  loadAssessments,
  loadUserProfile
} from '../../utils/storage.js'
import { buildCandidateQuestions } from './profileFollowup.js'
import { findPersonalityGuideMessageIndex } from './personalityAssessmentGuide.js'

const scrollTop = ref(0)
const profile = ref(loadUserProfile())
const assessments = ref(loadAssessments())
const personalityGuideDismissed = ref(isPersonalityGuideDismissed())
const { chatStore, inputText, isStreaming, onSend, onRetry } = useChat()
const messages = computed(() => chatStore.messages)
const isProfileReady = computed(() => isProfileComplete(profile.value))
const hasStartedPersonalityTest = computed(() => Boolean(
  assessments.value.mbti.questionIndex > 0 ||
  (Array.isArray(assessments.value.mbti.answers) && assessments.value.mbti.answers.length > 0)
))
const personalityGuideMessageIndex = computed(() => {
  if (
    isStreaming.value ||
    assessments.value.mbti.completed ||
    personalityGuideDismissed.value
  ) {
    return -1
  }
  return findPersonalityGuideMessageIndex(messages.value)
})
const welcomeMsg = computed(() => (
  getProfileReportMode(profile.value) === 'planning'
    ? '你不用先想出一个完美问题。当前先做提前升学规划：一起看专业方向、学科能力、探索任务和家庭约束，不需要先有正式分数和位次。'
    : '你不用先想出一个完美问题。我们先把分数、位次、专业方向和现实约束拆开看；我会尽量用分数线说话，也会直接提醒不值得赌的地方。'
))
const quickQuestions = computed(() => buildCandidateQuestions(profile.value))
const showWelcomeSuggestions = computed(() => messages.value.length === 0 && isProfileReady.value)
const inputPlaceholder = computed(() => (
  isProfileReady.value ? '写下你的纠结，或直接选上面的处境...' : '先补充省份和科类，可暂不填正式分数'
))
const hasUserMessage = computed(() => messages.value.some((msg) => msg.role === 'user'))

onShow(() => {
  profile.value = loadUserProfile()
  assessments.value = loadAssessments()
  personalityGuideDismissed.value = isPersonalityGuideDismissed()
  chatStore.loadHistory()
})

function scrollToBottom() {
  nextTick(() => {
    scrollTop.value = scrollTop.value === 0 ? 1 : 0
    setTimeout(() => {
      scrollTop.value = 999999
    }, 50)
  })
}

function focusUserMessage(index) {
  nextTick(() => {
    setTimeout(() => {
      const query = uni.createSelectorQuery()
      query.select('.chat-scroll').boundingClientRect()
      query.select('.chat-scroll').scrollOffset()
      query.select(`#message-${index}`).boundingClientRect()
      query.exec((res) => {
        const [containerRect, scrollOffset, messageRect] = res || []
        if (!containerRect || !scrollOffset || !messageRect) return

        const desiredTop = containerRect.height * 0.52
        const nextScrollTop = scrollOffset.scrollTop + messageRect.top - containerRect.top - desiredTop
        scrollTop.value = Math.max(0, nextScrollTop)
      })
    }, 80)
  })
}

function onQuickSelect(question) {
  if (!isProfileReady.value) {
    goCompleteProfile()
    return
  }
  inputText.value = question
  handleSend()
}

function handleSend() {
  if (!isProfileReady.value) {
    uni.showToast({ title: '请先补充基础资料', icon: 'none' })
    return
  }
  onSend({
    onScrollToBottom: scrollToBottom,
    onUserMessageAppended: focusUserMessage,
    onAiResponseStarted: () => {},
    onProfileUpdated: (updatedProfile) => {
      profile.value = updatedProfile
    },
  })
}

function goCompleteProfile() {
  uni.switchTab({ url: '/pages/index/index' })
  setTimeout(() => uni.$emit('open-profile-sheet'), 200)
}

function goPersonalityTest() {
  uni.navigateTo({ url: '/pages/mbti/mbti' })
}

function dismissPersonalityGuideCard() {
  dismissPersonalityGuide()
  personalityGuideDismissed.value = true
}

function handleRetry() {
  onRetry({
    onScrollToBottom: scrollToBottom,
    onUserMessageAppended: focusUserMessage,
    onAiResponseStarted: () => {},
    onProfileUpdated: (updatedProfile) => {
      profile.value = updatedProfile
    },
  })
}

function canRegenerateMessage(msg, index) {
  return Boolean(
    msg.role === 'ai' &&
    msg.canRegenerate &&
    index === messages.value.length - 1 &&
    hasUserMessage.value &&
    !isStreaming.value
  )
}

</script>

<style lang="scss">
page {
  height: 100%;
  overflow: hidden;
}
</style>

<style lang="scss" scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #e4f4ff 0%, #f3ecff 100%);
}

.chat-glow {
  position: absolute;
  width: 620rpx;
  height: 620rpx;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(2rpx);
}

.chat-glow-blue {
  top: -140rpx;
  left: -170rpx;
  background: radial-gradient(circle, rgba(45, 212, 191, 0.2) 0%, rgba(255, 255, 255, 0) 68%);
}

.chat-glow-purple {
  right: -170rpx;
  bottom: 180rpx;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.17) 0%, rgba(255, 255, 255, 0) 68%);
}

.chat-scroll {
  flex: 1;
  height: 0;
  min-height: 0;
  box-sizing: border-box;
  z-index: 2;
}

.scroll-content {
  padding: 28rpx 0 0;
}

.message-anchor {
  position: relative;
}

.profile-gate {
  margin: -8rpx 32rpx 30rpx 128rpx;
  padding: 24rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.78);
  border: 2rpx solid rgba(255, 255, 255, 0.82);
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.05);
  box-sizing: border-box;
}

.profile-gate-title {
  display: block;
  color: #1f2937;
  font-size: 28rpx;
  font-weight: 800;
  margin-bottom: 8rpx;
}

.profile-gate-desc {
  display: block;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.5;
  margin-bottom: 18rpx;
}

.profile-gate-btn {
  height: 68rpx;
  border-radius: 14rpx;
  background: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-gate-btn-text {
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 800;
}

.suggestion-panel {
  margin: -12rpx 32rpx 30rpx 128rpx;
  padding: 18rpx 20rpx 20rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.72);
  border: 2rpx solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.05);
  box-sizing: border-box;
}

.suggestion-title {
  display: block;
  margin-bottom: 14rpx;
  color: #8a94a6;
  font-size: 22rpx;
  line-height: 1.25;
  font-weight: 700;
}

.suggestion-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.suggestion-chip {
  max-width: 100%;
  border-radius: 999rpx;
  padding: 10rpx 18rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 2rpx solid rgba(37, 99, 235, 0.12);
  box-sizing: border-box;
}

.suggestion-chip:active {
  background: rgba(255, 247, 237, 0.95);
  border-color: rgba(249, 115, 22, 0.28);
}

.suggestion-chip-text {
  color: #4b5563;
  font-size: 23rpx;
  line-height: 1.35;
}

.retry-bar {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 0 32rpx 26rpx 128rpx;
  box-sizing: border-box;
}

.retry-hint {
  color: #8a94a6;
  font-size: 23rpx;
}

.retry-btn {
  height: 50rpx;
  padding: 0 24rpx;
  border-radius: 10rpx;
  border: 2rpx solid rgba(249, 115, 22, 0.22);
  background: rgba(255, 247, 237, 0.78);
  display: flex;
  align-items: center;
}

.retry-btn-text {
  color: #f97316;
  font-size: 23rpx;
  font-weight: 700;
}

.scroll-bottom-space {
  height: 40rpx;
}

.input-bar {
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: #ffffff;
  border-top: 2rpx solid rgba(15, 23, 42, 0.06);
  box-sizing: border-box;
}

.input-field {
  flex: 1;
  min-width: 0;
  height: 78rpx;
  padding: 0 32rpx;
  border-radius: 999rpx;
  background: #f1f5f9;
  color: #111827;
  font-size: 28rpx;
  box-sizing: border-box;
  border: 2rpx solid #e2e8f0;
}

.input-placeholder {
  color: #8a94a6;
}

.send-btn {
  width: 78rpx;
  height: 78rpx;
  border-radius: 50%;
  background: #f1f5f9;
  border: 2rpx solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-sizing: border-box;
}

.send-btn.active {
  background: #f97316;
  border-color: #f97316;
  box-shadow: 0 8rpx 18rpx rgba(249, 115, 22, 0.22);
}

.send-icon {
  color: #9ca3af;
  font-size: 40rpx;
  line-height: 1;
  font-weight: 800;
}

.send-btn.active .send-icon {
  color: #ffffff;
}
</style>
