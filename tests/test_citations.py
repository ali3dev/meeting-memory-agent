
from pathlib import Path

from meeting_memory_agent.validation.citations import (
    validate_citations,
)


DB_PATH = Path("data/meeting_memory_full.db")


def test_valid_citations_from_two_meetings():
    citations = [
        {
            "meeting_id": "TS3006d",
            "quote": (
                "We lose our whole concept. "
                "Uh so No we just We keep the L_C_D_."
            ),
        },
        {
            "meeting_id": "TS3006b",
            "quote": (
                "And we do have to integrate the "
                "screen and the the speech alright."
            ),
        },
    ]

    result = validate_citations(
        DB_PATH,
        "TS3006",
        citations,
    )

    assert result["valid"] is True
    assert len(result["validated_citations"]) == 2


def test_reject_fabricated_quote():
    citations = [
        {
            "meeting_id": "TS3006d",
            "quote": (
                "The team decided to remove speech recognition."
            ),
        },
        {
            "meeting_id": "TS3006b",
            "quote": (
                "The team decided to keep the LCD screen."
            ),
        },
    ]

    result = validate_citations(
        DB_PATH,
        "TS3006",
        citations,
    )

    assert result["valid"] is False


def test_reject_insufficient_meetings():
    citations = [
        {
            "meeting_id": "TS3006d",
            "quote": (
                "We lose our whole concept. "
                "Uh so No we just We keep the L_C_D_."
            ),
        },
    ]

    result = validate_citations(
        DB_PATH,
        "TS3006",
        citations,
    )

    assert result["valid"] is False
    assert any(
        "distinct meetings" in error
        for error in result["errors"]
    )


if __name__ == "__main__":
    test_valid_citations_from_two_meetings()
    test_reject_fabricated_quote()
    test_reject_insufficient_meetings()
    print("All citation validation checks passed.")
