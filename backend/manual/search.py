from __future__ import annotations

import re
from typing import Any, Sequence


def _tokenize_query(query: str) -> list[str]:
    q = (query or "").strip()
    if not q:
        return []
    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", q)
    keywords = [
        "科目",
        "教师",
        "监考",
        "考场",
        "座位",
        "资料打印",
        "台角纸",
        "桌角纸",
        "准考证",
        "信息表",
        "导入",
        "导出",
        "模板",
        "映射",
        "失败",
        "冲突",
        "时间",
        "排查",
        "报错",
    ]
    for kw in keywords:
        if kw in q:
            tokens.append(kw)
    if len(q) >= 2:
        tokens.append(q)
    return list(dict.fromkeys([t.strip() for t in tokens if t.strip()]))


def search_sections(sections: Sequence[dict[str, Any]], query: str, *, top_k: int = 4) -> list[dict[str, Any]]:
    tokens = _tokenize_query(query)
    if not tokens:
        return []

    scored: list[tuple[int, dict[str, Any]]] = []
    for sec in sections or []:
        title = sec.get("title", "")
        content = sec.get("content", "")
        hay = f"{title}\n{content}".lower()
        score = 0
        for t in tokens:
            t_lower = t.lower()
            score += hay.count(t_lower) * (3 if t_lower in title.lower() else 1)
        if score > 0:
            scored.append((score, sec))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_k]]


def format_context_snippets(sections: Sequence[dict[str, Any]], *, max_chars: int = 5000) -> str:
    parts: list[str] = []
    used = 0
    for sec in sections or []:
        title = (sec.get("title", "") or "").strip()
        content = (sec.get("content", "") or "").strip()
        block = f"### {title}\n{content}\n"
        if used + len(block) > max_chars:
            remain = max_chars - used
            if remain > 200:
                parts.append(block[:remain] + "\n（内容截断）\n")
            break
        parts.append(block)
        used += len(block)
    return "\n".join(parts).strip()

