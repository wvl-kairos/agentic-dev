"""Capability and RoleTemplate models for skills matrix framework."""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from talentlens.models.base import Base, TimestampMixin, UUIDMixin


class Capability(Base, UUIDMixin, TimestampMixin):
    """An engineering capability (e.g., Frontend, Backend, Data Engineering)."""

    __tablename__ = "capabilities"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50))  # lucide icon name
    order: Mapped[int] = mapped_column(Integer, default=0)

    levels = relationship("CapabilityLevel", back_populates="capability", order_by="CapabilityLevel.level")
    technologies = relationship("Technology", back_populates="capability", order_by="Technology.order")
    role_requirements = relationship("RoleCapabilityRequirement", back_populates="capability")


class CapabilityLevel(Base, UUIDMixin, TimestampMixin):
    """Proficiency level description for a capability (1-5)."""

    __tablename__ = "capability_levels"

    capability_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capabilities.id", ondelete="CASCADE"), index=True
    )
    level: Mapped[int] = mapped_column(Integer)  # 1-5
    title: Mapped[str] = mapped_column(String(100))  # e.g., "Junior", "Senior"
    description: Mapped[str | None] = mapped_column(Text)

    capability = relationship("Capability", back_populates="levels")


class RoleTemplate(Base, UUIDMixin, TimestampMixin):
    """A role template defining required capability levels."""

    __tablename__ = "role_templates"

    venture_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ventures.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    venture = relationship("Venture")
    requirements = relationship(
        "RoleCapabilityRequirement",
        back_populates="role_template",
        cascade="all, delete-orphan",
    )
    technology_requirements = relationship(
        "RoleTechnologyRequirement",
        back_populates="role_template",
        cascade="all, delete-orphan",
    )


class RoleCapabilityRequirement(Base, UUIDMixin, TimestampMixin):
    """Required proficiency level for a capability within a role template."""

    __tablename__ = "role_capability_requirements"

    role_template_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_templates.id", ondelete="CASCADE"), index=True
    )
    capability_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capabilities.id", ondelete="CASCADE"), index=True
    )
    required_level: Mapped[int] = mapped_column(Integer)  # 1-5

    role_template = relationship("RoleTemplate", back_populates="requirements")
    capability = relationship("Capability", back_populates="role_requirements")


class Technology(Base, UUIDMixin, TimestampMixin):
    """A specific technology stack (e.g., React, Python) under a capability."""

    __tablename__ = "technologies"

    capability_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capabilities.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    icon: Mapped[str | None] = mapped_column(String(50))
    order: Mapped[int] = mapped_column(Integer, default=0)

    capability = relationship("Capability", back_populates="technologies")
    role_requirements = relationship("RoleTechnologyRequirement", back_populates="technology")


class RoleTechnologyRequirement(Base, UUIDMixin, TimestampMixin):
    """Required proficiency level for a technology within a role template."""

    __tablename__ = "role_technology_requirements"
    __table_args__ = (
        UniqueConstraint("role_template_id", "technology_id", name="uq_role_tech_req"),
    )

    role_template_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_templates.id", ondelete="CASCADE"), index=True
    )
    technology_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("technologies.id", ondelete="CASCADE"), index=True
    )
    required_level: Mapped[int] = mapped_column(Integer)  # 1-5

    role_template = relationship("RoleTemplate", back_populates="technology_requirements")
    technology = relationship("Technology", back_populates="role_requirements")
