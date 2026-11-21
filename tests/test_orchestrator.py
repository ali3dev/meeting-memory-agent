
from pathlib import Path

from meeting_memory_agent.agent import orchestrator


def sample_retrieval(coverage_satisfied=True):
    return {
        "team_id": "TS3006",
        "queries_used": 2,
        "evidence": [
            {
                "turn_id": 1,
                "meeting_id": "TS3006b",
                "turn_index": 10,
                "text": "The team discussed the LCD screen.",
            },
            {
                "turn_id": 2,
                "meeting_id": "TS3006d",
                "turn_index": 20,
                "text": "The team decided to keep the LCD screen.",
            },
        ],
        "meetings_found": ["TS3006b", "TS3006d"],
        "meeting_count": 2,
        "required_meetings": 2,
        "coverage_satisfied": coverage_satisfied,
    }


def sample_generation():
    return {
        "answer": {
            "question_id": "Q01",
            "answer": "The team kept the LCD screen because it was central to the product concept.",
            "citations": [
                {
                    "meeting_id": "TS3006b",
                    "quote": "The team discussed the LCD screen in detail.",
                },
                {
                    "meeting_id": "TS3006d",
                    "quote": "We lose our whole concept. We keep the LCD screen.",
                },
            ],
        },
        "model": "test-model",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }


def sample_validation(valid=True):
    if not valid:
        return {
            "valid": False,
            "stage": "citations",
            "errors": ["Citation quote was not found."],
            "answer": None,
        }

    generation = sample_generation()

    return {
        "valid": True,
        "stage": "complete",
        "errors": [],
        "answer": generation["answer"],
        "validated_citations": [],
    }


def test_insufficient_coverage_skips_generation(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "retrieve_team_evidence",
        lambda **kwargs: sample_retrieval(False),
    )

    def unexpected_generation(**kwargs):
        raise AssertionError("Generation should not be called")

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        unexpected_generation,
    )

    result = orchestrator.run_question(
        db_path=Path("test.db"),
        question_id="Q01",
        question="Why did the team keep the LCD screen?",
        team_id="TS3006",
        queries=["LCD screen"],
    )

    assert result["status"] == "insufficient_evidence"
    assert result["answer"] is None


def test_orchestrator_accepts_valid_answer(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "retrieve_team_evidence",
        lambda **kwargs: sample_retrieval(True),
    )

    monkeypatch.setattr(
        orchestrator,
        "expand_evidence_context",
        lambda **kwargs: kwargs["evidence"],
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        lambda **kwargs: sample_generation(),
    )

    monkeypatch.setattr(
        orchestrator,
        "validate_answer",
        lambda **kwargs: sample_validation(True),
    )

    result = orchestrator.run_question(
        db_path=Path("test.db"),
        question_id="Q01",
        question="Why did the team keep the LCD screen?",
        team_id="TS3006",
        queries=["LCD screen"],
    )

    assert result["status"] == "success"
    assert result["answer"]["question_id"] == "Q01"
    assert result["errors"] == []


def test_orchestrator_rejects_invalid_answer(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "retrieve_team_evidence",
        lambda **kwargs: sample_retrieval(True),
    )

    monkeypatch.setattr(
        orchestrator,
        "expand_evidence_context",
        lambda **kwargs: kwargs["evidence"],
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        lambda **kwargs: sample_generation(),
    )

    monkeypatch.setattr(
        orchestrator,
        "validate_answer",
        lambda **kwargs: sample_validation(False),
    )

    result = orchestrator.run_question(
        db_path=Path("test.db"),
        question_id="Q01",
        question="Why did the team keep the LCD screen?",
        team_id="TS3006",
        queries=["LCD screen"],
    )

    assert result["status"] == "validation_failed"
    assert result["answer"] is None
    assert "Citation quote was not found." in result["errors"]
