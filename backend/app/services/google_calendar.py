"""Google Calendar service utilities."""
import logging
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.google_token import GoogleToken

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_valid_credentials(db: Session, user_id: int) -> Credentials | None:
    """Get valid Google credentials for a user, refreshing if needed.

    Returns None if user has no token or refresh fails.
    """
    token = db.query(GoogleToken).filter(GoogleToken.user_id == user_id).first()
    if not token:
        return None

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Update stored tokens
            token.access_token = creds.token
            if creds.refresh_token:
                token.refresh_token = creds.refresh_token
            token.token_expiry = creds.expiry
            db.commit()
            logger.info("Google token refreshed for user %d", user_id)
        except Exception:
            logger.exception("Failed to refresh Google token for user %d", user_id)
            return None

    return creds


def create_calendar_event(
    db: Session,
    user_id: int,
    summary: str,
    description: str = "",
    event_date: str | None = None,  # YYYY-MM-DD — all-day event
    start_datetime: str | None = None,  # ISO 8601 — timed event
    end_datetime: str | None = None,
    reminder_minutes: int = 1440,  # default: 24h prima
) -> dict | None:
    """Create a Google Calendar event for the given user.

    Supports two modes:
    - All-day event: pass event_date (YYYY-MM-DD)
    - Timed event: pass start_datetime + end_datetime (ISO 8601)

    Returns the created event dict from Google API, or None on failure.
    """
    creds = get_valid_credentials(db, user_id)
    if not creds:
        logger.warning("No valid Google credentials for user %d", user_id)
        return None

    try:
        service = build("calendar", "v3", credentials=creds)

        event_body: dict = {
            "summary": summary,
            "description": description,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": reminder_minutes},
                ],
            },
        }

        if event_date:
            # All-day event
            event_body["start"] = {"date": event_date}
            event_body["end"] = {"date": event_date}
        elif start_datetime and end_datetime:
            # Timed event
            event_body["start"] = {"dateTime": start_datetime, "timeZone": "Europe/Rome"}
            event_body["end"] = {"dateTime": end_datetime, "timeZone": "Europe/Rome"}
        else:
            logger.error("create_calendar_event: no date provided")
            return None

        result = service.events().insert(calendarId="primary", body=event_body).execute()
        logger.info("Google Calendar event created for user %d: %s", user_id, result.get("id"))
        return result

    except Exception:
        logger.exception("Failed to create Google Calendar event for user %d", user_id)
        return None
