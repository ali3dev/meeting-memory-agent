
import argparse
import json
from pathlib import Path
from typing import Any

from meeting_memory_agent.agent.orchestrator import run_question

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_PATH = PROJECT_ROOT / "data" / "questions.json"
DATABASE_PATH = PROJECT_ROOT / "data" / "meeting_memory_full.db"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "batch_run_report.json"

RETRIEVAL_LIMIT = 10
PER_MEETING_LIMIT = 3
CONTEXT_WINDOW = 1
MIN_MEETINGS = 2


def load_questions() -> list[dict[str, Any]]:
    """Load and validate the question dataset."""

    with QUESTIONS_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, dict):
        raise TypeError("Question dataset root must be a JSON object")

    questions = dataset.get("questions")

    if not isinstance(questions, list) or not questions:
        raise ValueError("Question dataset is empty or invalid")

    required_fields = {"question_id", "team", "question"}
    seen_ids = set()

    for item in questions:
        if not isinstance(item, dict):
            raise TypeError("Every question must be a JSON object")

        missing = required_fields - item.keys()

        if missing:
            raise ValueError(
                f"Question is missing fields: {sorted(missing)}"
            )

        question_id = item["question_id"]
        team_id = item["team"]
        question = item["question"]

        if not isinstance(question_id, str) or not question_id.strip():
            raise ValueError("Question ID must be a non-empty string")

        if question_id in seen_ids:
            raise ValueError(f"Duplicate question ID: {question_id}")

        if not isinstance(team_id, str) or not team_id.strip():
            raise ValueError(
                f"Question {question_id} has an invalid team ID"
            )

        if not isinstance(question, str) or not question.strip():
            raise ValueError(
                f"Question {question_id} has an invalid question"
            )

        seen_ids.add(question_id)

    return questions


def run_batch(
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run questions sequentially and preserve individual failures."""

    successful_answers = []
    failed_questions = []

    total_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    for index, item in enumerate(questions, start=1):
        question_id = item["question_id"]
        team_id = item["team"]
        question = item["question"]

        print(
            f"\n[{index}/{len(questions)}] "
            f"Processing {question_id} ({team_id})"
        )

        try:
            result = run_question(
                db_path=DATABASE_PATH,
                question_id=question_id,
                question=question,
                team_id=team_id,
                queries=[question],
                limit=RETRIEVAL_LIMIT,
                per_meeting_limit=PER_MEETING_LIMIT,
                min_meetings=MIN_MEETINGS,
                context_window=CONTEXT_WINDOW,
            )

            if result["status"] != "success":
                failure = {
                    "question_id": question_id,
                    "team_id": team_id,
                    "status": result["status"],
                    "errors": result.get("errors", []),
                }

                for key in (
                    "generated_answer",
                    "validation_stage",
                    "validation_details",
                    "retrieval",
                    "generation",
                ):
                    if key in result:
                        failure[key] = result[key]

                failed_questions.append(failure)

                print(
                    f"FAILED: {question_id} - {result['status']}"
                )
                continue

            successful_answers.append(result["answer"])

            usage = result["generation"]["usage"]

            for key in total_usage:
                total_usage[key] += usage.get(key, 0)

            print(f"SUCCESS: {question_id}")

        except Exception as exc:  # noqa: BLE001
            # Isolate unexpected failures so remaining questions continue.
            failed_questions.append({
                "question_id": question_id,
                "team_id": team_id,
                "status": "unexpected_error",
                "errors": [f"{type(exc).__name__}: {exc}"],
            })

            print(
                f"ERROR: {question_id} - "
                f"{type(exc).__name__}: {exc}"
            )

    return {
        "total_questions": len(questions),
        "successful_count": len(successful_answers),
        "failed_count": len(failed_questions),
        "answers": successful_answers,
        "failed_questions": failed_questions,
        "token_usage": total_usage,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Meeting Memory question-answering pipeline"
    )

    parser.add_argument(
        "--question-id",
        help="Run only one question, for example Q01",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Run only the first N questions",
    )

    args = parser.parse_args()

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Meeting database not found: {DATABASE_PATH}"
        )

    questions = load_questions()

    if args.question_id:
        questions = [
            item for item in questions
            if item["question_id"] == args.question_id
        ]

        if not questions:
            raise ValueError(
                f"Question not found: {args.question_id}"
            )

    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be greater than zero")

        questions = questions[:args.limit]

    print(f"Starting batch: {len(questions)} question(s)")
    print(
        "Retrieval settings: "
        f"limit={RETRIEVAL_LIMIT}, "
        f"per_meeting={PER_MEETING_LIMIT}, "
        f"context_window={CONTEXT_WINDOW}"
    )

    report = run_batch(questions)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n========== BATCH SUMMARY ==========")
    print(f"Total: {report['total_questions']}")
    print(f"Successful: {report['successful_count']}")
    print(f"Failed: {report['failed_count']}")
    print(f"Token usage: {report['token_usage']}")
    print(f"Report saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
