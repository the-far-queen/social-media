# AGENTS.md - (social-media repo)

> A course is not a vibe.

This file is the contract. Every commit gate checks against it.
Every course references it. Every test reads it.

If you change the schema, update AGENTS.md first. The repo is downstream
of this file.

## What this repo is

courses, exams, multiple-choice questions, study guides, online lessons,
academic subjects (AP, college, certification), the publishing pipeline.
Test-prep materials that are saleable on Amazon + sellable as online courses.

## Packet

course  Course | Exam | Lesson | AssetRef
exam    Exam   | Question | AssetRef
question Question | stem | choices | choices | explanation

**No asset without course_id + hash.** The gate refuses naked assets.

## Error this repo exists to stop

conflating all study content into one house style. 'Make it educational'
is not an axis. Voice register, claim density, and structural template are.

## Axes (the course contract)

A course is a named study program, characterized by:

| Axis | Type | Values |
|---|---|---|
| name | string | unique course id |
| subject_area | enum | humanities, sciences, math, languages, business, law, medicine, engineering, arts |
| level | enum | k-12, ap-high, college-undergrad, college-grad, certification, professional, language-cert |
| exam_format | enum | mc, essay, short-answer, lab, oral, coding |
| duration_hours | int | estimated study time |
| voice | ref | foreign-key to far-writing voice id |
| sheet | ref | foreign-key to far-art sheet id |
| activity | enum | read, quiz, project, lab, discussion, role-play, simulation, hands-on |
| pedagogy | enum | socratic, didactic, problem-based, project-based, inquiry-based, mastery-based, experiential |
| notices | string[] | what this course pays attention to |
| refuses | string[] | what this course never does |

## Voice (the course's tone)

Borrow from far-writing. The course voice is one of the canonical voices
(lean, gritty, lyric, didactic) or a custom voice. Voice gates are enforced
by far-writing gate.py.

## Sheet (the course's visuals)

Borrow from far-visual. Covers + diagrams use the far-art sheet system
(56-axis schema). Visual gates are enforced by far-art gate.py.

## Surface

course.compile(axes)
exam.compile(course, axes)
question.compile(exam, axes)
course.gate(course)
exam.gate(exam)
question.gate(question)

## Gate

commit_asset defaults to gate. The gate checks:

1. course_id is set
2. voice references an existing voice in the voice catalog
3. sheet references an existing sheet in the sheet catalog
4. duration_hours > 0 and <= 1000
5. No refuses violation
7. pedagogy in canonical list

A naked asset (no course_id) is refused with reason no_course_id.

## Tests (to be written)

| # | Test | What it checks |
|---|---|---|
| C1 | repro id | Course with same axes -> same id |
| C2 | exam inherits | Exam axes inherit from Course axes |
| C3 | refuses violated | refuses=[homeopathy] + lesson with homeopathy -> refused |
| C4 | voice ref valid | Course references non-existent voice -> refused |
| C5 | two different voice refs | Vary voice id; different course ids |

## Anti-patterns

- house-voice default
- vibe paragraphs without axes
- unverified facts
- educational theater (a long document nobody uses)
- listing facts without source links

## Related

- the-far-queen/far-writing/ - voice schema + voice.py
- the-far-queen/far-art/ - sheet schema + sheet.py
- the-far-queen/simself/ - AI substrate + constitutional kernel

## License

MIT. Free for all agents, human and non-human.
