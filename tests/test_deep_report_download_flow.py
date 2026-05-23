import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeepReportDownloadFlowTests(unittest.TestCase):
    def read(self, relpath):
        return (ROOT / relpath).read_text(encoding="utf-8")

    def test_report_data_client_uses_internal_data_api_with_token(self):
        script = textwrap.dedent(
            """
            const assert = require('assert')
            const {
              listReports,
              fetchReportDetail,
            } = require('./gaokao-proxy/lib/report-data-client')

            process.env.REPORT_DATA_API_URL = 'http://159.75.110.157/score-api'
            process.env.REPORT_DATA_API_TOKEN = 'secret-token'

            const calls = []
            global.fetch = async (url, options = {}) => {
              calls.push({ url, options })
              return {
                ok: true,
                status: 200,
                async json() {
                  if (url.includes('/majors/080901')) {
                    return { code: '080901', name: '计算机科学与技术' }
                  }
                  return { total: 1, data: [{ code: '080901', name: '计算机科学与技术' }] }
                },
              }
            }

            ;(async () => {
              const list = await listReports('major', { search: '计算机', page_size: 3 })
              assert.equal(list.total, 1)
              assert.equal(calls[0].url, 'http://159.75.110.157/score-api/api/reports/majors?search=%E8%AE%A1%E7%AE%97%E6%9C%BA&page_size=3')
              assert.equal(calls[0].options.headers['X-Report-Token'], 'secret-token')

              const detail = await fetchReportDetail('major', '080901')
              assert.equal(detail.name, '计算机科学与技术')
              assert.equal(calls[1].url, 'http://159.75.110.157/score-api/api/reports/majors/080901')
              assert.equal(calls[1].options.headers['X-Report-Token'], 'secret-token')
            })().catch((err) => {
              console.error(err)
              process.exit(1)
            })
            """
        )
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    def test_miniprogram_declares_deep_report_download_page_and_pdf_guards(self):
        pages = json.loads(self.read("gaokao-miniprogram/src/pages.json"))
        page_paths = [page["path"] for page in pages["pages"]]

        self.assertIn("pages/deep-report-download/deep-report-download", page_paths)

        report_page = self.read("gaokao-miniprogram/src/pages/report/report.vue")
        download_page = self.read("gaokao-miniprogram/src/pages/deep-report-download/deep-report-download.vue")

        self.assertIn("openDeepReportDownload", report_page)
        self.assertIn("application/pdf", report_page)
        self.assertIn("/api/reports/deep/pdf", download_page)
        self.assertIn("Authorization", download_page)
        self.assertIn("Bearer ${membershipStore.sessionToken}", download_page)
        self.assertIn("application/pdf", download_page)
        self.assertIn("5000 字以上完整报告", download_page)

    def test_gaokao_api_exposes_token_protected_report_endpoints(self):
        api = self.read("data/gaokao_api.py")

        for snippet in [
            "REPORT_API_TOKEN",
            "REPORT_PG_CONFIG",
            "require_report_token",
            '@app.route("/api/reports/health")',
            '@app.route("/api/reports/majors")',
            '@app.route("/api/reports/majors/<code>")',
            '@app.route("/api/reports/universities")',
            '@app.route("/api/reports/universities/<path:name>")',
            "gaokao_db",
        ]:
            self.assertIn(snippet, api)

    def test_proxy_routes_include_paid_deep_pdf_endpoint(self):
        server = self.read("gaokao-proxy/server.js")
        prompt = self.read("gaokao-proxy/lib/prompts/report-template.js")

        self.assertIn("/api/reports/deep/pdf", server)
        self.assertIn("requireMembershipForReports", server)
        self.assertIn("buildDeepReportHtml", server)
        self.assertIn("完整 5000 字以上 PDF", prompt)
        self.assertIn("深度报告下载页", prompt)


if __name__ == "__main__":
    unittest.main()
