
from pathlib import Path

from meeting_memory_agent.validation.pipeline import validate_answer


DB_PATH = Path("data/meeting_memory_full.db")


def valid_answer_data():
    return {
        "question_id": "Q01",
        "answer": (
            "Earlier, the team discussed integrating both "
            "the screen and speech recognition. Later, they "
            "kept the LCD screen and dropped speech recognition."
        ),
        "citations": [
            {
                "meeting_id": "TS3006b",
                "quote": (
                    "And we do have to integrate the screen "
                    "and the the speech alright."
                ),
            },
            {
                "meeting_id": "TS3006d",
                "quote": (
                    "We lose our whole concept. Uh so No we just "
                    "We keep the L_C_D_."
                ),
            },
        ],
    }


def test_pipeline_accepts_valid_answer():
    result = validate_answer(
        DB_PATH,
        "TS3006",
        valid_answer_data(),
        expected_question_id="Q01",
    )

    assert result["valid"] is True
    assert result["stage"] == "complete"
    assert len(result["validated_citations"]) == 2


def test_pipeline_rejects_invalid_quote():
    data = valid_answer_data()
    data["citations"][1]["quote"] = (
        "The team decided to remove speech recognition."
    )

    result = validate_answer(
        DB_PATH,
        "TS3006",
        data,
        expected_question_id="Q01",
    )

    assert result["valid"] is False
    assert result["stage"] == "citations"


def test_pipeline_rejects_same_meeting_twice():
    data = valid_answer_data()
    data["citations"][1]["meeting_id"] = "TS3006b"

    result = validate_answer(
        DB_PATH,
        "TS3006",
        data,
        expected_question_id="Q01",
    )

    assert result["valid"] is False
    assert result["stage"] == "citations"


def test_pipeline_rejects_wrong_question_id():
    result = validate_answer(
        DB_PATH,
        "TS3006",
        valid_answer_data(),
        expected_question_id="Q02",
    )

    assert result["valid"] is False
    assert result["stage"] == "question_id"


def test_pipeline_rejects_invalid_structure():
    data = valid_answer_data()
    data["answer"] = "First. Second. Third. Fourth."

    result = validate_answer(
        DB_PATH,
        "TS3006",
        data,
    )

    assert result["valid"] is False
    assert result["stage"] == "structure"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
