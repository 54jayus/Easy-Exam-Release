import argparse
import re
from pathlib import Path


FENCE_RE = re.compile(r"^```")
FENCE_THEME_RE = re.compile(r"^```(\w+)\s+theme=\{null\}\s*$")
DIV_HEADING_RE = re.compile(r"^(#{2,6})\s*<div[^>]*>.*?(?:</svg>|<svg[^>]*/>)\s*([^<]+?)\s*</div>\s*$")
TAB_OPEN_RE = re.compile(r'^\s*<Tab\s+title="([^"]+)">\s*$')
STEP_OPEN_RE = re.compile(r'^\s*<Step\s+title="([^"]+)"(?:\s+stepNumber=\{(\d+)\})?.*?>\s*$')
CARD_OPEN_RE = re.compile(r'^\s*<Card\s+title="([^"]+)".*?>\s*$')
VIDEO_SRC_RE = re.compile(r'src="([^"]+)"')


def clean_mdx_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    in_code = False
    in_card = False
    card_title = ""
    card_buf: list[str] = []
    in_note = False
    note_kind = ""
    note_buf: list[str] = []

    def flush_card() -> None:
        nonlocal in_card, card_title, card_buf
        text = " ".join(s.strip() for s in card_buf if s.strip())
        if card_title.strip():
            if text:
                out.append(f"- **{card_title.strip()}**：{text}")
            else:
                out.append(f"- **{card_title.strip()}**")
        in_card = False
        card_title = ""
        card_buf = []

    def flush_note() -> None:
        nonlocal in_note, note_kind, note_buf
        text = " ".join(s.strip() for s in note_buf if s.strip())
        if text:
            out.append(f"> {note_kind}：{text}")
        in_note = False
        note_kind = ""
        note_buf = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        if FENCE_RE.match(line):
            m = FENCE_THEME_RE.match(line)
            if m:
                out.append(f"```{m.group(1)}")
            else:
                out.append(line)
            in_code = not in_code
            continue

        if in_code:
            out.append(line)
            continue

        if in_card:
            if line.strip() == "</Card>":
                flush_card()
            else:
                if not line.strip().startswith("<svg"):
                    card_buf.append(line)
            continue

        if in_note:
            if line.strip() in ("</Tip>", "</Warning>"):
                flush_note()
            else:
                note_buf.append(line)
            continue

        heading_match = DIV_HEADING_RE.match(line)
        if heading_match:
            out.append(f"{heading_match.group(1)} {heading_match.group(2).strip()}")
            continue

        tab_match = TAB_OPEN_RE.match(line)
        if tab_match:
            out.append(f"### {tab_match.group(1).strip()}")
            continue

        step_match = STEP_OPEN_RE.match(line)
        if step_match:
            title = step_match.group(1).strip()
            step_no = step_match.group(2)
            if step_no:
                out.append(f"### {step_no}. {title}")
            else:
                out.append(f"### {title}")
            continue

        card_match = CARD_OPEN_RE.match(line)
        if card_match:
            in_card = True
            card_title = card_match.group(1)
            card_buf = []
            continue

        stripped = line.strip()
        if stripped in (
            "<Tabs>",
            "</Tabs>",
            "<Steps>",
            "</Steps>",
            "</Step>",
            "</CardGroup>",
        ):
            continue

        if stripped.startswith("<CardGroup"):
            continue

        if stripped in ("<Tip>", "<Warning>"):
            in_note = True
            note_kind = "提示" if stripped == "<Tip>" else "注意"
            note_buf = []
            continue

        if stripped == "</Tab>":
            continue

        if stripped.startswith("<video"):
            m = VIDEO_SRC_RE.search(stripped)
            if m:
                out.append(f"[视频]({m.group(1)})")
            continue

        if "<br" in line and "|" not in line:
            line = line.replace("<br />", "").replace("<br/>", "").replace("<br>", "")

        if stripped.startswith("<") and stripped.endswith(">"):
            continue

        out.append(line)

    if in_card:
        flush_card()
    if in_note:
        flush_note()

    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()

    cleaned: list[str] = []
    prev_blank = False
    for l in out:
        is_blank = not l.strip()
        if is_blank and prev_blank:
            continue
        cleaned.append(l)
        prev_blank = is_blank

    return [l + "\n" for l in cleaned]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str)
    parser.add_argument("-o", "--output", type=str, default="")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(str(input_path))

    output_path = Path(args.output) if args.output else input_path.with_suffix(".clean.md")
    text = input_path.read_text(encoding="utf-8")
    cleaned = clean_mdx_lines(text.splitlines(True))
    output_path.write_text("".join(cleaned), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
