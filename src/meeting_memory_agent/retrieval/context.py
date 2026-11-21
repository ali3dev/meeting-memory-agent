import sqlite3
from pathlib import Path


def expand_evidence_context(
    db_path: Path,
    evidence: list[dict],
    window: int = 3,
) -> list[dict]:
    """
    Expand retrieved evidence with surrounding speaker turns.

    Each original evidence record is preserved.
    Context is added separately so citations can still
    reference the exact original speaker turn.
    """

    if window < 0:
        raise ValueError("Window cannot be negative")

    if not evidence:
        return []

    expanded = []

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row

        for item in evidence:
            meeting_id = item["meeting_id"]
            turn_index = item["turn_index"]

            rows = connection.execute(
                """
                SELECT
                    turn_index,
                    timestamp,
                    speaker_id,
                    text
                FROM speaker_turns
                WHERE meeting_id = ?
                  AND turn_index BETWEEN ? AND ?
                ORDER BY turn_index
                """,
                (
                    meeting_id,
                    max(0, turn_index - window),
                    turn_index + window,
                ),
            ).fetchall()

            context_turns = [
                dict(row) for row in rows
            ]

            expanded.append({
                **item,
                "context_turns": context_turns,
            })

    return expanded
