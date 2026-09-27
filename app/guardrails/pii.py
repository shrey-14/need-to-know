# Redact salary / email / DOB / employee-ID patterns from responses. Guardrails phase.
# PII - Personally Identifiable Information makes sure to mask any sensitive information in the responses. This is a guardrail to ensure that no sensitive data like salary, email, DOB, or employee-ID is leaked in the output, or to the AI.
import re

from app.core.roles import allowed_categories

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SALARY_PATTERN = re.compile(r"₹[\d,]+\.\d{2}")
DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
EMPLOYEE_ID_PATTERN = re.compile(r"\bFINEMP\d+\b")


def _mask(text: str) -> str:
    text = EMAIL_PATTERN.sub("[REDACTED EMAIL]", text)
    text = SALARY_PATTERN.sub("[REDACTED AMOUNT]", text)
    text = DATE_PATTERN.sub("[REDACTED DATE]", text)
    text = EMPLOYEE_ID_PATTERN.sub("[REDACTED ID]", text)
    return text


def redact_pii(text: str, role: str) -> str:
    """Mask HR PII patterns unless the role is legitimately allowed to see HR data."""
    if "hr" in allowed_categories(role):
        return text
    return _mask(text)


if __name__ == "__main__":
    sample = (
        "Aadhya Patel (employee ID FINEMP1000) works as a Sales Manager. "
        "Their email is aadhya.patel@fintechco.com and date of birth is 1991-04-03. "
        "They earn a salary of ₹1,332,478.37."
    )

    print("--- role=marketing (should redact) ---")
    print(redact_pii(sample, role="marketing"))

    print()
    print("--- role=hr (should NOT redact) ---")
    print(redact_pii(sample, role="hr"))

    print()
    print("--- role=c_level (should NOT redact) ---")
    print(redact_pii(sample, role="c_level"))
