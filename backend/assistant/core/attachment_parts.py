import base64
import os


def _ext(path):
    return os.path.splitext(path or "")[1].lower().strip(".")


def _mime_for_image(ext):
    if ext in ("jpg", "jpeg"):
        return "image/jpeg"
    if ext == "webp":
        return "image/webp"
    if ext == "bmp":
        return "image/bmp"
    return "image/png"


def _read_text_file(path, max_chars=6000):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except Exception:
        return ""


def _read_pdf_text(path, max_pages=6, max_chars=12000):
    try:
        from pypdf import PdfReader
    except Exception:
        return ""

    try:
        reader = PdfReader(path)
        out = []
        for i, page in enumerate(reader.pages[:max_pages]):
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if t.strip():
                out.append(t.strip())
            if sum(len(x) for x in out) > max_chars:
                break
        text = "\n\n".join(out).strip()
        return text[:max_chars]
    except Exception:
        return ""


def _read_excel_text(path, max_rows=200, max_chars=12000):
    try:
        import pandas as pd
    except Exception:
        return ""

    try:
        df = pd.read_excel(path, sheet_name=0, nrows=max_rows, dtype=str)
        df = df.fillna("")
        csv_text = df.to_csv(index=False)
        csv_text = csv_text.replace("\r\n", "\n")
        return csv_text[:max_chars]
    except Exception:
        return ""


def build_attachment_parts(paths):
    parts = []
    for p in paths or []:
        if not p or not os.path.exists(p):
            continue
        ext = _ext(p)
        name = os.path.basename(p)

        if ext in ("png", "jpg", "jpeg", "bmp", "webp"):
            try:
                with open(p, "rb") as f:
                    data = f.read()
                if len(data) > 6 * 1024 * 1024:
                    parts.append({"type": "text", "text": f"附件图片 {name} 过大，已跳过（建议压缩后再上传）。"})
                    continue
                b64 = base64.b64encode(data).decode("ascii")
                mime = _mime_for_image(ext)
                parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
                continue
            except Exception:
                parts.append({"type": "text", "text": f"读取图片附件 {name} 失败。"})
                continue

        if ext in ("xlsx",):
            text = _read_excel_text(p)
            if text.strip():
                parts.append({"type": "text", "text": f"Excel 附件：{name}\n\n{_truncate(text)}"})
            else:
                parts.append({"type": "text", "text": f"Excel 附件：{name}\n\n（无法解析内容）"})
            continue

        if ext in ("pdf",):
            text = _read_pdf_text(p)
            if text.strip():
                parts.append({"type": "text", "text": f"PDF 附件：{name}\n\n{_truncate(text)}"})
            else:
                parts.append({"type": "text", "text": f"PDF 附件：{name}\n\n（无法解析内容，建议改为截图或复制文字）"})
            continue

        if ext in ("txt",):
            text = _read_text_file(p)
            if text.strip():
                parts.append({"type": "text", "text": f"文本附件：{name}\n\n{_truncate(text)}"})
            else:
                parts.append({"type": "text", "text": f"文本附件：{name}\n\n（文件为空或无法读取）"})
            continue

        parts.append({"type": "text", "text": f"收到附件：{name}\n（当前仅支持图片/Excel/PDF/TXT 的内容解析）"})

    return parts


def _truncate(text, max_chars=8000):
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    return t[:max_chars] + "\n（内容截断）"

