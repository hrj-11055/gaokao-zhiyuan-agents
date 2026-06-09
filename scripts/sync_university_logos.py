#!/usr/bin/env python3
"""Sync cached university logos for reports already in the local library."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "data" / "大学评估报告_json_v2"
CACHE_DIR = ROOT / "gaokao-proxy" / "public" / "university-logos"
MANIFEST_PATH = CACHE_DIR / "manifest.json"
SCHOOL_NAME_URL = "https://static-data.gaokao.cn/www/2.0/school/name.json"
LOGO_URL = "https://static-data.gaokao.cn/upload/logo/{school_id}.jpg"


def normalize_name(name: str) -> str:
    return (
        str(name or "")
        .removeprefix("_")
        .replace("（", "(")
        .replace("）", ")")
        .replace(" ", "")
        .strip()
    )


def clean_report_name(name: str) -> str:
    cleaned = re.sub(r"^\d+_", "", str(name or ""))
    cleaned = re.sub(r"^(大学深度研究报告|大学深度评估报告)_", "", cleaned)
    cleaned = re.sub(r"_(深度研究报告|deep_research)$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"(大学深度评估报告|大学深度研究报告|深度评估报告|深度研究报告)$", "", cleaned)
    return cleaned.strip()


def fetch_json(url: str, timeout: int) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "gaokao-logo-sync/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bytes(url: str, timeout: int) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "gaokao-logo-sync/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "image/jpeg")
        return response.read(), content_type


def report_names() -> list[str]:
    names = []
    for path in sorted(REPORT_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        name = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            name = data.get("layer1_overview", {}).get("name") or name
        except (json.JSONDecodeError, OSError):
            pass
        names.append(clean_report_name(name))
    return names


def alias_values(school: dict) -> set[str]:
    values = set()
    for key in ("name", "short", "answer_short", "old_name"):
        raw = school.get(key) or ""
        for item in re.split(r"[,，、]", str(raw)):
            normalized = normalize_name(item)
            if normalized:
                values.add(normalized)
    return values


def build_school_index(schools: list[dict]) -> dict[str, dict]:
    index = {}
    for school in schools:
        for alias in alias_values(school):
            index.setdefault(alias, school)
    return index


def load_manifest() -> dict:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def save_manifest(manifest: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_logos(limit: int | None, timeout: int, sleep_seconds: float, force: bool) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    schools_payload = fetch_json(SCHOOL_NAME_URL, timeout)
    schools = schools_payload.get("data") or []
    school_index = build_school_index(schools)
    manifest = load_manifest()

    stats = {"total": 0, "matched": 0, "downloaded": 0, "cached": 0, "missing": 0, "failed": 0}
    for name in report_names()[:limit]:
        stats["total"] += 1
        key = normalize_name(name)
        school = school_index.get(key)
        if not school:
            stats["missing"] += 1
            manifest.setdefault(key, {"name": name, "missing": True})
            continue

        stats["matched"] += 1
        school_id = str(school["school_id"])
        target = CACHE_DIR / f"{school_id}.jpg"
        if target.exists() and not force:
            stats["cached"] += 1
            manifest[key] = {
                "name": school.get("name") or name,
                "school_id": school_id,
                "content_type": manifest.get(key, {}).get("content_type", "image/jpeg"),
                "source_url": LOGO_URL.format(school_id=school_id),
                "cached_at": manifest.get(key, {}).get("cached_at"),
            }
            continue

        try:
            content, content_type = fetch_bytes(LOGO_URL.format(school_id=school_id), timeout)
            if not content_type.startswith("image/"):
                raise ValueError(f"unexpected content type {content_type}")
            target.write_bytes(content)
            manifest[key] = {
                "name": school.get("name") or name,
                "school_id": school_id,
                "content_type": content_type,
                "source_url": LOGO_URL.format(school_id=school_id),
                "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            stats["downloaded"] += 1
            if sleep_seconds:
                time.sleep(sleep_seconds)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            stats["failed"] += 1
            manifest[key] = {
                "name": school.get("name") or name,
                "school_id": school_id,
                "source_url": LOGO_URL.format(school_id=school_id),
                "error": str(exc),
            }

    save_manifest(manifest)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync university logo cache.")
    parser.add_argument("--limit", type=int, default=None, help="limit number of report schools to process")
    parser.add_argument("--timeout", type=int, default=10, help="network timeout in seconds")
    parser.add_argument("--sleep", type=float, default=0.03, help="sleep seconds between downloads")
    parser.add_argument("--force", action="store_true", help="redownload existing logos")
    args = parser.parse_args()

    stats = sync_logos(args.limit, args.timeout, args.sleep, args.force)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
