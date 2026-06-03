#!/usr/bin/env python3
"""
Dify 知识库上传脚本 v2
支持多省份录取分数线数据上传到 Dify KB-2 知识库

功能：
  1. 登录 Dify Console 获取认证
  2. 查找或创建 KB-2 数据集
  3. 按省份上传录取分数线 Markdown 文件
  4. 大文件自动拆分（超过阈值按学校拆分）
  5. 支持增量上传（已存在的文档可跳过或覆盖）

用法：
  python3 data/upload_to_dify.py                          # 上传所有待上传的 kb2 文件
  python3 data/upload_to_dify.py --files kb2-scores-广东.md  # 只上传指定文件
  python3 data/upload_to_dify.py --dry-run                # 只检查不上传
  python3 data/upload_to_dify.py --status                 # 查看 Dify 知识库状态
"""

import argparse
import base64
import json
import os
import re
import sys
import time

import requests

# ============================================================
# 配置
# ============================================================

def require_env(name):
    value = os.environ.get(name)
    if not value:
        print(f"错误: 未设置环境变量 {name}")
        sys.exit(1)
    return value


DIFY_BASE = os.environ.get("DIFY_BASE", "http://159.75.110.157")
EMAIL = require_env("DIFY_EMAIL")
PASSWORD = require_env("DIFY_PASSWORD")

# 知识库配置
DATASETS = {
    "KB-1": {"name": "KB-1 张雪峰语料库", "id": "a6851f4b-4a6c-47af-a094-c37496560b81"},
    "KB-2": {"name": "KB-2 录取分数线",   "id": "bfd78007-f881-471a-8f35-d0df1d3967c9"},  # 自动创建或查找
    "KB-3": {"name": "KB-3 专业百科",     "id": "0294eb86-b602-4efb-aab7-ed726ca84adb"},
}

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge-base")

# 上传参数
MAX_FILE_SIZE_KB = 4500    # 单文件最大 KB（Dify 文档上限约 5MB）
CHUNK_SIZE = 500            # Dify 分块大小（tokens）
CHUNK_OVERLAP = 50          # 分块重叠
INDEXING_MODE = "economy"   # economy（经济）或 high_quality（高质量）


# ============================================================
# Dify Console API 封装
# ============================================================

