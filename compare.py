"""
Week 4 evidence — open-ended generation vs. constrained decision, head to head.

Approach A (open-ended):
    Ask the model to explain, in a full sentence, whether a message is urgent.
    Then run simple text parsing to pull "urgent" / "not urgent" out of that sentence.

Approach B (constrained):
    Ask the model to return ONLY a label (urgent / not urgent) and a confidence
    score, no free-text explanation allowed.

For each of the 15 test messages, both approaches are run and timed, and the
open-ended approach's output is checked for whether it could be parsed cleanly.

USAGE
-----
If an ANTHROPIC_API_KEY is set, this calls the real Claude API (haiku, for
speed) and produces real timing + real parsing-failure data.

If no key is set, it falls back to a clearly-labeled SIMULATED backend, so you
can see the script run end-to-end and inspect the output format before you
have API access. Simulated numbers are NOT real evidence — re-run with a key
before using this for your submission.

Run:
    python3 compare.py
Output:
    results-log.csv   (per-message results)
    summary.txt       (aggregate numbers)
"""

import os
import re
import csv
import time
import random
import statistics

from messages import TEST_MESSAGES

USE_REAL_API = bool(os.environ.get("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# Backend A: real Anthropic API (used only if a key is present)
# ---------------------------------------------------------------------------
def call_real_open_ended(text):
    from anthropic import Anthropic
    client = Anthropic()
    t0 = time.perf_counter()
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                "Here is a support message:\n\n"
                f'"{text}"\n\n'
                "In a full sentence, explain whether this message is urgent "
                "and why."
            ),
        }],
    )
    elapsed = time.perf_counter() - t0
    return resp.content[0].text, elapsed


def call_real_constrained(text):
    from anthropic import Anthropic
    client = Anthropic()
    t0 = time.perf_counter()
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=20,
        messages=[{
            "role": "user",
            "content": (
                "Classify this support message as exactly one of: "
                "urgent, not urgent.\n\n"
                f'Message: "{text}"\n\n'
                "Respond in this exact format and nothing else:\n"
                "label: <urgent|not urgent>\nconfidence: <0.00-1.00>"
            ),
        }],
    )
    elapsed = time.perf_counter() - t0
    return resp.content[0].text, elapsed


# ---------------------------------------------------------------------------
# Backend B: SIMULATED fallback (no API key available in this environment)
#
# This models the *mechanism* we're comparing (one sequential token-by-token
# pass that has to be parsed back out, vs. one short constrained pass) using
# realistic relative timing, not invented "proof." It is here so the script
# is runnable and the output format is real — swap in the real backend above
# the moment a key is available.
# ---------------------------------------------------------------------------
def simulate_open_ended(text, true_label):
    """Simulate a model writing a full explanatory sentence, token by token."""
    # Longer responses take proportionally longer: ~25-45 tokens of reasoning.
    n_tokens = random.randint(25, 45)
    per_token_latency = random.uniform(0.018, 0.026)  # seconds/token, generation-bound
    t0 = time.perf_counter()
    time.sleep(n_tokens * per_token_latency)
    elapsed = time.perf_counter() - t0

    # Simulate the model's free-text answer, including occasional messy phrasing
    # that a simple parser would fail on (this is the real failure mode we saw
    # when testing this by hand).
    templates_clean = [
        "This message is {label} because it describes {reason}.",
        "I would classify this as {label}, since {reason}.",
    ]
    templates_messy = [
        "It's hard to say definitively, but there are signs this could need attention soon regarding {reason}.",
        "This seems like something to keep an eye on — {reason} — though it's not immediately clear-cut.",
    ]

    reason = "a clear operational problem" if true_label == "urgent" else (
        "a routine, non-blocking request" if true_label == "not urgent" else "a developing issue"
    )

    if true_label == "ambiguous" and random.random() < 0.6:
        output = random.choice(templates_messy).format(reason=reason)
    else:
        label_text = "urgent" if true_label == "urgent" else "not urgent"
        output = random.choice(templates_clean).format(label=label_text, reason=reason)

    return output, elapsed


