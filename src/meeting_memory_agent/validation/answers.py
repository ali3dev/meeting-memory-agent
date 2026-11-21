import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Citation(BaseModel):
    """A source quote linked to one meeting."""

    model_config = ConfigDict(extra="forbid")

    meeting_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)

    @field_validator("meeting_id", "quote")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot contain only whitespace")
        return value.strip()


class AnswerRecord(BaseModel):
    """One answer to one assessment question."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    citations: list[Citation] = Field(
        min_length=1,
        max_length=3,
    )

    @field_validator("question_id", "answer")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot contain only whitespace")
        return value.strip()

    @field_validator("answer")
    @classmethod
    def validate_sentence_count(cls, value: str) -> str:
        # Count sentence-ending punctuation followed by whitespace
        # or the end of the answer.
        sentence_endings = re.findall(
            r"[.!?](?=\s|$)",
            value.strip(),
        )

        sentence_count = len(sentence_endings)

        if not 1 <= sentence_count <= 3:
            raise ValueError(
                "Answer must contain between 1 and 3 sentences"
            )

        return value
