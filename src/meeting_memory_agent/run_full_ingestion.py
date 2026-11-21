import sqlite3
from pathlib import Path

from meeting_memory_agent.ingestion.batch import (
    parse_transcript_directory,
)
from meeting_memory_agent.storage.batch import save_meetings

transcript_dir = Path("data/transcripts")
db_path = Path("data/meeting_memory_full.db")

# Use a fresh database for this initial full-ingestion run.
db_path.unlink(missing_ok=True)

# Stage 1: Parse all transcript files.
meetings, parse_errors = parse_transcript_directory(
    transcript_dir
)

print("=== PARSING REPORT ===")
print("Parsed meetings:", len(meetings))
print("Parsing failures:", len(parse_errors))

# Stage 2: Save valid meetings independently.
saved_count, save_errors = save_meetings(
    db_path,
    meetings,
)

print("\n=== STORAGE REPORT ===")
print("Successfully saved:", saved_count)
print("Storage failures:", len(save_errors))

# Stage 3: Verify actual database records.
with sqlite3.connect(db_path) as connection:
    meeting_count = connection.execute(
        "SELECT COUNT(*) FROM meetings"
    ).fetchone()[0]

    turn_count = connection.execute(
        "SELECT COUNT(*) FROM speaker_turns"
    ).fetchone()[0]

print("\n=== DATABASE VERIFICATION ===")
print("Meetings in database:", meeting_count)
print("Speaker turns in database:", turn_count)

print("\nParsing errors:", parse_errors)
print("Storage errors:", save_errors)
