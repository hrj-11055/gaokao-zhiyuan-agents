import argparse
import logging
import os
import re
import shutil
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

from typing import Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_json_block(content: str) -> Tuple[str, Optional[str]]:
    """
    Separates the Markdown content from the trailing JSON block.
    Returns: (cleaned_markdown, json_content)
    """
    # Regex to match the section header and the json code block
    # Looking for something like: ## 模块九：结构化数据导出 (JSON)\n\n```json\n{...}\n```
    pattern = r"(##\s*模块九：结构化数据导出\s*\(JSON\).*?```json\s*)([\s\S]*?)(\s*```)"
    match = re.search(pattern, content, re.IGNORECASE)
    
    if match:
        json_content = match.group(2).strip()
        # Remove the entire Module 9 section from the markdown
        full_match = match.group(0)
        cleaned_markdown = content.replace(full_match, "").strip()
        return cleaned_markdown, json_content
    
    return content, None

def clean_markdown_with_llm(text: str) -> str:
    """Uses Gemini CLI to remove uncertainty markers while preserving flow."""
    prompt = f"""你是一个纯粹的文本处理管道，不具备对话能力。你的任务是接收 Markdown 文本并输出清洗后的文本，其他任何内容都不要输出。

处理规则：
1. 删除所有类似 `[待核实]`, `[未检索到]`, `未确定`, `[部分待核实]` 等表示数据不确定的标签词汇。
2. 如果删除标记导致句子不通顺（例如表格中的某项仅剩一个单独的括号，或“来源：”后无内容），请做语义顺滑处理（如改为“暂无数据”或直接删除该行无意义内容）。
3. 绝对不能修改原文的其他实质性内容、核心数据和 Markdown 格式结构（表格必须保持对齐）。
4. 如果原文包含类似 ‘8.2 未检索到数据清单’ 这种整块都是说明“没找到数据”的章节，请直接将该小节标题及下方的内容整体删除。

【极其重要】：
你的输出将被直接写入文件。你必须**只输出**清洗后的 Markdown 文本。
绝对不要输出任何开头语、解释、总结或类似 "I have completed cleaning" / "Here is the cleaned markdown" 的废话。
绝对不要省略正文内容。保留所有的长篇大论。

待处理文本如下：
====================
{text}
====================
"""
    
    try:
        # Save prompt to a temporary file
        temp_prompt_file = "tmp_clean_prompt.txt"
        with open(temp_prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        # Call Gemini CLI
        result = subprocess.run(
            ["gemini", "-p", f"@{temp_prompt_file}", "--model", "gemini-2.5-flash", "-o", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Clean up temp file
        if os.path.exists(temp_prompt_file):
            os.remove(temp_prompt_file)

        if result.stdout:
            try:
                # The CLI outputs JSON containing the response
                parsed_output = json.loads(result.stdout)
                cleaned_text = parsed_output.get("response", "").strip()
            except json.JSONDecodeError:
                # Fallback if it's not JSON for some reason
                cleaned_text = result.stdout.strip()
                
            # Remove markdown codeblock wrappers if the model adds them
            if cleaned_text.startswith("```markdown"):
                cleaned_text = cleaned_text[11:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
                
            return cleaned_text.strip()
        else:
             logger.error("Gemini CLI returned empty response.")
             return text
    except subprocess.CalledProcessError as e:
         logger.error(f"Gemini CLI Error: {e.stderr}")
         if os.path.exists(temp_prompt_file):
            os.remove(temp_prompt_file)
         return text
    except Exception as e:
         logger.error(f"Unexpected Error: {e}")
         if os.path.exists(temp_prompt_file):
            os.remove(temp_prompt_file)
         return text

def main():
    parser = argparse.ArgumentParser(description="Clean university evaluation reports.")
    parser.add_argument("--test", action="store_true", help="Run in test mode (only process 1-2 files).")
    args = parser.parse_args()

    data_dir = Path("data/大学评估报告")
    if not data_dir.exists():
        logger.error(f"Directory not found: {data_dir}")
        return

    logger.info(f"Starting cleanup. Test mode: {args.test}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"data/report-cleaning-backups/univ-reports-{timestamp}")
    json_dir = Path("data/大学评估报告_json")

    backup_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    md_files = [f for f in data_dir.glob("*.md") if f.name != "CLAUDE.md" and not f.name.startswith("_")]
    if args.test:
        # Specifically test on known files like 三峡大学.md
        test_files = [data_dir / "三峡大学.md", data_dir / "三峡大学科技学院.md"]
        md_files = [f for f in test_files if f.exists()]

    logger.info(f"Found {len(md_files)} files to process. Backing up...")
    
    for file_path in md_files:
        shutil.copy2(file_path, backup_dir / file_path.name)
        
    logger.info(f"Backup completed to {backup_dir}")

    for file_path in md_files:
        logger.info(f"Processing {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        md_text, json_str = extract_json_block(content)
        
        if json_str:
            json_file_path = json_dir / f"{file_path.stem}.json"
            try:
                # Parse and re-dump to ensure it's valid JSON and formatted nicely
                parsed_json = json.loads(json_str)
                with open(json_file_path, 'w', encoding='utf-8') as jf:
                    json.dump(parsed_json, jf, ensure_ascii=False, indent=2)
                logger.info(f"  -> Extracted JSON to {json_file_path.name}")
            except json.JSONDecodeError as e:
                logger.warning(f"  -> Failed to parse JSON in {file_path.name}: {e}")
                # Still save the raw string if parsing fails, but with a .txt extension to flag it
                with open(json_dir / f"{file_path.stem}_invalid_json.txt", 'w', encoding='utf-8') as jf:
                    jf.write(json_str)
        else:
             logger.info(f"  -> No JSON block found.")
             
        logger.info(f"  -> Sending to Gemini CLI for semantic cleaning...")
        cleaned_md_text = clean_markdown_with_llm(md_text)
        
        with open(file_path, 'w', encoding='utf-8') as f:
             f.write(cleaned_md_text)
             
        logger.info(f"  -> Saved cleaned file: {file_path.name}")

if __name__ == "__main__":
    main()
