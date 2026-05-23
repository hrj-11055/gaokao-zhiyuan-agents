# Model Switch to Gemini Evaluation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run university evaluation for 内蒙古自治区 using `gemini-3.1-flash-lite-preview`.

**Architecture:** Utilize `run_univ_eval_gemini_cli.py` (which supports Gemini models) to conduct evaluation.

**Tech Stack:** Python 3, Gemini CLI / API tools.

---

### Task 1: Execution

- [ ] **Step 1: Set model environment variable**

Run: `export GEMINI_MODEL="gemini-3.1-flash-lite-preview"`

- [ ] **Step 2: Run evaluation for 内蒙古自治区**

Run: `python3 run_univ_eval_gemini_cli.py 内蒙古自治区`

- [ ] **Step 3: Verify logs and progress**

Run: `python3 run_univ_eval_gemini_cli.py --status`
