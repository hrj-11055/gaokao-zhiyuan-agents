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

      <view v-if="results.length === 0" class="state-block">
        <text>输入学校或专业名称后查询可下载报告。</text>
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

const membershipStore = useMembershipStore()

const collection = computed(() => mode.value === 'major' ? 'majors' : 'universities')

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
  loading.value = true
  errorMsg.value = ''
  try {
    const params = [`page_size=20`]
    if (keyword.value) {
      params.push(`search=${encodeURIComponent(keyword.value)}`)
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
    uni.showToast({
      title: err.message || '请先开通会员',
      icon: 'none',
      duration: 2200,
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
</style>
