
from pathlib import Path

from meeting_memory_agent.retrieval.context import (
    expand_evidence_context,
)


DB_PATH = Path("data/meeting_memory_full.db")


def test_context_expansion():
    evidence = [
        {
            "meeting_id": "TS3006d",
            "turn_index": 85,
            "speaker_id": "B",
            "text": "Could drop the speech recognition.",
            "fused_score": 0.016,
        }
    ]

    result = expand_evidence_context(
        db_path=DB_PATH,
        evidence=evidence,
        window=3,
    )

    assert len(result) == 1

    item = result[0]

    assert item["meeting_id"] == "TS3006d"
    assert item["speaker_id"] == "B"
    assert item["text"] == "Could drop the speech recognition."

    assert len(item["context_turns"]) == 7

    assert any(
        turn["text"] == "Could drop the speech recognition."
        for turn in item["context_turns"]
    )


if __name__ == "__main__":
    test_context_expansion()
    print("Context expansion test passed.")
