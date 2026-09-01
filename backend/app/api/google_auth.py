import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.google_token import GoogleToken
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/google", tags=["google"])

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# In-memory state store (state → user_id). Entries expire naturally.
# TODO: migrate to Redis if scaling beyond single instance.
_pending_states: dict[str, int] = {}


def _create_flow() -> Flow:
    """Create a Google OAuth2 flow from settings."""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow


class GoogleStatusOut(BaseModel):
    connected: bool
    scope: str | None = None


@router.get("/authorize")
def google_authorize(current_user: User = Depends(get_current_user)):
    """Generate Google OAuth2 authorization URL and return it."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integration not configured",
        )

    flow = _create_flow()
    state = secrets.token_urlsafe(32)
    _pending_states[state] = current_user.id

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return {"authorization_url": authorization_url}


@router.get("/callback")
def google_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth2 callback. Exchanges code for tokens and saves them."""
    user_id = _pending_states.pop(state, None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter",
        )

    flow = _create_flow()
    try:
        flow.fetch_token(code=code)
    except Exception:
        logger.exception("Failed to exchange Google OAuth2 code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code",
        )

    credentials = flow.credentials

    # Upsert token
    existing = db.query(GoogleToken).filter(GoogleToken.user_id == user_id).first()
    if existing:
        existing.access_token = credentials.token
        existing.refresh_token = credentials.refresh_token or existing.refresh_token
        existing.token_expiry = credentials.expiry
        existing.scope = " ".join(credentials.scopes or SCOPES)
    else:
        token = GoogleToken(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token or "",
            token_expiry=credentials.expiry,
            scope=" ".join(credentials.scopes or SCOPES),
        )
        db.add(token)

    db.commit()
    logger.info("Google OAuth2 tokens saved for user %d", user_id)

    # Redirect to frontend profile page with success indicator
    frontend_base = settings.GOOGLE_REDIRECT_URI.replace("/api/v1/google/callback", "")
    return RedirectResponse(url=f"{frontend_base}/profilo?google=connected")


@router.get("/status", response_model=GoogleStatusOut)
def google_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if current user has Google Calendar connected."""
    token = db.query(GoogleToken).filter(GoogleToken.user_id == current_user.id).first()
    if token:
        return GoogleStatusOut(connected=True, scope=token.scope)
    return GoogleStatusOut(connected=False)


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def google_disconnect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove Google Calendar connection for current user."""
    token = db.query(GoogleToken).filter(GoogleToken.user_id == current_user.id).first()
    if token:
        db.delete(token)
        db.commit()
        logger.info("Google Calendar disconnected for user %d", current_user.id)
