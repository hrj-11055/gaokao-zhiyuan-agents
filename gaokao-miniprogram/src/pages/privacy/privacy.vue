<template>
  <scroll-view scroll-y class="privacy-page">
    <view class="privacy-header">
      <text class="privacy-title">隐私保护指引</text>
      <text class="privacy-date">更新日期：2026年5月19日 | 生效日期：2026年5月19日</text>
    </view>

    <view class="section">
      <text class="section-title">一、引言</text>
      <text class="section-text">「峰哥咨询参考」小程序（以下简称"本产品"）由开发者独立运营。我们深知个人信息对您的重要性，将以高度审慎的态度对待您的个人信息。本隐私保护指引旨在向您说明我们如何收集、使用、存储和保护您的个人信息。</text>
      <text class="section-text">使用本产品即表示您同意本指引所述的信息处理方式。如果您不同意本指引的任何内容，请停止使用本产品。</text>
    </view>

    <view class="section">
      <text class="section-title">二、我们收集的信息</text>
      <text class="section-text">为提供高考志愿填报咨询服务，我们会收集以下信息：</text>
      <text class="section-text">1. 基本信息：您主动填写的省份、考试科目（文/理/新高考）、高考分数、全省位次等志愿填报相关数据。</text>
      <text class="section-text">2. 问卷答案：您在五环问卷、MBTI 性格测试、霍兰德职业兴趣测试中选择的项目。</text>
      <text class="section-text">3. 对话内容：您在 AI 对话中发送的问题及 AI 生成的回答。</text>
      <text class="section-text">4. 身份标识：微信 OpenID（用于区分用户身份，不包含您的微信昵称、头像等个人信息）。</text>
      <text class="section-text">5. 设备信息：我们会通过微信小程序框架获取必要的运行环境信息以保障服务稳定性。</text>
    </view>

    <view class="section">
      <text class="section-title">三、我们如何使用信息</text>
      <text class="section-text">收集的信息将用于以下目的：</text>
      <text class="section-text">1. 提供智能志愿填报咨询和个性化推荐服务。</text>
      <text class="section-text">2. 生成个人综合志愿分析报告。</text>
      <text class="section-text">3. 维护您的会员权益和订单管理。</text>
      <text class="section-text">4. 改善 AI 回复质量和服务体验。</text>
      <text class="section-text">我们不会将您的信息用于上述目的以外的其他用途，也不会对您的信息进行用户画像、自动化决策或精准推送。</text>
    </view>

    <view class="section">
      <text class="section-title">四、信息存储与安全</text>
      <text class="section-text">1. 本地存储：您的基本信息和测评结果存储在您的设备本地（微信小程序 Storage），可随时通过"我的 → 清除数据"删除。</text>
      <text class="section-text">2. 服务器存储：对话记录、报告数据存储在服务器端，使用 PostgreSQL 数据库加密存储，通过 HTTPS 协议传输。</text>
      <text class="section-text">3. 我们采取了合理的技术和管理措施来保护您的信息安全，防止未经授权的访问、使用或泄露。</text>
    </view>

    <view class="section">
      <text class="section-title">五、第三方服务</text>
      <text class="section-text">为实现产品功能，我们会将部分数据传输给以下第三方服务：</text>
      <text class="section-text">1. Dify + DeepSeek：为您提供 AI 智能对话服务。您的聊天问题会被发送至 Dify 平台并调用 DeepSeek 大语言模型生成回答。</text>
      <text class="section-text">2. 微信支付：用于处理会员购买支付流程。支付信息由微信支付系统直接处理，我们不存储您的银行卡等支付敏感信息。</text>
      <text class="section-text">3. 火山引擎：用于将 AI 回复文本转换为语音（TTS 功能）。</text>
      <text class="section-text">以上第三方服务均有各自的隐私政策，我们建议您查阅了解。</text>
    </view>

    <view class="section">
      <text class="section-title">六、信息共享</text>
      <text class="section-text">我们不会向任何第三方出售、出租或交易您的个人信息。仅在以下情况下会共享必要信息：</text>
      <text class="section-text">1. 经您事先同意。</text>
      <text class="section-text">2. 根据法律法规要求，或政府主管部门的强制性要求。</text>
    </view>

    <view class="section">
      <text class="section-title">七、您的权利</text>
      <text class="section-text">1. 查询和更正：您可以随时在小程序内查看和修改您的个人信息。</text>
      <text class="section-text">2. 删除：您可以通过"我的 → 清除数据"删除本地存储的所有个人数据。如需删除服务器端数据，请联系我们。</text>
      <text class="section-text">3. 撤回同意：您可以随时停止使用本产品来撤回对信息处理的同意。</text>
    </view>

    <view class="section">
      <text class="section-title">八、未成年人保护</text>
      <text class="section-text">我们充分认识到主要用户群体为高中学生。我们将对未成年人的个人信息提供额外保护：</text>
      <text class="section-text">1. 不会主动收集未成年人的身份证明文件。</text>
      <text class="section-text">2. 不会向未成年人推送商业广告。</text>
      <text class="section-text">3. 如发现未成年人个人信息被不当收集或使用，我们将立即删除相关信息。</text>
    </view>

    <view class="section">
      <text class="section-title">九、隐私政策的更新</text>
      <text class="section-text">我们可能会适时修订本指引。更新后的指引将在本页面发布，并通过小程序内通知或其他合理方式告知您。对于重大变更，我们会在获得您的明确同意后继续处理您的个人信息。</text>
    </view>

    <view class="section">
      <text class="section-title">十、联系我们</text>
      <text class="section-text">如您对本隐私保护指引有任何疑问、意见或建议，可通过以下方式联系我们：</text>
      <text class="section-text">电子邮箱：gaokao@aicoming.com.cn</text>
      <text class="section-text">我们将在收到您的问题后尽快予以回复。</text>
    </view>

    <view class="footer-spacer"></view>
  </scroll-view>
</template>

<script setup>
</script>

<style lang="scss" scoped>
.privacy-page {
  height: 100vh;
  background-color: #F9FAFB;
}

.privacy-header {
  padding: 40rpx 40rpx 24rpx;
  background-color: #FFFFFF;
  border-bottom: 1rpx solid #F3F4F6;
}

.privacy-title {
  display: block;
  font-size: 36rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12rpx;
}

.privacy-date {
  display: block;
  font-size: 24rpx;
  color: #9CA3AF;
}

.section {
  padding: 32rpx 40rpx;
  background-color: #FFFFFF;
  margin-bottom: 2rpx;
}

.section-title {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #374151;
  margin-bottom: 16rpx;
}

.section-text {
  display: block;
  font-size: 26rpx;
  color: #6B7280;
  line-height: 1.7;
  margin-bottom: 12rpx;
}

.footer-spacer {
  height: 60rpx;
}
</style>
