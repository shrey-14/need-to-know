"""The access map itself, its frontend display copy, and PII redaction."""
import re
from pathlib import Path

import pytest

from app.core.roles import ALL_CATEGORIES, ROLE_ACCESS, allowed_categories
from app.guardrails.pii import redact_pii

EXPECTED_ACCESS = {
    "finance": {"finance", "general"},
    "marketing": {"marketing", "general"},
    "hr": {"hr", "general"},
    "engineering": {"engineering", "general"},
    "employee": {"general"},
    "c_level": {"finance", "marketing", "hr", "engineering", "general"},
}


def test_access_map_is_exactly_the_documented_one() -> None:
    # Any change to who can read what must be deliberate: it fails here first.
    assert {role: set(cats) for role, cats in ROLE_ACCESS.items()} == EXPECTED_ACCESS


def test_unknown_role_has_no_access() -> None:
    assert allowed_categories("intern") == set()


def test_frontend_display_map_mirrors_backend() -> None:
    # frontend/src/roles.ts is display-only, but if it drifted the UI would tell
    # users they can (or can't) read departments that the backend says otherwise.
    source = (Path(__file__).parents[1] / "frontend" / "src" / "roles.ts").read_text()
    block = re.search(r"ROLE_ACCESS[^{]*\{(.*?)\n\};", source, re.S).group(1)
    frontend = {}
    for role, value in re.findall(r"(\w+):\s*(\[[^\]]*\]|ALL_CATEGORIES)", block):
        frontend[role] = set(ALL_CATEGORIES) if value == "ALL_CATEGORIES" else set(re.findall(r'"(\w+)"', value))
    assert frontend == EXPECTED_ACCESS


SAMPLE = (
    "Aadhya Patel (employee ID FINEMP1000) works as a Sales Manager. "
    "Email aadhya.patel@fintechco.com, born 1991-04-03, salary ₹1,332,478.37."
)
PII_FRAGMENTS = ["FINEMP1000", "aadhya.patel@fintechco.com", "1991-04-03", "₹1,332,478.37"]


@pytest.mark.parametrize("role", ["finance", "marketing", "engineering", "employee"])
def test_pii_is_masked_for_roles_without_hr_access(role: str) -> None:
    out = redact_pii(SAMPLE, role)
    for fragment in PII_FRAGMENTS:
        assert fragment not in out
    assert "Aadhya Patel" in out  # names aren't PII here; only the listed fields are


@pytest.mark.parametrize("role", ["hr", "c_level"])
def test_pii_is_kept_for_roles_with_hr_access(role: str) -> None:
    assert redact_pii(SAMPLE, role) == SAMPLE
