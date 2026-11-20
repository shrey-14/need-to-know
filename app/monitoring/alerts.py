# Threshold check against daily_cost_alert_usd, with an email notifier over
# SMTP. Provider-agnostic on purpose: Gmail (app password), a transactional
# provider (Resend, SendGrid, Postmark, Amazon SES) or Azure Communication
# Services all accept plain SMTP, so switching provider is a config change,
# not a code change. Monitoring phase.
import datetime
import smtplib
from email.message import EmailMessage

import psycopg

from app.core.config import get_settings

settings = get_settings()

# In-memory "did we already alert today" guard, so a threshold that's already
# been crossed doesn't send another email on every subsequent request for the
# rest of the day. Resets naturally when the date changes. Losing this on a
# server restart just risks one duplicate alert, not lost data — unlike
# cost_log itself, this doesn't need to be persisted in Supabase.
_last_alert_date: datetime.date | None = None


def get_today_cost() -> float:
    """Sum estimated_cost from cost_log for rows timestamped today — using the
    database's own clock (CURRENT_DATE), not Python's, so app-server/DB
    timezone differences can't put a row on the "wrong" day."""
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        result = conn.execute(
            """
            SELECT COALESCE(SUM(estimated_cost), 0)
            FROM cost_log
            WHERE timestamp::date = CURRENT_DATE
            """
        ).fetchone()
    return float(result[0])


def email_configured() -> bool:
    return bool(settings.alert_email_to and settings.smtp_host and settings.smtp_username)


def send_email_alert(subject: str, body: str) -> None:
    """Send one plain-text alert email. Never raises — a notification failure
    must not break the chat response that triggered it."""
    if not email_configured():
        print(f"[alerts] email not configured — would have alerted: {subject}")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.alert_email_from or settings.smtp_username
    message["To"] = settings.alert_email_to
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            try:
                smtp.login(settings.smtp_username, settings.smtp_password)
            except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected) as exc:
                # Gmail either rejects or simply drops the connection on bad
                # credentials, so both mean "check the login", not "network".
                print(
                    f"[alerts] SMTP login rejected ({exc}). Check SMTP_USERNAME, and that "
                    "SMTP_PASSWORD is an app password (Gmail: 16 letters, needs 2-Step "
                    "Verification), not the account password."
                )
                return
            smtp.send_message(message)
        print("[alerts] alert email sent.")
    except Exception as exc:
        print(f"[alerts] failed to send alert email: {exc}")


def check_daily_cost_threshold() -> None:
    """Check today's cost against the configured threshold, and alert at most
    once per day if it's exceeded. Call this after every logged LLM request."""
    global _last_alert_date

    today_cost = get_today_cost()
    if today_cost < settings.daily_cost_alert_usd:
        return

    today = datetime.date.today()
    if _last_alert_date == today:
        return  # already alerted today, don't spam

    threshold = settings.daily_cost_alert_usd
    send_email_alert(
        subject=f"[FinSolve Assistant] Daily LLM cost ${today_cost:.4f} exceeded ${threshold:.2f}",
        body=(
            f"Today's estimated LLM cost is ${today_cost:.6f}, above the daily alert "
            f"threshold of ${threshold:.2f} (DAILY_COST_ALERT_USD).\n\n"
            f"Date (server): {today.isoformat()}\n\n"
            "Where to look:\n"
            "- Supabase: the cost_log table, for per-request tokens, cost, role and latency.\n"
            "- Groq console: usage and limits for the API key.\n\n"
            "You'll get at most one of these per day."
        ),
    )
    _last_alert_date = today


if __name__ == "__main__":
    print(f"Today's cost so far: ${get_today_cost():.6f}")
    check_daily_cost_threshold()
