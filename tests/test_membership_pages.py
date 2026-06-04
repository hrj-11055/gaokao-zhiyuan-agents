import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MembershipPagesTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_profile_page_is_membership_center(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")

        for snippet in [
            "尊享 VIP",
            "未解锁",
            "志愿填报 VIP",
            "咨询记录",
            "我的测评",
            "邀请好友",
            "修改档案",
            "投诉建议",
            "剩余下载次数",
            "useMembershipStore",
            "membershipStore.loadStatus",
            "onMembershipAction",
            "onPayWithWechat",
            "membershipStore.openMembership",
            "onShareAppMessage",
            "inviterId=${membershipStore.userId",
            "CUSTOMER_WECHAT_ID",
            "复制微信号",
        ]:
            self.assertIn(snippet, text)
        self.assertIn("HRJ-11055", self.read("gaokao-miniprogram/src/config.js"))

        home = self.read("gaokao-miniprogram/src/pages/index/index.vue")
        self.assertIn("邀请 5 位同学免费获取", home)
        self.assertNotIn("邀请 3 人免费", home)

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
        ]:
            self.assertIn(snippet, text)

        self.assertNotIn("功能开发中", text)
        self.assertIn("CUSTOMER_WECHAT_QR_IMAGE", config)
        self.assertIn("/static/contact/wechat-qr.png", config)
        self.assertTrue((ROOT / "gaokao-miniprogram/src/static/contact/wechat-qr.png").exists())

    def test_profile_page_summarizes_score_mode_without_requiring_score(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")

        self.assertIn("getProfileReportMode", text)
        self.assertIn("profileScoreDisplay", text)
        self.assertIn("profileScoreLabel", text)
        self.assertIn("预估", text)
        self.assertIn("提前规划", text)
        self.assertIn("有效邀请：新用户通过你的分享进入，并完成基础资料才计数", text)
        self.assertNotIn("完成省份、科类、分数基础资料", text)

    def test_report_page_has_membership_lock_and_auth_header(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")
        api = self.read("gaokao-miniprogram/src/api/report.js")

        for snippet in [
            "membershipStore.loadStatus",
            "allAssessmentsDone",
            "onPayWithWechat",
            "buildReportAssessmentPayload",
            "loadHistory",
            "sessionToken: membershipStore.sessionToken",
            "已保留草稿",
            "生成{{ reportModeLabel }}需要 VIP",
            "开通后可生成{{ reportModeLabel }}",
            "reportModeLabel",
            "邀请 5 位新用户",
            "输入会员邀请码",
            "showUnlockSheet",
            "redeemCodeFromSheet",
            "deep-report-package",
            "院校深度研究报告",
            "专业研究报告",
            "剩余下载次数",
            "onShareAppMessage",
            "inviterId=${membershipStore.userId",
        ]:
            self.assertIn(snippet, text)

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
