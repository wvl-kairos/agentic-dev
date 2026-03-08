import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from talentlens.models.base import Base, TimestampMixin, UUIDMixin


class PipelineStage(str, enum.Enum):
    initial_interview = "initial_interview"
    screening = "screening"
    coderpad = "coderpad"
    technical_interview = "technical_interview"
    final_interview = "final_interview"
    decision = "decision"
    hired = "hired"
    rejected = "rejected"


class Candidate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "candidates"

    venture_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ventures.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    role: Mapped[str | None] = mapped_column(String(200))
    stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage), default=PipelineStage.screening
    )
    role_template_id: Mapped["UUID | None"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_templates.id"), nullable=True
    )
    cv_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    venture = relationship("Venture", back_populates="candidates")
    role_template = relationship("RoleTemplate")
    interviews = relationship("Interview", back_populates="candidate")
    assessments = relationship("Assessment", back_populates="candidate")
