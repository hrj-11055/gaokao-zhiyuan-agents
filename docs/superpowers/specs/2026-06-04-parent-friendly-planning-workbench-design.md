# Parent-Friendly Planning Workbench Design

Date: 2026-06-04
Product: 峰哥咨询参考 WeChat mini program
Scope: home workbench, profile intake, assessment result handoff, report readiness, parent-oriented experience framing

## Background

The current product flow is strongest for senior high school students who already have a Gaokao score. The target audience now needs to expand to parents, including parents of Grade 10 and Grade 11 students who want to understand majors, ability fit, and preparation direction before official scores are available.

The product should not split the homepage into separate modes. It should keep one planning workflow and let users choose their current stage when filling basic information.

## Product Positioning

The product remains a Gaokao advising reference tool, but it supports three score states:

- Official score: used for school positioning, major recommendations, risk reminders, and report generation.
- Estimated score: used for estimated positioning. The report may discuss school tiers and rough reach/match/safety direction, but must remind users to recalibrate after official score and rank are available.
- No score: used for early planning. The report must not promise precise school positioning. It should focus on major direction, student profile, ability gaps, learning path, score goals, and parent action items.

This keeps the overall process close to the Grade 12 flow while avoiding over-claiming when score data is missing.

## User Flow

The homepage shows a unified lightweight planning workbench. Users tap the basic information step and choose a profile mode inside the sheet:

- Score or estimated score: for users with an official score or a realistic estimated score.
- Early planning: for Grade 10, Grade 11, or families exploring before a stable score exists.

After saving basic information, all users continue through the same four-step flow:

1. Fill basic information.
2. Complete at least one AI consultation round.
3. Complete two assessments.
4. Generate a report.

The report output adapts to score state rather than forcing a separate homepage path.

## Basic Information Sheet

The sheet should feel like a natural intake step, not a hard gate.

Fields shared by both modes:

- Province.
- Subject category.
- Family goals or constraints.
- City or region preference.
- Interested or excluded subject/major directions, when available.

Score or estimated score mode:

- Score type selector: official score or estimated score.
- Score field.
- Rank field, optional.
- Copy should say that estimated-score reports need recalibration after official score/rank are released.

Early planning mode:

- Grade or identity, such as Grade 10 parent, Grade 11 parent, Grade 12 parent, or student.
- Estimated score range, optional.
- Score can be skipped.
- Copy should say that early planning reports focus on major direction and preparation path, not precise school positioning.

Completion logic:

- Official score and estimated score profiles are complete when province, category, and score are present.
- Early planning profiles are complete when province and category are present. Grade/identity is strongly encouraged but should not block continuation.
- A skipped score should not block chat, assessments, or early planning report generation.

## Home UI

Use a light workbench, not a heavy dashboard.

The first screen should include:

- Brand and short greeting.
- A shallow white progress module with thin border.
- Four tiny progress segments.
- Current step count, such as `第 1 / 4 步`.
- One next action, such as `先补充基础资料`.

Avoid dark hero cards, large dashboard visuals, and strong completion pressure. The desired feeling is that the workflow quietly supports the user.

The four home steps remain visible below the progress module. Each step should use light borders, small numbered marks, and concise copy:

- Basic information: `选择已有成绩、预估成绩或提前规划`.
- AI consultation: `把城市、预算、家庭期待说清楚`.
- Assessments: `补充分数之外的专业匹配依据`.
- Report: `无分数看专业规划，有分数看院校定位`.

## Assessment And Report Handoff

Assessment result pages should stay focused on the result content. They should not show a full workbench.

Use a low-presence next-step bar near the bottom:

- If only one assessment is done: `已完成 1/2 项测评，下一步：完成另一项测评`.
- If both assessments are done but report is not generated: `测评已完成，下一步：生成规划报告`.
- If report exists: `报告已生成，点击查看`.

The bar should look like navigation, not promotion. It should use a white or translucent background, subtle border, and a short action label.

The report page should align readiness with the same four-step logic rather than showing only the two-assessment percentage. This prevents confusion when the page says report readiness is high but profile or chat is still missing.

## Report Behavior

Report generation remains available for all completed profiles after the required consultation and assessments are done.

Report naming and content emphasis should adapt:

- Official score: `院校定位报告`.
- Estimated score: `预估定位报告`.
- No score: `专业规划报告`.

No-score reports should recommend majors and planning paths, not specific school positioning. Estimated-score reports may discuss school tier and rough positioning, with clear recalibration language.

## Parent Experience Map

Entry:
Parents arrive with anxiety and incomplete information. The homepage should feel calm and usable, not like a form that rejects them.

Basic information:
The first relief moment is discovering that official scores are not required. Parents can enter with an estimated score or no score.

Assessment:
The first peak moment is when results describe the child in a way that feels recognizable: strengths, interests, learning tendencies, and risk areas.

Consultation:
The product earns trust by accepting real family constraints such as city preference, budget sensitivity, stability expectations, and excluded paths.

Report:
The report gives different value depending on score state. With a score it helps position schools. Without a score it helps choose major directions and preparation priorities.

Return:
The product should invite parents back when official scores or ranks become available, so they can recalibrate from planning to positioning.

## Peak-End Rule

Peak:
The peak should happen in assessment results and the report opening. Parents should feel that the product understands the child beyond a score.

End:
The ending should not be a generic report close. It should provide the next concrete action:

- For early planning: what subject, ability, or exploration task to work on next.
- For estimated score: what information to verify after official score/rank release.
- For official score: what school/major risk to inspect next.

The final feeling should be: `I know what to do next`.

## Implementation Notes

Likely frontend touchpoints:

- `gaokao-miniprogram/src/utils/storage.js`: profile normalization and completion logic.
- `gaokao-miniprogram/src/composables/useHomeProgress.js`: progress state should use the updated profile completion semantics.
- `gaokao-miniprogram/src/pages/index/index.vue`: light workbench and profile sheet modes.
- `gaokao-miniprogram/src/pages/chat/chat.vue`: profile gate copy and readiness behavior should allow early planning profiles.
- `gaokao-miniprogram/src/pages/report/report.vue`: four-step readiness, adaptive report naming, and generation blocker copy.
- `gaokao-miniprogram/src/pages/mbti/mbti-result.vue`: low-presence next-step bar.
- `gaokao-miniprogram/src/pages/holland/holland-result.vue`: low-presence next-step bar.
- `gaokao-miniprogram/src/pages/profile/profile.vue`: profile summary should show score type or early planning state instead of assuming a score.

## Non-Goals

- Do not create a separate homepage for parents.
- Do not promise precise school positioning without score data.
- Do not remove the Grade 12 official-score workflow.
- Do not redesign the entire visual language of the mini program.
- Do not change membership pricing or entitlement logic in this design pass.

## Acceptance Criteria

- A parent can start with province and category only, continue to chat and assessments, and understand that the report will be planning-oriented.
- A parent with an estimated score can save it as estimated score and receive estimated-positioning copy rather than official-score copy.
- A Grade 12 user with official score can still follow the existing score-based path.
- The homepage workbench feels light and appears in the first screen.
- Assessment result pages tell users the next step without overwhelming the result content.
- Report readiness uses the same four-step model as the homepage.
