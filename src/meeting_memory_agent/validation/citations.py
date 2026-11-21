
import sqlite3
from pathlib import Path
from typing import Any


def normalize_text(text: str) -> str:
    """
    Normalize whitespace and casing for quote comparison.
    """
    return " ".join(text.casefold().split())


def validate_citations(
    db_path: Path,
    team_id: str,
    citations: list[dict[str, Any]],
    min_quote_words: int = 6,
    min_distinct_meetings: int = 2,
    max_citations: int = 3,
) -> dict[str, Any]:
    """
    Validate citations against exact speaker turns in SQLite.

    A valid citation must:
    - Reference an existing meeting belonging to the team.
    - Match a single speaker turn.
    - Contain at least min_quote_words words.
    - Use a unique meeting/quote combination.
    - Provide evidence from enough distinct meetings.
    """

    errors = []
    validated = []

    if not citations:
        return {
            "valid": False,
            "errors": ["At least one citation is required."],
            "validated_citations": [],
        }

    if len(citations) > max_citations:
        errors.append(
            f"Maximum {max_citations} citations are allowed."
        )

    seen = set()

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row

        for index, citation in enumerate(citations):
            meeting_id = citation.get("meeting_id")
            quote = citation.get("quote")

            if not isinstance(meeting_id, str) or not meeting_id.strip():
                errors.append(
                    f"Citation {index + 1}: Invalid meeting_id."
                )
                continue

            if not isinstance(quote, str) or not quote.strip():
                errors.append(
                    f"Citation {index + 1}: Quote is missing."
                )
                continue

            normalized_quote = normalize_text(quote)
            word_count = len(normalized_quote.split())

            if word_count < min_quote_words:
                errors.append(
                    f"Citation {index + 1}: Quote has "
                    f"{word_count} words; minimum is "
                    f"{min_quote_words}."
                )
                continue

            duplicate_key = (meeting_id, normalized_quote)

            if duplicate_key in seen:
                errors.append(
                    f"Citation {index + 1}: Duplicate citation."
                )
                continue

            seen.add(duplicate_key)

            rows = connection.execute(
                """
                SELECT st.turn_id, st.speaker_id, st.text
                FROM speaker_turns AS st
                JOIN meetings AS m
                    ON m.meeting_id = st.meeting_id
                WHERE m.meeting_id = ?
                  AND m.team_id = ?
                """,
                (meeting_id, team_id),
            ).fetchall()

            matching_turn = next(
                (
                    row
                    for row in rows
                    if normalized_quote
                    in normalize_text(row["text"])
                ),
                None,
            )

            if matching_turn is None:
                errors.append(
                    f"Citation {index + 1}: Quote does not "
                    f"match a single speaker turn in "
                    f"{meeting_id} for team {team_id}."
                )
                continue

            validated.append({
                "meeting_id": meeting_id,
                "speaker_id": matching_turn["speaker_id"],
                "quote": quote,
                "turn_id": matching_turn["turn_id"],
            })

    distinct_meetings = {
        item["meeting_id"] for item in validated
    }

    if len(distinct_meetings) < min_distinct_meetings:
        errors.append(
            f"Citations must cover at least "
            f"{min_distinct_meetings} distinct meetings; "
            f"found {len(distinct_meetings)}."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "validated_citations": validated,
    }
