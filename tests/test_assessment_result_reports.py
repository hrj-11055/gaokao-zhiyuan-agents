import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AssessmentResultReportTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def run_node_assertions(self, script):
        subprocess.run(
            ["node", "--input-type=module", "-e", textwrap.dedent(script)],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_profile_save_label_does_not_imply_auto_navigation(self):
        text = self.read("gaokao-miniprogram/src/pages/index/index.vue")

        self.assertIn("保存信息", text)
        self.assertNotIn("保存并继续", text)

    def test_mbti_result_uses_prebuilt_reports_and_major_profiles(self):
        text = self.read("gaokao-miniprogram/src/pages/mbti/mbti-result.vue")

        self.assertIn("MBTI_RESULT_REPORTS", text)
        self.assertIn("buildMajorCards", text)
        self.assertIn("major.insight.summary", text)
        self.assertNotIn("getMajorDesc", text)
        self.assertNotIn("热门专业方向", text)

    def test_holland_result_uses_prebuilt_reports_and_major_profiles(self):
        text = self.read("gaokao-miniprogram/src/pages/holland/holland-result.vue")

        self.assertIn("HOLLAND_RESULT_REPORTS", text)
        self.assertIn("buildMajorCards", text)
        self.assertIn("major.insight.summary", text)
        self.assertIn("saveAssessments(assessments)", text)
        self.assertIn("getHollandDimensionMaxScores", text)
        self.assertIn("{{ dim.maxScoreText }}", text)
        self.assertNotIn("<text class=\"td text-light\">40</text>", text)
        self.assertNotIn("getMajorDesc", text)
        self.assertNotIn("热门专业方向", text)

    def test_assessment_result_pages_have_light_next_step_bars(self):
        mbti = self.read("gaokao-miniprogram/src/pages/mbti/mbti-result.vue")
        holland = self.read("gaokao-miniprogram/src/pages/holland/holland-result.vue")

        for text in [mbti, holland]:
            self.assertIn("next-step-bar", text)
            self.assertIn("下一步", text)
            self.assertIn("goNextStep", text)
            self.assertIn("/pages/report/report", text)

        self.assertIn("/pages/holland/holland", mbti)
        self.assertIn("/pages/mbti/mbti", holland)

    def test_user_facing_personality_test_label_hides_mbti(self):
        user_facing_files = [
            "gaokao-miniprogram/src/pages.json",
            "gaokao-miniprogram/src/pages/index/index.vue",
            "gaokao-miniprogram/src/pages/report/report.vue",
            "gaokao-miniprogram/src/pages/assessments/assessments.vue",
            "gaokao-miniprogram/src/pages/mbti/mbti.vue",
            "gaokao-miniprogram/src/pages/mbti/mbti-result.vue",
            "gaokao-miniprogram/src/pages/major-detail/major-detail.vue",
            "gaokao-miniprogram/src/pages/privacy/privacy.vue",
        ]
        forbidden = ["MBTI 性格", "MBTI 测试", "MBTI 测评", "MBTI 匹配", "MBTI 16型", ">MBTI "]
        for relpath in user_facing_files:
            text = self.read(relpath)
            for snippet in forbidden:
                self.assertNotIn(snippet, text, relpath)

    def test_result_report_maps_and_major_profiles_are_complete(self):
        self.run_node_assertions(
            """
            import assert from 'node:assert/strict'

            const mbti = await import('./gaokao-miniprogram/src/data/mbti-questions.js')
            const holland = await import('./gaokao-miniprogram/src/data/holland-questions.js')
            const profiles = await import('./gaokao-miniprogram/src/data/major-learning-profiles.js')

            const mbtiTypes = Object.keys(mbti.MBTI_RESULT_REPORTS).sort()
            assert.deepEqual(mbtiTypes, [
              'ENFJ', 'ENFP', 'ENTJ', 'ENTP',
              'ESFJ', 'ESFP', 'ESTJ', 'ESTP',
              'INFJ', 'INFP', 'INTJ', 'INTP',
              'ISFJ', 'ISFP', 'ISTJ', 'ISTP',
            ])

            assert.equal(Object.keys(holland.HOLLAND_RESULT_REPORTS).length, 120)
            assert.ok(holland.HOLLAND_RESULT_REPORTS.RIA.majors.length > 0)
            assert.ok(holland.HOLLAND_RESULT_REPORTS.CES.majors.length > 0)
            assert.equal(holland.getHollandMaxScore('basic'), 8)
            assert.equal(holland.getHollandMaxScore('full'), 40)
            assert.deepEqual(holland.getHollandDimensionMaxScores('basic'), {
              R: 8,
              I: 8,
              A: 8,
              S: 8,
              E: 8,
              C: 8,
            })
            assert.deepEqual(holland.getHollandDimensionMaxScores('full'), {
              R: 40,
              I: 40,
              A: 40,
              S: 40,
              E: 40,
              C: 40,
            })

            assert.equal(profiles.normalizeMajorName('计算机科学'), '计算机科学与技术')
            assert.equal(profiles.normalizeMajorName('新闻传播'), '新闻学')
            assert.equal(profiles.normalizeMajorName('技术文档写作'), '编辑出版学')

            const techWriting = profiles.getMajorLearningProfile('技术文档写作')
            assert.equal(techWriting.name, '编辑出版学')
            assert.ok(techWriting.courses.includes('编辑学概论'))
            assert.ok(techWriting.abilities.includes('事实核验'))

            const cards = profiles.buildMajorCards(['计算机科学', '计算机科学与技术', '新闻传播'])
            assert.deepEqual(cards.map((card) => card.name), ['计算机科学与技术', '新闻学'])
            assert.ok(cards.every((card) => card.insight.summary && card.insight.courses.length > 0))

            const marketing = profiles.getMajorLearningProfile('市场营销', {
              summary: '数据库暂未匹配到该专业，以下为通用参考。',
              courses: ['通识基础课', '专业基础课', '专业核心课', '实践训练课'],
              abilities: ['持续学习', '信息检索', '表达沟通', '解决复杂问题'],
              salarySummary: '薪资受城市、院校层次、学历和岗位方向影响较大，建议结合目标城市核验。',
            })
            assert.ok(marketing.courses.includes('消费者行为学'))
            assert.ok(marketing.abilities.includes('用户洞察'))
            assert.equal(marketing.source, 'curated')
            """
        )


if __name__ == "__main__":
    unittest.main()
