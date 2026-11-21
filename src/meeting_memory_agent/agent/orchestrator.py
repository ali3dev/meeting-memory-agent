
from pathlib import Path
from typing import Any

from openai import OpenAI

from meeting_memory_agent.generation.generator import (
    GenerationError,
    generate_answer,
)
from meeting_memory_agent.retrieval.context import (
    expand_evidence_context,
)
from meeting_memory_agent.retrieval.search import (
    retrieve_team_evidence,
)
from meeting_memory_agent.validation.pipeline import (
    validate_answer,
)


def run_question(
    db_path: Path,
    question_id: str,
    question: str,
    team_id: str,
    queries: list[str],
    limit: int = 30,
    per_meeting_limit: int = 8,
    min_meetings: int = 2,
    context_window: int = 3,
    client: OpenAI | None = None,
) -> dict[str, Any]:
    """
    Execute the complete Meeting Memory question-answering pipeline.

    Pipeline:
        Retrieval -> Coverage check -> Context expansion
        -> Generation -> Validation -> Accepted answer
    """

    retrieval = retrieve_team_evidence(
        db_path=db_path,
        team_id=team_id,
        queries=queries,
        limit=limit,
        per_meeting_limit=per_meeting_limit,
        min_meetings=min_meetings,
    )

    evidence = retrieval["evidence"]

    retrieval_details = {
        "meetings_found": retrieval["meetings_found"],
        "meeting_count": retrieval["meeting_count"],
        "required_meetings": retrieval["required_meetings"],
        "evidence_count": len(evidence),
        "queries_used": retrieval.get("queries_used", []),
    }

    if not retrieval["coverage_satisfied"]:
        return {
            "status": "insufficient_evidence",
            "question_id": question_id,
            "team_id": team_id,
            "answer": None,
            "errors": [
                (
                    "Retrieved evidence does not cover enough "
                    "distinct meetings."
                )
            ],
            "retrieval": retrieval_details,
        }

    expanded_evidence = expand_evidence_context(
        db_path=db_path,
        evidence=evidence,
        window=context_window,
    )

    try:
        generation = generate_answer(
            question_id=question_id,
            question=question,
            team_id=team_id,
            evidence=expanded_evidence,
            client=client,
        )
    except GenerationError as exc:
        return {
            "status": "generation_failed",
            "question_id": question_id,
            "team_id": team_id,
            "answer": None,
            "errors": [str(exc)],
            "retrieval": retrieval_details,
        }

    validation = validate_answer(
        db_path=db_path,
        team_id=team_id,
        answer_data=generation["answer"],
        expected_question_id=question_id,
    )

    generation_details = {
        "model": generation["model"],
        "usage": generation["usage"],
    }

    if not validation["valid"]:
        return {
            "status": "validation_failed",
            "question_id": question_id,
            "team_id": team_id,
            "answer": None,
            "generated_answer": generation["answer"],
            "errors": validation["errors"],
            "validation_stage": validation["stage"],
            "validation_details": validation,
            "retrieval": retrieval_details,
            "generation": generation_details,
        }

    return {
        "status": "success",
        "question_id": question_id,
        "team_id": team_id,
        "answer": validation["answer"],
        "validated_citations": validation["validated_citations"],
        "errors": [],
        "retrieval": retrieval_details,
        "generation": generation_details,
    }
