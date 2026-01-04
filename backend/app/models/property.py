"""property and calculation database models"""

from datetime import datetime
from typing import Optional, Any

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class Property(Base):
    """material property (computed or experimental)"""

    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )

    # Property identification
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # electronic, magnetic, thermal, whatever etc.

    # Value storage
    value_numeric: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_string: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_json: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Uncertainty
    uncertainty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Source
    source: Mapped[str] = mapped_column(String(50), default="calculated")
    calculation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("calculations.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="properties")
    calculation: Mapped[Optional["Calculation"]] = relationship(
        "Calculation", back_populates="properties"
    )

    __table_args__ = (
        Index("ix_properties_material_name", "material_id", "name"),
        Index("ix_properties_category_name", "category", "name"),
    )


class Calculation(Base):
    """DFT or other calculation metadata"""

    __tablename__ = "calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )

    # Calculation metadata
    task_id: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True
    )  # e.g., mp-1234-GGA
    calc_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # GGA, GGA+U, HSE, etc.
    functional: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pseudopotential: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Run info
    run_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # static, relax, etc.
    is_hubbard: Mapped[bool] = mapped_column(default=False)
    hubbard_u: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # Convergence info
    is_converged: Mapped[bool] = mapped_column(default=True)
    energy_cutoff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    kpoints: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # Computed values
    energy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    energy_per_atom: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    formation_energy_per_atom: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    energy_above_hull: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_stable: Mapped[Optional[bool]] = mapped_column(nullable=True)

    # Band structure
    band_gap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_gap_direct: Mapped[Optional[bool]] = mapped_column(nullable=True)
    cbm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Conduction band minimum
    vbm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Valence band maximum
    efermi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Magnetic properties
    total_magnetization: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_magnetic: Mapped[Optional[bool]] = mapped_column(nullable=True)

    # Timestamps
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="calculations")
    properties: Mapped[list["Property"]] = relationship(
        "Property", back_populates="calculation"
    )

    __table_args__ = (
        Index("ix_calculations_material_type", "material_id", "calc_type"),
        Index("ix_calculations_band_gap", "band_gap"),
        Index("ix_calculations_energy_above_hull", "energy_above_hull"),
    )


from app.models.material import Material
