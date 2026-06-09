import re
import subprocess
import tempfile
import textwrap
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProfileStorageAndInputsTests(unittest.TestCase):
    def run_node_test(self, module_source: str, imports: str, test_body: str):
        with tempfile.TemporaryDirectory() as tmp:
            module_path = Path(tmp) / "module.mjs"
            test_path = Path(tmp) / "test.mjs"
            module_path.write_text(module_source, encoding="utf-8")
            test_path.write_text(
                textwrap.dedent(f"""
                    import assert from 'node:assert/strict'
                    {imports}

                    {test_body}
                """),
                encoding="utf-8",
            )

            subprocess.run(["node", str(test_path)], check=True, text=True, capture_output=True)

    def run_node_script(self, script: str):
        subprocess.run(
            ["node", "-e", script],
            check=True,
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    def test_user_profile_is_saved_loaded_and_checked(self):
        source = (ROOT / "gaokao-miniprogram" / "src" / "utils" / "storage.js").read_text(encoding="utf-8")

        self.run_node_test(
            source,
            "import { saveUserProfile, loadUserProfile, normalizeUserProfile, isProfileComplete, buildProfileInputs, getProfileReportMode } from './module.mjs'",
            """
            const storage = new Map()
            globalThis.uni = {
              getStorageSync(key) {
                return storage.get(key) || ''
              },
              setStorageSync(key, value) {
                storage.set(key, value)
              }
            }
            Date.now = () => 1710000000000

            assert.equal(isProfileComplete({ province: '广东', category: '物理类', score: 600 }), true)
            assert.equal(isProfileComplete({ province: '广东', category: '物理类' }), false)
            assert.equal(isProfileComplete({ province: '广东', category: '物理类', planning_mode: 'early' }), true)
            assert.equal(isProfileComplete({ province: '广东', category: '物理类', planning_mode: 'score', score_type: 'estimated', score: 560 }), true)
            assert.equal(isProfileComplete({ province: '广东', category: '物理类', planning_mode: 'score', score_type: 'estimated' }), false)

            const early = normalizeUserProfile({
              province: '广东',
              category: '物理类',
              planning_mode: 'early',
              grade: '高二',
              identity: '家长',
              score_range: '520-560'
            })
            assert.deepEqual(
              {
                planning_mode: early.planning_mode,
                score_type: early.score_type,
                grade: early.grade,
                identity: early.identity,
                score_range: early.score_range,
                report_mode: getProfileReportMode(early)
              },
              {
                planning_mode: 'early',
                score_type: '',
                grade: '高二',
                identity: '家长',
                score_range: '520-560',
                report_mode: 'planning'
              }
            )
            assert.deepEqual(buildProfileInputs(early), {
              province: '广东',
              category: '物理类',
              planning_mode: 'early',
              score_range: '520-560',
              grade: '高二',
              identity: '家长',
              report_mode: 'planning'
            })

            const earlyWithEstimatedScore = normalizeUserProfile({
              province: '广东',
              category: '物理类',
              planning_mode: 'early',
              grade: '高二',
              score: 550
            })
            assert.equal(getProfileReportMode(earlyWithEstimatedScore), 'planning')
            assert.deepEqual(buildProfileInputs(earlyWithEstimatedScore), {
              province: '广东',
              category: '物理类',
              planning_mode: 'early',
              grade: '高二',
              score: '550',
              report_mode: 'planning'
            })

            saveUserProfile({
              province: '广东',
              category: '物理类',
              planning_mode: 'score',
              score_type: 'estimated',
              score: '600',
              rank: '32000',
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机',
              region_preference: '优先广东和长三角',
              career_goal: '优先高薪，能接受考研'
            })

            assert.deepEqual(loadUserProfile(), {
              nickname: '',
              province: '广东',
              category: '物理类',
              planning_mode: 'score',
              score_type: 'estimated',
              score_range: '',
              grade: '',
              identity: '',
              score: 600,
              rank: 32000,
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机',
              region_preference: '优先广东和长三角',
              career_goal: '优先高薪，能接受考研',
              updatedAt: 1710000000000
            })
            assert.deepEqual(buildProfileInputs(loadUserProfile()), {
              province: '广东',
              category: '物理类',
              planning_mode: 'score',
              report_mode: 'estimated',
              score_type: 'estimated',
              score: '600',
              rank: '32000',
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机',
              region_preference: '优先广东和长三角',
              career_goal: '优先高薪，能接受考研'
            })
            """.replace("1710000000000", str(1710000000000)),
        )

    def test_clear_all_local_data_removes_profile_identity(self):
        source = (ROOT / "gaokao-miniprogram" / "src" / "utils" / "storage.js").read_text(encoding="utf-8")

        self.run_node_test(
            source,
            "import { clearAllLocalData } from './module.mjs'",
            """
            const removedKeys = []
            globalThis.uni = {
              removeStorageSync(key) {
                removedKeys.push(key)
              }
            }

            clearAllLocalData()

            assert.equal(removedKeys.includes('profile_identity'), true)
            """,
        )

    def test_dify_stream_request_includes_profile_inputs(self):
        source = (ROOT / "gaokao-miniprogram" / "src" / "api" / "dify.js").read_text(encoding="utf-8")
        source = re.sub(
            r"import \{ API_BASE \} from '../config\.js'",
            "const API_BASE = 'http://localhost:3001'",
            source,
        )
        source = re.sub(
            r"import \{ requestBackend \} from './backend\.js'",
            "async function requestBackend() { return { statusCode: 200, data: {} } }",
            source,
        )
        source = re.sub(
            r"import \{ getStoredSession \} from './membership\.js'",
            "function getStoredSession() { return { sessionToken: '' } }",
            source,
        )

        self.run_node_test(
            source,
            "import { sendMessageStream } from './module.mjs'",
            """
            let requestPayload = null
            globalThis.uni = {
              request(options) {
                requestPayload = options.data
                return {
                  onChunkReceived() {},
                  abort() {}
                }
              }
            }

            sendMessageStream({
              query: '帮我推荐学校',
              conversationId: '',
              user: 'user_1',
              inputs: { province: '广东', category: '物理类', score: '600', rank: '32000' },
              onChunk() {},
              onEnd() {},
              onError() {}
            })

            assert.deepEqual(requestPayload.inputs, {
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000'
            })
            """,
        )

    def test_profile_followup_asks_one_field_at_a_time(self):
        source = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "profileFollowup.js").read_text(encoding="utf-8")

        self.run_node_test(
            source,
            "import { buildCandidateQuestions, containsProfileFollowupQuestion, getNextCoreProfileFollowup, getNextPersonalProfileFollowup, getNextRecommendationProfileFollowup, isCoreProfileField, isRecommendationIntent, mergeFollowupAnswer, mergeProfileFactsFromText } from './module.mjs'",
            """
            assert.equal(isRecommendationIntent('帮我推荐几所稳妥的学校'), true)
            assert.equal(isRecommendationIntent('你好'), false)
            assert.equal(isRecommendationIntent('中山大学在广东录取线是多少'), false)
            assert.equal(isRecommendationIntent('物理类更适合工科还是理科？'), false)
            assert.equal(isRecommendationIntent('按我广东物理类600分，适合什么学校层次？'), true)

            const province = getNextCoreProfileFollowup({})
            assert.equal(province.field, 'province')
            assert.equal(/科类|分数|家庭|兴趣|地域|考研|考公/.test(province.question), false)

            const category = getNextCoreProfileFollowup({ province: '广东' })
            assert.equal(category.field, 'category')
            assert.equal(/分数|家庭|兴趣|地域|考研|考公/.test(category.question), false)

            const score = getNextCoreProfileFollowup({ province: '广东', category: '物理类' })
            assert.equal(score.field, 'score')
            assert.equal(/家庭|兴趣|地域|考研|考公/.test(score.question), false)

            assert.equal(getNextCoreProfileFollowup({ province: '广东', category: '物理类', planning_mode: 'early', report_mode: 'planning' }), null)
            assert.equal(getNextCoreProfileFollowup({ province: '广东', category: '物理类', score: '600' }), null)

            const rank = getNextPersonalProfileFollowup({ province: '广东', category: '物理类', score: '600' })
            assert.equal(rank.field, 'rank')
            assert.equal(/家庭|兴趣|地域|考研|考公/.test(rank.question), false)
            assert.deepEqual(mergeFollowupAnswer({}, 'rank', '位次32000'), { rank: 32000 })

            const earlyPersonal = getNextPersonalProfileFollowup({
              province: '广东',
              category: '物理类',
              planning_mode: 'early',
              report_mode: 'planning',
              grade: '高二'
            })
            assert.equal(earlyPersonal.field, 'family_resources')
            assert.equal(/全省位次|同分段/.test(earlyPersonal.question), false)

            const firstRecommendationProfile = getNextRecommendationProfileFollowup({
              province: '广东',
              category: '物理类',
              score: '600'
            })
            assert.equal(firstRecommendationProfile.field, 'family_resources')
            assert.equal(/全省位次|同分段/.test(firstRecommendationProfile.question), false)

            const family = getNextPersonalProfileFollowup({ province: '广东', category: '物理类', score: '600', rank: '32000' })
            assert.equal(family.field, 'family_resources')
            assert.equal(/兴趣|地域|考研|考公/.test(family.question), false)
            assert.equal(
              containsProfileFollowupQuestion(
                '我再问一个关键问题：家里预算和资源大概是什么情况？比如能不能接受民办/中外合作，父母行业有没有能帮你实习就业的方向。',
                family
              ),
              true
            )
            assert.equal(
              containsProfileFollowupQuestion('先按已知分数给你一个冲稳保方向，不补充问题。', family),
              false
            )

            const interest = getNextPersonalProfileFollowup({
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000',
              family_resources: '家庭年收入30万，父母是老师和医生'
            })
            assert.equal(interest.field, 'interest_subjects')

            const region = getNextPersonalProfileFollowup({
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000',
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机'
            })
            assert.equal(region.field, 'region_preference')
            assert.equal(
              containsProfileFollowupQuestion('城市有没有硬要求？是优先省内，还是可以去外省？', region),
              true
            )

            const goal = getNextPersonalProfileFollowup({
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000',
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机',
              region_preference: '优先广东和长三角'
            })
            assert.equal(goal.field, 'career_goal')

            const done = getNextPersonalProfileFollowup({
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000',
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机',
              region_preference: '优先广东和长三角',
              career_goal: '优先高薪，能接受考研'
            })
            assert.equal(done, null)
            assert.equal(isCoreProfileField('score'), true)
            assert.equal(isCoreProfileField('family_resources'), false)

            assert.deepEqual(mergeFollowupAnswer({}, 'province', ' 广东省 '), { province: '广东' })
            assert.deepEqual(mergeFollowupAnswer({}, 'category', '物理'), { category: '物理类' })
            assert.deepEqual(mergeFollowupAnswer({}, 'score', '600分，位次32000'), { score: 600, rank: 32000 })
            assert.deepEqual(
              mergeFollowupAnswer({}, 'career_goal', '优先高薪，能接受考研'),
              { career_goal: '优先高薪，能接受考研' }
            )

            assert.deepEqual(
              mergeProfileFactsFromText({}, '我是广东考生，物理类，考了580分').profile,
              { province: '广东', category: '物理类', score: 580 }
            )
            assert.deepEqual(
              mergeProfileFactsFromText({ province: '广东', category: '物理类', score: 610 }, '我改成历史类，我考了580').profile,
              { province: '广东', category: '历史类', score: 580 }
            )
            assert.deepEqual(
              mergeProfileFactsFromText({ province: '广东', category: '物理类', score: 610 }, '位次32000').profile,
              { province: '广东', category: '物理类', score: 610, rank: 32000 }
            )

            const questions = buildCandidateQuestions({
              province: '广东',
              category: '物理类',
              score: 600,
              family_resources: '能接受公办，民办要谨慎'
            })
            assert.equal(questions.length, 4)
            assert.ok(questions.some((question) => question.includes('广东') && question.includes('600分')))
            assert.ok(questions.some((question) => question.includes('踩坑')))
            assert.ok(questions.some((question) => question.includes('怎么排序')))
            assert.ok(questions.some((question) => question.includes('3 条报考路线')))
            assert.ok(questions.some((question) => question.includes('热门专业')))
            assert.equal(questions.some((question) => /工科还是理科|补充哪些个人信息/.test(question)), false)

            const earlyQuestions = buildCandidateQuestions({
              province: '广东',
              category: '物理类',
              planning_mode: 'early',
              grade: '高二',
              identity: '家长'
            })
            assert.equal(earlyQuestions.length, 4)
            assert.ok(earlyQuestions.some((question) => question.includes('优先验证')))
            assert.ok(earlyQuestions.some((question) => question.includes('真实体验')))
            assert.ok(earlyQuestions.some((question) => question.includes('能力')))
            assert.ok(earlyQuestions.some((question) => question.includes('行动清单')))
            assert.equal(earlyQuestions.some((question) => /分数|位次|冲稳保|能上什么学校/.test(question)), false)
            """,
        )

    def test_chat_automatically_updates_profile_from_user_message(self):
        use_chat = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js").read_text(encoding="utf-8")

        self.assertIn("mergeProfileFactsFromText", use_chat)
        self.assertIn("applyProfileFactsFromText(text", use_chat)
        self.assertIn("syncProfileWhenReady(updatedProfile)", use_chat)

    def test_proxy_profile_gate_only_blocks_missing_core_fields(self):
        gate_path = str(ROOT / "gaokao-proxy" / "lib" / "profile-followup-gate.js")
        script = f"""
        const assert = require('node:assert/strict')
        const {{ buildProfileGateAnswer }} = require({json.dumps(gate_path)})

        assert.equal(buildProfileGateAnswer({{ query: '你好', inputs: {{}} }}), null)

        const province = buildProfileGateAnswer({{ query: '帮我推荐学校', inputs: {{}} }})
        assert.equal(province.metadata.profile_gate, true)
        assert.equal(province.metadata.field, 'province')
        assert.equal(/科类|分数|家庭|兴趣|地域|考研|考公/.test(province.answer), false)

        const completeCore = buildProfileGateAnswer({{
          query: '帮我推荐学校',
          inputs: {{ province: '广东', category: '物理类', score: '600' }}
        }})
        assert.equal(completeCore, null)

        const earlyPlanning = buildProfileGateAnswer({{
          query: '帮我推荐学校',
          inputs: {{
            province: '广东',
            category: '物理类',
            planning_mode: 'early',
            report_mode: 'planning',
            grade: '高二'
          }}
        }})
        assert.equal(earlyPlanning, null)

        const afterOnePersonalField = buildProfileGateAnswer({{
          query: '帮我推荐学校',
          inputs: {{
            province: '广东',
            category: '物理类',
            score: '600',
            family_resources: '家庭年收入30万，父母是老师和医生'
          }}
        }})
        assert.equal(afterOnePersonalField, null)

        const done = buildProfileGateAnswer({{
          query: '帮我推荐学校',
          inputs: {{
            province: '广东',
            category: '物理类',
            score: '600',
            family_resources: '家庭年收入30万，父母是老师和医生',
            interest_subjects: '喜欢数学和计算机',
            region_preference: '优先广东和长三角',
            career_goal: '优先高薪，能接受考研'
          }}
        }})
        assert.equal(done, null)
        """

        self.run_node_script(script)

    def test_chat_send_uses_fresh_stored_profile_inputs(self):
        text = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js").read_text(encoding="utf-8")

        self.assertIn("loadUserProfile", text)
        self.assertIn("buildProfileInputs", text)
        self.assertIn("getNextCoreProfileFollowup", text)
        self.assertIn("getNextPersonalProfileFollowup", text)
        self.assertIn("getNextRecommendationProfileFollowup", text)
        self.assertIn("containsProfileFollowupQuestion", text)
        self.assertIn("appendPostAnswerFollowup", text)
        self.assertIn("pendingQuery && isRecommendationIntent(pendingQuery)", text)
        self.assertIn("AI 正文已经问过同一个画像问题", text)
        self.assertIn("isCoreProfileField", text)
        self.assertIn("pendingProfileField", text)
        self.assertIn("pendingRecommendationQuery", text)
        self.assertIn("const freshProfile = loadUserProfile()", text)
        self.assertIn("const profileInputs = buildProfileInputs(freshProfile)", text)
        self.assertIn("inputs: profileInputs", text)
        self.assertNotIn("!hasAnyPersonalProfileInput(profileInputs)", text)

    def test_proxy_preserves_planning_mode_inputs(self):
        server = (ROOT / "gaokao-proxy" / "server.js").read_text(encoding="utf-8")

        self.assertIn("inputs.planning_mode", server)
        self.assertIn("inputs.report_mode", server)
        self.assertIn("inputs.score_type", server)
        self.assertIn("'score_range'", server)
        self.assertIn("'grade'", server)
        self.assertIn("'identity'", server)

    def test_chat_page_blocks_input_until_core_profile_is_complete(self):
        chat_page = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue").read_text(encoding="utf-8")
        use_chat = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js").read_text(encoding="utf-8")

        self.assertIn("isProfileComplete", chat_page)
        self.assertIn("const isProfileReady = computed(() => isProfileComplete(profile.value))", chat_page)
        self.assertIn("v-if=\"!isProfileReady\"", chat_page)
        self.assertIn("基础资料可以先不填正式分数", chat_page)
        self.assertIn("showWelcomeSuggestions", chat_page)
        self.assertIn("messages.value.length === 0 && isProfileReady.value", chat_page)
        self.assertIn(":disabled=\"isStreaming || !isProfileReady\"", chat_page)
        self.assertIn("!isProfileReady", chat_page)
        self.assertNotIn("请先补全省份、科类和分数", chat_page)

        self.assertIn("if (!isProfileComplete(loadUserProfile()))", use_chat)
        self.assertIn("请先补充基础资料", use_chat)

    def test_home_page_uses_light_parent_planning_workbench(self):
        home = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "index" / "index.vue").read_text(encoding="utf-8")

        self.assertIn("规划进度", home)
        self.assertIn("成绩/预估成绩", home)
        self.assertIn("提前规划", home)
        self.assertIn("预估分数区间", home)
        self.assertIn("无分数看专业规划，有分数看院校定位", home)
        self.assertIn("calc(92rpx + env(safe-area-inset-top))", home)
        self.assertIn("width: 104rpx; height: 104rpx", home)
        self.assertIn("selectPlanningMode", home)
        self.assertIn("selectScoreType", home)
        self.assertNotIn("progress-card.ready", home)
        self.assertNotIn("请补全省份、科类和分数", home)

    def test_home_profile_sheet_uses_province_picker(self):
        home = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "index" / "index.vue").read_text(encoding="utf-8")

        self.assertIn("<picker", home)
        self.assertIn('mode="selector"', home)
        self.assertIn(":range=\"PROVINCE_OPTIONS\"", home)
        self.assertIn("@change=\"selectProvince\"", home)
        self.assertIn("provincePickerIndex", home)
        self.assertIn("province-picker", home)
        self.assertNotIn('v-model.trim="draft.province" class="field-input" placeholder="例如：广东"', home)

    def test_chat_guides_multi_round_answers_to_personality_test(self):
        chat_page = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue").read_text(encoding="utf-8")
        guide = (ROOT / "gaokao-miniprogram" / "src" / "components" / "PersonalityAssessmentGuide.vue").read_text(encoding="utf-8")
        trigger = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "personalityAssessmentGuide.js").read_text(encoding="utf-8")

        self.assertIn("showWelcomeSuggestions", chat_page)
        self.assertIn('v-if="index === personalityGuideMessageIndex"', chat_page)
        self.assertIn("findPersonalityGuideMessageIndex", chat_page)
        self.assertIn("loadAssessments", chat_page)
        self.assertIn("assessments.value.mbti.completed", chat_page)
        self.assertIn("PERSONALITY_GUIDE_LONG_ANSWER_MIN_ROUND = 3", trigger)
        self.assertIn("PERSONALITY_GUIDE_LONG_ANSWER_MIN_LENGTH = 500", trigger)
        self.assertIn("PERSONALITY_GUIDE_FALLBACK_ROUND = 6", trigger)
        self.assertIn("message.truncated", trigger)
        self.assertIn("去做性格测试", guide)
        self.assertIn("稍后再说", guide)
        self.assertIn("uni.navigateTo({ url: '/pages/mbti/mbti' })", chat_page)
        self.assertIn("suggestion-panel", chat_page)
        self.assertIn("从关键决策开始", chat_page)
        self.assertIn("messages.value.length === 0 && isProfileReady.value", chat_page)
        self.assertNotIn("shouldShowSuggestionsAfterMessage", chat_page)
        self.assertNotIn("建议下一问", chat_page)
        self.assertNotIn("<!-- Chips -->", chat_page)
        self.assertNotIn("v-if=\"messages.length === 0 && isProfileReady\"", chat_page)

    def test_chat_resets_dify_conversation_when_profile_inputs_change(self):
        chat_store = (ROOT / "gaokao-miniprogram" / "src" / "stores" / "chat.js").read_text(encoding="utf-8")
        use_chat = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js").read_text(encoding="utf-8")

        self.assertIn("profileInputsKey", chat_store)
        self.assertIn("setProfileInputsKey", chat_store)
        self.assertIn("const profileInputsKey = getProfileInputsKey(profileInputs)", use_chat)
        self.assertIn("chatStore.conversationId = ''", use_chat)
        self.assertIn("chatStore.setProfileInputsKey(profileInputsKey)", use_chat)
        self.assertIn("planning_mode: inputs.planning_mode || ''", use_chat)
        self.assertIn("score_type: inputs.score_type || ''", use_chat)
        self.assertIn("score_range: inputs.score_range || ''", use_chat)
        self.assertIn("report_mode: inputs.report_mode || ''", use_chat)
        self.assertIn("family_resources: inputs.family_resources || ''", use_chat)
        self.assertIn("career_goal: inputs.career_goal || ''", use_chat)

    def test_proxy_forwards_chat_inputs_to_dify(self):
        text = (ROOT / "gaokao-proxy" / "server.js").read_text(encoding="utf-8")

        self.assertIn("inputs = {}", text)
        self.assertIn("inputs: finalInputs", text)
        self.assertIn("buildProfileGateAnswer", text)
        self.assertIn("buildRecommendationGuidedQuery", text)
        self.assertIn("query: guidedQuery", text)

    def test_proxy_guides_recommendation_answers_to_include_reason_risk_next_step(self):
        gate_path = str(ROOT / "gaokao-proxy" / "lib" / "profile-followup-gate.js")
        script = f"""
        const assert = require('node:assert/strict')
        const {{
          buildProfileGateAnswer,
          buildDeepProfileGateAnswer,
          buildPostAnswerFollowupInstruction,
          buildRecommendationGuidedQuery,
          buildSchoolScoreGuidedQuery,
          buildStarterGuidanceAnswer,
          classifyScoreQuestion,
          extractProfileInputsFromText,
          extractSchoolScoreLookup,
          formatSchoolScoreContext,
          isRecommendationIntent,
          isStarterGuidanceIntent,
          normalizeScoreApiCategory,
          shouldUseScoreContext
        }} = require({json.dumps(gate_path)})

        assert.equal(classifyScoreQuestion('中山大学在广东录取线是多少'), 'direct_score_lookup')
        assert.equal(classifyScoreQuestion('广东600分物理类能上什么学校'), 'score_context')
        assert.equal(classifyScoreQuestion('物理类更适合工科还是理科？'), 'score_context')
        assert.equal(classifyScoreQuestion('什么是平行志愿？'), 'general_advice')
        assert.equal(shouldUseScoreContext('物理类更适合工科还是理科？'), true)
        assert.equal(isRecommendationIntent('物理类更适合工科还是理科？'), false)
        assert.equal(normalizeScoreApiCategory('山东', '物理类'), '综合')
        assert.equal(normalizeScoreApiCategory('浙江省', '历史类'), '综合')
        assert.equal(normalizeScoreApiCategory('广东', '理科'), '物理类')
        assert.equal(normalizeScoreApiCategory('广东', '历史类'), '历史类')

        const guided = buildRecommendationGuidedQuery('帮我推荐几所学校')
        assert.match(guided, /为什么推荐/)
        assert.match(guided, /风险点/)
        assert.match(guided, /下一步/)
        assert.match(guided, /先回答/)
        assert.match(guided, /最低分\\/位次/)
        assert.match(guided, /后端分数线查询结果/)
        assert.match(guided, /必须完整收尾/)
        assert.match(guided, /现在是 2026 年 6 月/)
        assert.match(guided, /2026 年高考生/)
        assert.match(guided, /2025 年后端分数线/)

        const directionGuided = buildRecommendationGuidedQuery('物理类更适合工科还是理科？', {{
          inputs: {{
            province: '广东',
            category: '物理类',
            score: '600',
            family_resources: '普通家庭',
            interest_subjects: '数学和物理还可以',
            region_preference: '优先广东',
            career_goal: '就业和考研兼顾'
          }},
          scoreContext: '查询条件：广东 物理类 600分，年份 2025\\n稳1. 华东理工大学：610分，最低位次 20036，专业：计算机类; 电子信息类'
        }})
        assert.match(directionGuided, /不一定是在要最终冲稳保名单/)
        assert.match(directionGuided, /先精准回答原问题/)
        assert.match(directionGuided, /稳1\\. 华东理工大学/)
        assert.match(directionGuided, /用户原问题：物理类更适合工科还是理科/)

        assert.equal(
          buildProfileGateAnswer({{
            query: '广东600分物理类能上什么学校',
            inputs: {{ province: '广东', category: '物理类', score: '600' }}
          }}),
          null
        )
        const deepGate = buildDeepProfileGateAnswer({{
          query: '广东600分物理类能上什么学校',
          inputs: {{ province: '广东', category: '物理类', score: '600' }}
        }})
        assert.equal(deepGate.metadata.deep_profile_gate, true)
        assert.equal(deepGate.metadata.field, 'family_resources')
        assert.match(deepGate.answer, /先别急着直接排冲稳保/)
        assert.doesNotMatch(deepGate.answer, /全省位次/)

        const earlyDeepGate = buildDeepProfileGateAnswer({{
          query: '帮我推荐学校',
          inputs: {{
            province: '广东',
            category: '物理类',
            planning_mode: 'early',
            report_mode: 'planning',
            grade: '高二'
          }}
        }})
        assert.equal(earlyDeepGate.metadata.field, 'family_resources')
        assert.match(earlyDeepGate.answer, /提前升学规划/)
        assert.doesNotMatch(earlyDeepGate.answer, /分数|位次|冲稳保/)

        const readyForRecommendation = buildDeepProfileGateAnswer({{
          query: '广东600分物理类能上什么学校',
          inputs: {{
            province: '广东',
            category: '物理类',
            score: '600',
            family_resources: '公办优先，民办谨慎',
            interest_subjects: '喜欢数学和计算机',
            region_preference: '广东和长三角',
            career_goal: '优先就业薪资'
          }}
        }})
        assert.equal(readyForRecommendation, null)
        assert.equal(
          buildProfileGateAnswer({{
            query: '我考了600分能上什么学校',
            inputs: {{ score: '600' }}
          }}).metadata.field,
          'province'
        )

        const followup = buildPostAnswerFollowupInstruction({{
          province: '广东',
          category: '物理类',
          score: '600'
        }})
        assert.match(followup, /回答完用户当前问题后/)
        assert.match(followup, /全省位次/)

        const earlyFollowup = buildPostAnswerFollowupInstruction({{
          province: '广东',
          category: '物理类',
          planning_mode: 'early',
          report_mode: 'planning',
          grade: '高二'
        }})
        assert.match(earlyFollowup, /家里预算和资源/)
        assert.doesNotMatch(earlyFollowup, /全省位次/)

        const guidedWithInputs = buildRecommendationGuidedQuery('广东600分物理类能上什么学校', {{
          inputs: {{ province: '广东', category: '物理类', score: '600' }},
          scoreContext: '稳1. 山东大学：609分，最低位次 16821'
        }})
        assert.match(guidedWithInputs, /稳1\\. 山东大学/)
        assert.match(guidedWithInputs, /全省位次/)

        assert.deepEqual(
          extractProfileInputsFromText('四川530分理科能报什么？位次大概65000'),
          {{ province: '四川', category: '物理类', score: '530', rank: '65000' }}
        )
        assert.deepEqual(
          extractProfileInputsFromText('广东历史类580分推荐学校'),
          {{ province: '广东', category: '历史类', score: '580' }}
        )
        assert.equal(buildRecommendationGuidedQuery('你好，我想咨询高考志愿'), '你好，我想咨询高考志愿')
        assert.notEqual(buildRecommendationGuidedQuery('四川530分理科能报什么？'), '四川530分理科能报什么？')
        assert.equal(isStarterGuidanceIntent('你好，我想咨询高考志愿'), true)
        assert.equal(isStarterGuidanceIntent('广东600分物理类能上什么学校'), false)
        const starter = buildStarterGuidanceAnswer({{
          inputs: {{ province: '广东', category: '物理类', score: '600' }}
        }})
        assert.equal(starter.metadata.starter_guidance, true)
        assert.match(starter.answer, /你不用会提问/)
        assert.match(starter.answer, /专业排雷/)

        const earlyStarter = buildStarterGuidanceAnswer({{
          inputs: {{
            province: '广东',
            category: '物理类',
            planning_mode: 'early',
            report_mode: 'planning',
            grade: '高二'
          }}
        }})
        assert.match(earlyStarter.answer, /提前升学规划/)
        assert.doesNotMatch(earlyStarter.answer, /分数和位次|冲稳保/)

        const earlyGuided = buildRecommendationGuidedQuery('帮我推荐学校', {{
          inputs: {{
            province: '广东',
            category: '物理类',
            planning_mode: 'early',
            report_mode: 'planning',
            grade: '高二'
          }}
        }})
        assert.match(earlyGuided, /提前升学规划/)
        assert.match(earlyGuided, /不能输出精确冲稳保/)
        assert.match(earlyGuided, /年级：高二/)
        assert.doesNotMatch(earlyGuided, /2026 年高考生/)
        assert.doesNotMatch(earlyGuided, /每个关键推荐必须包含/)

        assert.deepEqual(
          extractSchoolScoreLookup('中山大学在广东录取线是多少', {{}}),
          {{ schoolName: '中山大学', province: '广东' }}
        )
        assert.deepEqual(
          extractSchoolScoreLookup('山东大学在广东物理类分数线是多少', {{}}),
          {{ schoolName: '山东大学', province: '广东' }}
        )

        const schoolContext = formatSchoolScoreContext({{
          school: '中山大学',
          province: '广东',
          majors: [
            {{ year: 2024, category: '物理类', major_name: '计算机类', min_score: 644, min_rank: 3982, avg_score: 646 }}
          ],
          total: 1
        }}, {{ schoolName: '中山大学', province: '广东', year: 2024 }})
        const schoolGuided = buildSchoolScoreGuidedQuery('中山大学在广东录取线是多少', schoolContext)
        assert.match(schoolGuided, /后端学校分数线查询结果/)
        assert.match(schoolGuided, /计算机类：最低分 644/)
        assert.match(schoolGuided, /最低位次 3982/)
        """

        self.run_node_script(script)

    def test_commerce_store_saves_and_loads_normalized_profile(self):
        store_path = str(ROOT / "gaokao-proxy" / "lib" / "commerce-store.js")
        script = f"""
        const assert = require('node:assert/strict')
        const {{ createCommerceStore }} = require({json.dumps(store_path)})
        const store = createCommerceStore({{
          dbPath: ':memory:',
          now: () => 1710000000000,
          idFactory: (prefix) => `${{prefix}}_fixed`,
        }})

        const user = store.upsertWechatUser({{ openid: 'openid_1' }})
        const saved = store.saveProfile(user.userId, {{
          province: ' 广东 ',
          category: '物理类',
          score: '600',
          rank: '32000',
        }})

        assert.deepEqual(saved, {{
          province: '广东',
          category: '物理类',
          planning_mode: 'score',
          score_type: 'official',
          score_range: '',
          grade: '',
          identity: '',
          score: 600,
          rank: 32000,
          family_resources: '',
          interest_subjects: '',
          region_preference: '',
          career_goal: '',
          updatedAt: 1710000000000,
        }})
        assert.deepEqual(store.getProfile(user.userId), saved)
        assert.throws(
          () => store.saveProfile(user.userId, {{ province: '广东', category: '物理类' }}),
          /score is invalid/
        )
        store.close()
        """

        self.run_node_script(script)

    def test_proxy_exposes_profile_routes_and_merges_server_profile_inputs(self):
        text = (ROOT / "gaokao-proxy" / "server.js").read_text(encoding="utf-8")

        self.assertIn("app.post('/api/profile'", text)
        self.assertIn("app.get('/api/profile'", text)
        self.assertIn("function mergeProfileInputs", text)
        self.assertIn("const finalInputs = mergeProfileInputs", text)
        self.assertIn("inputs: finalInputs", text)

    def test_miniprogram_syncs_profile_to_backend(self):
        api = (ROOT / "gaokao-miniprogram" / "src" / "api" / "membership.js").read_text(encoding="utf-8")
        store = (ROOT / "gaokao-miniprogram" / "src" / "stores" / "membership.js").read_text(encoding="utf-8")
        index = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "index" / "index.vue").read_text(encoding="utf-8")

        self.assertIn("saveUserProfileToServer", api)
        self.assertIn("fetchUserProfileFromServer", api)
        self.assertIn("async syncProfile(profile)", store)
        self.assertIn("membershipStore.syncProfile(profile.value)", index)

    def test_dify_config_documents_profile_initialization_gate(self):
        text = (ROOT / "docs" / "dify" / "agent-config-v1.md").read_text(encoding="utf-8")

        self.assertIn("Start 输入变量", text)
        self.assertIn("province", text)
        self.assertIn("category", text)
        self.assertIn("score", text)
        self.assertIn("rank", text)
        self.assertIn("信息完整性闸门", text)
        self.assertIn("禁止默认物理类", text)


if __name__ == "__main__":
    unittest.main()
