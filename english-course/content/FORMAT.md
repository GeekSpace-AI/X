# Lesson file format

One lesson per file: `content/bookN/dayNN.txt`. Every line is `@key: value`; blank lines and lines starting with `#` are ignored.
Multi-field values are separated by ` | ` (space, pipe, space) — never put ` | ` inside a field; use `／` or `；` instead.
`content/bookN/book.yaml` holds the book's front and back matter; `content/book1/PLAN.md` is the writing plan (assigned words, anchor sentences).

Inline markup inside any value: `**bold**` (new word in the story, sentence stress in 【G】), `` `ipa` `` (IPA font),
`[[word]]` (recycled word on review days; the day it was first taught is looked up automatically), `‿` (linking), `\n` (line break).

## Header and section A (今日目标)

| Key | Fields | Notes |
| --- | --- | --- |
| `@day`, `@week` | number | `@week` must exist in `book.yaml` → `weeks` |
| `@review` | `true` | review day: review 8-step plan, "新情境" headings, recycled-word hints |
| `@title_cn`, `@title_en`, `@topic` | text | |
| `@think_short` | text | short list of the day's Chinese-thinking points (TOC, roadmap) |
| `@goal_scene`, `@goal_expr`, `@goal_vocab` | text | scene, key expressions, vocabulary range |
| `@done` | text | repeatable; completion standards ("能做到什么") |
| `@plan` | name \| minutes \| how | optional, repeatable; replaces the default 120-minute plan (must add up to 120) |
| `@warmup` | 中文 \| English \| D# | 5–6 items from earlier days |
| `@warmup_hint` | text | optional, replaces the default warm-up hint |

## B–D: situation, story, vocabulary

| Key | Fields | Notes |
| --- | --- | --- |
| `@scene` | text | 中文场景导入 |
| `@sp` | label \| text | 人物关系 / 沟通目的 / 已知信息 / 表达重点 |
| `@story_title`, `@story_type` | text | |
| `@s` | English \| 中文 | one story sentence; `Name: …` marks a speaker; numbered S1, S2… |
| `@br` | (empty) | paragraph break |
| `@v` | form \| head \| pos \| ipa \| meaning \| scene \| collocations \| example \| 例句中文 \| pitfall | 10 fields; `head` = `=` when same as form; `pos` = `phr.` for phrases; the form must be bolded in an `@s` line; headwords must be unique across the book |

## E–F: Chinese vs English, core expressions

| Key | Fields | Notes |
| --- | --- | --- |
| `@diff` | title | starts a difference block (2–4 per day) |
| `@d_cn`, `@d_en`, `@d_why`, `@d_when`, `@d_vs` | text | Chinese meaning, natural English, why, when, contrast examples |
| `@d_task` | task \| answer | |
| `@core` | expression \| use \| substitutions \| 正式 / 随意 | 5–8 per day |

## G: pronunciation and listening

| Key | Fields | Notes |
| --- | --- | --- |
| `@pw` | word \| ipa \| syllables & stress \| tip | |
| `@ps` | sentence with **stress**, `/` pauses, `‿` links \| note | |
| `@pnote` | text | weak forms, contractions, written vs spoken |
| `@lfocus` | text | what to listen for |
| `@dict` | `S#` | dictation sentences |
| `@res` | text | optional; search hints only, never unverified URLs |

## H–I: speaking, output, checks, review

| Key | Fields | Notes |
| --- | --- | --- |
| `@mimic` | text | level 1 (review days: retell without the text) |
| `@swap` | base \| hint \| sample | level 2 |
| `@free` | 中文情境 \| sample | level 3 |
| `@output`, `@output_sample` | text | 12-minute output task and model answer |
| `@check` | question \| answer | |
| `@next1`, `@next7` | text | next-day and seven-day review lists |
| `@assess` | can-do statement \| related days | stage assessment (Day 30) |
| `@weak` | weak item \| how to fix | weak-item record (Day 30) |
| `@improve` | text | next-stage improvement advice (review days) |

Run `python3 build.py check` after editing: it reports duplicate headwords, unbolded vocabulary, plans that don't add up to 120 minutes, missing fields, and per-day counts.
