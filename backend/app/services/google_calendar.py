"""Google Calendar service utilities."""
import logging
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
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
