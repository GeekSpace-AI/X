#!/usr/bin/env python3
"""Build the course PDFs from the plain-text lesson files.

    python3 build.py            # build syllabus + phase 1
    python3 build.py --check    # only validate lesson files (duplicates, missing fields)

Lesson files (content/phase1/dayNN.txt) use one field per line:  @key: value
See content/FORMAT.md for the field list.
"""
import html
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import jinja2
import yaml

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
BUILD = ROOT / "build"
OUTPUT = ROOT / "output"
FONTS = ROOT / "fonts"

FONT_URLS = {
    "NotoSans-Regular.ttf": "https://fonts.gstatic.com/s/notosans/v42/o-0mIpQlx3QUlC5A4PNB6Ryti20_6n1iPHjcz6L1SoM-jCpoiyD9A99d.ttf",
    "NotoSans-Bold.ttf": "https://fonts.gstatic.com/s/notosans/v42/o-0mIpQlx3QUlC5A4PNB6Ryti20_6n1iPHjcz6L1SoM-jCpoiyAaBN9d.ttf",
    "NotoSansSC-Regular.ttf": "https://fonts.gstatic.com/s/notosanssc/v41/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYw.ttf",
    "NotoSansSC-Bold.ttf": "https://fonts.gstatic.com/s/notosanssc/v41/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaGzjCnYw.ttf",
    "NotoSerif-Regular.ttf": "https://fonts.gstatic.com/s/notoserif/v33/ga6iaw1J5X9T9RW6j9bNVls-hfgvz8JcMofYTa32J4wsL2JAlAhZqFCjwA.ttf",
    "NotoSerif-Bold.ttf": "https://fonts.gstatic.com/s/notoserif/v33/ga6iaw1J5X9T9RW6j9bNVls-hfgvz8JcMofYTa32J4wsL2JAlAhZT1ejwA.ttf",
    "NotoSerif-Italic.ttf": "https://fonts.gstatic.com/s/notoserif/v33/ga6saw1J5X9T9RW6j9bNfFIMZhhWnFTyNZIQD1-_FXP0RgnaOg9MYBNLg8cP.ttf",
}

# (环节, 分钟) — the same 2-hour routine every day
PLAN = [
    ("① 热身复习", 10),
    ("② 短剧精读 + 词汇", 35),
    ("③ 中文思维对照", 15),
    ("④ 对话跟读 + 发音", 25),
    ("⑤ 口语练习", 20),
    ("⑥ 词汇理解题", 15),
]

SCALAR_KEYS = {
    "day", "week", "week_name", "title_cn", "title_en", "scene", "review",
    "story_title", "story_intro", "culture_title", "think_title", "think_short",
    "think_tip", "dlg_title", "dlg_intro", "pron_title", "pron_drill", "shadow",
    "talk_topic", "talk_sample", "warmup_hint", "bank",
}
LIST_KEYS = {"goal": "goals", "culture": "culture", "think_intro": "think_intro",
             "pron": "pron", "frame": "talk_frame", "assess": "assess", "next": "next_steps"}
SPLIT_KEYS = {
    "warmup": ("warmup", ["cn", "en"]),
    "pair": ("pairs", ["zh", "bad", "good", "note"]),
    "line": ("lines", ["who", "en", "zh"]),
    "chunk": ("chunks", ["en", "zh", "use"]),
    "say": ("say", ["zh", "en"]),
    "respond": ("respond", ["q", "a"]),
    "fill": ("fill", ["q", "a", "zh"]),
    "fix": ("fix", ["wrong", "right", "why"]),
}
REQUIRED = ["day", "week", "title_cn", "title_en", "scene", "story_title", "think_title",
            "dlg_title", "shadow", "talk_topic", "talk_sample", "bank"]


class LessonError(Exception):
    pass


def split_fields(val, names, where):
    parts = [p.strip() for p in val.split(" | ")]
    if len(parts) > len(names) or len(parts) < len(names) - (1 if names[-1] == "zh" and names[0] == "q" else 0):
        raise LessonError(f"{where}: expected {len(names)} fields separated by ' | ', got {len(parts)}: {val[:80]}")
    parts += [""] * (len(names) - len(parts))
    return dict(zip(names, parts))


