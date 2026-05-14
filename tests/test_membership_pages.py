import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MembershipPagesTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_profile_page_is_membership_center(self):
        text = self.read("gaokao-miniprogram/src/pages/profile/profile.vue")

        for snippet in [
            "深度填报会员",
            "¥29 一次性解锁",
            "邀请 3 人免费解锁",
            "大学深度研究",
            "综合志愿报告",
            "PDF 下载",
            "useMembershipStore",
            "openMembership",
            "shareInvite",
            "membershipStore.inviteProgressText",
        ]:
            self.assertIn(snippet, text)

    def test_report_page_has_membership_lock_and_auth_header(self):
        text = self.read("gaokao-miniprogram/src/pages/report/report.vue")

        for snippet in [
            "membershipStore.loadStatus",
            "status === 'locked'",
            "MEMBERSHIP_REQUIRED",
            "Authorization",
            "Bearer ${membershipStore.sessionToken}",
            "解锁并生成报告",
            "邀请 3 人免费解锁",
            "useMembershipStore",
        ]:
            self.assertIn(snippet, text)


if __name__ == "__main__":
    unittest.main()
