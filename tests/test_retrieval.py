
from pathlib import Path

from meeting_memory_agent.retrieval.search import (
    retrieve_team_evidence,
    search_turns,
)


DB_PATH = Path("data/meeting_memory_full.db")


def test_team_search():
    results = search_turns(
        DB_PATH,
        query="design",
        team_id="TS3012",
        limit=10,
    )

    assert results
    assert all(row["team_id"] == "TS3012" for row in results)

    print("Search results:", len(results))


def test_multi_meeting_retrieval():
    result = retrieve_team_evidence(
        db_path=DB_PATH,
        team_id="TS3012",
        queries=[
            "design decisions",
            "cost budget",
            "features changes",
        ],
        limit=30,
    )

    print("Meetings found:", result["meetings_found"])
    print("Evidence count:", len(result["evidence"]))
    print("Coverage satisfied:", result["coverage_satisfied"])

    assert result["coverage_satisfied"]
    assert len(result["meetings_found"]) >= 2

    assert all(
        item["team_id"] == "TS3012"
        for item in result["evidence"]
    )


if __name__ == "__main__":
    test_team_search()
    test_multi_meeting_retrieval()
