from datetime import datetime, timezone
from zoneinfo import ZoneInfo


LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_now() -> datetime:
    return datetime.now(LOCAL_TIMEZONE)


def format_local_datetime(value: datetime | None) -> str:
    if not value:
        return "-"

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(LOCAL_TIMEZONE).strftime("%d/%m/%Y %H:%M")
