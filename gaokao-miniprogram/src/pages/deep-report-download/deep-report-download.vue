<template>
  <view class="download-page">
    <view class="page-header">
      <text class="eyebrow">PDF 报告库</text>
      <text class="title">深度报告下载</text>
      <text class="subtitle">选择学校或专业，下载数据库中 5000 字以上完整报告。</text>
    </view>

    <view class="mode-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="mode-tab"
        :class="{ active: mode === tab.value }"
        @click="switchMode(tab.value)"
      >
        {{ tab.label }}
      </button>
    </view>

    <view class="search-row">
      <input
        v-model.trim="keyword"
        class="search-input"
        confirm-type="search"
        :placeholder="mode === 'university' ? '搜索学校，如 中山大学' : '搜索专业，如 计算机'"
        @confirm="searchReports"
      />
      <button class="search-btn" @click="searchReports">搜索</button>
    </view>

    <view class="helper-row">
      <text class="helper-label">{{ mode === 'university' ? '常搜学校' : '常搜专业' }}</text>
      <button
        v-for="item in exampleKeywords"
        :key="item"
        class="example-chip"
        @click="searchExample(item)"
      >
        {{ item }}
      </button>
    </view>

    <view class="access-card" :class="{ active: membershipStore.isActive }">
      <text class="access-title">{{ membershipStore.isActive ? '会员权益已开通' : '下载 PDF 需要会员权益' }}</text>
      <text class="access-desc">
        {{ membershipStore.isActive ? '可直接下载 5000 字以上完整报告。' : '可先搜索查看报告是否入库，下载完整 PDF 时再开通。' }}
      </text>
      <button v-if="!membershipStore.isActive" class="access-btn" @click="goMembership">去开通</button>
    </view>

    <view v-if="loading" class="state-block">
      <text>正在查询报告库...</text>
    </view>

    <view v-else-if="errorMsg" class="state-block error">
      <text>{{ errorMsg }}</text>
    </view>

    <view v-else class="result-list">
      <view v-for="item in results" :key="itemKey(item)" class="result-item">
        <view class="result-main">
          <text class="item-title">{{ itemTitle(item) }}</text>
          <text class="item-meta">{{ itemMeta(item) }}</text>
          <text class="item-summary">{{ item.summary || '该报告已入库，可下载完整 PDF 查看。' }}</text>
        </view>
        <button class="download-btn" @click="downloadDeepPdf(item)">下载 PDF</button>
      </view>

      <view v-if="results.length === 0" class="empty-panel">
        <text class="empty-title">{{ emptyTitle }}</text>
        <text class="empty-desc">{{ emptyDesc }}</text>
        <view class="empty-actions">
          <button class="empty-action" @click="searchExample(exampleKeywords[0])">{{ exampleKeywords[0] }}</button>
          <button class="empty-action secondary" @click="switchMode(otherMode)">{{ otherModeLabel }}</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { API_BASE } from '../../config.js'
import { requestBackendData } from '../../api/backend.js'
import { useMembershipStore } from '../../stores/membership.js'

const tabs = [
  { label: '大学报告', value: 'university' },
  { label: '专业报告', value: 'major' },
]

const mode = ref('university')
const keyword = ref('')
const results = ref([])
const loading = ref(false)
const errorMsg = ref('')
const hasSearched = ref(false)

const membershipStore = useMembershipStore()

const collection = computed(() => mode.value === 'major' ? 'majors' : 'universities')
const otherMode = computed(() => mode.value === 'major' ? 'university' : 'major')
const otherModeLabel = computed(() => mode.value === 'major' ? '搜大学报告' : '搜专业报告')
const exampleKeywords = computed(() => (
  mode.value === 'major'
    ? ['计算机', '临床医学', '法学']
    : ['中山大学', '华南理工大学', '深圳大学']
))

const emptyTitle = computed(() => {
  if (!hasSearched.value) return '先搜索学校或专业'
  if (!keyword.value) return '输入关键词后查看报告'
  return '暂未找到可下载报告'
})

const emptyDesc = computed(() => {
  if (!hasSearched.value || !keyword.value) {
    return mode.value === 'major'
      ? '可输入专业名称或专业代码，系统会匹配 5000 字以上完整报告。'
      : '可输入学校全称或关键词，系统会匹配 5000 字以上完整报告。'
  }
  return '换一个更完整的名称试试，或切换到另一类报告继续查询。'
})

