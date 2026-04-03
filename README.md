# AI Tutor

A Socratic learning skill for Claude Code, based on Bloom's Two Sigma research.

Instead of explaining things to you, it asks you questions — adapting difficulty in real time based on your answers. Learning progress is saved to files so it persists across sessions.

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/Aolinkun/ai-tutor/main/install.sh | bash
```

Requires: Claude Code, macOS/Linux

---

## Usage

In any Claude Code session:

```
我想学维特根斯坦的逻辑哲学论
我想学 Rust 的所有权系统
我想学抖音  ← Claude will ask what you actually want to solve first
继续学维特根斯坦  ← resumes from last session
```

Claude will clarify vague topics, run a diagnostic to find your knowledge boundary, then generate learning units that adapt to your level.

Progress is saved to `./learning/[topic]/` in your project directory.

---

## How it works

Based on Benjamin Bloom's 1984 finding that one-on-one tutoring + mastery learning produces 2 sigma improvement over classroom instruction (outperforming 98% of students).

Key behaviors:
- **Clarifies topic first** — "I want to learn TikTok" → asks what problem you're solving → narrows to precise topic
- **Diagnoses before teaching** — 2-3 questions to find your actual knowledge boundary
- **Mastery gating** — moves forward only when ≥80% correct, backs up when stuck
- **Tiered hints** — 3 levels of hints before giving away the answer
- **Spaced review** — review unit every 5 units
- **Emotion-aware** — detects frustration, slows down, switches approach
- **Context compression** — saves key info to file every 3 units to survive long sessions
- **Cross-topic linking** — notices when new concepts relate to things you've learned before

---

## File structure

```
~/.claude/skills/ai-tutor/
├── SKILL.md                        # Main skill file
└── references/
    ├── theory.md                   # Bloom Two Sigma background
    └── difficulty-levels.md        # Difficulty scaling by subject
```

Learning progress (per project):
```
./learning/
└── [topic]/
    ├── progress.md                 # State, weak points, compressed history
    ├── unit-01-[title].md
    ├── unit-02-[title].md
    └── summary.md                  # Generated on completion
```

---

## Version

Current: **v1.3.0**

| Version | Changes |
|---------|---------|
| v1.3.0 | Topic clarification step — vague topics get narrowed before teaching starts |
| v1.2.0 | Tiered hints, error correction methods, emotion sensing, context compression, cross-topic linking |
| v1.1.0 | Resume from last session, spaced review, graduation criteria |
| v1.0.0 | Initial release |

To verify your installed version:
```bash
grep "^# Version" ~/.claude/skills/ai-tutor/SKILL.md
```

---

## License

MIT
