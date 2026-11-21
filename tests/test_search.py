
from pathlib import Path

from meeting_memory_agent.retrieval.search import (
    initialize_search_index,
    search_turns,
)


db_path = Path("data/meeting_memory_full.db")

initialize_search_index(db_path)

results = search_turns(
    db_path=db_path,
    query="design",
    team_id="TS3012",
    limit=10,
)

print("Results found:", len(results))

for result in results:
    print("\n--------------------")
    print("Meeting:", result["meeting_id"])
    print("Speaker:", result["speaker_id"])
    print("Timestamp:", result["timestamp"])
    print("Relevance:", result["relevance"])
    print("Text:", result["text"])
