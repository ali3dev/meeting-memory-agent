
from pathlib import Path

from meeting_memory_agent.ingestion.parser import parse_meeting_file
from meeting_memory_agent.models import Meeting


def parse_transcript_directory(
    directory: Path,
) -> tuple[list[Meeting], list[dict[str, str]]]:
    """
    Parse all transcript files in a directory.

    Successful meetings and failed files are returned separately.
    One failed file does not stop the remaining files.
    """

    if not directory.exists():
        raise FileNotFoundError(
            f"Transcript directory does not exist: {directory}"
        )

    if not directory.is_dir():
        raise NotADirectoryError(
            f"Expected a directory, received: {directory}"
        )

    transcript_files = sorted(directory.glob("*.txt"))

    meetings: list[Meeting] = []
    errors: list[dict[str, str]] = []

    for file_path in transcript_files:
        try:
            meeting = parse_meeting_file(file_path)
            meetings.append(meeting)

        except (OSError, ValueError) as exc:
            errors.append(
                {
                    "file": file_path.name,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    return meetings, errors
