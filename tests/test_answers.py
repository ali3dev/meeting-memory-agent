
import pytest
from pydantic import ValidationError

from meeting_memory_agent.validation.answers import AnswerRecord


def valid_answer_data():
    return {
        "question_id": "Q01",
        "answer": (
            "The team dropped speech recognition but kept "
            "the LCD screen. Removing the screen would require "
            "many extra buttons and undermine their concept."
        ),
        "citations": [
            {
                "meeting_id": "TS3006d",
                "quote": (
                    "We lose our whole concept. Uh so No we just "
                    "We keep the L_C_D_."
                ),
            },
            {
                "meeting_id": "TS3006b",
                "quote": (
                    "And we do have to integrate the screen "
                    "and the the speech alright."
                ),
            },
        ],
    }


def test_valid_answer_record():
    result = AnswerRecord.model_validate(valid_answer_data())

    assert result.question_id == "Q01"
    assert len(result.citations) == 2


def test_reject_four_sentences():
    data = valid_answer_data()
    data["answer"] = "First. Second. Third. Fourth."

    with pytest.raises(ValidationError):
        AnswerRecord.model_validate(data)


def test_reject_missing_citations():
    data = valid_answer_data()
    data["citations"] = []

    with pytest.raises(ValidationError):
        AnswerRecord.model_validate(data)


def test_reject_more_than_three_citations():
    data = valid_answer_data()
    data["citations"].append({
        "meeting_id": "TS3006c",
        "quote": "This is an additional citation for testing.",
    })
    data["citations"].append({
        "meeting_id": "TS3006a",
        "quote": "This is another additional citation for testing.",
    })

    with pytest.raises(ValidationError):
        AnswerRecord.model_validate(data)


def test_reject_unexpected_fields():
    data = valid_answer_data()
    data["unexpected_field"] = "not allowed"

    with pytest.raises(ValidationError):
        AnswerRecord.model_validate(data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
