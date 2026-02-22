# Learning Planner

A CLI tool that generates a structured 1-week learning plan for any topic using the Anthropic API. Plans are tailored to your current familiarity with the topic and designed to leave you confident and ready to work on real projects by the end of the week.

## How it works

Two AI agents collaborate on every plan:

1. **Generator Agent** drafts an initial Monday–Friday plan tailored to your topic and familiarity level
2. **Critic Agent** evaluates the draft against four criteria — difficulty progression, resource credibility, exercise practicality, and confidence outcome — then produces a refined version

The final output shown to you (and saved, if requested) is always the refined plan.

## Features

- Two-agent pipeline: Generator → Critic → refined plan
- Familiarity selector (Novice / A little familiar / Quite familiar) that adjusts pacing and depth
- Gradual difficulty progression — Day 1 is conceptual, Day 5 is production-ready
- `--verbose` mode to see the original draft and the critic's feedback alongside the final plan
- Optional save to a dated Markdown file

## Requirements

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/ar0000n/learning-planner.git
cd learning-planner

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env
# Open .env and replace your-api-key-here with your actual key
```

Get your API key from [console.anthropic.com](https://console.anthropic.com/).

## Usage

### Basic — topic as an argument

```bash
python planner.py "Kubernetes"
```

### Interactive — prompts for the topic

```bash
python planner.py
# Enter the topic you want to learn: Docker
```

### Show the full agent pipeline with `--verbose`

```bash
python planner.py "GraphQL" --verbose
```

Verbose mode shows three sections in sequence:
1. **Generator Agent** — the initial draft, streamed live
2. **Critic Agent — evaluating** — the critique covering progression, resources, exercises, and outcome
3. **Critic Agent — refined plan** — the final improved plan

Without `--verbose`, only the refined plan is shown.

### Save to a Markdown file

```bash
python planner.py "GraphQL" --save
# Saves to: learning-plan-graphql-2026-02-22.md

python planner.py --save
# Prompts for topic, then saves
```

Flags can be combined:

```bash
python planner.py "Redis" --verbose --save
python planner.py "Redis" -v -s
```

## Example sessions

### Default (refined plan only)

```
$ python planner.py "Apache Kafka"

How familiar are you with Apache Kafka?

  1. Novice            —  Never worked with it before
  2. A little familiar  —  Seen it or done a quick tutorial
  3. Quite familiar    —  Used it in small projects or prototypes

Select [1-3]: 1

Got it — tailoring the plan for: Novice

Generating plan... done.
Refining with Critic Agent... done.

1-Week Learning Plan: Apache Kafka
============================================================
**Day: Monday**
- Focus: Understanding what Kafka is and why it exists ...
...
============================================================
Plan complete. Good luck with your studies!
```

### Verbose (full pipeline visible)

```
$ python planner.py "Apache Kafka" --verbose

...familiarity selection...

────────────────────────────────────────────────────────────
 Generator Agent
────────────────────────────────────────────────────────────

**Day: Monday**
- Focus: ...   ← streams live

────────────────────────────────────────────────────────────
 Critic Agent — evaluating...
────────────────────────────────────────────────────────────

The difficulty progression is largely sound, however Day 3
jumps from basic consumers to partition management without
enough scaffolding...  ← critique

────────────────────────────────────────────────────────────
 Critic Agent — refined plan
────────────────────────────────────────────────────────────

1-Week Learning Plan: Apache Kafka
============================================================
**Day: Monday**  ← improved plan
...
```

## Output file format

When `--save` is used, the file is written to the current directory with this naming pattern:

```
learning-plan-<topic-slug>-<YYYY-MM-DD>.md
```

Examples:
```
learning-plan-apache-kafka-2026-02-22.md
learning-plan-graphql-2026-02-22.md
learning-plan-rust-programming-2026-02-22.md
```

The file includes a title, generation date, familiarity level, and the full plan in Markdown.

## Familiarity levels

| Level | Best for | Day 1 approach | Week outcome |
|---|---|---|---|
| **Novice** | No prior exposure | Pure concepts, no code | Ready to contribute to a real codebase |
| **A little familiar** | Done a tutorial or read an overview | Sharpen mental models | Confident enough to own a feature |
| **Quite familiar** | Built small projects with the topic | Challenge existing knowledge | Ready to architect and lead |

## Project structure

```
learning-planner/
├── planner.py        # CLI tool
├── requirements.txt  # dependencies
├── .env.example      # API key template (copy to .env and fill in)
├── .env              # your API key — never committed
├── .gitignore
└── README.md
```
