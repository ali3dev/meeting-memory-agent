
import json
from pathlib import Path

from meeting_memory_agent.retrieval.context import expand_evidence_context
from meeting_memory_agent.generation.generator import generate_answer
from meeting_memory_agent.validation.pipeline import validate_answer

DB_PATH = Path("data/meeting_memory_full.db")

# These are exact speaker turns from the real AMI transcripts.
evidence = [
    {
        "meeting_id": "TS3006b",
        "turn_index": 165,
        "speaker_id": "C",
        "text": "And we do have to integrate the screen and the the speech alright.",
    },
    {
        "meeting_id": "TS3006d",
        "turn_index": 103,
        "speaker_id": "B",
        "text": "We lose our whole concept. Uh so No we just We keep the L_C_D_.",
    },
    {
        "meeting_id": "TS3006d",
        "turn_index": 105,
        "speaker_id": "C",
        "text": "We uh we we haven't really integrated this the speech into the system, so we can might as well s drop that.",
    },
]

# Fetch surrounding turns from the real database.
expanded_evidence = expand_evidence_context(
    DB_PATH,
    evidence,
    window=2,
)

# Generate through the real OpenRouter API.
generation_result = generate_answer(
    question_id="Q01",
    question=(
        "Team TS3006 planned both an LCD screen and speech recognition. "
        "When the costs forced a cut, which feature did they drop, "
        "which did they keep, and why?"
    ),
    team_id="TS3006",
    evidence=expanded_evidence,
)

print("\n--- GENERATED ANSWER ---")
print(json.dumps(generation_result, indent=2))

# Verify the answer against the real SQLite database.
validation_result = validate_answer(
    db_path=DB_PATH,
    team_id="TS3006",
    answer_data=generation_result["answer"],
    expected_question_id="Q01",
)

print("\n--- VALIDATION RESULT ---")
print(json.dumps(validation_result, indent=2, default=str))
