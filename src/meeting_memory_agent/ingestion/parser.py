import re
from pathlib import Path

from meeting_memory_agent.models import Meeting, SpeakerTurn

# Identifies the beginning of each speaker turn.
TURN_PATTERN = re.compile(
    r"(?m)^(\d{2}:\d{2}:\d{2})\s+Speaker\s+([A-D])\s*$"
)


def extract_metadata(content: str) -> dict:
    """
    Extract meeting-level metadata from a transcript.
    """

    meeting_match = re.search(
        r"(?m)^Meeting:\s*(.+?)\s*$",
        content,
    )

    team_match = re.search(
        r"(?m)^Team:\s*(.+?)\s*$",
        content,
    )

    number_match = re.search(
        r"(?m)^Meeting number:\s*(.+?)\s*$",
        content,
    )

    if not meeting_match:
        raise ValueError("Missing Meeting metadata")

    if not team_match:
        raise ValueError("Missing Team metadata")

    if not number_match:
        raise ValueError("Missing Meeting number metadata")

    meeting_label = number_match.group(1)

    # Extract the numeric part: "1 (a)" becomes 1.
    numeric_match = re.match(r"^\s*(\d+)", meeting_label)

    if not numeric_match:
        raise ValueError("Invalid meeting number metadata")

    return {
        "meeting_id": meeting_match.group(1),
        "team_id": team_match.group(1),
        "meeting_number": int(numeric_match.group(1)),
        "meeting_label": meeting_label,
    }


def extract_turns(content: str) -> list[SpeakerTurn]:
    """
    Split transcript content into individual speaker turns.
    """

    matches = list(TURN_PATTERN.finditer(content))

    if not matches:
        raise ValueError("No speaker turns found in transcript")

    turns = []

    for index, match in enumerate(matches):

        timestamp = match.group(1)
        speaker_id = match.group(2)

        # The current turn ends where the next turn begins.
        if index + 1 < len(matches):
            turn_end = matches[index + 1].start()
        else:
            turn_end = len(content)

        text = content[match.end():turn_end].strip()

        turns.append(
            SpeakerTurn(
                timestamp=timestamp,
                speaker_id=speaker_id,
                text=text,
            )
        )

    return turns


def parse_meeting_text(content: str) -> Meeting:
    """
    Convert raw transcript text into a validated Meeting object.
    """

    metadata = extract_metadata(content)
    turns = extract_turns(content)

    return Meeting(
        **metadata,
        turns=turns,
    )


def parse_meeting_file(file_path: Path) -> Meeting:
    """
    Read a transcript file and convert it into a Meeting object.
    """

    content = file_path.read_text(encoding="utf-8")

    return parse_meeting_text(content)
