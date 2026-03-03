from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from talentlens.models.base import Base, TimestampMixin, UUIDMixin


class Assessment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assessments"

    candidate_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), index=True
    )
    interview_id: Mapped["UUID | None"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=True
    )
    rubric_id: Mapped["UUID | None"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rubrics.id"), nullable=True
    )
    stage: Mapped[str] = mapped_column(String(50))  # matches PipelineStage value
    overall_score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(String(50))  # "strong_yes", "yes", "no", etc.
    raw_response: Mapped[dict | None] = mapped_column(JSON)  # full Claude response for audit

    candidate = relationship("Candidate", back_populates="assessments")
    criterion_scores = relationship("CriterionScore", back_populates="assessment")


class CriterionScore(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "criterion_scores"

    assessment_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id"), index=True
    )
    criterion_name: Mapped[str] = mapped_column(String(200))
    score: Mapped[int] = mapped_column(Integer)
    max_score: Mapped[int] = mapped_column(Integer, default=5)
    reasoning: Mapped[str | None] = mapped_column(Text)

    assessment = relationship("Assessment", back_populates="criterion_scores")
    evidence = relationship("Evidence", back_populates="criterion_score")
