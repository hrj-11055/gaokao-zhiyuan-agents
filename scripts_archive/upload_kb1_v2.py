#!/usr/bin/env python3
"""通过 Dify Knowledge API 上传更新后的 KB-1 语料库"""

import requests
import os
import sys
import time
import json

def require_env(name):
    value = os.environ.get(name)
    if not value:
        print(f"错误: 未设置环境变量 {name}")
        sys.exit(1)
    return value


DIFY_BASE = os.environ.get("DIFY_BASE", "http://8.135.37.159:8080")
DATASET_TOKEN = require_env("DIFY_DATASET_TOKEN")
KB1_DATASET_ID = "a6851f4b-4a6c-47af-a094-c37496560b81"
KB1_FILE = os.path.join(os.path.dirname(__file__), "knowledge-base", "kb1-zhangxuefeng-corpus.md")


def list_documents():
    """列出数据集中的所有文档"""
    resp = requests.get(
        f"{DIFY_BASE}/v1/datasets/{KB1_DATASET_ID}/documents",
        headers={"Authorization": f"Bearer {DATASET_TOKEN}"},
        params={"page": 1, "limit": 50},
        timeout=30
    )
    if resp.status_code == 200:
        data = resp.json()
        docs = data.get("data", [])
        for doc in docs:
            print(f"  {doc.get('name')} (id={doc.get('id')}, words={doc.get('word_count', '?')})")
        return docs
    else:
        print(f"List failed: {resp.status_code} {resp.text[:200]}")
        return []


def delete_document(doc_id):
    """删除文档"""
    resp = requests.delete(
        f"{DIFY_BASE}/v1/datasets/{KB1_DATASET_ID}/documents/{doc_id}",
        headers={"Authorization": f"Bearer {DATASET_TOKEN}"},
        timeout=30
    )
    if resp.status_code == 200:
        print(f"  Deleted: {doc_id}")
        return True
    else:
        print(f"  Delete failed: {resp.status_code} {resp.text[:200]}")
        return False


def upload_document(file_path):
    """通过 Knowledge API 上传文件"""
    filename = os.path.basename(file_path)

    # Use the create_by_file endpoint
    data = {
        "data": json.dumps({
            "indexing_technique": "economy",
            "process_rule": {
                "mode": "automatic"
            }
        })
    }

    with open(file_path, "rb") as f:
        files = {
            "file": (filename, f, "text/markdown")
        }
        resp = requests.post(
            f"{DIFY_BASE}/v1/datasets/{KB1_DATASET_ID}/document/create_by_file",
            headers={"Authorization": f"Bearer {DATASET_TOKEN}"},
            data=data,
            files=files,
            timeout=120
        )

    if resp.status_code in (200, 201):
        result = resp.json()
        doc = result.get("document", {})
        print(f"  Uploaded: {filename} (id={doc.get('id')})")
        return True
    else:
        print(f"  Upload failed: {resp.status_code} {resp.text[:300]}")
        return False


def main():
    if not os.path.exists(KB1_FILE):
        print(f"KB-1 file not found: {KB1_FILE}")
        sys.exit(1)

    file_size = os.path.getsize(KB1_FILE) / 1024
    print(f"KB-1 file: {KB1_FILE} ({file_size:.0f}KB)")

    # 列出旧文档
    print(f"\nExisting documents in KB-1:")
    docs = list_documents()

    # 删除旧文档
    if docs:
        print(f"\nDeleting {len(docs)} old documents...")
        for doc in docs:
            delete_document(doc["id"])
            time.sleep(1)

    # 等待删除完成
    print("\nWaiting for deletion...")
    time.sleep(3)

    # 上传新文档
    print(f"\nUploading new KB-1 corpus...")
    if upload_document(KB1_FILE):
        print("\nKB-1 corpus updated successfully!")
    else:
        print("\nFailed to upload KB-1 corpus")
        sys.exit(1)

    # 验证
    print("\nVerifying...")
    time.sleep(2)
    docs = list_documents()
    if docs:
        print(f"\nDone! KB-1 now has {len(docs)} document(s)")
    else:
        print("\nWarning: No documents found after upload (indexing may still be in progress)")


if __name__ == "__main__":
    main()
