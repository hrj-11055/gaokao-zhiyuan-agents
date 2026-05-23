# University Research Reports Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute university research reports for 吉林省, 广西壮族自治区, and 黑龙江省 in the background and monitor their progress.

**Architecture:** Use `run_univ_eval_claude_cli.py` in three parallel background processes, each handling one province, with output redirected to log files in `logs/univ_eval/`.

**Tech Stack:** Python 3, Claude Code CLI, Bash.

---

### Task 1: Environment Preparation

**Files:**
- Create: `logs/univ_eval/`

- [ ] **Step 1: Create logs directory**

Run: `mkdir -p logs/univ_eval`

- [ ] **Step 2: Verify Claude CLI and Script**

Run: `claude --version && python3 run_univ_eval_claude_cli.py --status`
Expected: Claude version displayed and status table shown.

### Task 2: Launch Background Processes

**Files:**
- Modify: `logs/univ_eval/jilin.log` (stdout/stderr)
- Modify: `logs/univ_eval/guangxi.log` (stdout/stderr)
- Modify: `logs/univ_eval/heilongjiang.log` (stdout/stderr)

- [ ] **Step 1: Start process for 吉林省**

Run: `python3 run_univ_eval_claude_cli.py 吉林省 > logs/univ_eval/jilin.log 2>&1`
(is_background=true)

- [ ] **Step 2: Start process for 广西壮族自治区**

Run: `python3 run_univ_eval_claude_cli.py 广西壮族自治区 > logs/univ_eval/guangxi.log 2>&1`
(is_background=true)

- [ ] **Step 3: Start process for 黑龙江省**

Run: `python3 run_univ_eval_claude_cli.py 黑龙江省 > logs/univ_eval/heilongjiang.log 2>&1`
(is_background=true)

### Task 3: Monitoring and Verification

- [ ] **Step 1: Check background processes**

Run: `list_background_processes`

- [ ] **Step 2: Periodically check status**

Run: `python3 run_univ_eval_claude_cli.py --status`
Expected: Progress bars for Jilin, Guangxi, and Heilongjiang should start increasing over time.

- [ ] **Step 3: Check logs for errors**

Run: `tail -n 20 logs/univ_eval/*.log`
