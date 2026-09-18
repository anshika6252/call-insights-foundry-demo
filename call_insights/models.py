"""Provider-independent, Unicode-preserving data contracts."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InputMode(str, Enum):
    ENGLISH = "english"
    HINDI = "hindi"


class SummaryLanguage(str, Enum):
    ENGLISH = "english"
    HINDI = "hindi"


class CallStatus(str, Enum):
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Segment(ContractModel):
    id: str = Field(min_length=1)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    text: str = Field(min_length=1)
    speaker: str | None = None
    locale: str | None = None

    @model_validator(mode="after")
    def validate_timing(self):
        if self.end_ms < self.start_ms:
            raise ValueError("Segment end must not precede its start")
        return self


class Transcript(ContractModel):
    segments: list[Segment] = Field(min_length=1)
    detected_locales: list[str] = Field(default_factory=list)
    duration_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_segments(self):
        ids = [segment.id for segment in self.segments]
        if len(set(ids)) != len(ids):
            raise ValueError("Transcript segment IDs must be unique")
        if self.duration_ms is not None and any(
            segment.end_ms > self.duration_ms for segment in self.segments
        ):
            raise ValueError("Segment exceeds transcript duration")
        return self


class EvidenceItem(ContractModel):
    text: str = Field(min_length=1)
    segment_ids: list[str] = Field(min_length=1)

    @field_validator("segment_ids")
    @classmethod
    def validate_references(cls, values):
        if any(not value.strip() for value in values):
            raise ValueError("Evidence references must be nonempty")
        if len(set(values)) != len(values):
            raise ValueError("Evidence references must be unique")
        return values


class ActionItem(ContractModel):
    description: str = Field(min_length=1)
    owner: str | None = None
    due_date: str | None = None
    segment_ids: list[str] = Field(min_length=1)

    @field_validator("segment_ids")
    @classmethod
    def validate_references(cls, values):
        return EvidenceItem.validate_references(values)

    @field_validator("owner", "due_date")
    @classmethod
    def empty_to_none(cls, value):
        return value or None


class CallSummary(ContractModel):
    overview: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    key_points: list[str] = Field(default_factory=list)
    decisions: list[EvidenceItem] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    outcome: str = Field(min_length=1)

    def validate_evidence(self, transcript: Transcript) -> "CallSummary":
        """Validate referential integrity, not factual entailment."""
        valid_ids = {segment.id for segment in transcript.segments}
        for item in [*self.decisions, *self.action_items]:
            if any(reference not in valid_ids for reference in item.segment_ids):
                raise ValueError("Summary evidence references an unknown transcript segment")
        return self
