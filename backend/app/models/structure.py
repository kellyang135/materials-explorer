"""crystal structure database models"""

from typing import Optional, Any, List

from sqlalchemy import String, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON, Text

from app.db.base import Base


class Lattice(Base):
    """lattice parameters for a crystal structure"""

    __tablename__ = "lattices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Lattice parameters
    a: Mapped[float] = mapped_column(Float, nullable=False)
    b: Mapped[float] = mapped_column(Float, nullable=False)
    c: Mapped[float] = mapped_column(Float, nullable=False)
    alpha: Mapped[float] = mapped_column(Float, nullable=False)
    beta: Mapped[float] = mapped_column(Float, nullable=False)
    gamma: Mapped[float] = mapped_column(Float, nullable=False)

    # Volume
    volume: Mapped[float] = mapped_column(Float, nullable=False)

    # Lattice matrix (3x3) stored as JSON
    matrix: Mapped[Any] = mapped_column(JSON, nullable=False)

    # Relationships
    structure: Mapped[Optional["Structure"]] = relationship(
        "Structure", back_populates="lattice", uselist=False
    )


class Structure(Base):
    """crystal structure with lattice and sites"""

    __tablename__ = "structures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    lattice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lattices.id"), nullable=False
    )

    # Structure info
    num_sites: Mapped[int] = mapped_column(Integer, nullable=False)
    is_ordered: Mapped[bool] = mapped_column(default=True)

    # Symmetry
    spacegroup_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spacegroup_symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    point_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    crystal_system: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Full structure as JSON (for quick serialization)
    structure_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # CIF representation
    cif_string: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="structure")
    lattice: Mapped["Lattice"] = relationship("Lattice", back_populates="structure")
    sites: Mapped[List["Site"]] = relationship(
        "Site", back_populates="structure", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_structures_spacegroup", "spacegroup_number"),
        Index("ix_structures_crystal_system", "crystal_system"),
    )


class Site(Base):
    """atomic site within a crystal structure"""

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    structure_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("structures.id", ondelete="CASCADE"), nullable=False
    )

    # Site info
    species: Mapped[str] = mapped_column(String(10), nullable=False)  # Element symbol
    label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    site_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Coordinates stored as JSON for SQLite compatibility
    frac_coords: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Fractional coordinates [x, y, z] as JSON
    cart_coords: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Cartesian coordinates [x, y, z] as JSON

    # Occupancy (for disordered structures)
    occupancy: Mapped[float] = mapped_column(Float, default=1.0)

    # Additional properties
    properties: Mapped[Optional[Any]] = mapped_column(
        JSON, nullable=True
    )  # magnetic moment, charge, etc

    # Relationships
    structure: Mapped["Structure"] = relationship("Structure", back_populates="sites")

    __table_args__ = (
        Index("ix_sites_structure_species", "structure_id", "species"),
    )


from app.models.material import Material
