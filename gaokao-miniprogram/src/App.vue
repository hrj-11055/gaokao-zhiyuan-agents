<script>
export default {}
</script>

<style>
/* 引入免费开源的思源黑体 (Noto Sans SC) 和思源宋体 (Noto Serif SC) */
/* 使用 Google Fonts 的切片技术，按需加载，极大地减少小程序加载体积 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@400;700&display=swap');

page {
  background-color: #f5f5f5;
  /* 
   * 字体回退链 (Font Stack) 策略：
   * 1. 优先使用苹果/操作系统的系统自带无版权风险字体 (-apple-system, PingFang SC 等)，性能最好且符合用户习惯。
   * 2. 当系统字体不存在时，自动网络下载并使用 Noto Sans SC (思源黑体)。
   * 3. 彻底移除了有侵权风险的 Microsoft YaHei。
   */
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', Helvetica, 'Noto Sans SC', sans-serif;
}

/* 提供辅助类，方便在生成海报或需要特殊排版的组件中强制调用指定字体 */
.font-sans {
  font-family: 'Noto Sans SC', sans-serif;
}

.font-serif {
  font-family: 'Noto Serif SC', serif;
}
</style>
