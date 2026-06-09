"""Shared 2025 admissions recommendation context builder."""

import re


DATA_VERSION_PREFIX = "scores"
TIERS = ("冲", "稳", "保")


def parse_score_range(value):
    """Return a normalized (low, high) tuple from strings such as 520-560."""
    numbers = [int(item) for item in re.findall(r"\d{3}", str(value or ""))]
    if not numbers:
        return None
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])


def resolve_recommendation_query(args):
    """Normalize official, estimated-score, and estimated-range requests."""
    mode = str(args.get("mode") or "").strip().lower()
    score = _positive_int(args.get("score"))
    rank = _positive_int(args.get("rank"))
    score_range = parse_score_range(args.get("score_range"))

    if score_range is None:
        score_min = _positive_int(args.get("score_min"))
        score_max = _positive_int(args.get("score_max"))
        if score_min or score_max:
            score_range = (
                min(value for value in (score_min, score_max) if value),
                max(value for value in (score_min, score_max) if value),
            )

    if not score and score_range:
        score = round((score_range[0] + score_range[1]) / 2)

    if mode not in ("official", "estimated", "planning"):
        mode = "official" if rank else ("estimated" if score or score_range else "planning")

    if mode == "official" and not rank:
        match_basis = "score"
    elif mode == "official":
        match_basis = "rank"
    elif score_range and score_range[0] != score_range[1]:
        match_basis = "estimated_score_range"
    else:
        match_basis = "estimated_score"

    return {
        "mode": mode,
        "score": score,
        "rank": rank,
        "score_range": score_range,
        "match_basis": match_basis,
    }


def build_recommendation_context(records, query, limit_per_tier=10):
    """Build one deterministic candidate pool consumed by chat and reports."""
    limit_per_tier = max(1, min(int(limit_per_tier or 10), 30))
    usable = [
        dict(record)
        for record in records
        if record.get("school_name") and _positive_int(record.get("min_score"))
    ]
    rank_records = [record for record in usable if _positive_int(record.get("min_rank"))]
    use_rank = query.get("match_basis") == "rank" and query.get("rank") and rank_records
    match_basis = "rank" if use_rank else (
        "score" if query.get("match_basis") == "rank" else query.get("match_basis", "estimated_score")
    )

    grouped = {}
    for record in usable:
        school = record["school_name"]
        distance = _record_distance(record, query, use_rank=bool(use_rank))
        if distance is None:
            continue
        grouped.setdefault(school, []).append((distance, record))

    candidates = []
    for school, matches in grouped.items():
        matches.sort(key=lambda item: item[0])
        _, primary = matches[0]
        tier = _classify_tier(primary, query, use_rank=bool(use_rank))
        if not tier:
            continue

        score = _positive_int(query.get("score"))
        rank = _positive_int(query.get("rank"))
        min_score = _positive_int(primary.get("min_score"))
        min_rank = _positive_int(primary.get("min_rank"))
        nearby_majors = []
        seen_majors = set()
        for _, row in matches:
            major = str(row.get("major_name") or "").strip()
            if major and major not in seen_majors:
                nearby_majors.append(major)
                seen_majors.add(major)
            if len(nearby_majors) >= 5:
                break

        candidates.append({
            "school_name": school,
            "major_name": primary.get("major_name") or "",
            "majors": "; ".join(nearby_majors),
            "batch": primary.get("batch") or "",
            "category": primary.get("category") or "",
            "min_score": min_score,
            "min_rank": min_rank,
            "score_gap": min_score - score if score and min_score else None,
            "rank_gap": min_rank - rank if rank and min_rank else None,
            "tier": tier,
            "bucket": tier,
            "year": primary.get("year") or query.get("year"),
            "source_year": primary.get("year") or query.get("year"),
            "source_record_id": primary.get("source_record_id") or primary.get("id"),
            "reason": _reason(primary, query, tier, use_rank=bool(use_rank)),
        })

    tiers = {tier: [] for tier in TIERS}
    for candidate in candidates:
        tiers[candidate["tier"]].append(candidate)
    for tier in TIERS:
        tiers[tier].sort(key=lambda item: _candidate_sort_key(item, query, use_rank=bool(use_rank)))
        tiers[tier] = tiers[tier][:limit_per_tier]

    returned = sum(len(rows) for rows in tiers.values())
    rank_coverage = round(len(rank_records) / len(usable), 4) if usable else 0
    mode = query.get("mode", "estimated")
    return {
        "query": {
            "province": query.get("province", ""),
            "category": query.get("category", ""),
            "query_category": query.get("query_category", query.get("category", "")),
            "score": query.get("score"),
            "rank": query.get("rank"),
            "score_range": list(query["score_range"]) if query.get("score_range") else None,
            "year": query.get("year"),
            "mode": mode,
        },
        "data_version": f"{DATA_VERSION_PREFIX}-{query.get('year')}-v1",
        "match_basis": match_basis,
        "positioning_label": "正式冲稳保" if mode == "official" else "预估院校层次",
        "quality": {
            "status": "complete" if returned >= min(9, limit_per_tier * 3) else "limited",
            "usable_records": len(usable),
            "returned_schools": returned,
            "rank_coverage": rank_coverage,
        },
        "tiers": tiers,
        "冲": tiers["冲"],
        "稳": tiers["稳"],
        "保": tiers["保"],
        "recommendations": tiers["冲"] + tiers["稳"] + tiers["保"],
    }


def _positive_int(value):
    try:
        number = int(float(value))
        return number if number > 0 else None
    except (TypeError, ValueError):
        return None


def _record_distance(record, query, use_rank=False):
    if use_rank:
        min_rank = _positive_int(record.get("min_rank"))
        rank = _positive_int(query.get("rank"))
        if not min_rank or not rank:
            return None
        ratio = min_rank / rank
        return abs(ratio - 1)

    min_score = _positive_int(record.get("min_score"))
    score = _positive_int(query.get("score"))
    if not min_score or not score:
        return None
    return abs(min_score - score)


def _classify_tier(record, query, use_rank=False):
    if use_rank:
        ratio = _positive_int(record.get("min_rank")) / _positive_int(query.get("rank"))
        if 0.72 <= ratio < 0.95:
            return "冲"
        if 0.95 <= ratio <= 1.12:
            return "稳"
        if 1.12 < ratio <= 1.45:
            return "保"
        return None

    gap = _positive_int(record.get("min_score")) - _positive_int(query.get("score"))
    if 10 < gap <= 35:
        return "冲"
    if -10 <= gap <= 10:
        return "稳"
    if -35 <= gap < -10:
        return "保"
    return None


def _candidate_sort_key(candidate, query, use_rank=False):
    if use_rank and candidate.get("rank_gap") is not None:
        return abs(candidate["rank_gap"])
    if candidate.get("score_gap") is not None:
        return abs(candidate["score_gap"])
    return 10**9


def _reason(record, query, tier, use_rank=False):
    mode_prefix = "正式位次" if query.get("mode") == "official" else "预估分数"
    tier_label = tier if query.get("mode") == "official" else {
        "冲": "较高目标层",
        "稳": "匹配目标层",
        "保": "保守目标层",
    }[tier]
    if use_rank and record.get("min_rank"):
        return f"按2025年最低位次与考生{mode_prefix}比较，属于{tier_label}参考"
    return f"按2025年最低分与考生{mode_prefix}比较，属于{tier_label}参考"
