
import sqlite3
from pathlib import Path

from meeting_memory_agent.ingestion.parser import parse_meeting_file
from meeting_memory_agent.storage.database import (
    initialize_database,
)


def test_transaction_rollback():
    db_path = Path("data/rollback_test.db")
    transcript_path = Path("data/transcripts/TS3012a.txt")

    meeting = parse_meeting_file(transcript_path)

    initialize_database(db_path)

    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO meetings
                    (meeting_id, team_id, meeting_number, meeting_label)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        meeting.meeting_id,
                        meeting.team_id,
                        meeting.meeting_number,
                        meeting.meeting_label,
                    ),
                )

                for index, turn in enumerate(meeting.turns):
                    speaker_id = (
                        "Z" if index == 50 else turn.speaker_id
                    )

                    connection.execute(
                        """
                        INSERT INTO speaker_turns
                        (meeting_id, turn_index, timestamp, speaker_id, text)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            meeting.meeting_id,
                            index,
                            turn.timestamp,
                            speaker_id,
                            turn.text,
                        ),
                    )

        except sqlite3.IntegrityError as exc:
            print("Expected database failure:", exc)

        meeting_count = connection.execute(
            "SELECT COUNT(*) FROM meetings"
        ).fetchone()[0]

        turn_count = connection.execute(
            "SELECT COUNT(*) FROM speaker_turns"
        ).fetchone()[0]

        print("Meetings after rollback:", meeting_count)
        print("Turns after rollback:", turn_count)

        assert meeting_count == 0
        assert turn_count == 0

        print("ROLLBACK TEST PASSED")

    finally:
        connection.close()


if __name__ == "__main__":
    test_transaction_rollback()
