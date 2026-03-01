import os
import re
import sys


def _get_base_path():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _try_read_utf8(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def load_manual_markdown():
    base = _get_base_path()
    content = _try_read_utf8(os.path.join(base, "使用说明书.md"))
    if content.strip():
        return content
    embedded = _try_read_utf8(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "使用说明书.md")))
    return embedded or "# 智能考务系统使用说明书\n\n（说明书内容未加载）\n"


def _slugify(text):
    safe = re.sub(r"\s+", "-", (text or "").strip())
    safe = re.sub(r"[^\w\u4e00-\u9fff\-]+", "", safe)
    return safe[:60] or "section"


def build_sections(markdown_text):
    lines = (markdown_text or "").splitlines()
    sections = []
    current = None
    used = set()

    def finalize():
        nonlocal current
        if not current:
            return
        current["content"] = "\n".join(current["content"]).strip()
        sections.append(current)
        current = None

    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            finalize()
            level = len(m.group(1))
            title = m.group(2).strip()
            base = _slugify(title)
            anchor = base
            idx = 2
            while anchor in used:
                anchor = f"{base}-{idx}"
                idx += 1
            used.add(anchor)
            current = {"level": level, "title": title, "anchor": anchor, "content": []}
        else:
            if current is None:
                current = {"level": 1, "title": "文档", "anchor": "top", "content": []}
                used.add("top")
            current["content"].append(line)

    finalize()
    return sections


def _tokenize_query(query):
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


def search_sections(sections, query, top_k=4):
    tokens = _tokenize_query(query)
    if not tokens:
        return []

    scored = []
    for sec in sections or []:
        title = sec.get("title", "")
        content = sec.get("content", "")
        hay = f"{title}\n{content}"
        score = 0
        for t in tokens:
            score += hay.count(t) * (4 if t in title else 1)
        if score > 0:
            scored.append((score, sec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_k]]


def format_context_snippets(sections, max_chars=5000):
    parts = []
    used = 0
    for sec in sections or []:
        title = sec.get("title", "").strip()
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
