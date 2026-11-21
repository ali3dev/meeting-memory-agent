
from meeting_memory_agent.generation.prompts import (
    build_generation_messages,
)


def test_build_generation_messages():
    evidence = [
        {
            "meeting_id": "TS3006d",
            "turn_index": 103,
            "speaker_id": "B",
            "text": "We keep the LCD.",
            "context_turns": [
                {
                    "turn_index": 103,
                    "speaker_id": "B",
                    "text": "We keep the LCD.",
                }
            ],
        }
    ]

    messages = build_generation_messages(
        question_id="Q01",
        question="Which feature did the team keep?",
        team_id="TS3006",
        evidence=evidence,
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "TS3006d" in messages[1]["content"]
    assert "Which feature did the team keep?" in messages[1]["content"]


def test_empty_evidence_is_rejected():
    try:
        build_generation_messages(
            question_id="Q01",
            question="Which feature did the team keep?",
            team_id="TS3006",
            evidence=[],
        )
    except ValueError as exc:
        assert "Evidence cannot be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
