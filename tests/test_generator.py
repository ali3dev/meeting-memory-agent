
import json
from unittest.mock import MagicMock, patch

import pytest

from meeting_memory_agent.generation.generator import (
    GenerationError,
    generate_answer,
)


@pytest.fixture
def sample_evidence():
    return [
        {
            "meeting_id": "TS3006d",
            "turn_index": 103,
            "speaker_id": "B",
            "text": (
                "We decided to keep the LCD screen "
                "in our final design."
            ),
            "context_turns": [],
        },
        {
            "meeting_id": "TS3006c",
            "turn_index": 50,
            "speaker_id": "A",
            "text": (
                "We discussed keeping the LCD screen "
                "during our earlier meeting."
            ),
            "context_turns": [],
        },
    ]


def make_mock_response(content):
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(content=content),
            finish_reason="stop",
        )
    ]
    response.model = "anthropic/claude-sonnet-4.5"
    response.usage = MagicMock(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
    )
    return response


def make_valid_answer():
    return {
        "question_id": "Q01",
        "answer": (
            "The team kept the LCD screen because removing it "
            "would undermine the product concept."
        ),
        "citations": [
            {
                "meeting_id": "TS3006d",
                "quote": (
                    "We decided to keep the LCD screen "
                    "in our final design."
                ),
            },
            {
                "meeting_id": "TS3006c",
                "quote": (
                    "We discussed keeping the LCD screen "
                    "during our earlier meeting."
                ),
            },
        ],
    }


def patch_model_name():
    return patch(
        "meeting_memory_agent.generation.generator.get_model_name",
        return_value="anthropic/claude-sonnet-4.5",
    )


def test_generate_answer_success(sample_evidence):
    valid_answer = make_valid_answer()

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = (
        make_mock_response(json.dumps(valid_answer))
    )

    with patch_model_name():
        result = generate_answer(
            question_id="Q01",
            question="Which feature did the team keep?",
            team_id="TS3006",
            evidence=sample_evidence,
            client=mock_client,
        )

    assert result["answer"]["question_id"] == "Q01"
    assert result["model"] == "anthropic/claude-sonnet-4.5"
    assert result["usage"]["total_tokens"] == 150
    assert result["attempts"] == 1

    mock_client.chat.completions.create.assert_called_once()


def test_generate_answer_rejects_invalid_json(sample_evidence):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = (
        make_mock_response("This is not JSON")
    )

    with patch_model_name(), pytest.raises(GenerationError, match="invalid JSON"):
        generate_answer(
            question_id="Q01",
            question="Which feature did the team keep?",
            team_id="TS3006",
            evidence=sample_evidence,
            client=mock_client,
        )

    # First attempt and one repair attempt.
    assert mock_client.chat.completions.create.call_count == 2


def test_generate_answer_rejects_invalid_schema(sample_evidence):
    invalid_answer = {
        "question_id": "Q01",
        "answer": "The team kept the LCD screen.",
        "citations": [],
    }

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = (
        make_mock_response(json.dumps(invalid_answer))
    )

    with patch_model_name(), pytest.raises(GenerationError, match="invalid answer"):
        generate_answer(
            question_id="Q01",
            question="Which feature did the team keep?",
            team_id="TS3006",
            evidence=sample_evidence,
            client=mock_client,
        )

    assert mock_client.chat.completions.create.call_count == 2


def test_generate_answer_rejects_wrong_question_id(sample_evidence):
    wrong_answer = make_valid_answer()
    wrong_answer["question_id"] = "Q02"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = (
        make_mock_response(json.dumps(wrong_answer))
    )

    with patch_model_name(), pytest.raises(
        GenerationError,
        match="Expected question ID",
    ):
        generate_answer(
            question_id="Q01",
            question="Which feature did the team keep?",
            team_id="TS3006",
            evidence=sample_evidence,
            client=mock_client,
        )

    assert mock_client.chat.completions.create.call_count == 2


def test_generate_answer_repairs_invalid_first_attempt(sample_evidence):
    invalid_answer = {
        "question_id": "Q01",
        "answer": "The team kept the LCD screen.",
        "citations": [
            {
                "meeting_id": "TS3006d",
                "quote": "We decided to keep the LCD screen in our final design.",
            },
            {
                "meeting_id": "TS3006d",
                "quote": "We decided to keep the LCD screen in our final design.",
            },
        ],
    }

    valid_answer = make_valid_answer()

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        make_mock_response(json.dumps(invalid_answer)),
        make_mock_response(json.dumps(valid_answer)),
    ]

    with patch_model_name():
        result = generate_answer(
            question_id="Q01",
            question="Which feature did the team keep?",
            team_id="TS3006",
            evidence=sample_evidence,
            client=mock_client,
        )

    assert result["answer"]["question_id"] == "Q01"
    assert result["attempts"] == 2
    assert mock_client.chat.completions.create.call_count == 2

    # Both API calls should contribute to reported token usage.
    assert result["usage"]["total_tokens"] == 300