def simulate_constrained(text, true_label):
    """Simulate a short constrained response: label + confidence, nothing else."""
    n_tokens = random.randint(4, 7)
    per_token_latency = random.uniform(0.018, 0.026)
    t0 = time.perf_counter()
    time.sleep(n_tokens * per_token_latency)
    elapsed = time.perf_counter() - t0

    if true_label == "ambiguous":
        label = random.choice(["urgent", "not urgent"])
        confidence = round(random.uniform(0.50, 0.68), 2)
    else:
        label = true_label
        confidence = round(random.uniform(0.80, 0.97), 2)

    output = f"label: {label}\nconfidence: {confidence:.2f}"
    return output, elapsed


# ---------------------------------------------------------------------------
# Parsing logic for the open-ended approach (this is the extra step the
# constrained approach doesn't need)
# ---------------------------------------------------------------------------
def parse_open_ended_output(text):
    """
    Try to extract 'urgent' / 'not urgent' from a free-text sentence.
    Returns (label_or_None, parse_ok: bool).
    """
    lowered = text.lower()
    has_not_urgent = "not urgent" in lowered
    has_urgent = re.search(r"\burgent\b", lowered) is not None

    if has_not_urgent:
        return "not urgent", True
    if has_urgent:
        return "urgent", True
    return None, False  # couldn't confidently extract a label


def parse_constrained_output(text):
    match = re.search(r"label:\s*(urgent|not urgent)", text.lower())
    if match:
        return match.group(1), True
    return None, False


# ---------------------------------------------------------------------------
# Main comparison loop
# ---------------------------------------------------------------------------
def main():
    random.seed(42)  # reproducible simulated run

    rows = []
    for msg in TEST_MESSAGES:
        if USE_REAL_API:
            open_text, open_time = call_real_open_ended(msg["text"])
            constrained_text, constrained_time = call_real_constrained(msg["text"])
        else:
            open_text, open_time = simulate_open_ended(msg["text"], msg["true_label"])
            constrained_text, constrained_time = simulate_constrained(msg["text"], msg["true_label"])

        open_label, open_parsed_ok = parse_open_ended_output(open_text)
        constrained_label, constrained_parsed_ok = parse_constrained_output(constrained_text)

        rows.append({
            "id": msg["id"],
            "message": msg["text"],
            "true_label": msg["true_label"],
            "open_ended_output": open_text.replace("\n", " "),
            "open_ended_time_s": round(open_time, 4),
            "open_ended_parsed_label": open_label or "FAILED_TO_PARSE",
            "open_ended_parse_ok": open_parsed_ok,
            "constrained_output": constrained_text.replace("\n", " "),
            "constrained_time_s": round(constrained_time, 4),
            "constrained_parsed_label": constrained_label or "FAILED_TO_PARSE",
            "constrained_parse_ok": constrained_parsed_ok,
        })

    # Write per-message CSV
    with open("results-log.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Aggregate summary
    open_times = [r["open_ended_time_s"] for r in rows]
    constrained_times = [r["constrained_time_s"] for r in rows]
    open_fail_count = sum(1 for r in rows if not r["open_ended_parse_ok"])
    constrained_fail_count = sum(1 for r in rows if not r["constrained_parse_ok"])

    summary_lines = [
        f"Backend used: {'REAL Anthropic API' if USE_REAL_API else 'SIMULATED (no API key present — re-run with ANTHROPIC_API_KEY set for real evidence)'}",
        f"Messages tested: {len(rows)}",
        "",
        "--- Timing ---",
        f"Open-ended   avg: {statistics.mean(open_times):.4f}s   median: {statistics.median(open_times):.4f}s",
        f"Constrained  avg: {statistics.mean(constrained_times):.4f}s   median: {statistics.median(constrained_times):.4f}s",
        f"Speedup (avg): {statistics.mean(open_times) / statistics.mean(constrained_times):.2f}x",
        "",
        "--- Parsing reliability ---",
        f"Open-ended   parse failures: {open_fail_count} / {len(rows)}",
        f"Constrained  parse failures: {constrained_fail_count} / {len(rows)}",
    ]
    summary = "\n".join(summary_lines)

    with open("summary.txt", "w") as f:
        f.write(summary + "\n")

    print(summary)
    print("\nWrote results-log.csv and summary.txt")


if __name__ == "__main__":
    main()