def parse_day(path):
    d = {k: [] for k in ["goals", "culture", "think_intro", "pron", "talk_frame", "paras", "choose",
                         "assess", "next_steps"]}
    for _, (dest, _) in SPLIT_KEYS.items():
        d[dest] = []
    d.update(review=False, warmup_hint="不看答案，用英文说出下面的中文（都来自前一天的内容），说不出来就回前一天找。")
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        where = f"{path.name}:{n}"
        if not line.startswith("@") or ":" not in line:
            raise LessonError(f"{where}: line must look like '@key: value'")
        key, _, val = line[1:].partition(":")
        key, val = key.strip(), val.strip()
        if key in SCALAR_KEYS:
            d[key] = val
        elif key in LIST_KEYS:
            d[LIST_KEYS[key]].append(val)
        elif key in SPLIT_KEYS:
            dest, names = SPLIT_KEYS[key]
            d[dest].append(split_fields(val, names, where))
        elif key == "p":
            d["paras"].append({"en": val, "cn": "", "words": []})
        elif key == "cn":
            d["paras"][-1]["cn"] = val
        elif key == "w":
            w = split_fields(val, ["word", "pos", "ipa", "meaning", "scene"], where)
            w["src"] = where
            d["paras"][-1]["words"].append(w)
        elif key == "choose":
            d["choose"].append({"q": val, "opts": [], "a": "", "why": ""})
        elif key == "opt":
            d["choose"][-1]["opts"].append(val)
        elif key == "ans":
            a, _, why = val.partition(" | ")
            d["choose"][-1].update(a=a.strip(), why=why.strip())
        else:
            raise LessonError(f"{where}: unknown key @{key}")
    missing = [k for k in REQUIRED if not d.get(k)]
    if missing:
        raise LessonError(f"{path.name}: missing {missing}")
    d["day"] = int(d["day"])
    d["week"] = int(d["week"])
    d["review"] = str(d["review"]).lower() in ("1", "true", "yes")
    d["fill_bank"] = [b.strip() for b in d["bank"].split(",")]
    d["word_count"] = sum(len(p["words"]) for p in d["paras"])
    return d


def headword_key(word):
    w = re.sub(r"\(.*?\)", "", word.lower())
    w = re.sub(r"\bsb\b|\bsth\b|\.\.\.|…", "", w)
    return re.sub(r"\s+", " ", w).strip()


def validate(days):
    problems, warnings = [], []
    seen = {}
    for d in days:
        for p in d["paras"]:
            bold = [b.lower() for b in re.findall(r"\*\*(.+?)\*\*", p["en"])]
            for w in p["words"]:
                k = headword_key(w["word"])
                if k in seen:
                    problems.append(f"duplicate word '{w['word']}' in {w['src']} (first in {seen[k]})")
                else:
                    seen[k] = w["src"]
                if not w["ipa"] or not w["meaning"] or not w["scene"]:
                    problems.append(f"incomplete entry '{w['word']}' in {w['src']}")
                first = k.split(" ")[0][:4]
                if not any(first in b or b.startswith(first[:3]) for b in bold):
                    warnings.append(f"'{w['word']}' not bolded in its paragraph ({w['src']})")
        for c in d["choose"]:
            if not c["a"] or len(c["opts"]) < 2:
                problems.append(f"day {d['day']}: choose item incomplete: {c['q'][:40]}")
    return problems, warnings, len(seen)


def md(text):
    """Tiny inline markup: **bold**, `ipa`, [[recycled word]], ‿ linking mark, \\n line breaks."""
    if text is None:
        return ""
    s = html.escape(str(text), quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r'<span class="ipa">\1</span>', s)
    s = re.sub(r"\[\[(.+?)\]\]", r'<span class="rcy">\1</span>', s)
    s = s.replace("‿", '<span class="lk">‿</span>')
    s = s.replace("\\n", "<br>")
    return jinja2.utils.markupsafe.Markup(s)


def plain(text):
    return re.sub(r"\*\*|`|\[\[|\]\]", "", text)


def ensure_fonts():
    FONTS.mkdir(exist_ok=True)
    for name, url in FONT_URLS.items():
        f = FONTS / name
        if not f.exists():
            print("downloading", name)
            urllib.request.urlretrieve(url, f)


