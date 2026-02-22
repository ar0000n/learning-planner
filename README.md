# Learning Planner

A CLI tool that generates a structured 1-week learning plan for any topic using the Anthropic API. Plans are tailored to your current familiarity with the topic and designed to leave you confident and ready to work on real projects by the end of the week.

## Features

- Monday–Friday plan with a daily focus, 2 resources, and a hands-on exercise per day
- Familiarity selector (Novice / A little familiar / Quite familiar) that adjusts pacing and depth
- Gradual difficulty progression — Day 1 is conceptual, Day 5 is production-ready
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

### Save to a Markdown file

```bash
python planner.py "GraphQL" --save
# Saves to: learning-plan-graphql-2026-02-22.md

python planner.py --save
# Prompts for topic, then saves
```

The `-s` short flag also works:

```bash
python planner.py "Redis" -s
```

## Example session

```
$ python planner.py "Apache Kafka"

How familiar are you with Apache Kafka?

  1. Novice          —  Never worked with it before
  2. A little familiar  —  Seen it or done a quick tutorial
  3. Quite familiar  —  Used it in small projects or prototypes

Select [1-3]: 1

Got it — tailoring the plan for: Novice

1-Week Learning Plan: Apache Kafka
============================================================
**Day: Monday**
- Focus: Understanding what Kafka is and why it exists ...
...
============================================================
Plan complete. Good luck with your studies!
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
