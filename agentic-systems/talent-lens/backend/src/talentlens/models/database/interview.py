import enum

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from talentlens.models.base import Base, TimestampMixin, UUIDMixin


class InterviewType(str, enum.Enum):
    screening = "screening"
    coderpad = "coderpad"
    technical = "technical"
    final = "final"


class Interview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "interviews"

    candidate_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), index=True
    )
    interview_type: Mapped[InterviewType] = mapped_column(Enum(InterviewType))
    source: Mapped[str | None] = mapped_column(String(100))  # "fireflies", "coderpad", "manual"
    external_id: Mapped[str | None] = mapped_column(String(500))  # Fireflies meeting ID, etc.

    transcript: Mapped[str | None] = mapped_column(Text)
    diarization: Mapped[dict | None] = mapped_column(JSON)  # speaker-labeled segments
    talk_ratio: Mapped[float | None] = mapped_column(Float)  # candidate talk time ratio
    duration_seconds: Mapped[int | None]

    candidate = relationship("Candidate", back_populates="interviews")
