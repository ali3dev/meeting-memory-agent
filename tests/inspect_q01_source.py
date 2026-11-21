import sqlite3
from pathlib import Path

DB_PATH = Path("data/meeting_memory_full.db")

with sqlite3.connect(DB_PATH) as connection:
    rows = connection.execute(
        """
        SELECT meeting_id, turn_index, speaker_id, text
        FROM speaker_turns
        WHERE meeting_id IN (
            'TS3006a',
            'TS3006b',
            'TS3006c',
            'TS3006d'
        )
        AND (
            LOWER(text) LIKE '%lcd%'
            OR LOWER(text) LIKE '%speech recognition%'
            OR LOWER(text) LIKE '%speech%'
        )
        ORDER BY meeting_id, turn_index
        """
    ).fetchall()

for meeting_id, turn_index, speaker_id, text in rows:
    print(
        f"\n{meeting_id} | Turn {turn_index} | "
        f"Speaker {speaker_id}\n{text}"
    )