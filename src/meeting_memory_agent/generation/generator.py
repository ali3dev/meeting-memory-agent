
import json
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from meeting_memory_agent.generation.client import (
    create_llm_client,
    get_model_name,
)
from meeting_memory_agent.generation.prompts import (
    _collect_citation_candidates,
    build_generation_messages,
)
from meeting_memory_agent.validation.answers import AnswerRecord


class GenerationError(RuntimeError):
    """Raised when the model returns an unusable answer."""


MAX_GENERATION_ATTEMPTS = 2


def _validate_generated_answer(
    content: str,
    question_id: str,
    candidate_quotes: set[tuple[str, str]],
    candidate_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate model output and resolve citation IDs to exact quotes."""

    try:
        answer_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise GenerationError(
            "The model returned invalid JSON"
        ) from exc

    if not isinstance(answer_data, dict):
        raise GenerationError("The model response must be a JSON object")

    citation_ids = answer_data.pop("citation_ids", None)

    if citation_ids is not None:
        if not isinstance(citation_ids, list):
            raise GenerationError("citation_ids must be a list")

        if not 2 <= len(citation_ids) <= 3:
            raise GenerationError(
                "The model must select between 2 and 3 citation IDs"
            )

        if candidate_map is None:
            raise GenerationError(
                "Citation ID mapping is unavailable"
            )

        if len(set(citation_ids)) != len(citation_ids):
            raise GenerationError("Duplicate citation IDs are not allowed")

        citations = []

        for citation_id in citation_ids:
            candidate = candidate_map.get(citation_id)

            if candidate is None:
                raise GenerationError(
                    f"Unknown citation ID: {citation_id}"
                )

            citations.append(
                {
                    "meeting_id": candidate["meeting_id"],
                    "quote": candidate["quote"],
                }
            )

        answer_data["citations"] = citations

    try:
        answer = AnswerRecord.model_validate(answer_data)
    except ValidationError as exc:
        raise GenerationError(
            f"The model returned an invalid answer: {exc}"
        ) from exc

    if answer.question_id != question_id:
        raise GenerationError(
            f"Expected question ID {question_id}, "
            f"received {answer.question_id}"
        )

    cited_meetings = set()

    for index, citation in enumerate(answer.citations, start=1):
        quote = citation.quote
        meeting_id = citation.meeting_id

        if len(quote.split()) < 6:
            raise GenerationError(
                f"Citation {index}: quote has fewer than six words."
            )

        if (meeting_id, quote) not in candidate_quotes:
            raise GenerationError(
                f"Citation {index}: quote is not an exact "
                "supplied citation candidate."
            )

        cited_meetings.add(meeting_id)

    if len(cited_meetings) < 2:
        raise GenerationError(
            "Citations must cover at least two distinct meetings."
        )

    return answer.model_dump()


def generate_answer(
    question_id: str,
    question: str,
    team_id: str,
    evidence: list[dict[str, Any]],
    client: OpenAI | None = None,
) -> dict[str, Any]:
    """Generate an answer and resolve citations deterministically."""

    if client is None:
        client = create_llm_client()

    model = get_model_name()

    candidates = _collect_citation_candidates(evidence)

    candidate_quotes = {
        (candidate["meeting_id"], candidate["quote"])
        for candidate in candidates
    }

    candidate_map = {
        candidate["citation_id"]: candidate
        for candidate in candidates
    }

    eligible_meetings = {
        candidate["meeting_id"]
        for candidate in candidates
    }

    if len(eligible_meetings) < 2:
        raise GenerationError(
            "Evidence contains fewer than two meetings "
            "with eligible citation candidates."
        )

    messages = build_generation_messages(
        question_id=question_id,
        question=question,
        team_id=team_id,
        evidence=evidence,
    )

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    last_error = None
    last_content = None

    for attempt in range(MAX_GENERATION_ATTEMPTS):
        request_messages = list(messages)

        if attempt > 0:
            request_messages.extend(
                [
                    {
                        "role": "assistant",
                        "content": last_content or "{}",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response failed: {last_error}. "
                            "Return corrected JSON. Select only valid "
                            "citation IDs from the original payload. "
                            "Use at least two distinct meeting IDs."
                        ),
                    },
                ]
            )

        response = client.chat.completions.create(
            model=model,
            messages=request_messages,
            temperature=0.2,
            max_completion_tokens=512,
            response_format={"type": "json_object"},
            extra_body={
                "reasoning_effort": "low",
                "include_reasoning": False,
            },
        )

        usage = response.usage

        if usage:
            total_prompt_tokens += usage.prompt_tokens or 0
            total_completion_tokens += usage.completion_tokens or 0
            total_tokens += usage.total_tokens or 0

        if not response.choices:
            last_error = "The model returned no choices"
            continue

        choice = response.choices[0]
        content = choice.message.content
        last_content = content

        if choice.finish_reason == "length":
            last_error = "The model reached its token limit"
            continue

        if not content:
            last_error = (
                f"Empty model response: {choice.finish_reason}"
            )
            continue

        try:
            answer_data = _validate_generated_answer(
                content=content,
                question_id=question_id,
                candidate_quotes=candidate_quotes,
                candidate_map=candidate_map,
            )
        except GenerationError as exc:
            last_error = str(exc)
            continue

        return {
            "answer": answer_data,
            "model": response.model,
            "usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens,
            },
            "attempts": attempt + 1,
        }

    raise GenerationError(
        f"Generation failed after {MAX_GENERATION_ATTEMPTS} attempts. "
        f"Last error: {last_error}"
    )
