
import re
from datetime import datetime
from itertools import pairwise

from pydantic import BaseModel, Field, field_validator, model_validator


class SpeakerTurn(BaseModel):
    timestamp: str
    speaker_id: str
    text: str = Field(min_length=1)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        if not re.fullmatch(r"\d{2}:\d{2}:\d{2}", value):
            raise ValueError(
                "Timestamp must use exact HH:MM:SS format"
            )

        try:
            datetime.strptime(value, "%H:%M:%S")
        except ValueError:
            raise ValueError(
                "Timestamp must be a valid time in HH:MM:SS format"
            )

        return value

    @field_validator("speaker_id")
    @classmethod
    def validate_speaker_id(cls, value: str) -> str:
        if value not in {"A", "B", "C", "D"}:
            raise ValueError("Speaker must be A, B, C, or D")
        return value

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "Transcript text cannot contain only whitespace"
            )
        return value


class Meeting(BaseModel):
    meeting_id: str = Field(min_length=1)
    team_id: str = Field(min_length=1)
    meeting_number: int = Field(gt=0)
    meeting_label: str
    turns: list[SpeakerTurn] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_turn_order(self):
        timestamps = [
            datetime.strptime(turn.timestamp, "%H:%M:%S")
            for turn in self.turns
        ]

        for previous, current in pairwise(timestamps):
            if current < previous:
                raise ValueError(
                    "Speaker turns must be in chronological order"
                )

        return self
