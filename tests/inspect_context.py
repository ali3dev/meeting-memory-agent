
from pathlib import Path

from meeting_memory_agent.retrieval.search import retrieve_team_evidence
from meeting_memory_agent.retrieval.context import expand_evidence_context


DB_PATH = Path("data/meeting_memory_full.db")


def main():
    result = retrieve_team_evidence(
        DB_PATH,
        "TS3006",
        [
            "drop speech recognition",
            "keep LCD screen extra buttons",
            "lose the screen whole concept",
        ],
        limit=20,
    )

    expanded = expand_evidence_context(
        DB_PATH,
        result["evidence"],
        window=3,
    )

    for item in expanded:
        if item["meeting_id"] != "TS3006d":
            continue

        print(
            f"\n--- {item['meeting_id']} | "
            f"Speaker {item['speaker_id']} | "
            f"Turn {item['turn_index']} ---"
        )

        for turn in item["context_turns"]:
            print(
                f"{turn['turn_index']} | "
                f"{turn['speaker_id']} | "
                f"{turn['text']}"
            )


if __name__ == "__main__":
    main()
