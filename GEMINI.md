# GEMINI.md - 高考志愿填报项目 (峰哥咨询参考)

本文件为 Gemini CLI 提供项目上下文、架构说明及操作指南。

## 1. 项目概述
「**峰哥咨询参考**」是一个基于 AI 的高考志愿填报咨询系统。它通过深度数据研究（专业/院校）、AI 智能体对话（Dify + DeepSeek/Gemini）以及标准化评估报告，为考生提供科学的填报建议。

### 核心价值流程 (六步法)
1. **个人特质分析**：生成「个人内在地图」。
2. **专业匹配分析**：筛选 10 个潜力专业。
3. **专业深度研究**：AI 量化评估（七大模块）。
4. **家庭战略会议**：提供沟通与决策指南。
5. **大学深度研究**：院校 360 度剖析（Citadel 计划）。
6. **最终决策报告**：生成最终排序与风险评估。

## 2. 技术架构
- **前端**: UniApp (Vue 3 + Vite + Sass)，编译为微信小程序 (`gaokao-miniprogram/`)。
- **后端代理**: Node.js Express (`gaokao-proxy/`)，负责请求转发、SSE 流式解析、限流及安全校验。
- **AI 引擎**: Dify (Docker 部署)，集成 DeepSeek-V3、Gemini、Claude 等模型。
- **数据层**: PostgreSQL (分数线数据) + Dify 知识库 (Markdown 语料)。
- **评估工具**: Python 3 脚本，用于自动化跑批生成专业/院校深度报告。

## 3. 关键目录与文件
- `gaokao-miniprogram/`: 微信小程序源码。
- `gaokao-proxy/`: 后端代理服务器。
- `data/`: 
  - `专业评估报告/`: 自动生成的专业深度研究报告。
  - `大学评估报告/`: 自动生成的院校评估报告。
  - `knowledge-base/`: Dify 知识库源文件 (Markdown)。
  - `本科专业目录_2025.csv`: 核心专业清单。
- `docs/`: PRD、技术设计及路线图。
- `tests/`: 回归测试用例。

## 4. 常用开发与评估命令

### 专业评估 (Claude/Gemini)
```bash
# 查看所有门类进度
python3 run_major_eval.py --status
# 跑指定门类 (如 06 历史学)
python3 run_major_eval.py 06
# 重跑失败项
python3 run_major_eval.py 06 --retry
```

### 院校评估 (Gemini 版)
```bash
# 跑指定省份所有本科院校
python3 run_univ_eval_gemini.py 广东省
# 仅跑指定大学
python3 run_univ_eval_gemini.py 广东省 --only 中山大学 华南理工大学
```

### 质检与数据处理
```bash
# 检查生成报告的完整性与字数
python3 check_reports.py --min-chars 3000
# 爬取录取分数线
python3 data/crawl_scores_v5.py --provinces 44
# 上传至 Dify 知识库
python3 data/upload_to_dify.py
```

### 前后端启动
```bash
# 小程序开发 (需安装依赖)
cd gaokao-miniprogram && npm run dev:mp-weixin
# 代理服务器启动
cd gaokao-proxy && npm run dev
```

## 5. 开发规范
- **Python**: 优先使用标准库。函数/变量使用 `snake_case`。路径操作使用 `pathlib`。
- **报告格式**: 专业报告命名为 `{专业代码}_{专业名称}.md`。必须符合 8 大模块输出要求。
- **SSE 通信**: 小程序与代理之间通过 SSE (Server-Sent Events) 实现流式对话。
- **安全性**: 严禁将 `.env` 或敏感 API 密钥提交至 Git。使用环境变量管理。

## 6. 当前阶段 (W3-W4)
- **W3 目标**: 补齐专业研究数据，启动全国院校大规模评估。
- **W4 核心**: MVP 端到端联调，实现「个人信息表单 -> 报告生成 -> 报告展示」闭环。

---
*注：本文件由 Gemini CLI 根据项目分析自动生成，更新于 2026-05-01。*
