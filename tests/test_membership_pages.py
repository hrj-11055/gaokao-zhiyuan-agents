import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MembershipPagesTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_profile_page_is_membership_center(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")

        for snippet in [
            "报告未解锁",
            "VIP · 报告已解锁",
            "考生信息",
            "我的咨询记录",
            "我的测评结果",
            "邀请好友",
            "VIP 权益",
            "邀请进度",
            "会员邀请码",
            "剩余下载次数",
            "useMembershipStore",
            "membershipStore.loadStatus",
            "onShareAppMessage",
            "inviterId=${membershipStore.userId",
        ]:
            self.assertIn(snippet, text)

        home = self.read("gaokao-miniprogram/src/pages/index/index.vue")
        self.assertIn("邀请 5 人免费", home)
        self.assertNotIn("邀请 3 人免费", home)

    def test_report_page_has_membership_lock_and_auth_header(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")
        api = self.read("gaokao-miniprogram/src/api/report.js")

        for snippet in [
            "membershipStore.loadStatus",
            "allAssessmentsDone",
            "unlock-options",
            "onPayWithWechat",
            "unlockTrialAndGenerate",
            "loadQuestionnaire",
            "loadAssessments",
            "loadHistory",
            "questionnaire.answers",
            "sessionToken: membershipStore.sessionToken",
            "已保留草稿",
            "VIP 报告权益",
            "解锁完整志愿报告",
            "邀请 5 位新用户",
            "输入会员邀请码",
            "showUnlockSheet",
            "redeemCodeFromSheet",
            "deep-report-package",
            "院校深度研究报告",
            "专业研究报告",
            "剩余下载次数",
        ]:
            self.assertIn(snippet, text)

        for snippet in [
            "requestBackendData",
            "path: '/api/report/generate'",
            "Authorization",
            "Bearer ${sessionToken}",
            "timeout: 180000",
        ]:
            self.assertIn(snippet, api)

        self.assertIn("通常需要 1-2 分钟", text)
        self.assertNotIn("通常需要 15-30 秒", text)

    def test_report_page_exposes_trial_unlock_only_as_non_release_guarded_flow(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")
        store = self.read("gaokao-miniprogram/src/stores/membership.js")
        api = self.read("gaokao-miniprogram/src/api/membership.js")

        for snippet in [
            "体验版解锁并生成",
            "showTrialUnlock",
            "membershipStore.canUseTrialUnlock",
            "activateLimitedFree",
        ]:
            self.assertIn(snippet, text)

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
