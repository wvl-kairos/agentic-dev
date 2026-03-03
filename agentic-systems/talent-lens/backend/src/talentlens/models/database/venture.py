from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from talentlens.models.base import Base, TimestampMixin, UUIDMixin


class Venture(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ventures"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(1000))

    candidates = relationship("Candidate", back_populates="venture")
    rubrics = relationship("Rubric", back_populates="venture")
