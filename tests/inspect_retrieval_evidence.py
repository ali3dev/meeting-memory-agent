
import json
from pathlib import Path


INPUT_PATH = Path("outputs/retrieval_candidates.json")


def main():
    with INPUT_PATH.open(encoding="utf-8") as file:
        records = json.load(file)

    # Start with Q01 as our pilot question.
    question = next(
        item for item in records
        if item["question_id"] == "Q01"
    )

    evidence = sorted(
        question["evidence"],
        key=lambda item: item["fused_score"],
        reverse=True,
    )

    print("=" * 80)
    print("QUESTION:", question["question_id"])
    print("TEAM:", question["team"])
    print(question["question"])
    print("=" * 80)

    meeting_counts = {}

    for item in question["evidence"]:
        meeting_id = item["meeting_id"]
        meeting_counts[meeting_id] = (
            meeting_counts.get(meeting_id, 0) + 1
        )

    print("\nMEETING DISTRIBUTION:")
    for meeting_id, count in sorted(meeting_counts.items()):
        print(f"{meeting_id}: {count} passages")

    print("\nTOP 15 EVIDENCE PASSAGES:")

    for index, item in enumerate(evidence[:15], start=1):
        print("\n" + "-" * 80)
        print(
            f"Rank: {index} | "
            f"Meeting: {item['meeting_id']} | "
            f"Speaker: {item['speaker_id']} | "
            f"Time: {item['timestamp']}"
        )
        print(f"Score: {item['fused_score']:.6f}")
        print("Text:", item["text"])


if __name__ == "__main__":
    main()
