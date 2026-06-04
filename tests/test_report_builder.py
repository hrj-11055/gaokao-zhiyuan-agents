import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportBuilderTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def run_node_test(self, test_body: str):
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "test.js"
            test_path.write_text(
                textwrap.dedent(f"""
                    const assert = require('node:assert/strict')
                    const {{
                      buildFinalHtml,
                      buildHollandRadarSVG,
                      buildReportExpansionPrompt,
                      countReportContentChars,
                      getReportQualityIssues,
                      humanizeReportCopy,
                      normalizeReportHtml,
                      requestDeepSeekJson,
                      renderReadableText,
                    }} = require('{ROOT / "gaokao-proxy" / "lib" / "report-builder.js"}')

                    {test_body}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def test_build_final_html_contains_static_print_report(self):
        self.run_node_test(r"""
            const content = JSON.stringify({
              conclusions: ['先稳层次，再看专业适配。'],
              modules: [
                {
                  id: 'tab1',
                  title: '总览',
                  summary: '摘要',
                  blocks: [{ type: 'text', title: '判断', content: '正文内容' }]
                },
                {
                  id: 'tab2',
                  title: '测评画像',
                  blocks: [{ type: 'list', title: '方向', items: ['计算机类', '电子信息类'] }]
                }
              ]
            })
            const html = buildFinalHtml(content, { province: '广东', category: '物理类', score: 600 }, {
              holland: { scores: { R: 20, I: 30, A: 10, S: 25, E: 15, C: 22 } }
            })

            assert.equal(html.includes('class="pdf-print-report"'), true)
            assert.equal(html.includes('@media print'), true)
            assert.equal(html.includes('家长先看结论'), true)
            assert.equal(html.includes('先稳层次，再看专业适配。'), true)
            assert.equal(html.includes('测评画像'), true)
            assert.equal(html.includes('霍兰德职业兴趣图谱'), true)
            assert.equal(html.includes('章节导航'), true)
            assert.equal(html.includes('scrollToModule'), true)
            assert.equal(html.includes('activeTab'), false)
            assert.equal(html.includes('v-show="activeTab'), false)
        """)

    def test_build_final_html_accepts_parsed_object_directly(self):
        self.run_node_test(r"""
            const data = {
              conclusions: ['结论一'],
              modules: [
                { id: 'tab1', title: '总览', blocks: [{ type: 'text', content: '正文' }] }
              ]
            }
            // Pass object directly (no JSON.stringify)
            const html = buildFinalHtml(data, { province: '广东' }, {})
            assert.equal(html.includes('结论一'), true)
            assert.equal(html.includes('总览'), true)
            assert.equal(html.includes('正文'), true)

            // Pass string (backward compat)
            const html2 = buildFinalHtml(JSON.stringify(data), { province: '广东' }, {})
            assert.equal(html2.includes('结论一'), true)
        """)

    def test_deepseek_timeout_retries_flash_model(self):
        self.run_node_test(r"""
            const calls = []
            global.fetch = async (_url, options) => {
              const body = JSON.parse(options.body)
              calls.push(body.model)
              if (calls.length === 1) {
                const err = new Error('The operation was aborted due to timeout')
                err.name = 'TimeoutError'
                throw err
              }
              return {
                ok: true,
                json: async () => ({
                  choices: [{ message: { content: '{"ok":true}' }, finish_reason: 'stop' }]
                })
              }
            }

            ;(async () => {
              const content = await requestDeepSeekJson('请输出合法 JSON')
              assert.equal(content, '{"ok":true}')
              assert.deepEqual(calls, ['deepseek-v4-flash', 'deepseek-v4-flash'])
            })().catch((err) => {
              console.error(err)
              process.exitCode = 1
            })
        """)

    def test_deepseek_bad_request_does_not_fall_back(self):
        self.run_node_test(r"""
            const calls = []
            global.fetch = async (_url, options) => {
              const body = JSON.parse(options.body)
              calls.push(body.model)
              return {
                ok: false,
                status: 400,
                text: async () => '{"error":{"message":"bad prompt"}}'
              }
            }

            ;(async () => {
              await assert.rejects(
                () => requestDeepSeekJson('请输出合法 JSON'),
                /DeepSeek API error 400/
              )
              assert.deepEqual(calls, ['deepseek-v4-flash'])
            })().catch((err) => {
              console.error(err)
              process.exitCode = 1
            })
        """)

    def test_report_generation_uses_report_specific_flash_model(self):
        builder = self.read("gaokao-proxy/lib/report-builder.js")

        self.assertIn("REPORT_DEEPSEEK_MODEL", builder)
        self.assertIn("deepseek-v4-flash", builder)
        self.assertNotIn("deepseek-v4-pro", builder)
        self.assertNotIn("process.env.DEEPSEEK_MODEL", builder)

    def test_holland_radar_scales_basic_results_to_basic_max_score(self):
        self.run_node_test(r"""
            const scores = { R: 8, I: 8, A: 8, S: 8, E: 8, C: 8 }
            const basicSvg = buildHollandRadarSVG(scores, 'basic')
            const fullSvg = buildHollandRadarSVG(scores, 'full')
            const dataPolygon = /<polygon points="([^"]+)" fill="rgba\(37, 99, 235, 0\.15\)"/
            const basicPoints = basicSvg.match(dataPolygon)?.[1] || ''
            const fullPoints = fullSvg.match(dataPolygon)?.[1] || ''

            assert.equal(basicPoints.includes('100,35'), true)
            assert.equal(fullPoints.includes('100,87'), true)
        """)

    def test_report_quality_gate_counts_visible_content_per_module(self):
        self.run_node_test(r"""
            const longText = '专业判断需要结合分数位次兴趣能力家庭资源城市偏好就业路径培养方案风险核验行动安排'.repeat(70)
            const data = {
              conclusions: ['先看风险，再看冲刺。'],
              modules: [
                {
                  id: 'tab1',
                  title: '自我评估总结',
                  summary: longText,
                  blocks: [{ type: 'text', title: '判断', content: longText }]
                },
                {
                  id: 'tab2',
                  title: '个人特质分析',
                  blocks: [{ type: 'list', items: [longText, longText] }]
                },
                {
                  id: 'tab3',
                  title: '专业匹配分析',
                  blocks: [{ type: 'alert', content: longText, items: [longText] }]
                },
                {
                  id: 'tab4',
                  title: '专业深度研究',
                  blocks: [{ type: 'quote', content: longText + longText }]
                },
                {
                  id: 'tab5',
                  title: '大学深度研究',
                  blocks: [{ type: 'text', content: longText + longText }]
                },
                {
                  id: 'tab6',
                  title: '综合决策报告',
                  blocks: [{ type: 'text', content: '太短' }]
                }
              ]
            }

            assert.equal(countReportContentChars('中文内容ABC 123'), 6)
            const issues = getReportQualityIssues(data, 1000)
            assert.deepEqual(issues.map((issue) => issue.id), ['tab6'])
        """)

    def test_short_module_expansion_is_env_gated(self):
        builder = self.read("gaokao-proxy/lib/report-builder.js")
        server = self.read("gaokao-proxy/server.js")

        self.assertIn("skipExpansion", server)
        self.assertIn("skipExpansion: Boolean(skipExpansion)", server)
        self.assertIn("skipExpansion = false", builder)
        self.assertIn("REPORT_AUTO_EXPAND_SHORT_MODULES", builder)
        self.assertIn("process.env.REPORT_AUTO_EXPAND_SHORT_MODULES === 'true'", builder)
        self.assertIn("REPORT_AUTO_EXPAND_SHORT_MODULES && !skipExpansion", builder)
        self.assertIn("REPORT_ENFORCE_MODULE_LENGTH", builder)
        self.assertIn("process.env.REPORT_ENFORCE_MODULE_LENGTH === 'true'", builder)

        self.run_node_test(r"""
            const prompt = buildReportExpansionPrompt({
              conclusions: [],
              modules: [{ id: 'tab3', title: '专业匹配分析', blocks: [] }]
            }, [{ id: 'tab3', title: '专业匹配分析', chars: 300, min: 1000 }])

            assert.equal(prompt.includes('固定 HTML 模板的数据 JSON'), true)
            assert.equal(prompt.includes('tab3 专业匹配分析：当前 300，最低 1000'), true)
        """)

    def test_report_text_renderer_splits_paragraphs_and_emphasizes_labels(self):
        self.run_node_test(r"""
            const text = '核心判断：适合优先看计算机类和电子信息类。风险提醒：如果数学基础薄弱，要先核验课程难度。行动建议：先看培养方案，再看近三年就业质量报告。'
            const html = renderReadableText(text)

            assert.equal(html.includes('<p>'), true)
            assert.equal((html.match(/<p>/g) || []).length >= 2, true)
            assert.equal(html.includes('<strong>核心判断：</strong>'), true)
            assert.equal(html.includes('<strong>风险提醒：</strong>'), true)
            assert.equal(html.includes('<strong>行动建议：</strong>'), true)
            assert.equal(html.includes('<script>'), false)

            const reportHtml = buildFinalHtml({
              conclusions: [],
              modules: [{
                id: 'tab1',
                title: '总览',
                summary: text,
                blocks: [{ type: 'text', title: '重点', content: text }]
              }]
            }, { province: '广东' }, {})

            assert.equal(reportHtml.includes('readableParagraphs'), true)
            assert.equal(reportHtml.includes('v-html="formatInlineText(paragraph)"'), true)
            assert.equal(reportHtml.includes('print-readable-text'), true)
        """)

    def test_normalize_and_humanize_report_copy_remove_ai_flavored_labels(self):
        self.run_node_test(r"""
            const raw = '<h2>AI 总评</h2><p>作为AI，我建议先了解更多信息。</p><p>大模型认为需要谨慎。</p>'
            const html = normalizeReportHtml(raw)
            const copy = humanizeReportCopy(raw)

            assert.equal(html.includes('AI 总评'), false)
            assert.equal(html.includes('作为AI'), false)
            assert.equal(html.includes('大模型认为'), false)
            assert.equal(copy.includes('顾问结论'), true)
            assert.equal(copy.includes('建议判断'), true)
        """)

    def test_report_prompt_uses_compact_assessment_results_without_five_ring_answers(self):
        builder = self.read("gaokao-proxy/lib/report-builder.js")
        self.assertIn("fetchMajorReports({})", builder)
        self.assertIn("buildPrompt(profile, messages, majorReports, univData, assessments)", builder)
        self.assertNotIn("fetchMajorReports(questionnaire)", builder)

        script = textwrap.dedent(f"""
            const assert = require('node:assert/strict')
            const buildPrompt = require('{ROOT / "gaokao-proxy" / "lib" / "prompts" / "report-template.js"}')

            const prompt = buildPrompt(
              {{ province: '广东', category: '物理类', score: 600 }},
              [],
              [],
              {{ recommendations: [], reports: [] }},
              {{
                mbti: {{
                  completed: true,
                  type: 'INTJ',
                  report: {{
                    name: '建筑师',
                    tags: ['独立', '战略'],
                    traits: ['富有想象力和战略性的思考者'],
                    careers: ['软件架构师'],
                    majors: ['计算机科学与技术']
                  }}
                }},
                holland: {{
                  completed: true,
                  code: 'RIA',
                  scores: {{ R: 20, I: 30, A: 10, S: 25, E: 15, C: 22 }},
                  indicators: [
                    {{ type: 'I', label: '研究型', score: 30 }},
                    {{ type: 'S', label: '社会型', score: 25 }},
                    {{ type: 'C', label: '常规型', score: 22 }}
                  ]
                }}
              }}
            )

            assert.equal(prompt.includes('【问卷答案（五环框架）】'), false)
            assert.equal(prompt.includes('先理解原理，再做题'), false)
            assert.equal(prompt.includes('Q1='), false)
            assert.equal(prompt.includes('MBTI 测评结果：INTJ 型（建筑师）'), true)
            assert.equal(prompt.includes('核心标签：独立、战略'), true)
            assert.equal(prompt.includes('霍兰德职业兴趣：RIA 型'), true)
            assert.equal(prompt.includes('I研究型=30'), true)
          """)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt-test.js"
            path.write_text(script, encoding="utf-8")
            subprocess.run(["node", str(path)], check=True, capture_output=True, text=True)

    def test_report_prompt_localizes_2025_score_context_to_university_module(self):
        script = textwrap.dedent(f"""
            const assert = require('node:assert/strict')
            const buildPrompt = require('{ROOT / "gaokao-proxy" / "lib" / "prompts" / "report-template.js"}')

            const prompt = buildPrompt(
              {{ province: '广东', category: '物理类', score: 600, rank: 21000 }},
              [],
              [],
              {{
                recommendations: [
                  {{
                    bucket: '稳',
                    school_name: '广东工业大学',
                    major_name: '计算机类',
                    batch: '本科批',
                    min_score: 598,
                    min_rank: 21500,
                    year: 2025
                  }}
                ],
                reports: []
              }},
              {{}}
            )

            assert.equal(prompt.includes('2026 年 6 月至 7 月'), true)
            assert.equal(prompt.includes('2025 年录取分数线已经可作为核心历史参考'), true)
            assert.equal(prompt.includes('服务端已经固定 HTML 页面格式'), true)
            assert.equal(prompt.includes('Tab 5 院校研究核心依据'), true)
            assert.equal(prompt.includes('稳 | 广东工业大学 | 计算机类 | 本科批 | 2025年最低598分 | 位次21500 | 分差-2'), true)
            assert.equal(prompt.includes('冲稳保候选池只约束 Tab 5'), true)
            assert.equal(prompt.includes('不要让冲稳保分数线挤占 Tab 1-4'), true)
            assert.equal(prompt.includes('不得把 2025 年历史录取线表述为 2026 年最终录取线'), true)
          """)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt-2025-score-context-test.js"
            path.write_text(script, encoding="utf-8")
            subprocess.run(["node", str(path)], check=True, capture_output=True, text=True)

    def test_report_prompt_branches_by_score_state(self):
        script = textwrap.dedent(f"""
            const assert = require('node:assert/strict')
            const buildPrompt = require('{ROOT / "gaokao-proxy" / "lib" / "prompts" / "report-template.js"}')

            assert.equal(buildPrompt.classifyReportMode({{ province: '广东', category: '物理类', score: 600 }}), 'official')
            assert.equal(buildPrompt.classifyReportMode({{ province: '广东', category: '物理类', planning_mode: 'score', score_type: 'estimated', score: 560 }}), 'estimated')
            assert.equal(buildPrompt.classifyReportMode({{ province: '广东', category: '物理类', planning_mode: 'early' }}), 'planning')

            const officialPrompt = buildPrompt(
              {{ province: '广东', category: '物理类', score: 600 }},
              [],
              [],
              {{ recommendations: [{{ school_name: '中山大学', min_score: 600 }}], reports: [] }},
              {{}}
            )
            assert.equal(officialPrompt.includes('2025 年结构化冲稳保候选池'), true)
            assert.equal(officialPrompt.includes('Tab 5 可围绕候选池学校做院校定位'), true)

            const estimatedPrompt = buildPrompt(
              {{ province: '广东', category: '物理类', planning_mode: 'score', score_type: 'estimated', score: 560 }},
              [],
              [],
              {{ recommendations: [], reports: [] }},
              {{}}
            )
            assert.equal(estimatedPrompt.includes('预估分数'), true)
            assert.equal(estimatedPrompt.includes('不是分数预测产品'), true)
            assert.equal(estimatedPrompt.includes('不要反复用校准提醒打断报告'), true)
            assert.equal(estimatedPrompt.includes('专业适配、孩子画像、家庭约束'), true)

            const planningPrompt = buildPrompt(
              {{ province: '广东', category: '物理类', planning_mode: 'early', grade: '高二', identity: '家长' }},
              [],
              [],
              {{ recommendations: [], reports: [] }},
              {{}}
            )
            assert.equal(planningPrompt.includes('出分后、家长和考生集中填报志愿的关键阶段'), false)
            assert.equal(planningPrompt.includes('院校层次认知与后续校准策略'), true)
            assert.equal(planningPrompt.includes('严禁输出精确冲稳保院校排序'), true)
          """)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt-mode-test.js"
            path.write_text(script, encoding="utf-8")
            subprocess.run(["node", str(path)], check=True, capture_output=True, text=True)

    def test_pdf_generator_runtime_style_uses_print_layout_v4(self):
        text = self.read("gaokao-proxy/lib/pdf-generator.js")

        self.assertIn("const PDF_GENERATOR_VERSION = 'print-layout-v4'", text)
        self.assertIn("await page.emulateMediaType('print')", text)
        self.assertIn("preferCSSPageSize: true", text)
        self.assertIn(".tab-pane,", text)
        self.assertIn(".tab-content,", text)
        self.assertIn("display: block !important;", text)
        self.assertIn("#app [style*=\"display: none\"]", text)

    def test_request_deep_seek_json_rejects_empty_choices(self):
        builder = self.read("gaokao-proxy/lib/report-builder.js")
        # Verify the null-check guard exists
        self.assertIn("data?.choices?.[0]?.message?.content", builder)
        self.assertIn("DeepSeek 返回空内容", builder)


if __name__ == "__main__":
    unittest.main()