def env():
    e = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES), autoescape=True)
    e.filters["md"] = md
    return e


def chrome_pdf(html_path, pdf_path):
    npm_root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    subprocess.run(["node", str(ROOT / "tools" / "render.cjs"), str(html_path), str(pdf_path)],
                   check=True, env={**__import__("os").environ, "NODE_PATH": npm_root})


def find_pages(pdf_path, patterns):
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf_path))
    found = {}
    for i in range(len(doc)):
        text = doc[i].get_textpage().get_text_range()
        for label, rx in patterns:
            if label not in found and re.search(rx, text):
                found[label] = i + 1
        for m in re.finditer(r"D\s*A\s*Y\s*(\d{2})\b", text):
            found.setdefault(f"DAY {m.group(1)}", i + 1)
    return found


def build_doc(template, context, out_name, footer, patterns):
    BUILD.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    shutil.copy(TEMPLATES / "style.css", BUILD / "style.css")
    tpl = env().get_template(template)
    stem = Path(out_name).stem
    html_path = BUILD / f"{stem}.html"
    raw = BUILD / f"{stem}.raw.pdf"
    pages = {}
    for _ in range(2):  # pass 1 finds page numbers, pass 2 prints them in the TOC
        html_path.write_text(tpl.render(pages=pages, plan=PLAN, footer=footer, **context), encoding="utf-8")
        chrome_pdf(html_path, raw)
        pages = find_pages(raw, patterns)
    shutil.copy(raw, OUTPUT / out_name)
    print(f"wrote output/{out_name}")


def load_phase(n):
    files = sorted((CONTENT / f"phase{n}").glob("day*.txt"))
    days = [parse_day(f) for f in files]
    meta = yaml.safe_load((CONTENT / f"phase{n}" / "phase.yaml").read_text(encoding="utf-8"))
    for d in days:
        d.setdefault("week_name", meta["weeks"][d["week"]])
        d.setdefault("think_short", plain(d["think_title"]))
    return meta, days


def word_index(days):
    idx = []
    for d in days:
        for p in d["paras"]:
            for w in p["words"]:
                meaning = re.sub(r"[；;].*$", "", plain(w["meaning"]))
                idx.append({"word": w["word"], "meaning_plain": meaning, "day": d["day"],
                            "sort_key": re.sub(r"[^a-z ]", "", w["word"].lower()).strip() or w["word"].lower()})
    return sorted(idx, key=lambda x: x["sort_key"])


def distinct_word_forms(days):
    """Distinct English word forms used in the stories and dialogues."""
    forms = set()
    for d in days:
        texts = [p["en"] for p in d["paras"]] + [l["en"] for l in d["lines"]]
        for t in texts:
            forms.update(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]*", plain(t).replace("\\n", " ")))
    return len(forms)


def main():
    meta, days = load_phase(1)
    problems, warnings, total = validate(days)
    for w in warnings:
        print("warn:", w)
    for p in problems:
        print("ERROR:", p)
    print(f"{len(days)} days, {total} unique words/phrases")
    if problems:
        sys.exit(1)
    if "--check" in sys.argv:
        return
    ensure_fonts()
    targets = [a for a in sys.argv[1:] if not a.startswith("-")] or ["syllabus", "phase1"]
    if "syllabus" in targets:
        syllabus = yaml.safe_load((CONTENT / "syllabus.yaml").read_text(encoding="utf-8"))
        build_doc("syllabus.html.j2", {"s": syllabus, "p1days": days, "distinct_words": f"{distinct_word_forms(days):,}"},
                  "00-课程总纲-90天商务英语路线图.pdf", "中文思维学商务英语 · 课程总纲", [])
    if "phase1" in targets:
        build_doc("phase.html.j2", {"phase": meta, "days": days, "index": word_index(days)},
                  "01-第一阶段-开口期-Day01-30.pdf", "中文思维学商务英语 · 第一阶段 开口期（Day 1–30）",
                  [("INDEX", r"INDEX · 词汇总表")])


if __name__ == "__main__":
    try:
        main()
    except LessonError as e:
        sys.exit(f"ERROR: {e}")
