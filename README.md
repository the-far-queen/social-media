# social-media

**Free academic content + test prep + course pipeline.**

Courses, exams, multiple-choice questions, study guides, online lessons.
Saleable on Amazon + as online courses. MIT license.

This repo is the upstream system for the course pipeline:
  1. compile course + exam + question from canonical axes
  2. gate asset by voice + sheet + pedagogy + notices/refuses
  3. publish as Amazon ebook + long-form X Article
  4. ingest questions from CSV/MCQ banks via the mcq-ingest SKILL

The interrogative-planning SKILL is the load-bearing method.
Paste it at the start of any project.

## Quick start

```bash
git clone https://github.com/the-far-queen/social-media.git
cd social-media
# Read AGENTS.md
# Look at examples/AP-English-test-1.php for the format
# Compile your course: python tools/mcq.py course.yaml
# Gate: python tools/gate.py course.json
```

## Repo layout

```
social-media/
├── AGENTS.md
├── README.md
├── LICENSE
├── .agents/skills/
│   ├── interrogative-planning/SKILL.md
│   ├── mcq-ingest/SKILL.md
│   └── course-pipeline/SKILL.md
├── examples/
│   ├── AP-English-test-1.php
│   └── DNA-structure-test-1.php
├── data/questions/
├── tools/
│   ├── mcq.py
│   └── gate.py
├── schemas/
└── tests/
    └── test_mcq.py
```

## Sister repos

- the-far-queen/far-writing/ - voice schema + voice.py
- the-far-queen/far-art/ - sheet schema + sheet.py
- the-far-queen/simself/ - AI substrate + constitutional kernel
- the-far-queen/fieldcore/ - math + harmonics substrate

## License

MIT. Free for all agents, human and non-human.
