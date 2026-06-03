<template>
  <image :src="svgDataUri" :style="{ width: size, height: size }" class="lucide-icon" mode="aspectFit" />
</template>

<script setup>
import { computed } from 'vue'
import { icons } from '../utils/icons.js'

const props = defineProps({
  name: {
    type: String,
    required: true
  },
  size: {
    type: String,
    default: '48rpx'
  },
  color: {
    type: String,
    default: '#1d2129' // Default to a standard text color
  }
})

// Simple btoa polyfill since WeChat MiniProgram doesn't have window.btoa reliably
function myBtoa(input) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  let str = String(input);
  for (var block, charCode, idx = 0, map = chars, output = ''; str.charAt(idx | 0) || (map = '=', idx % 1); output += map.charAt(63 & block >> 8 - idx % 1 * 8)) {
    charCode = str.charCodeAt(idx += 3 / 4);
    block = block << 8 | charCode;
  }
  return output;
}

const svgDataUri = computed(() => {
  let svgStr = icons[props.name]
  if (!svgStr) {
    console.warn(`[LucideIcon] Icon not found: ${props.name}`)
    // fallback empty svg
    svgStr = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"></svg>`
  }

  // Replace {color} placeholders
  const colorizedSvg = svgStr.replace(/\{color\}/g, props.color)
  
  // Safe Base64 encoding for Unicode strings (though Lucide SVGs are ASCII)
  const encodedSvg = myBtoa(unescape(encodeURIComponent(colorizedSvg)))
  return `data:image/svg+xml;base64,${encodedSvg}`
})
</script>

<style scoped>
.lucide-icon {
  display: inline-block;
  vertical-align: middle;
}
</style>
