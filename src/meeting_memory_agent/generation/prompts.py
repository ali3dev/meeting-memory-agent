
import json
from typing import Any

SYSTEM_PROMPT = """
You are a careful meeting-memory research assistant.

Answer using ONLY the supplied meeting evidence.

RULES:
1. Never invent facts, decisions, dates, costs, names, or speaker identities.
2. Distinguish proposals, discussions, and final decisions.
3. Explain how decisions evolved when relevant.
4. Answer in 1 to 3 plain sentences.
5. Use evidence from at least TWO DISTINCT meetings.
6. Select between 2 and 3 citation IDs.
7. Every selected citation must directly support the answer.
8. Never select two citations from the same meeting.
9. Never invent or modify a citation ID.
10. If evidence is insufficient, say so rather than inventing facts.
11. Identify speakers by A, B, C, or D only when relevant.
12. Include a speaker role only when explicitly established.

CITATION RULES:
- Select IDs ONLY from the supplied citation_candidates.
- Each candidate represents one exact speaker turn.
- Python will attach the original transcript quote.
- NEVER generate quotations yourself.
- NEVER return meeting IDs or quote text.
- Choose the most relevant candidates from different meetings.

Return ONLY valid JSON in this format:

{
  "question_id": "Q01",
  "answer": "Your answer in 1 to 3 sentences.",
  "citation_ids": ["C001", "C002"]
}
"""


def _collect_citation_candidates(
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect exact speaker turns eligible for citation."""

    candidates: list[dict[str, Any]] = []
    seen_turns: set[tuple[str, int]] = set()

    for item in evidence:
        meeting_id = item["meeting_id"]

        turns = [
            {
                "turn_index": item["turn_index"],
                "speaker_id": item["speaker_id"],
                "text": item["text"],
            }
        ]

        turns.extend(item.get("context_turns", []))

        for turn in turns:
            text = turn.get("text", "")
            turn_index = turn.get("turn_index")
            speaker_id = turn.get("speaker_id")

            if not isinstance(text, str) or len(text.split()) < 6:
                continue

            if turn_index is None or speaker_id is None:
                continue

            key = (meeting_id, turn_index)

            if key in seen_turns:
                continue

            seen_turns.add(key)

            candidates.append(
                {
                    "citation_id": f"C{len(candidates) + 1:03d}",
                    "meeting_id": meeting_id,
                    "turn_index": turn_index,
                    "speaker_id": speaker_id,
                    "quote": text,
                }
            )

    return candidates


def build_generation_messages(
    question_id: str,
    question: str,
    team_id: str,
    evidence: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build compact messages sent to the LLM."""

    if not question_id.strip():
        raise ValueError("Question ID cannot be empty")

    if not question.strip():
        raise ValueError("Question cannot be empty")

    if not team_id.strip():
        raise ValueError("Team ID cannot be empty")

    if not evidence:
        raise ValueError("Evidence cannot be empty")

    candidates = _collect_citation_candidates(evidence)

    evidence_payload = []

    for item in evidence:
        evidence_payload.append(
            {
                "meeting_id": item["meeting_id"],
                "turn_index": item["turn_index"],
                "speaker_id": item["speaker_id"],
                "text": item["text"],
                "context_turns": item.get("context_turns", []),
            }
        )

    user_payload = {
        "question_id": question_id,
        "team_id": team_id,
        "question": question,
        "evidence": evidence_payload,
        "citation_candidates": [
            {
                "citation_id": item["citation_id"],
                "meeting_id": item["meeting_id"],
                "speaker_id": item["speaker_id"],
                "quote": item["quote"],
            }
            for item in candidates
        ],
    }

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": json.dumps(
                user_payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        },
    ]
