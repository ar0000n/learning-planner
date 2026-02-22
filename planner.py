#!/usr/bin/env python3
"""
CLI tool to generate a structured 1-week learning plan using the Anthropic API.

Two AI agents collaborate on every plan:
  - Generator Agent  creates the initial plan
  - Critic Agent     evaluates and produces a refined version

The final output is always the refined plan.

Usage:
    python planner.py "Python programming"
    python planner.py "Docker" --verbose   # also shows original + critique
    python planner.py --save "Kubernetes"  # saves refined plan to markdown
    python planner.py                      # prompts interactively
"""

import sys
import re
import argparse
from datetime import date
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Generator Agent prompt ────────────────────────────────────────────────────

GENERATOR_SYSTEM_PROMPT = (
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

GENERATOR_PROMPT_TEMPLATE = """\
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

# ── Critic Agent prompt ───────────────────────────────────────────────────────

CRITIC_SYSTEM_PROMPT = (
    "You are an expert learning plan critic. Your job is to rigorously evaluate a "
    "generated learning plan and produce a meaningfully improved version. "
    "Assess the plan on four criteria: "
    "(1) Difficulty progression — does it increase gradually across all five days without sudden spikes? "
    "(2) Resource quality — are the resources credible, specific, and genuinely useful rather than vague or generic? "
    "(3) Exercise practicality — can each exercise realistically be completed in 30–60 minutes "
    "and does it build real, transferable skill? "
    "(4) Confidence outcome — will someone who completes this plan feel genuinely ready to work "
    "professionally with the topic by Friday? "
    "Be specific and direct in your assessment. Name exactly what is weak and why. "
    "Then produce a refined plan that concretely fixes every issue you identified. "
    "The refined plan must use the same day-by-day format as the original."
)

CRITIC_PROMPT_TEMPLATE = """\
Below is a 1-week learning plan for the topic "{topic}" written for a learner \
at the "{familiarity_label}" familiarity level.

Evaluate it, then produce an improved version. Your response must use this exact structure \
with no text outside it:

## Assessment
<Your critique covering difficulty progression, resource credibility, exercise practicality, \
and confidence outcome. Be specific about what is weak and why.>

## Refined Plan
<The improved Monday–Friday plan using the same format as the original. \
Fix every issue raised in your assessment.>

---
Original plan:
{original_plan}
"""

# ── Familiarity levels ────────────────────────────────────────────────────────

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

# ── Helpers ───────────────────────────────────────────────────────────────────

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


def section(title: str) -> None:
    """Print a labelled section divider."""
    print("\n" + "─" * 60)
    print(f" {title}")
    print("─" * 60 + "\n")

# ── Agents ────────────────────────────────────────────────────────────────────

def run_generator(client: anthropic.Anthropic, topic: str, familiarity: dict, verbose: bool) -> str:
    """
    Generator Agent — drafts the initial learning plan.
    Streams to stdout when verbose; always returns the full plan text.
    """
    prompt = GENERATOR_PROMPT_TEMPLATE.format(
        topic=topic,
        familiarity_label=familiarity["label"],
        familiarity_description=familiarity["description"],
        familiarity_context=familiarity["context"],
    )

    chunks: list[str] = []
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=GENERATOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            if verbose:
                print(text, end="", flush=True)
            chunks.append(text)

    return "".join(chunks)


def run_critic(
    client: anthropic.Anthropic, topic: str, familiarity: dict, original_plan: str
) -> tuple[str, str]:
    """
    Critic Agent — evaluates the draft plan and returns an improved version.
    Returns (assessment, refined_plan).
    """
    prompt = CRITIC_PROMPT_TEMPLATE.format(
        topic=topic,
        familiarity_label=familiarity["label"],
        original_plan=original_plan,
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        system=CRITIC_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    full_text = response.content[0].text
    marker = "## Refined Plan"

    if marker in full_text:
        before, after = full_text.split(marker, 1)
        assessment = before.replace("## Assessment", "").strip()
        refined = after.strip()
    else:
        # Fallback: the critic didn't follow the format; treat everything as refined
        assessment = ""
        refined = full_text.strip()

    return assessment, refined

# ── Orchestrator ──────────────────────────────────────────────────────────────

def generate_learning_plan(
    topic: str, familiarity: dict, save: bool = False, verbose: bool = False
) -> None:
    client = anthropic.Anthropic()

    # ── Step 1: Generator Agent ───────────────────────────────
    if verbose:
        section("Generator Agent")
    else:
        print("\nGenerating plan...", end="", flush=True)

    original_plan = run_generator(client, topic, familiarity, verbose)

    if not verbose:
        print(" done.")

    # ── Step 2: Critic Agent ──────────────────────────────────
    if verbose:
        section("Critic Agent — evaluating...")
    else:
        print("Refining with Critic Agent...", end="", flush=True)

    assessment, refined_plan = run_critic(client, topic, familiarity, original_plan)

    if not verbose:
        print(" done.\n")

    # ── Step 3: Display results ───────────────────────────────
    if verbose and assessment:
        print(assessment)
        section("Critic Agent — refined plan")

    print(f"1-Week Learning Plan: {topic}")
    print("=" * 60)
    print(refined_plan)
    print("\n" + "=" * 60)
    print("Plan complete. Good luck with your studies!")

    # ── Step 4: Save to markdown ──────────────────────────────
    if save:
        today = date.today().strftime("%Y-%m-%d")
        slug = slugify(topic)
        filename = f"learning-plan-{slug}-{today}.md"
        output_path = Path(filename)

        md_content = (
            f"# 1-Week Learning Plan: {topic}\n\n"
            f"*Generated on {today} · Familiarity: {familiarity['label']}*\n\n"
            + refined_plan
        )
        output_path.write_text(md_content, encoding="utf-8")
        print(f"Saved to: {output_path.resolve()}")

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a 1-week learning plan for any topic using Claude AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python planner.py "Python programming"\n'
            '  python planner.py "machine learning"\n'
            '  python planner.py "Docker" --verbose\n'
            '  python planner.py "Redis" --save\n'
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
        help="Save the refined plan to a markdown file named learning-plan-<topic>-<date>.md",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help=(
            "Show the Generator Agent's original plan and the Critic Agent's feedback "
            "before the final refined plan."
        ),
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
        generate_learning_plan(topic, familiarity, save=args.save, verbose=args.verbose)
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
