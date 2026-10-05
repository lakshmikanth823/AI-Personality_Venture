from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    hypothesis = Column(Text, nullable=False)
    variable_tested = Column(String(64), nullable=False) # "tone", "humor_intensity", "language_mix", "cta_style"
    status = Column(String(32), default="active", nullable=False) # "active", "completed", "paused"
    target_metric = Column(String(64), default="wmcr") # "wmcr", "shares_per_1000", "retention_d7"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    variants = relationship("ExperimentVariant", back_populates="experiment", cascade="all, delete-orphan")

class ExperimentVariant(Base):
    __tablename__ = "experiment_variants"

    id = Column(String(36), primary_key=True, index=True)
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    variant_key = Column(String(64), nullable=False) # e.g. "control_english", "variant_hinglish", "variant_telugu_infused"
    name = Column(String(128), nullable=False)
    prompt_modifier = Column(Text, nullable=False)
    allocation_percent = Column(Float, default=50.0)
    samples_count = Column(Integer, default=0)
    conversions_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    retention_count = Column(Integer, default=0)

    experiment = relationship("Experiment", back_populates="variants")
