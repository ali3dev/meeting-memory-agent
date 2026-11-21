
import sqlite3
from pathlib import Path

from meeting_memory_agent.models import Meeting
from meeting_memory_agent.storage.database import (
    initialize_database,
    save_meeting,
)


def save_meetings(
    db_path: Path,
    meetings: list[Meeting],
) -> tuple[int, list[dict[str, str]]]:
    """
    Save multiple meetings independently.

    If one meeting fails, record its error and continue
    processing the remaining meetings.
    """

    initialize_database(db_path)

    saved_count = 0
    errors: list[dict[str, str]] = []

    for meeting in meetings:
        try:
            save_meeting(db_path, meeting)
            saved_count += 1

        except sqlite3.Error as exc:
            errors.append(
                {
                    "meeting_id": meeting.meeting_id,
                    "team_id": meeting.team_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    return saved_count, errors
