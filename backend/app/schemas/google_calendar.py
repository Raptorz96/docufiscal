from pydantic import BaseModel


class CalendarEventCreate(BaseModel):
    scadenza_id: int | None = None  # se collegato a una scadenza specifica
    summary: str  # titolo evento
    description: str = ""
    event_date: str | None = None  # YYYY-MM-DD per all-day
    start_datetime: str | None = None  # ISO 8601 per evento con orario
    end_datetime: str | None = None
    reminder_minutes: int = 1440  # 24h default


class CalendarEventFromScadenza(BaseModel):
    scadenza_id: int
    reminder_minutes: int = 1440


class CalendarEventOut(BaseModel):
    success: bool
    event_id: str | None = None
    event_link: str | None = None
    error: str | None = None
