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
            "import { saveUserProfile, loadUserProfile, isProfileComplete, buildProfileInputs } from './module.mjs'",
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

            saveUserProfile({
              province: '广东',
              category: '物理类',
              score: '600',
              rank: '32000',
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机',
              region_preference: '优先广东和长三角',
              career_goal: '优先高薪，能接受考研'
            })

            assert.deepEqual(loadUserProfile(), {
              province: '广东',
              category: '物理类',
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
              score: '600',
              rank: '32000',
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机',
              region_preference: '优先广东和长三角',
              career_goal: '优先高薪，能接受考研'
            })
            """.replace("1710000000000", str(1710000000000)),
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
            "import { containsProfileFollowupQuestion, getNextCoreProfileFollowup, getNextPersonalProfileFollowup, isCoreProfileField, isRecommendationIntent, mergeFollowupAnswer, mergeProfileFactsFromText } from './module.mjs'",
            """
            assert.equal(isRecommendationIntent('帮我推荐几所稳妥的学校'), true)
            assert.equal(isRecommendationIntent('你好'), false)

            const province = getNextCoreProfileFollowup({})
            assert.equal(province.field, 'province')
            assert.equal(/科类|分数|家庭|兴趣|地域|考研|考公/.test(province.question), false)

            const category = getNextCoreProfileFollowup({ province: '广东' })
            assert.equal(category.field, 'category')
            assert.equal(/分数|家庭|兴趣|地域|考研|考公/.test(category.question), false)

            const score = getNextCoreProfileFollowup({ province: '广东', category: '物理类' })
            assert.equal(score.field, 'score')
            assert.equal(/家庭|兴趣|地域|考研|考公/.test(score.question), false)

            assert.equal(getNextCoreProfileFollowup({ province: '广东', category: '物理类', score: '600' }), null)

            const family = getNextPersonalProfileFollowup({ province: '广东', category: '物理类', score: '600' })
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
              family_resources: '家庭年收入30万，父母是老师和医生'
            })
            assert.equal(interest.field, 'interest_subjects')

            const region = getNextPersonalProfileFollowup({
              province: '广东',
              category: '物理类',
              score: '600',
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
              family_resources: '家庭年收入30万，父母是老师和医生',
              interest_subjects: '喜欢数学和计算机',
              region_preference: '优先广东和长三角'
            })
            assert.equal(goal.field, 'career_goal')

            const done = getNextPersonalProfileFollowup({
              province: '广东',
              category: '物理类',
              score: '600',
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
            """,
        )

    def test_chat_automatically_updates_profile_from_user_message(self):
        use_chat = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js").read_text(encoding="utf-8")

        self.assertIn("mergeProfileFactsFromText", use_chat)
        self.assertIn("applyProfileFactsFromText(text", use_chat)
        self.assertIn("syncProfileWhenReady(updatedProfile)", use_chat)

    def test_proxy_profile_gate_returns_one_question_before_dify(self):
        gate_path = str(ROOT / "gaokao-proxy" / "lib" / "profile-followup-gate.js")
        script = f"""
        const assert = require('node:assert/strict')
        const {{ buildProfileGateAnswer }} = require({json.dumps(gate_path)})

        assert.equal(buildProfileGateAnswer({{ query: '你好', inputs: {{}} }}), null)

        const province = buildProfileGateAnswer({{ query: '帮我推荐学校', inputs: {{}} }})
        assert.equal(province.metadata.profile_gate, true)
        assert.equal(province.metadata.field, 'province')
        assert.equal(/科类|分数|家庭|兴趣|地域|考研|考公/.test(province.answer), false)

        const family = buildProfileGateAnswer({{
          query: '帮我推荐学校',
          inputs: {{ province: '广东', category: '物理类', score: '600' }}
        }})
        assert.equal(family, null)

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
        self.assertIn("containsProfileFollowupQuestion", text)
        self.assertIn("appendPostAnswerFollowup", text)
        self.assertIn("AI 正文已经问过同一个画像问题", text)
        self.assertIn("isCoreProfileField", text)
        self.assertIn("pendingProfileField", text)
        self.assertIn("pendingRecommendationQuery", text)
        self.assertIn("const freshProfile = loadUserProfile()", text)
        self.assertIn("const profileInputs = buildProfileInputs(freshProfile)", text)
        self.assertIn("inputs: profileInputs", text)

    def test_chat_page_blocks_input_until_core_profile_is_complete(self):
        chat_page = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "chat.vue").read_text(encoding="utf-8")
        use_chat = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js").read_text(encoding="utf-8")

        self.assertIn("isProfileComplete", chat_page)
        self.assertIn("const isProfileReady = computed(() => isProfileComplete(profile.value))", chat_page)
        self.assertIn("v-if=\"!isProfileReady\"", chat_page)
        self.assertIn("messages.length === 0 && isProfileReady", chat_page)
        self.assertIn(":disabled=\"isStreaming || !isProfileReady\"", chat_page)
        self.assertIn("!isProfileReady", chat_page)

        self.assertIn("if (!isProfileComplete(loadUserProfile()))", use_chat)
        self.assertIn("请先补全省份、科类和分数", use_chat)

    def test_chat_resets_dify_conversation_when_profile_inputs_change(self):
        chat_store = (ROOT / "gaokao-miniprogram" / "src" / "stores" / "chat.js").read_text(encoding="utf-8")
        use_chat = (ROOT / "gaokao-miniprogram" / "src" / "pages" / "chat" / "useChat.js").read_text(encoding="utf-8")

        self.assertIn("profileInputsKey", chat_store)
        self.assertIn("setProfileInputsKey", chat_store)
        self.assertIn("const profileInputsKey = getProfileInputsKey(profileInputs)", use_chat)
        self.assertIn("chatStore.conversationId = ''", use_chat)
        self.assertIn("chatStore.setProfileInputsKey(profileInputsKey)", use_chat)
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
        const {{ buildRecommendationGuidedQuery }} = require({json.dumps(gate_path)})

        assert.equal(buildRecommendationGuidedQuery('你好'), '你好')

        const guided = buildRecommendationGuidedQuery('帮我推荐几所学校')
        assert.match(guided, /为什么推荐/)
        assert.match(guided, /风险点/)
        assert.match(guided, /下一步/)
        assert.match(guided, /先回答/)
        assert.match(guided, /最多 3 个/)
        assert.match(guided, /必须完整收尾/)
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
