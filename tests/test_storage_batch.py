from pathlib import Path

from meeting_memory_agent.ingestion.parser import (
    parse_meeting_file,
)
from meeting_memory_agent.storage.batch import save_meetings


transcript_dir = Path("data/transcripts")
db_path = Path("data/batch_test.db")

# Reset only this dedicated test database.
db_path.unlink(missing_ok=True)

meetings = [
    parse_meeting_file(transcript_dir / "TS3012a.txt"),
    parse_meeting_file(transcript_dir / "TS3012b.txt"),
]

saved_count, errors = save_meetings(db_path, meetings)

print("Expected meetings:", len(meetings))
print("Successfully saved:", saved_count)
print("Failed:", len(errors))
print("Errors:", errors)
print("Database:", db_path)
