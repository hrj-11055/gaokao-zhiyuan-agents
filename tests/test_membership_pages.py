import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MembershipPagesTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_profile_page_is_membership_center(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")

        for snippet in [
            "综合报告会员",
            "price-val\">29",
            "邀请 3 位同学免费开通",
            "院校深度研究",
            "智能志愿报告",
            "报告打印下载",
            "useMembershipStore",
            "openMembership",
            "shareInvite",
            "membershipStore.effectiveInviteCount",
            "paymentUnavailableText",
            "copyInviteLink",
            "refreshMembershipStatus",
            "备案中，先邀请解锁",
            "邀请进度已刷新",
        ]:
            self.assertIn(snippet, text)

    def test_report_page_has_membership_lock_and_auth_header(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")

        for snippet in [
            "membershipStore.loadStatus",
            "status === 'assessment'",
            "去完成测评",
            "uni.switchTab({ url: '/pages/assessments/assessments' })",
            "status === 'locked'",
            "MEMBERSHIP_REQUIRED",
            "Authorization",
            "Bearer ${membershipStore.sessionToken}",
            "paymentActionText",
            "邀请 3 名好友免费解锁",
            "useMembershipStore",
            "PAYMENT_ENABLED",
            "支付功能正在备案配置中",
            "goInvite",
        ]:
            self.assertIn(snippet, text)

    def test_report_page_blocks_pdf_download_until_https_domain_is_ready(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")

        for snippet in [
            "PDF_DOWNLOAD_ENABLED",
            "PDF 下载正在等待 HTTPS 合法域名配置",
            "downloadUnavailableText",
            "uni.showModal",
            "if (!PDF_DOWNLOAD_ENABLED)",
        ]:
            self.assertIn(snippet, text)

    def test_report_page_does_not_expose_limited_free_test_unlock(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")

        self.assertNotIn("限时免费测试入口", text)
        self.assertNotIn("免费解锁并生成报告", text)
        self.assertNotIn("activateLimitedFreeAndGenerate", text)
        self.assertNotIn("limited-free-panel", text)


if __name__ == "__main__":
    unittest.main()
