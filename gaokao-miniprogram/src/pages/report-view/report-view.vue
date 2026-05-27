<template>
  <web-view :src="url" />
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'

const url = ref('')
const isDeepReader = computed(() => url.value.includes('/reports/deep/view/'))

onLoad((options) => {
  if (options.url) {
    url.value = decodeURIComponent(options.url)
  }
})

// 允许分享给微信好友
onShareAppMessage(() => {
  if (isDeepReader.value) {
    return {
      title: '深度报告库',
      path: '/pages/deep-report-download/deep-report-download',
    }
  }
  return {
    title: '我的高考志愿综合评估报告',
    path: `/pages/report-view/report-view?url=${encodeURIComponent(url.value)}`,
  }
})

// 允许分享到朋友圈
onShareTimeline(() => {
  if (isDeepReader.value) {
    return {
      title: '深度报告库',
      query: '',
    }
  }
  return {
    title: '我的高考志愿综合评估报告',
    query: `url=${encodeURIComponent(url.value)}`,
  }
})
</script>
