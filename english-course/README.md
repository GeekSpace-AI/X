# 中文思维桥接英语 · 180 天课程

A 180-day English course for Chinese adult learners starting from a vocational-school (中专) level, in six 30-day books. Every lesson starts from what the learner wants to say in Chinese, then teaches the natural English for it. Vocabulary sits in original stories with US IPA, contextual meaning, usage scene, collocations, an example and the typical Chinese-learner mistake. Each day is a 120-minute, 8-step plan.

## Download

| File | Contents |
| --- | --- |
| [`output/00-课程总纲-180天路线图.pdf`](output/00-课程总纲-180天路线图.pdf) | Roadmap (21 pages): principles, the 8-step 120-minute day, the six books with weekly themes and measurable goals, where each Chinese-thinking point is taught, stage assessments, US IPA chart, resources with their verification status, 180-day tracker |
| [`output/01-第一册-基础表达与中文思维转换-Day01-30.pdf`](output/01-第一册-基础表达与中文思维转换-Day01-30.pdf) | Book 1, Day 1–30 (317 pages, A4): 30 complete lessons (4 review days, Day 30 stage test), 462 key words + 111 phrases, vocabulary coverage record, review index, progress log, Book 2 handoff record, copyable prompt for writing Book 2 |
| [`output/01-第一册-基础表达与中文思维转换-可编辑版.md`](output/01-第一册-基础表达与中文思维转换-可编辑版.md) / [`.docx`](output/01-第一册-基础表达与中文思维转换-可编辑版.docx) | Book 1 as editable Markdown and Word |

| [`output/02-第二册-生活交流时间表达和连续对话-Day31-60.pdf`](output/02-第二册-生活交流时间表达和连续对话-Day31-60.pdf) | Book 2, Day 31–60 (371 pages, A4): present perfect, past continuous, used to / be used to, telling a story and keeping a conversation going, life scenes (renting, moving, doctor, bank, returns, transport); 546 key words + 135 phrases (none repeated from Book 1); Book 3 handoff record and continuation prompt |
| [`output/02-第二册-生活交流时间表达和连续对话-可编辑版.md`](output/02-第二册-生活交流时间表达和连续对话-可编辑版.md) / [`.docx`](output/02-第二册-生活交流时间表达和连续对话-可编辑版.docx) | Book 2 as editable Markdown and Word |

Books 3–6 (Day 61–180) are planned in the roadmap and will be written in the same format.

## What each lesson contains

A 今日目标 (scene, key expressions, completion standard, 120-minute plan, warm-up) · B 中文场景导入 · C original story with sentence-aligned Chinese · D vocabulary notes in order of appearance · E 2–4 Chinese-vs-English differences with tasks · F core expressions · G pronunciation & four-step listening · H speaking in three levels + daily output · I checks, answers, checklist, next-day and seven-day review.

## Building

Requirements: Python 3 with `jinja2`, `pyyaml`, `pypdfium2`, `python-docx`; Node with `playwright` (Chromium); `pandoc` for the DOCX. Fonts are downloaded from Google Fonts on the first build into `fonts/` (git-ignored).

```bash
python3 build.py check      # validate lessons: duplicate headwords, unbolded words, 120-minute plans, counts
python3 build.py            # roadmap + every book (PDF, Markdown, DOCX) into output/
python3 build.py book1      # Book 1 only (book2, … likewise)
python3 build.py syllabus   # roadmap only
```

## Layout

```
content/
  syllabus.yaml        # 180-day roadmap
  FORMAT.md            # lesson file format
  book1/book.yaml      # Book 1 front/back matter, handoff record, continuation prompt
  book1/PLAN.md        # writing plan: each day's words, phrases, differences, anchor sentences
  book1/dayNN.txt      # one lesson per file
  book2/…              # same layout for Book 2 (Day 31–60)
templates/             # Jinja2 HTML / Markdown templates + print CSS
tools/render.cjs       # Chromium HTML → PDF
build.py               # parse, validate, track vocabulary, render, number the contents
```
