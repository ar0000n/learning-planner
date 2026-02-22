#!/usr/bin/env python3
"""
CLI tool to generate a structured 1-week learning plan using the Anthropic API.

Usage:
    python planner.py "Python programming"
    python planner.py "machine learning"
    python planner.py              # prompts interactively
"""

import sys
import re
import argparse
from datetime import date
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = (
    "You are an expert learning coach and curriculum designer specialising in onboarding "
    "experienced developers into new topics. "
    "Your audience is an intermediate developer — comfortable with code, abstractions, and "
    "system design — but completely new to the requested topic. "
    "Design every plan so difficulty increases slowly and consistently across all five days: "
    "Day 1 is purely conceptual and confidence-building (no code, no configuration); "
    "Day 2 introduces the simplest hands-on 'hello world' style task; "
    "Days 3 and 4 add one new concept per day, each building directly on the last; "
    "Day 5 ties everything together with a small but realistic project that mirrors "
    "the kind of task found in a professional or enterprise codebase — leaving the learner "
    "ready to start contributing to production-grade software. "
    "Never introduce more than one new concept per day. "
    "Never make a day feel overwhelming. "
    "Always explain why each concept matters before showing how it works. "
    "Be concise but complete: finishing all five days is the top priority. "
    "Never sacrifice coverage of a day for extra detail on an earlier one."
)

FAMILIARITY_LEVELS = [
    {
        "label": "Novice",
        "description": "Never worked with it before",
        "context": (
            "The learner has never worked with this topic before. "
            "Assume zero prior knowledge of the topic itself, though they are a competent developer. "
            "Day 1 must build confidence through pure concepts — no setup, no code. "
            "Every term introduced must be briefly defined. "
            "By the end of the week they should feel genuinely ready to contribute to a real codebase."
        ),
    },
    {
        "label": "A little familiar",
        "description": "Seen it or done a quick tutorial",
        "context": (
            "The learner has a passing familiarity — perhaps followed a getting-started tutorial "
            "or read an overview — but has never built anything real with this topic. "
            "Day 1 should consolidate and sharpen existing mental models rather than re-explain basics. "
            "Pick up pace gradually from Day 2 onward, filling gaps and building toward production patterns. "
            "By the end of the week they should feel confident enough to own a feature in a professional project."
        ),
    },
    {
        "label": "Quite familiar",
        "description": "Used it in small projects or prototypes",
        "context": (
            "The learner has used this topic in small projects and understands the core mechanics. "
            "Day 1 should challenge and deepen existing knowledge — focus on mental models, edge cases, "
            "or common misconceptions rather than re-covering ground they already know. "
            "Progress quickly toward advanced patterns, best practices, and production-readiness. "
            "By the end of the week they should feel ready to architect and lead work in this area."
        ),
    },
]

USER_PROMPT_TEMPLATE = """\
Create a structured 1-week learning plan for the topic: "{topic}"

Learner familiarity: {familiarity_label} — {familiarity_description}
{familiarity_context}

Cover Monday through Friday only. For each day provide exactly:

**Day: <Day name>**
- Focus: <one specific aspect of {topic} to concentrate on that day>
- Resources:
  1. <Resource name> — <one-sentence description and where to find it>
  2. <Resource name> — <one-sentence description and where to find it>
- Exercise: <a small, concrete hands-on activity completable in 30–60 minutes>

Build each day on the previous so the plan progresses logically and ends with the learner \
elevated in their understanding and ready to work confidently on real projects.
"""


def prompt_familiarity(topic: str) -> dict:
    """Display the familiarity menu and return the chosen level."""
    max_len = max(len(level["label"]) for level in FAMILIARITY_LEVELS)

    print(f"\nHow familiar are you with {topic}?\n")
    for i, level in enumerate(FAMILIARITY_LEVELS, 1):
        print(f"  {i}. {level['label']:<{max_len}}  —  {level['description']}")
    print()

    while True:
        try:
            raw = input(f"Select [1-{len(FAMILIARITY_LEVELS)}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)

        if raw.isdigit() and 1 <= int(raw) <= len(FAMILIARITY_LEVELS):
            chosen = FAMILIARITY_LEVELS[int(raw) - 1]
            print(f"\nGot it — tailoring the plan for: {chosen['label']}")
            return chosen

        print(f"Please enter a number between 1 and {len(FAMILIARITY_LEVELS)}.")


def slugify(text: str) -> str:
    """Convert a topic string into a safe filename fragment."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:50].strip("-")


def generate_learning_plan(topic: str, familiarity: dict, save: bool = False) -> None:
    client = anthropic.Anthropic()

    prompt = USER_PROMPT_TEMPLATE.format(
        topic=topic,
        familiarity_label=familiarity["label"],
        familiarity_description=familiarity["description"],
        familiarity_context=familiarity["context"],
    )

    print(f"\n1-Week Learning Plan: {topic}")
    print("=" * 60)

    chunks: list[str] = []

    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            if save:
                chunks.append(text)

    print("\n" + "=" * 60)
    print("Plan complete. Good luck with your studies!")

    if save:
        today = date.today().strftime("%Y-%m-%d")
        slug = slugify(topic)
        filename = f"learning-plan-{slug}-{today}.md"
        output_path = Path(filename)

        md_content = (
            f"# 1-Week Learning Plan: {topic}\n\n"
            f"*Generated on {today} · Familiarity: {familiarity['label']}*\n\n"
            + "".join(chunks)
        )
        output_path.write_text(md_content, encoding="utf-8")
        print(f"Saved to: {output_path.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a 1-week learning plan for any topic using Claude AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python planner.py "Python programming"\n'
            '  python planner.py "machine learning"\n'
            '  python planner.py "Spanish language"\n'
            "  python planner.py          # interactive prompt"
        ),
    )
    parser.add_argument(
        "topic",
        nargs="?",
        help="The topic you want to learn (wrap multi-word topics in quotes).",
    )
    parser.add_argument(
        "-s", "--save",
        action="store_true",
        help="Save the plan to a markdown file named learning-plan-<topic>-<date>.md",
    )

    args = parser.parse_args()

    topic = args.topic
    if not topic:
        try:
            topic = input("Enter the topic you want to learn: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)

    if not topic:
        print("Error: no topic provided.", file=sys.stderr)
        sys.exit(1)

    familiarity = prompt_familiarity(topic)

    try:
        generate_learning_plan(topic, familiarity, save=args.save)
    except anthropic.AuthenticationError:
        print(
            "Error: invalid or missing API key.\n"
            "Add it to your .env file: ANTHROPIC_API_KEY=your-key-here",
            file=sys.stderr,
        )
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("Error: could not connect to the Anthropic API. Check your internet connection.", file=sys.stderr)
        sys.exit(1)
    except anthropic.RateLimitError:
        print("Error: rate limit reached. Wait a moment and try again.", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIStatusError as e:
        print(f"API error {e.status_code}: {e.message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