onMounted(async () => {
  try {
    await membershipStore.loadStatus()
  } catch {
    // 列表查询不强制登录；下载时再提示登录/开通。
  }
  await searchReports()
})

function switchMode(nextMode) {
  if (mode.value === nextMode) return
  mode.value = nextMode
  keyword.value = ''
  results.value = []
  errorMsg.value = ''
  hasSearched.value = false
  searchReports()
}

function searchExample(nextKeyword) {
  keyword.value = nextKeyword
  searchReports()
}

function itemKey(item) {
  return item.code || item.name
}

function itemTitle(item) {
  if (mode.value === 'major') {
    return `${item.name || '专业'}${item.code ? `（${item.code}）` : ''}`
  }
  return item.name || '学校'
}

function itemMeta(item) {
  const parts = []
  if (item.province) parts.push(item.province)
  if (item.univ_type) parts.push(item.univ_type)
  if (item.category) parts.push(item.category)
  if (item.word_count) parts.push(`${item.word_count} 字`)
  parts.push('5000 字以上完整报告')
  return parts.join(' · ')
}

function getHeaderValue(headers, name) {
  if (!headers) return ''
  const lowerName = name.toLowerCase()
  const key = Object.keys(headers).find(item => item.toLowerCase() === lowerName)
  return key ? String(headers[key]) : ''
}

async function searchReports() {
  const query = keyword.value.trim()
  if (query.length === 1) {
    hasSearched.value = true
    results.value = []
    errorMsg.value = '请至少输入 2 个字，学校可输入全称，专业可输入专业名称关键词。'
    return
  }

  loading.value = true
  errorMsg.value = ''
  hasSearched.value = true
  try {
    const params = [`page_size=20`]
    if (query) {
      params.push(`search=${encodeURIComponent(query)}`)
    }
    const data = await requestBackendData({
      path: `/api/reports/${collection.value}?${params.join('&')}`,
      method: 'GET',
      timeout: 15000,
    })
    results.value = data.data || []
  } catch (err) {
    results.value = []
    errorMsg.value = err.message || '报告库暂时不可用'
  } finally {
    loading.value = false
  }
}

function deepPdfUrl(item) {
  const type = mode.value === 'major' ? 'major' : 'university'
  const id = mode.value === 'major' ? item.code : item.name
  return `${API_BASE}/api/reports/deep/pdf?type=${encodeURIComponent(type)}&id=${encodeURIComponent(id || '')}`
}

async function ensureMembership() {
  await membershipStore.loadStatus()
  if (!membershipStore.isActive) {
    throw new Error('完整深度报告属于付费权益，请先开通会员')
  }
  if (!membershipStore.sessionToken) {
    throw new Error('请先完成微信登录后再下载')
  }
}

async function downloadDeepPdf(item) {
  try {
    await ensureMembership()
  } catch (err) {
    uni.showModal({
      title: '需要会员权益',
      content: err.message || '请先开通会员后下载完整 PDF。',
      confirmText: '去开通',
      cancelText: '先看看',
      success: (res) => {
        if (res.confirm) goMembership()
      },
    })
    return
  }

  uni.showLoading({ title: '生成 PDF...' })
  uni.downloadFile({
    url: deepPdfUrl(item),
    header: {
      Authorization: `Bearer ${membershipStore.sessionToken}`,
    },
    success: (res) => {
      const contentType = getHeaderValue(res.header, 'content-type')
      if (res.statusCode === 200 && contentType.includes('application/pdf')) {
        uni.openDocument({
          filePath: res.tempFilePath,
          showMenu: true,
          success: () => uni.hideLoading(),
          fail: () => {
            uni.hideLoading()
            uni.showToast({ title: '打开 PDF 失败', icon: 'none' })
          },
        })
      } else {
        uni.hideLoading()
        uni.showToast({ title: 'PDF 生成失败，请稍后重试', icon: 'none' })
      }
    },
    fail: () => {
      uni.hideLoading()
      uni.showToast({ title: '网络请求失败', icon: 'none' })
    },
  })
}

function goMembership() {
  uni.switchTab({ url: '/pages/profile/profile' })
}
</script>

<style lang="scss" scoped>
.download-page {
  min-height: 100vh;
  background:
    radial-gradient(90% 45% at 20% 0%, rgba(37, 99, 235, 0.07) 0%, rgba(37, 99, 235, 0) 62%),
    linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%);
  padding: 36rpx 28rpx 64rpx;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 28rpx;
}

