# Lesson file format

One lesson per file (`content/phaseN/dayNN.txt`). Every line is `@key: value`; blank lines and lines starting with `#` are ignored. Multi-field values are separated by ` | ` (space, pipe, space).

Inline markup inside any value: `**bold**` (new word in a story / sentence stress in a dialogue), `` `ipa` `` (IPA font), `[[word]]` (recycled word on review days), `‿` (linking mark), `\n` (line break).

| Key | Fields | Notes |
| --- | --- | --- |
| `@day`, `@week` | number | `@week` must exist in `phase.yaml` → `weeks` |
| `@review` | `true` | marks a review day (badge + recycled-word hint) |
| `@title_cn`, `@title_en`, `@scene` | text | header |
| `@think_short` | text | short label used in the TOC and roadmap |
| `@goal` | text | repeatable |
| `@warmup_hint` | text | optional, overrides the default warm-up hint |
| `@warmup` | 中文 \| English | repeatable |
| `@story_title`, `@story_intro` | text | |
| `@p` | English paragraph | starts a new paragraph |
| `@cn` | Chinese translation | belongs to the last `@p` |
| `@w` | word \| pos \| ipa \| meaning \| usage scene | belongs to the last `@p`; headwords must be unique across the phase |
| `@culture_title`, `@culture` | text | culture box; `@culture` repeatable |
| `@think_title`, `@think_intro`, `@think_tip` | text | `@think_intro` repeatable |
| `@pair` | 中文 \| ✗ Chinglish \| ✓ English \| why | repeatable, all 4 fields required |
| `@dlg_title`, `@dlg_intro` | text | |
| `@line` | speaker \| English \| 中文 | repeatable |
| `@pron_title`, `@pron`, `@pron_drill` | text | `@pron` repeatable |
| `@chunk` | English \| 中文 \| when to use | repeatable |
| `@shadow` | text | shadowing instructions |
| `@say` | 中文 \| English | Chinese → English speaking items |
| `@respond` | situation \| sample answer | |
| `@talk_topic`, `@frame`, `@talk_sample` | text | 1-minute talk; `@frame` repeatable |
| `@bank` | comma-separated words | word bank for the fill-in exercise |
| `@fill` | sentence with ______ \| answer \| optional 中文 hint | |
| `@choose` / `@opt` / `@ans` | question / option / `B \| why` | `@opt` 2–4 times, then one `@ans` |
| `@fix` | wrong \| right \| why | |
| `@assess` | can-do statement \| related days | optional, test days only |
| `@next` | text | optional advice under the self-assessment |