class DifyClient:
    def __init__(self, base_url, email, password):
        self.base = base_url
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.csrf = None

    def login(self):
        """登录 Dify Console"""
        # 获取初始 cookies
        self.session.get(f"{self.base}/en/signin", timeout=10)

        # 登录
        encoded_pw = base64.b64encode(self.password.encode()).decode()
        resp = self.session.post(f"{self.base}/console/api/login", json={
            "email": self.email,
            "password": encoded_pw,
        }, timeout=10)

        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} {resp.text[:200]}")
            sys.exit(1)

        # 提取 CSRF token
        for cookie in self.session.cookies:
            if cookie.name == "csrf_token":
                self.csrf = cookie.value
                break
        if not self.csrf:
            print("No CSRF token found")
            sys.exit(1)

        self.session.headers.update({"X-Csrf-Token": self.csrf})
        print("Login OK")

    def list_datasets(self):
        """列出所有数据集"""
        datasets = []
        page = 1
        while True:
            resp = self.session.get(
                f"{self.base}/console/api/datasets",
                params={"page": page, "limit": 100},
                timeout=30,
            )
            if resp.status_code != 200:
                print(f"List datasets failed: {resp.status_code}")
                break
            data = resp.json()
            items = data.get("data", [])
            datasets.extend(items)
            if len(items) < 100:
                break
            page += 1
        return datasets

    def find_dataset(self, name):
        """按名称查找数据集"""
        datasets = self.list_datasets()
        for ds in datasets:
            if name in ds.get("name", ""):
                return ds["id"]
        return None

    def create_dataset(self, name):
        """创建新数据集"""
        resp = self.session.post(f"{self.base}/console/api/datasets", json={
            "name": name,
            "indexing_technique": INDEXING_MODE,
        }, timeout=30)

        if resp.status_code in (200, 201):
            ds = resp.json()
            print(f"Created dataset: {name} (id={ds['id']})")
            return ds["id"]
        else:
            print(f"Create dataset failed: {resp.status_code} {resp.text[:200]}")
            return None

    def list_documents(self, dataset_id):
        """列出数据集中的所有文档"""
        docs = []
        page = 1
        while True:
            resp = self.session.get(
                f"{self.base}/console/api/datasets/{dataset_id}/documents",
                params={"page": page, "limit": 100},
                timeout=30,
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            items = data.get("data", [])
            docs.extend(items)
            if len(items) < 100:
                break
            page += 1
        return docs

    def delete_document(self, dataset_id, document_id):
        """删除文档"""
        resp = self.session.delete(
            f"{self.base}/console/api/datasets/{dataset_id}/documents/{document_id}",
            timeout=30,
        )
        return resp.status_code == 200

    def upload_file(self, dataset_id, file_path, doc_name=None):
        """上传文件到数据集（Dify 1.13+ 两步流程）"""
        filename = doc_name or os.path.basename(file_path)

        # Step 1: 先上传文件到 /console/api/files/upload
        with open(file_path, "rb") as f:
            upload_resp = self.session.post(
                f"{self.base}/console/api/files/upload",
                files={"file": (filename, f, "text/markdown")},
                data={"source": "datasets"},
                timeout=300,
            )

        if upload_resp.status_code not in (200, 201):
            print(f"  File upload failed [{upload_resp.status_code}]: {upload_resp.text[:300]}")
            return False

        file_id = upload_resp.json().get("id")
        if not file_id:
            print(f"  No file_id in response: {upload_resp.text[:200]}")
            return False

        # Step 2: 用 file_id 创建文档
        doc_resp = self.session.post(
            f"{self.base}/console/api/datasets/{dataset_id}/documents",
            json={
                "data_source": {
                    "info_list": {
                        "data_source_type": "upload_file",
                        "file_info_list": {"file_ids": [file_id]},
                    },
                    "type": "upload_file",
                },
                "doc_form": "text_model",
                "indexing_technique": INDEXING_MODE,
                "process_rule": {
                    "mode": "automatic",
                    "rules": {
                        "pre_processing_rules": [
                            {"id": "remove_extra_spaces", "enabled": True},
                            {"id": "remove_urls_emails", "enabled": False},
                        ],
                        "segmentation": {
                            "separator": "\n##",
                            "max_tokens": CHUNK_SIZE,
                            "chunk_overlap": CHUNK_OVERLAP,
                        },
                    },
                },
            },
            timeout=60,
        )

        if doc_resp.status_code in (200, 201):
            print(f"  Uploaded: {filename} (file={file_id})")
            return True
        else:
            print(f"  Doc create failed [{doc_resp.status_code}]: {doc_resp.text[:300]}")
            return False


# ============================================================
# 文件处理
# ============================================================

def split_large_file(file_path, max_kb=MAX_FILE_SIZE_KB):
    """
    将大文件按 ## 标题拆分为多个小文件
    返回拆分后的文件路径列表
    """
    size_kb = os.path.getsize(file_path) / 1024
    if size_kb <= max_kb:
        return [file_path]

    print(f"  File too large ({size_kb:.0f}KB), splitting...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 按学校拆分（## 学校名 - 年份）
    parts = re.split(r"(?=\n## )", content)

    # 获取文件头（第一部分，包含 # 总标题和说明）
    header = ""
    school_parts = []
    for part in parts:
        if part.startswith("\n## ") or part.startswith("## "):
            school_parts.append(part)
        else:
            header = part

    # 合并为多个不超过限制的文件
    chunks = []
    current_chunk = header
    chunk_idx = 1
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    for part in school_parts:
        test = current_chunk + part
        if len(test.encode("utf-8")) / 1024 > max_kb and current_chunk != header:
            # 保存当前 chunk
            chunk_path = os.path.join(KB_DIR, f"{base_name}_part{chunk_idx}.md")
            with open(chunk_path, "w", encoding="utf-8") as f:
                f.write(current_chunk)
            chunks.append(chunk_path)
            chunk_idx += 1
            current_chunk = header + part
        else:
            current_chunk += part

    # 保存最后一个 chunk
    if current_chunk.strip() != header.strip():
        chunk_path = os.path.join(KB_DIR, f"{base_name}_part{chunk_idx}.md")
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(current_chunk)
        chunks.append(chunk_path)

    print(f"  Split into {len(chunks)} parts")
    return chunks


def get_kb2_files():
    """获取所有待上传的 KB-2 文件"""
    files = []
    if not os.path.exists(KB_DIR):
        return files
    for f in sorted(os.listdir(KB_DIR)):
        if f.startswith("kb2-scores-") and f.endswith(".md") and "_part" not in f:
            path = os.path.join(KB_DIR, f)
            size_kb = os.path.getsize(path) / 1024
            files.append((path, f, size_kb))
    return files


# ============================================================
# 命令：状态查看
# ============================================================

def cmd_status(client):
    """查看 Dify 知识库状态"""
    print("\n=== Dify 知识库状态 ===\n")

    datasets = client.list_datasets()
    print(f"数据集总数: {len(datasets)}\n")

    for ds in datasets:
        ds_id = ds["id"]
        ds_name = ds["name"]
        doc_count = ds.get("document_count", "?")

        # 匹配到已知 KB
        kb_tag = ""
        for kb_key, kb_info in DATASETS.items():
            if kb_info["id"] == ds_id or kb_info["name"] == ds_name:
                kb_tag = f" [{kb_key}]"
                # 更新缓存的 ID
                DATASETS[kb_key]["id"] = ds_id

        print(f"  {ds_name}{kb_tag}")
        print(f"    ID: {ds_id}")
        print(f"    文档数: {doc_count}")

        # 列出文档
        docs = client.list_documents(ds_id)
        if docs:
            for doc in docs[:10]:
                name = doc.get("name", "?")
                size = doc.get("word_count", 0)
                status = doc.get("indexing_status", "?")
                print(f"      - {name} ({size} words, {status})")
            if len(docs) > 10:
                print(f"      ... 还有 {len(docs) - 10} 个文档")
        print()

    # 本地待上传文件
    print("=== 本地待上传文件 ===\n")
    local_files = get_kb2_files()
    if local_files:
        for path, name, size in local_files:
            print(f"  {name}: {size:.0f}KB")
    else:
        print("  无 kb2-scores-*.md 文件")


# ============================================================
# 命令：上传
# ============================================================

def cmd_upload(client, specific_files=None, dry_run=False):
    """上传文件到 KB-2"""

    # 获取待上传文件
    if specific_files:
        files = []
        for fname in specific_files:
            path = os.path.join(KB_DIR, fname)
            if os.path.exists(path):
                size_kb = os.path.getsize(path) / 1024
                files.append((path, fname, size_kb))
            else:
                print(f"File not found: {fname}")
    else:
        files = get_kb2_files()

    if not files:
        print("No files to upload")
        return

    # 确保数据集存在
    kb2_id = DATASETS["KB-2"]["id"]
    if not kb2_id:
        kb2_id = client.find_dataset("KB-2")
    if not kb2_id:
        kb2_id = client.create_dataset("KB-2 录取分数线")
    if not kb2_id:
        print("Failed to get/create KB-2 dataset")
        return

    print(f"\nTarget dataset: KB-2 (id={kb2_id})")
    print(f"Files to upload: {len(files)}\n")

    if dry_run:
        for path, name, size in files:
            needs_split = size > MAX_FILE_SIZE_KB
            tag = " [需拆分]" if needs_split else ""
            print(f"  {name}: {size:.0f}KB{tag}")
        print("\n(dry run, no uploads)")
        return

    # 查看已有文档（避免重复）
    existing_docs = client.list_documents(kb2_id)
    existing_names = {doc.get("name", "") for doc in existing_docs}

    total = len(files)
    success = 0
    for i, (path, name, size) in enumerate(files):
        print(f"\n[{i+1}/{total}] {name} ({size:.0f}KB)")

        # 检查是否已存在
        if name in existing_names:
            print(f"  Already exists, skipping")
            success += 1
            continue

        # 处理大文件
        upload_files = split_large_file(path)

        for fpath in upload_files:
            fname = os.path.basename(fpath)
            ok = client.upload_file(kb2_id, fpath, doc_name=fname)
            if ok:
                success += 1
            time.sleep(2)

            # 清理临时拆分文件
            if fpath != path and os.path.exists(fpath):
                os.remove(fpath)

    print(f"\nDone! {success}/{total} files uploaded to KB-2")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="上传录取分数线数据到 Dify KB-2")
    parser.add_argument("--status", action="store_true", help="查看知识库状态")
    parser.add_argument("--files", nargs="+", help="只上传指定文件")
    parser.add_argument("--dry-run", action="store_true", help="只检查不上传")
    parser.add_argument("--recreate", action="store_true", help="重建 KB-2 数据集（删除旧的）")
    args = parser.parse_args()

    client = DifyClient(DIFY_BASE, EMAIL, PASSWORD)
    client.login()

    if args.status:
        cmd_status(client)
    else:
        cmd_upload(client, specific_files=args.files, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
