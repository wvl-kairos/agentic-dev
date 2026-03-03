from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from talentlens.models.base import Base, TimestampMixin, UUIDMixin


class Evidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "evidence"

    criterion_score_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("criterion_scores.id"), index=True
    )
    quote: Mapped[str] = mapped_column(Text)
    speaker: Mapped[str | None] = mapped_column(String(200))
    timestamp_start: Mapped[float | None]  # seconds into recording
    timestamp_end: Mapped[float | None]
    relevance: Mapped[str | None] = mapped_column(String(50))  # "supports", "contradicts"

    criterion_score = relationship("CriterionScore", back_populates="evidence")
