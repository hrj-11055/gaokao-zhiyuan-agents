#!/usr/bin/env python3
"""上传更新后的 KB-1 张雪峰语料库到 Dify"""

import requests
import os
import sys
import time
import base64

def require_env(name):
    value = os.environ.get(name)
    if not value:
        print(f"错误: 未设置环境变量 {name}")
        sys.exit(1)
    return value


DIFY_BASE = os.environ.get("DIFY_BASE", "http://159.75.110.157")
EMAIL = require_env("DIFY_EMAIL")
PASSWORD = require_env("DIFY_PASSWORD")
KB1_DATASET_ID = "a6851f4b-4a6c-47af-a094-c37496560b81"
KB1_FILE = os.path.join(os.path.dirname(__file__), "knowledge-base", "kb1-zhangxuefeng-corpus.md")


def login():
    """登录 Dify Console"""
    session = requests.Session()
    encoded_pw = base64.b64encode(PASSWORD.encode()).decode()
    session.get(f"{DIFY_BASE}/en/signin", timeout=10)
    resp = session.post(f"{DIFY_BASE}/console/api/login", json={
        "email": EMAIL,
        "password": encoded_pw
    }, timeout=10)

    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text[:200]}")
        sys.exit(1)

    csrf = None
    for cookie in session.cookies:
        if cookie.name == "csrf_token":
            csrf = cookie.value
            break

    if not csrf:
        print("No CSRF token found")
        sys.exit(1)

    session.headers.update({"X-Csrf-Token": csrf})
    print("Login successful")
    return session


def list_documents(session, dataset_id):
    """列出数据集中的所有文档"""
    resp = session.get(
        f"{DIFY_BASE}/console/api/datasets/{dataset_id}/documents",
        params={"page": 1, "limit": 50},
        timeout=30
    )
    if resp.status_code == 200:
        data = resp.json()
        docs = data.get("data", [])
        for doc in docs:
            print(f"  Document: {doc.get('name')} (id={doc.get('id')})")
        return docs
    else:
        print(f"List documents failed: {resp.status_code}")
        return []


def delete_document(session, dataset_id, doc_id):
    """删除数据集中的文档"""
    resp = session.delete(
        f"{DIFY_BASE}/console/api/datasets/{dataset_id}/documents/{doc_id}",
        timeout=30
    )
    if resp.status_code == 200:
        print(f"  Deleted: {doc_id}")
        return True
    else:
        print(f"  Delete failed: {resp.status_code} {resp.text[:200]}")
        return False


def upload_document(session, dataset_id, file_path):
    """上传文件到数据集"""
    filename = os.path.basename(file_path)
    data = {
        "data": '{"indexing_technique": "economy", "process_rule": {"mode": "automatic"}, "doc_form": "text_model"}'
    }

    with open(file_path, "rb") as f:
        files = {
            "file": (filename, f, "text/markdown")
        }
        resp = session.post(
            f"{DIFY_BASE}/console/api/datasets/{dataset_id}/document/create_by_file",
            data=data,
            files=files,
            timeout=120
        )

    if resp.status_code in (200, 201):
        print(f"  Uploaded: {filename}")
        return True
    else:
        print(f"  Upload failed: {resp.status_code} {resp.text[:200]}")
        return False


def main():
    if not os.path.exists(KB1_FILE):
        print(f"KB-1 file not found: {KB1_FILE}")
        sys.exit(1)

    file_size = os.path.getsize(KB1_FILE) / 1024
    print(f"KB-1 file: {KB1_FILE} ({file_size:.0f}KB)")

    # 登录
    session = login()

    # 列出旧文档
    print(f"\nExisting documents in KB-1 ({KB1_DATASET_ID}):")
    docs = list_documents(session, KB1_DATASET_ID)

    # 删除旧文档
    if docs:
        print(f"\nDeleting {len(docs)} old documents...")
        for doc in docs:
            delete_document(session, KB1_DATASET_ID, doc["id"])
            time.sleep(1)

    # 等待删除完成
    print("\nWaiting for deletion to complete...")
    time.sleep(3)

    # 上传新文档
    print(f"\nUploading new KB-1 corpus...")
    if upload_document(session, KB1_DATASET_ID, KB1_FILE):
        print("\nKB-1 corpus updated successfully!")
    else:
        print("\nFailed to upload KB-1 corpus")
        sys.exit(1)

    print(f"\nDataset ID: {KB1_DATASET_ID}")


if __name__ == "__main__":
    main()
