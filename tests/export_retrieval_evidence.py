
import json
from pathlib import Path

from meeting_memory_agent.retrieval.search import (
    retrieve_team_evidence,
)


DB_PATH = Path("data/meeting_memory_full.db")
QUESTIONS_PATH = Path("data/questions.json")
OUTPUT_PATH = Path("outputs/retrieval_candidates.json")


def main():
    with QUESTIONS_PATH.open(encoding="utf-8") as file:
        assessment = json.load(file)

    audit = []

    for question in assessment["questions"]:
        result = retrieve_team_evidence(
            db_path=DB_PATH,
            team_id=question["team"],
            queries=[question["question"]],
            limit=30,
            per_meeting_limit=8,
            min_meetings=2,
        )

        audit.append({
            "question_id": question["question_id"],
            "team": question["team"],
            "question": question["question"],
            "coverage_satisfied": result["coverage_satisfied"],
            "meetings_found": result["meetings_found"],
            "evidence": [
                {
                    "meeting_id": item["meeting_id"],
                    "speaker_id": item["speaker_id"],
                    "timestamp": item["timestamp"],
                    "turn_index": item["turn_index"],
                    "text": item["text"],
                    "fused_score": item["fused_score"],
                    "matched_queries": item["matched_queries"],
                }
                for item in result["evidence"]
            ],
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Questions exported:", len(audit))
    print("Evidence records:", sum(len(item["evidence"]) for item in audit))
    print("Output:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
