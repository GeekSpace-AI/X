# 中文思维学商务英语 · 90 天课程

A 90-day business-English course for Chinese learners, starting from a vocational-school (中专) level. Each day is a 2-hour lesson built around an episode of a workplace drama, with vocabulary taught in context and grammar taught by contrasting Chinese habits with English.

## Download

| File | Contents |
| --- | --- |
| [`output/00-课程总纲-90天商务英语路线图.pdf`](output/00-课程总纲-90天商务英语路线图.pdf) | Course overview (14 pages): method, daily 2-hour routine, 90-day roadmap, US IPA chart, Chinese-vs-English thinking, resources, check-in sheet |
| [`output/01-第一阶段-开口期-Day01-30.pdf`](output/01-第一阶段-开口期-Day01-30.pdf) | Phase 1, Day 1–30 (224 pages): 30 lessons, 780 vocabulary cards, 240 chunks, word index |

Phases 2 (Day 31–60) and 3 (Day 61–90) are planned in the overview and will be written in the same format.

## What each day contains

1. **热身复习**: say yesterday's sentences in English
2. **今日短剧**: a story episode; every new word sits right under its paragraph with US IPA, meaning and usage scene
3. **中文思维 → 英文表达**: one Chinese habit (不/没, 了, 在, 会, 要, 吧, 呢…) vs. natural English
4. **场景对话 + 发音小课**: dialogue marked with sentence stress and linking (‿)
5. **口语练习**: shadowing, Chinese→English, situational responses, 1-minute talk
6. **词汇理解**: fill-in-context, situation judgement, Chinglish fixes, with answer key

## Building the PDFs

Requirements: Python 3 with `jinja2`, `pyyaml`, `pypdfium2`; Node with `playwright` (Chromium). Fonts are downloaded from Google Fonts on first build into `fonts/` (git-ignored).

```bash
python3 build.py --check     # validate lesson files (duplicate words, missing fields)
python3 build.py             # build both PDFs into output/
python3 build.py phase1      # build only Phase 1
```

## Layout

```
content/
  syllabus.yaml           # overview content + Phase 2/3 day plan
  phase1/phase.yaml       # Phase 1 cover, how-to, cast
  phase1/dayNN.txt        # one lesson per file (see content/FORMAT.md)
templates/                # Jinja2 HTML templates + print CSS
tools/render.cjs          # Chromium HTML → PDF
build.py                  # parse, validate, render, page-number the TOC
```
