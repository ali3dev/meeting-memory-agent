
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from meeting_memory_agent.validation.answers import AnswerRecord
from meeting_memory_agent.validation.citations import validate_citations


def validate_answer(
    db_path: Path,
    team_id: str,
    answer_data: dict[str, Any],
    expected_question_id: str | None = None,
) -> dict[str, Any]:
    """
    Run structural and citation validation on one answer.

    Returns a normalized answer only when every check passes.
    """

    # Stage 1: Validate the answer's structure.
    try:
        answer = AnswerRecord.model_validate(answer_data)
    except ValidationError as exc:
        return {
            "valid": False,
            "stage": "structure",
            "errors": [
                error["msg"] for error in exc.errors()
            ],
            "answer": None,
        }

    # Stage 2: Check that the answer belongs to the expected question.
    if (
        expected_question_id is not None
        and answer.question_id != expected_question_id
    ):
        return {
            "valid": False,
            "stage": "question_id",
            "errors": [
                (
                    f"Expected question {expected_question_id}, "
                    f"received {answer.question_id}."
                )
            ],
            "answer": None,
        }

    # Stage 3: Verify citations against the transcript database.
    citation_result = validate_citations(
        db_path=db_path,
        team_id=team_id,
        citations=[
            citation.model_dump()
            for citation in answer.citations
        ],
        min_distinct_meetings=2,
        max_citations=3,
    )

    if not citation_result["valid"]:
        return {
            "valid": False,
            "stage": "citations",
            "errors": citation_result["errors"],
            "answer": None,
        }

    # Stage 4: Return the validated result.
    return {
        "valid": True,
        "stage": "complete",
        "errors": [],
        "answer": answer.model_dump(),
        "validated_citations": citation_result[
            "validated_citations"
        ],
    }