.eyebrow {
  color: #f97316;
  font-size: 22rpx;
  font-weight: 800;
  letter-spacing: 0;
}

.title {
  color: $text-primary;
  font-size: 46rpx;
  font-weight: 900;
  line-height: 1.2;
}

.subtitle {
  color: $text-secondary;
  font-size: 27rpx;
  line-height: 1.55;
}

.mode-tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
  margin-bottom: 22rpx;
}

.mode-tab {
  height: 78rpx;
  border-radius: $radius-lg;
  background: rgba(255, 255, 255, 0.96);
  color: $text-secondary;
  font-size: 28rpx;
  font-weight: 700;
  border: 1px solid $border-light;
}

.mode-tab.active {
  background: $grad-accent;
  color: #fff;
  border-color: transparent;
}

.search-row {
  display: flex;
  gap: 14rpx;
  margin-bottom: 28rpx;
}

.helper-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
  margin-bottom: 20rpx;
}

.helper-label {
  color: $text-muted;
  font-size: 24rpx;
}

.example-chip {
  height: 54rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid $border-light;
  color: $text-secondary;
  font-size: 24rpx;
  line-height: 54rpx;
}

.access-card {
  @include glass-panel;
  border-radius: $radius-lg;
  padding: 22rpx 24rpx;
  margin-bottom: 24rpx;
  background: rgba(255, 247, 237, 0.86);
  border-color: rgba(249, 115, 22, 0.18);
  display: grid;
  grid-template-columns: 1fr auto;
  column-gap: 18rpx;
  row-gap: 8rpx;
  align-items: center;
}

.access-card.active {
  background: rgba(236, 253, 245, 0.88);
  border-color: rgba(16, 185, 129, 0.2);
}

.access-title {
  color: $text-primary;
  font-size: 28rpx;
  font-weight: 850;
  line-height: 1.35;
}

.access-desc {
  color: $text-secondary;
  font-size: 24rpx;
  line-height: 1.5;
}

.access-btn {
  grid-row: 1 / span 2;
  grid-column: 2;
  min-width: 132rpx;
  height: 62rpx;
  border-radius: 999rpx;
  background: #f97316;
  color: #fff;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 62rpx;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 76rpx;
  padding: 0 24rpx;
  border-radius: $radius-lg;
  color: $text-primary;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid $border-light;
  font-size: 28rpx;
  box-sizing: border-box;
}

.search-btn {
  width: 136rpx;
  height: 76rpx;
  border-radius: $radius-lg;
  background: rgba(249, 115, 22, 0.95);
  color: #fff;
  font-size: 28rpx;
  font-weight: 800;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.result-item {
  @include glass-panel;
  background: rgba(255, 255, 255, 0.96);
  border-radius: $radius-xl;
  padding: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.result-main {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.item-title {
  color: $text-primary;
  font-size: 32rpx;
  font-weight: 850;
  line-height: 1.35;
}

.item-meta {
  color: #f97316;
  font-size: 24rpx;
  line-height: 1.45;
}

.item-summary {
  color: $text-secondary;
  font-size: 26rpx;
  line-height: 1.7;
}

.download-btn {
  width: 100%;
  height: 78rpx;
  border-radius: $radius-lg;
  background: $grad-royal;
  color: #fff;
  font-size: 28rpx;
  font-weight: 800;
}

.state-block {
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 44rpx 28rpx;
  color: $text-secondary;
  text-align: center;
  font-size: 28rpx;
}

.state-block.error {
  color: #dc2626;
}

.empty-panel {
  @include glass-panel;
  border-radius: $radius-xl;
  padding: 42rpx 30rpx;
  background: rgba(255, 255, 255, 0.96);
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  text-align: left;
}

.empty-title {
  color: $text-primary;
  font-size: 30rpx;
  font-weight: 850;
}

.empty-desc {
  color: $text-secondary;
  font-size: 26rpx;
  line-height: 1.65;
}

.empty-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 8rpx;
}

.empty-action {
  height: 70rpx;
  border-radius: $radius-lg;
  background: $grad-royal;
  color: #fff;
  font-size: 25rpx;
  font-weight: 800;
}

.empty-action.secondary {
  background: rgba(248, 250, 252, 0.96);
  color: $text-primary;
  border: 1px solid $border-light;
}
</style>
