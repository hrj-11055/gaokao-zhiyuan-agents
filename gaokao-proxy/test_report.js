require('dotenv').config();
const { generateReport, saveReport } = require('./lib/report-builder');
const mockProfile = { province: '广东', category: '理科', score: '620', rank: '15000' };
const mockAssessments = { holland: { scores: { R: 25, I: 35, A: 10, S: 15, E: 20, C: 30 } } };

async function main() {
  try {
    const html = await generateReport({
      profile: mockProfile,
      questionnaire: { q1: "喜欢专研", q2: "不善交际" },
      assessments: mockAssessments,
      conversationId: "test_convo",
      difyApiUrl: "http://127.0.0.1",
      difyApiKey: "test_key"
    });
    const file = await saveReport("test_user_new", html);
    console.log("Report generated:", file);
  } catch (err) {
    console.error(err);
  }
}
main();
