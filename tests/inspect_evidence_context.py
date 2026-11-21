
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


DB_PATH = Path("data/meeting_memory_full.db")
INPUT_PATH = Path("outputs/retrieval_candidates.json")


def main():
    with INPUT_PATH.open(encoding="utf-8") as file:
        records = json.load(file)

    question = next(
        item for item in records
        if item["question_id"] == "Q01"
    )

    grouped = defaultdict(list)

    for item in question["evidence"]:
        grouped[item["meeting_id"]].append(item)

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        for meeting_id, passages in sorted(grouped.items()):
            passages.sort(
                key=lambda item: item["fused_score"],
                reverse=True,
            )

            # Inspect the two highest-ranked passages per meeting.
            for index, item in enumerate(passages[:2], start=1):
                turn_index = item["turn_index"]

                rows = connection.execute(
                    """
                    SELECT turn_index, timestamp, speaker_id, text
                    FROM speaker_turns
                    WHERE meeting_id = ?
                      AND turn_index BETWEEN ? AND ?
                    ORDER BY turn_index
                    """,
                    (
                        meeting_id,
                        max(0, turn_index - 5),
                        turn_index + 5,
                    ),
                ).fetchall()

                print("\n" + "=" * 90)
                print(
                    f"{meeting_id} | Candidate {index} | "
                    f"Matched turn: {turn_index}"
                )
                print("=" * 90)

                for row in rows:
                    marker = (
                        ">>>"
                        if row["turn_index"] == turn_index
                        else "   "
                    )

                    print(
                        f"{marker} [{row['turn_index']}] "
                        f"{row['timestamp']} "
                        f"Speaker {row['speaker_id']}: "
                        f"{row['text']}"
                    )


if __name__ == "__main__":
    main()
