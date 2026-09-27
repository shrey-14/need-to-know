"""Role -> allowed data-category mapping.

Category names match the subfolder names under data/, which is what the
ingestion pipeline tags each chunk's metadata with.
"""

FINANCE = "finance"
MARKETING = "marketing"
HR = "hr"
ENGINEERING = "engineering"
GENERAL = "general"

ALL_CATEGORIES = {FINANCE, MARKETING, HR, ENGINEERING, GENERAL}

# Role -> set of data categories that role's queries may retrieve from.
ROLE_ACCESS: dict[str, set[str]] = {
    "finance": {FINANCE, GENERAL},
    "marketing": {MARKETING, GENERAL},
    "hr": {HR, GENERAL},
    "engineering": {ENGINEERING, GENERAL},
    "employee": {GENERAL},
    "c_level": set(ALL_CATEGORIES),
}


def allowed_categories(role: str) -> set[str]:
    """Categories a given role may retrieve from. Unknown roles get no access."""
    return ROLE_ACCESS.get(role, set())
