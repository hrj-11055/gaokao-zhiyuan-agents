# 大学评估报告数据清洗 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write a Python script to automatically extract trailing JSON data from Markdown university evaluation reports, save them separately, and use Gemini 2.5 Flash to intelligently remove uncertainty markers from the remaining text without altering the core semantics or structure.

**Architecture:** A single, self-contained Python script (`scripts/clean_university_reports.py`) will orchestrate the process. It will: 1) Find all `.md` files in `data/大学评估报告/`; 2) Create backups; 3) Use regex to separate the "Module 9" JSON block from the main body; 4) Save the JSON; 5) Call the `google-genai` SDK to process the main body text, removing markers like `[待核实]`; 6) Overwrite the original `.md` file with the cleaned content.

**Tech Stack:** Python 3, `google-genai` SDK, `pathlib`, `re`, `shutil`, `json`.

---

### Task 1: Setup Environment and Basic Script Structure

**Files:**
- Modify: `requirements.txt`
- Create: `scripts/clean_university_reports.py`

- [ ] **Step 1: Ensure required libraries are in `requirements.txt`**

Check if `google-genai` is in `requirements.txt`. If not, add it.

```bash
# Add to requirements.txt if not present
echo "google-genai>=0.1.0" >> requirements.txt
pip install -r requirements.txt
```

- [ ] **Step 2: Create the script skeleton with CLI args and logging**

```python
# scripts/clean_university_reports.py
import argparse
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Clean university evaluation reports.")
    parser.add_argument("--test", action="store_true", help="Run in test mode (only process 1-2 files).")
    args = parser.parse_args()

    data_dir = Path("data/大学评估报告")
    if not data_dir.exists():
        logger.error(f"Directory not found: {data_dir}")
        return

    logger.info(f"Starting cleanup. Test mode: {args.test}")
    # TODO: Implement backup and processing

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt scripts/clean_university_reports.py
git commit -m "feat(cleanup): add script skeleton and requirements"
```

---

### Task 2: Implement Backup and Directory Setup

**Files:**
- Modify: `scripts/clean_university_reports.py`

- [ ] **Step 1: Implement the backup logic**

Update the `main` function to create backups and the target JSON directory.

```python
# Insert into main() after checking if data_dir exists:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"data/report-cleaning-backups/univ-reports-{timestamp}")
    json_dir = Path("data/大学评估报告_json")

    backup_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    md_files = list(data_dir.glob("*.md"))
    if args.test:
        md_files = md_files[:2] # Just take the first two for testing

    logger.info(f"Found {len(md_files)} files to process. Backing up...")
    
    for file_path in md_files:
        shutil.copy2(file_path, backup_dir / file_path.name)
        
    logger.info(f"Backup completed to {backup_dir}")
```

- [ ] **Step 2: Commit**

```bash
git add scripts/clean_university_reports.py
git commit -m "feat(cleanup): implement backup and directory setup"
```

---

### Task 3: Implement JSON Extraction (Regex-based)

**Files:**
- Modify: `scripts/clean_university_reports.py`

- [ ] **Step 1: Add the extraction function**

Add a function to separate the main text from the JSON block.

```python
# Add before main()
def extract_json_block(content: str) -> tuple[str, str | None]:
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
```

- [ ] **Step 2: Integrate extraction into the main loop**

```python
# Update main() loop:
    import json
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
             
        # Temporarily save the markdown back (without AI cleaning yet)
        with open(file_path, 'w', encoding='utf-8') as f:
             f.write(md_text)
```

- [ ] **Step 3: Test the extraction logic**

Run the script in test mode to verify it copies files, extracts JSON, and removes the section.
```bash
python scripts/clean_university_reports.py --test
```

- [ ] **Step 4: Commit**

```bash
git add scripts/clean_university_reports.py
git commit -m "feat(cleanup): implement regex-based JSON extraction"
```

---

### Task 4: Implement LLM Cleaning (Gemini 2.5 Flash)

**Files:**
- Modify: `scripts/clean_university_reports.py`

- [ ] **Step 1: Add the Gemini cleaning function**

```python
# Add imports at the top
import time
from google import genai
from google.genai import types

# Add function before main()
def clean_markdown_with_llm(text: str) -> str:
    """Uses Gemini to remove uncertainty markers while preserving flow."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
         logger.warning("GEMINI_API_KEY not set. Skipping LLM cleaning.")
         return text
         
    client = genai.Client()
    
    prompt = """你是一个专业的文字编辑。请帮我清洗以下 Markdown 报告中的临时标记。
1. 删除所有类似 `[待核实]`, `[未检索到]`, `未确定`, `[部分待核实]` 等表示数据不确定的标签词汇。
2. 如果删除标记导致句子不通顺（例如表格中的某项仅剩一个单独的括号，或“来源：”后无内容），请做语义顺滑处理（如改为“暂无数据”或直接删除该行无意义内容）。
3. 绝对不能修改原文的其他实质性内容、核心数据和 Markdown 格式结构（表格必须保持对齐）。
4. 如果原文包含类似 ‘8.2 未检索到数据清单’ 这种整块都是说明“没找到数据”的章节，请直接将该小节及内容整体删除。
只返回清洗后的Markdown文本，不要有任何额外的解释或开头语。

待处理文本如下：
"""
    
    # We might need to handle large files. Gemini 2.5 Flash context window is huge (1M+), 
    # so we can send the whole file, but it's good practice to set safety settings.
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, text],
            config=types.GenerateContentConfig(
                 temperature=0.1, # Low temperature for consistent editing
            )
        )
        if response.text:
             # Remove markdown codeblock wrappers if the model adds them
             cleaned_text = response.text.strip()
             if cleaned_text.startswith("```markdown"):
                  cleaned_text = cleaned_text[11:]
             if cleaned_text.startswith("```"):
                  cleaned_text = cleaned_text[3:]
             if cleaned_text.endswith("```"):
                  cleaned_text = cleaned_text[:-3]
             return cleaned_text.strip()
        else:
             logger.error("LLM returned empty response.")
             return text
    except Exception as e:
         logger.error(f"LLM API Error: {e}")
         return text
```

- [ ] **Step 2: Integrate LLM cleaning into the main loop**

```python
# Update the saving part of the main() loop:

        # Replace:
        # # Temporarily save the markdown back (without AI cleaning yet)
        # with open(file_path, 'w', encoding='utf-8') as f:
        #      f.write(md_text)
        
        # With:
        logger.info(f"  -> Sending to Gemini for cleaning...")
        cleaned_md_text = clean_markdown_with_llm(md_text)
        
        with open(file_path, 'w', encoding='utf-8') as f:
             f.write(cleaned_md_text)
             
        # Add a small delay to avoid rate limits if processing many files
        time.sleep(2)
```

- [ ] **Step 3: Run the full test**

Ensure `GEMINI_API_KEY` is exported in the terminal.
```bash
python scripts/clean_university_reports.py --test
```
Inspect the output files in `data/大学评估报告/` to ensure `[待核实]` is gone, JSON is removed, and formatting is intact.

- [ ] **Step 4: Commit**

```bash
git add scripts/clean_university_reports.py
git commit -m "feat(cleanup): integrate Gemini 2.5 Flash for semantic cleaning"
```
