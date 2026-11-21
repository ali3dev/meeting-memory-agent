import re
import sqlite3
from pathlib import Path

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS speaker_turns_fts
USING fts5(
    text,
    content='speaker_turns',
    content_rowid='turn_id',
    tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS speaker_turns_ai
AFTER INSERT ON speaker_turns
BEGIN
    INSERT INTO speaker_turns_fts(rowid, text)
    VALUES (new.turn_id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS speaker_turns_ad
AFTER DELETE ON speaker_turns
BEGIN
    INSERT INTO speaker_turns_fts(
        speaker_turns_fts, rowid, text
    )
    VALUES ('delete', old.turn_id, old.text);
END;

CREATE TRIGGER IF NOT EXISTS speaker_turns_au
AFTER UPDATE ON speaker_turns
BEGIN
    INSERT INTO speaker_turns_fts(
        speaker_turns_fts, rowid, text
    )
    VALUES ('delete', old.turn_id, old.text);

    INSERT INTO speaker_turns_fts(rowid, text)
    VALUES (new.turn_id, new.text);
END;
"""


STOP_WORDS = {
    "what", "which", "who", "when", "where", "why", "how",
    "did", "does", "do", "was", "were", "is", "are", "the",
    "a", "an", "and", "or", "of", "to", "in", "on", "for",
    "their", "they", "them", "it", "its", "with", "about",
    "team", "meeting", "remote", "control",
}


def initialize_search_index(db_path: Path) -> None:
    """Create the FTS5 index and rebuild it only when needed."""

    with sqlite3.connect(db_path) as connection:
        existing_index = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'speaker_turns_fts'
            """
        ).fetchone()

        connection.executescript(FTS_SCHEMA)

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS search_index_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        initialized = connection.execute(
            """
            SELECT value
            FROM search_index_metadata
            WHERE key = 'fts5_rebuilt'
            """
        ).fetchone()

        if existing_index is None or initialized is None:
            connection.execute(
                """
                INSERT INTO speaker_turns_fts(speaker_turns_fts)
                VALUES ('rebuild')
                """
            )

            connection.execute(
                """
                INSERT INTO search_index_metadata (key, value)
                VALUES ('fts5_rebuilt', 'true')
                ON CONFLICT(key)
                DO UPDATE SET value = excluded.value
                """
            )


def build_fts_query(query: str) -> str:
    """Convert ordinary text into a safe, broad FTS5 OR query."""

    if not query.strip():
        raise ValueError("Search query cannot be empty")

    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())

    keywords = list(
        dict.fromkeys(
            token for token in tokens
            if token not in STOP_WORDS
        )
    )

    if not keywords:
        raise ValueError("Search query contains no useful keywords")

    return " OR ".join(f'"{word}"' for word in keywords)


def search_turns(
    db_path: Path,
    query: str,
    team_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Search transcript turns using ordinary text and team filtering."""

    if limit <= 0:
        raise ValueError("Limit must be greater than zero")

    fts_query = build_fts_query(query)

    sql = """
        SELECT
            s.turn_id,
            s.meeting_id,
            m.team_id,
            m.meeting_number,
            s.turn_index,
            s.timestamp,
            s.speaker_id,
            s.text,
            bm25(speaker_turns_fts) AS relevance

        FROM speaker_turns_fts

        JOIN speaker_turns AS s
            ON s.turn_id = speaker_turns_fts.rowid

        JOIN meetings AS m
            ON m.meeting_id = s.meeting_id

        WHERE speaker_turns_fts MATCH ?
    """

    parameters: list = [fts_query]

    if team_id is not None:
        sql += " AND m.team_id = ?"
        parameters.append(team_id)

    sql += """
        ORDER BY relevance ASC
        LIMIT ?
    """

    parameters.append(limit)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            sql,
            parameters,
        ).fetchall()

        return [dict(row) for row in rows]


def retrieve_team_evidence(
    db_path: Path,
    team_id: str,
    queries: list[str],
    limit: int = 30,
    per_meeting_limit: int = 8,
    min_meetings: int = 2,
) -> dict:
    """
    Retrieve and combine evidence from multiple queries.

    Reciprocal Rank Fusion combines rankings without assuming
    BM25 scores from different queries are directly comparable.
    """

    if not team_id.strip():
        raise ValueError("Team ID cannot be empty")

    if not queries:
        raise ValueError("At least one search query is required")

    if limit <= 0 or per_meeting_limit <= 0:
        raise ValueError("Limits must be greater than zero")

    if min_meetings <= 0:
        raise ValueError("Minimum meetings must be greater than zero")

    candidates: dict[int, dict] = {}
    rrf_constant = 60

    candidate_limit = max(limit * 4, 50)

    for query in queries:
        results = search_turns(
            db_path=db_path,
            query=query,
            team_id=team_id,
            limit=candidate_limit,
        )

        for rank, result in enumerate(results, start=1):
            turn_id = result["turn_id"]

            if turn_id not in candidates:
                candidates[turn_id] = {
                    **result,
                    "fused_score": 0.0,
                    "matched_queries": [],
                }

            candidates[turn_id]["fused_score"] += (
                1 / (rrf_constant + rank)
            )

            candidates[turn_id]["matched_queries"].append(query)

    ranked = sorted(
        candidates.values(),
        key=lambda item: item["fused_score"],
        reverse=True,
    )

    selected: list[dict] = []
    selected_ids: set[int] = set()
    meeting_counts: dict[str, int] = {}

    # First pass: prioritize coverage across distinct meetings.
    for candidate in ranked:
        meeting_id = candidate["meeting_id"]

        if meeting_id in meeting_counts:
            continue

        selected.append(candidate)
        selected_ids.add(candidate["turn_id"])
        meeting_counts[meeting_id] = 1

        if len(selected) >= limit:
            break

    # Second pass: fill remaining slots by relevance.
    for candidate in ranked:
        if len(selected) >= limit:
            break

        turn_id = candidate["turn_id"]

        if turn_id in selected_ids:
            continue

        meeting_id = candidate["meeting_id"]
        current_count = meeting_counts.get(meeting_id, 0)

        if current_count >= per_meeting_limit:
            continue

        selected.append(candidate)
        selected_ids.add(turn_id)
        meeting_counts[meeting_id] = current_count + 1

    meeting_ids = sorted(meeting_counts)

    return {
        "team_id": team_id,
        "queries_used": len(queries),
        "evidence": selected,
        "meetings_found": meeting_ids,
        "meeting_count": len(meeting_ids),
        "required_meetings": min_meetings,
        "coverage_satisfied": len(meeting_ids) >= min_meetings,
    }
