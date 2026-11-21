import json
from pathlib import Path

from meeting_memory_agent.retrieval.search import (
    retrieve_team_evidence,
)


DB_PATH = Path("data/meeting_memory_full.db")
QUESTIONS_PATH = Path("data/questions.json")


def main():
    with QUESTIONS_PATH.open(encoding="utf-8") as file:
        assessment = json.load(file)

    questions = assessment["questions"]

    passed = 0
    failed = 0

    print("\n========== QUESTION RETRIEVAL AUDIT ==========\n")

    for question in questions:
        question_id = question["question_id"]
        team_id = question["team"]
        question_text = question["question"]

        result = retrieve_team_evidence(
            db_path=DB_PATH,
            team_id=team_id,
            queries=[question_text],
            limit=30,
            per_meeting_limit=8,
            min_meetings=2,
        )

        coverage = result["coverage_satisfied"]

        if coverage:
            passed += 1
        else:
            failed += 1

        status = "PASS" if coverage else "FAIL"

        print(f"{question_id} | {team_id} | {status}")
        print("Meetings:", result["meetings_found"])
        print("Evidence:", len(result["evidence"]))
        print("Question:", question_text)
        print("-" * 70)

    print("\n========== FINAL REPORT ==========")
    print("Total questions:", len(questions))
    print("Coverage passed:", passed)
    print("Coverage failed:", failed)


if __name__ == "__main__":
    main()
