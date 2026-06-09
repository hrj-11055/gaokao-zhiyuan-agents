import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MembershipPagesTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_profile_page_shows_free_report_access_center(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")

        for snippet in [
            "报告开放",
            "志愿报告权益",
            "已开放",
            "1.3.0 免费开放",
            "无需支付或兑换码",
            "咨询记录",
            "我的测评",
            "邀请好友",
            "修改档案",
            "投诉建议",
            "关于我们",
            "useMembershipStore",
            "membershipStore.loadStatus",
            "onShareAppMessage",
            "inviterId=${membershipStore.userId",
            "CUSTOMER_WECHAT_ID",
            "复制微信号",
        ]:
            self.assertIn(snippet, text)
        for snippet in [
            "onPayWithWechat",
            "membershipStore.openMembership",
            "MEMBERSHIP_PRICE_LABEL",
            "付款截图",
        ]:
            self.assertNotIn(snippet, text)
        self.assertIn("HRJ-11055", self.read("gaokao-miniprogram/src/config.js"))

        home = self.read("gaokao-miniprogram/src/pages/index/index.vue")
        self.assertIn("1.3.0 免费开放", home)
        self.assertIn("无需支付或兑换码", home)
        self.assertIn("立即生成报告", home)
        self.assertIn("onShareAppMessage", home)
        self.assertIn("邀请你一起生成高考志愿参考报告", home)
        self.assertIn("inviterId=${membershipStore.userId", home)
        self.assertNotIn("邀请 3 人免费", home)
        self.assertNotIn("邀请 5 位同学免费获取", home)
        self.assertNotIn("MEMBERSHIP_PRICE_LABEL", home)

    def test_profile_contact_buttons_show_wechat_and_qr_code(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")
        config = self.read("gaokao-miniprogram/src/config.js")

        for snippet in [
            "CUSTOMER_WECHAT_ID",
            "CUSTOMER_WECHAT_QR_IMAGE",
            "showContactSheet",
            "contact-sheet",
            "copyCustomerWechatId",
            "previewCustomerWechatQr",
            "添加客服微信",
            "微信号已复制",
            "uni.previewImage",
            "contactSheetMode",
        ]:
            self.assertIn(snippet, text)

        self.assertNotIn("功能开发中", text)
        self.assertIn("CUSTOMER_WECHAT_QR_IMAGE", config)
        self.assertIn("/static/contact/wechat-qr.png", config)
        self.assertTrue((ROOT / "gaokao-miniprogram/src/static/contact/wechat-qr.png").exists())

    def test_about_sheet_uses_company_story_not_contact_copy(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")

        for snippet in [
            "contactSheetMode === 'about'",
            "深圳元说科技",
            "/static/yuanshuo-logo.png",
            "抹平信息差",
            "张雪峰老师",
            "AI 咨询模块",
            "openContactSheet('关于我们', 'about')",
        ]:
            self.assertIn(snippet, text)
        self.assertTrue((ROOT / "gaokao-miniprogram/src/static/yuanshuo-logo.png").exists())

    def test_profile_page_summarizes_score_mode_without_requiring_score(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")

        self.assertIn("getProfileReportMode", text)
        self.assertIn("profileScoreDisplay", text)
        self.assertIn("profileScoreLabel", text)
        self.assertIn("预估", text)
        self.assertIn("提前规划", text)
        self.assertIn("无需支付或兑换码", text)
        self.assertNotIn("有效邀请：新用户通过你的分享进入，并完成基础资料才计数", text)
        self.assertNotIn("完成省份、科类、分数基础资料", text)

    def test_report_page_allows_free_report_generation_and_keeps_auth_header(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")
        api = self.read("gaokao-miniprogram/src/api/report.js")

        for snippet in [
            "membershipStore.loadStatus",
            "allAssessmentsDone",
            "buildReportAssessmentPayload",
            "loadHistory",
            "sessionToken: membershipStore.sessionToken",
            "已保留草稿",
            "FREE_DEEP_REPORTS_ENABLED",
            "membershipStore.canUseDeepReports",
            "立即生成${reportModeLabel.value}",
            "1.3.0 免费开放",
            "reportModeLabel",
            "deep-report-package",
            "院校研究报告",
            "专业研究报告",
            "onShareAppMessage",
            "inviterId=${membershipStore.userId",
        ]:
            self.assertIn(snippet, text)

        for snippet in [
            "生成{{ reportModeLabel }}需要 VIP",
            "输入会员邀请码",
            "redeemCodeFromSheet",
            "onPayWithWechat",
        ]:
            self.assertNotIn(snippet, text)

        for snippet in [
            "requestBackendData",
            "path: '/api/report/generate'",
            "Authorization",
            "Bearer ${sessionToken}",
            "timeout: 360000",
        ]:
            self.assertIn(snippet, api)

        self.assertIn("通常需要 1-2 分钟", text)
        self.assertNotIn("通常需要 15-30 秒", text)

    def test_trial_unlock_is_store_guarded_and_not_exposed_on_report_page(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")
        store = self.read("gaokao-miniprogram/src/stores/membership.js")
        api = self.read("gaokao-miniprogram/src/api/membership.js")

        self.assertNotIn("体验版解锁并生成", text)
        self.assertNotIn("showTrialUnlock", text)
        self.assertNotIn("membershipStore.canUseTrialUnlock", text)
        self.assertIn("activateLimitedFree", store)
        self.assertIn("isTestMiniProgramEnv", store)
        self.assertIn("envVersion", api)
        self.assertIn("develop", api)
        self.assertIn("trial", api)

    def test_membership_store_supports_vip_code_and_download_quota(self):
        api = self.read("gaokao-miniprogram/src/api/membership.js")
        store = self.read("gaokao-miniprogram/src/stores/membership.js")

        for snippet in [
            "redeemMembershipCode",
            "url: '/api/membership/redeem-code'",
            "data: { code }",
        ]:
            self.assertIn(snippet, api)

        for snippet in [
            "downloadQuota",
            "canUseDeepReports",
            "FREE_DEEP_REPORTS_ENABLED",
            "redeemCode",
            "requiredInviteCount: 5",
            "请先邀请 5 位同学免费解锁",
        ]:
            self.assertIn(snippet, store)

    def test_report_page_does_not_expose_limited_free_test_unlock(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")

        self.assertNotIn("限时免费测试入口", text)
        self.assertNotIn("免费解锁并生成报告", text)
        self.assertNotIn("activateLimitedFreeAndGenerate", text)
        self.assertNotIn("limited-free-panel", text)


if __name__ == "__main__":
    unittest.main()
