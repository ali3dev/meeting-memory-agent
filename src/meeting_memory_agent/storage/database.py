
import sqlite3
from pathlib import Path

from meeting_memory_agent.models import Meeting

SCHEMA = """
CREATE TABLE IF NOT EXISTS meetings (
    meeting_id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    meeting_number INTEGER NOT NULL CHECK (meeting_number > 0),
    meeting_label TEXT NOT NULL,

    UNIQUE (team_id, meeting_number)
);

CREATE TABLE IF NOT EXISTS speaker_turns (
    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL CHECK (turn_index >= 0),
    timestamp TEXT NOT NULL,
    speaker_id TEXT NOT NULL
        CHECK (speaker_id IN ('A', 'B', 'C', 'D')),
    text TEXT NOT NULL CHECK (length(trim(text)) > 0),

    FOREIGN KEY (meeting_id)
        REFERENCES meetings(meeting_id)
        ON DELETE CASCADE,

    UNIQUE (meeting_id, turn_index)
);

CREATE INDEX IF NOT EXISTS idx_meetings_team
ON meetings(team_id);

CREATE INDEX IF NOT EXISTS idx_speaker_turns_meeting
ON speaker_turns(meeting_id, turn_index);
"""


def initialize_database(db_path: Path) -> None:
    """Create database tables if they do not exist."""

    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
    finally:
        connection.close()


def save_meeting(db_path: Path, meeting: Meeting) -> None:
    """Save one meeting and all its speaker turns atomically."""

    connection = sqlite3.connect(db_path)

    try:
        # Enable foreign-key enforcement for this connection.
        connection.execute("PRAGMA foreign_keys = ON")

        # One transaction: either everything succeeds or nothing does.
        with connection:

            connection.execute(
                """
                INSERT INTO meetings (
                    meeting_id,
                    team_id,
                    meeting_number,
                    meeting_label
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    meeting.meeting_id,
                    meeting.team_id,
                    meeting.meeting_number,
                    meeting.meeting_label,
                ),
            )

            turn_records = [
                (
                    meeting.meeting_id,
                    index,
                    turn.timestamp,
                    turn.speaker_id,
                    turn.text,
                )
                for index, turn in enumerate(meeting.turns)
            ]

            connection.executemany(
                """
                INSERT INTO speaker_turns (
                    meeting_id,
                    turn_index,
                    timestamp,
                    speaker_id,
                    text
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                turn_records,
            )

    finally:
        connection.close()
