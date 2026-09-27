# Threshold check against daily_cost_alert_usd, with a Slack webhook notifier.
# Monitoring phase.
import datetime

import psycopg
import requests

from app.core.config import get_settings

settings = get_settings()

# In-memory "did we already alert today" guard, so a threshold that's already
# been crossed doesn't re-post to Slack on every subsequent request for the
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


def send_slack_alert(message: str) -> None:
    """POST a message to the configured Slack incoming webhook. Never raises —
    a notification failure must not break the chat response that triggered it."""
    if not settings.slack_webhook_url:
        print(f"[alerts] SLACK_WEBHOOK_URL not set — would have alerted: {message}")
        return
    try:
        response = requests.post(settings.slack_webhook_url, json={"text": message}, timeout=5)
        response.raise_for_status()
        print("[alerts] Slack alert sent.")
    except Exception as exc:
        print(f"[alerts] failed to send Slack alert: {exc}")


def check_daily_cost_threshold() -> None:
    """Check today's cost against the configured threshold, and alert at most
    once per day if it's exceeded. Call this after every logged LLM request."""
    global _last_alert_date

    today_cost = get_today_cost()
    if today_cost < settings.daily_cost_alert_usd:
        print(f"Today's cost so far: ${today_cost:.6f}")
        return

    today = datetime.date.today()
    if _last_alert_date == today:
        return  # already alerted today, don't spam

    send_slack_alert(
        f"ALERT: FinSolve Terminal's cost today (${today_cost:.6f}) has exceeded "
        f"the ${settings.daily_cost_alert_usd:.6f} daily threshold."
    )
    _last_alert_date = today


if __name__ == "__main__":
    print(f"Today's cost so far: ${get_today_cost():.6f}")
    check_daily_cost_threshold()
