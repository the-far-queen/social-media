---
name: mcq-ingest
description: >-
  Use when the user wants to ingest multiple-choice question banks (CSV, PDF, PHP)
  into the social-media pipeline. Triggers: ingest MCQs, import questions, CSV to course.

canonical MCQuestion schema: question_id (sha256[:16]), stem, choices, answer,
explanation, source, subject_area, level. The 1-bit veto gate checks
every question for stem + answer + choices + canonical subject_area/level.
Duplicates collapsed by question_id. No answer = refused no_answer.
---

# MCQ Ingest

Version 1.0. Source: Desktop/testing/*.csv + Desktop/test-prep/*.php.

## How to use

CSV: python tools/mcq.py ingest path/to/file.csv --out questions.jsonl
PHP: python tools/mcq.py parse examples/AP-English-test-1.php --out questions.jsonl

## Subject areas (canonical)
humanities, sciences, math, languages, business, law, medicine, engineering, arts

## Levels (canonical)
k-12, ap-high, college-undergrad, college-grad, certification, professional, language-cert

## License
MIT.
