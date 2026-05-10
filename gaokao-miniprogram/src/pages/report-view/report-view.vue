<template>
  <web-view :src="url" />
</template>

<script setup>
const pages = getCurrentPages()
const page = pages[pages.length - 1]
const url = decodeURIComponent(page.options?.url || '')
</script>
