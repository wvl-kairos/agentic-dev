from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from talentlens.models.base import Base, TimestampMixin, UUIDMixin


class Rubric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rubrics"

    venture_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ventures.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    venture = relationship("Venture", back_populates="rubrics")
    criteria = relationship("RubricCriterion", back_populates="rubric")


class RubricCriterion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rubric_criteria"

    rubric_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rubrics.id"), index=True
    )
    capability_id: Mapped["UUID | None"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capabilities.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    max_score: Mapped[int] = mapped_column(Integer, default=5)
    order: Mapped[int] = mapped_column(Integer, default=0)

    rubric = relationship("Rubric", back_populates="criteria")
    capability = relationship("Capability")
