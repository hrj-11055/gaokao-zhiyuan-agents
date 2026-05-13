#!/usr/bin/env python3
"""将爬取的分数线数据上传到 Dify 知识库"""
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


DIFY_BASE = os.environ.get("DIFY_BASE", "http://8.135.37.159:8080")
# Dify Console 登录凭据
EMAIL = require_env("DIFY_EMAIL")
PASSWORD = require_env("DIFY_PASSWORD")
# 已有的 KB-1 和 KB-3 dataset IDs
KB1_DATASET_ID = "a6851f4b-4a6c-47af-a094-c37496560b81"  # 张雪峰语料
KB3_DATASET_ID = "0294eb86-b602-4efb-aab7-ed726ca84adb"  # 专业百科

OUTPUT_DIR = "/tmp/gaokao_scores"

def login():
    """登录 Dify Console 获取 cookies"""
    session = requests.Session()
    encoded_pw = base64.b64encode(PASSWORD.encode()).decode()

    # 先 GET login page 获取初始 cookies
    session.get(f"{DIFY_BASE}/en/signin", timeout=10)

    # 登录
    resp = session.post(f"{DIFY_BASE}/console/api/login", json={
        "email": EMAIL,
        "password": encoded_pw
    }, timeout=10)

    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text[:200]}")
        sys.exit(1)

    # 提取 CSRF token
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


def create_dataset(session, name):
    """创建新的知识库数据集"""
    resp = session.post(f"{DIFY_BASE}/console/api/datasets", json={
        "name": name,
        "indexing_technique": "economy",
    }, timeout=30)

    if resp.status_code == 200 or resp.status_code == 201:
        data = resp.json()
        dataset_id = data.get("id")
        print(f"Created dataset: {name} (id={dataset_id})")
        return dataset_id
    else:
        print(f"Failed to create dataset: {resp.status_code} {resp.text[:200]}")
        return None


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
    # 检查输出文件
    files = []
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".md"):
            path = os.path.join(OUTPUT_DIR, f)
            size_kb = os.path.getsize(path) / 1024
            files.append((path, f, size_kb))
            print(f"  {f}: {size_kb:.0f}KB")

    if not files:
        print("No score data files found in", OUTPUT_DIR)
        sys.exit(1)

    # 登录
    session = login()

    # 创建 KB-2 数据集
    kb2_id = create_dataset(session, "KB-2 录取分数线数据")
    if not kb2_id:
        print("Failed to create KB-2 dataset")
        sys.exit(1)

    # 上传所有文件
    for path, name, size in files:
        print(f"Uploading {name} ({size:.0f}KB)...")
        upload_document(session, kb2_id, path)
        time.sleep(2)

    print(f"\nDone! KB-2 dataset ID: {kb2_id}")
    print(f"Knowledge base IDs:")
    print(f"  KB-1 (张雪峰语料): {KB1_DATASET_ID}")
    print(f"  KB-2 (录取分数线): {kb2_id}")
    print(f"  KB-3 (专业百科):   {KB3_DATASET_ID}")


if __name__ == "__main__":
    main()
