"""material database models"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from app.db.base import Base


class Element(Base):
    """periodic table element"""

    __tablename__ = "elements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(3), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    atomic_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    atomic_mass: Mapped[float] = mapped_column(Float, nullable=False)
    electronegativity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    electron_configuration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    compositions: Mapped[List["Composition"]] = relationship(
        "Composition", back_populates="element"
    )


class Material(Base):
    """material/compound with its metadata"""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )  # e.g., mp-1234
    formula: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    formula_pretty: Mapped[str] = mapped_column(String(100), nullable=False)
    formula_anonymous: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    chemsys: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., Fe-O
    nelements: Mapped[int] = mapped_column(Integer, nullable=False)
    nsites: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Crystal system info
    crystal_system: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    spacegroup_symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    spacegroup_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Volume and density
    volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    density: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    density_atomic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Source tracking
    source: Mapped[str] = mapped_column(String(50), default="materials_project")
    source_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Vector embedding for similarity search (stored as JSON for SQLite compatibility)
    structure_embedding: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Relationships
    compositions: Mapped[List["Composition"]] = relationship(
        "Composition", back_populates="material", cascade="all, delete-orphan"
    )
    properties: Mapped[List["Property"]] = relationship(
        "Property", back_populates="material", cascade="all, delete-orphan"
    )
    calculations: Mapped[List["Calculation"]] = relationship(
        "Calculation", back_populates="material", cascade="all, delete-orphan"
    )
    structure: Mapped[Optional["Structure"]] = relationship(
        "Structure", back_populates="material", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_materials_chemsys_formula", "chemsys", "formula"),
        Index("ix_materials_crystal_system", "crystal_system"),
    )


class Composition(Base):
    """element composition within a material"""

    __tablename__ = "compositions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    element_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("elements.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # Stoichiometric amount
    weight_fraction: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    atomic_fraction: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="compositions")
    element: Mapped["Element"] = relationship("Element", back_populates="compositions")

    __table_args__ = (
        UniqueConstraint("material_id", "element_id", name="uq_composition_material_element"),
        Index("ix_compositions_element", "element_id"),
    )

#import stuff
from app.models.property import Property, Calculation
from app.models.structure import Structure
