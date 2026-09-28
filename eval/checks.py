# Deterministic (no-LLM) eval checks: text normalization, evidence matching
# against retrieved chunks, and must_contain matching against answers. Shared
# by retrieval_check.py (Tier 1) and run_evals.py (Tier 2). Eval phase.
import re
import subprocess
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

_DASHES = re.compile(r"[‐-―−]")        # hyphen/dash variants, incl. the non-breaking hyphen LLMs emit
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")       # 1,332,478 -> 1332478
_MARKUP = re.compile(r"[*`]")                          # markdown bold/italics, code ticks: deleted


def norm(text: str) -> str:
    """Normalize so formatting differences don't count as misses:
    '**Revenue**: $9.4 billion' and 'revenue: $9.4 billion' compare equal."""
    text = unicodedata.normalize("NFKC", text)        # also turns narrow no-break spaces into spaces
    text = _DASHES.sub("-", text)
    text = _THOUSANDS.sub("", text)
    text = _MARKUP.sub("", text)                      # "**Net Income**: $275" -> "Net Income: $275"
    text = text.replace("|", " ")                     # table cells: "| Sick Leave | 12 days" -> "Sick Leave 12 days"
    return " ".join(text.lower().split())


def _found(needle: str, haystack: str) -> bool:
    needle = norm(needle)
    if needle.isdigit():
        # Bare numbers match as whole numbers only: "15" must not match "2015",
        # "150" or "1.5", but a sentence-ending period is fine ("in 2016.").
        return re.search(rf"(?<!\d)(?<!\d\.){needle}(?!\.?\d)", haystack) is not None
    return needle in haystack


def evidence_hits(evidence: list, chunks: list[dict]) -> list[bool]:
    """For each evidence item, is it in at least one chunk? An item is either a
    string, or {"text", "source"} when the text is ambiguous across files
    (e.g. "$2 million" is both Q1's and Q3's marketing spend)."""
    normed = [(norm(c["text"]), Path(c["source"]).name) for c in chunks]
    hits = []
    for item in evidence:
        text, source = (item, None) if isinstance(item, str) else (item["text"], item["source"])
        hits.append(any(_found(text, t) and (source is None or s == source) for t, s in normed))
    return hits


def must_contain_hits(must_contain: list, answer: str) -> list[bool]:
    """For each item, does the answer contain it? A list item means any-of:
    ["2 days", "two days"] passes if either appears."""
    answer = norm(answer)
    return [
        any(_found(alt, answer) for alt in (item if isinstance(item, list) else [item]))
        for item in must_contain
    ]


def git_state() -> dict:
    def git(*args: str) -> str | None:
        try:
            return subprocess.run(
                ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    return {
        "commit": git("rev-parse", "HEAD"),  # None until the repo has a first commit
        # Only modified tracked files count: untracked files (e.g. the previous
        # run's results JSON) don't change what the code does.
        "dirty": bool(git("status", "--porcelain", "--untracked-files=no")),
    }
