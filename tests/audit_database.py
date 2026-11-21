import sqlite3
from pathlib import Path


db_path = Path("data/meeting_memory_full.db")

with sqlite3.connect(db_path) as connection:
    # 1. Check SQLite database integrity.
    integrity = connection.execute(
        "PRAGMA integrity_check"
    ).fetchall()

    # 2. Check foreign-key violations.
    foreign_key_errors = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    # 3. Check meetings without speaker turns.
    empty_meetings = connection.execute(
        """
        SELECT m.meeting_id
        FROM meetings AS m
        LEFT JOIN speaker_turns AS s
            ON m.meeting_id = s.meeting_id
        GROUP BY m.meeting_id
        HAVING COUNT(s.turn_id) = 0
        """
    ).fetchall()

    # 4. Check duplicate meeting IDs.
    duplicate_ids = connection.execute(
        """
        SELECT meeting_id, COUNT(*)
        FROM meetings
        GROUP BY meeting_id
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    # 5. Check duplicate turn positions.
    duplicate_positions = connection.execute(
        """
        SELECT meeting_id, turn_index, COUNT(*)
        FROM speaker_turns
        GROUP BY meeting_id, turn_index
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    # 6. Count meetings per team.
    team_counts = connection.execute(
        """
        SELECT team_id, COUNT(*)
        FROM meetings
        GROUP BY team_id
        ORDER BY team_id
        """
    ).fetchall()


print("=== DATABASE INTEGRITY AUDIT ===")
print("SQLite integrity:", integrity)
print("Foreign-key violations:", foreign_key_errors)
print("Meetings without turns:", empty_meetings)
print("Duplicate meeting IDs:", duplicate_ids)
print("Duplicate turn positions:", duplicate_positions)

print("\n=== MEETINGS PER TEAM ===")
for team_id, count in team_counts:
    print(f"{team_id}: {count}")
