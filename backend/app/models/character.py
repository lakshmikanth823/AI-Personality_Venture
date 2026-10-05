from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class CharacterVersion(Base):
    __tablename__ = "character_versions"

    id = Column(String(36), primary_key=True, index=True)
    version_tag = Column(String(32), unique=True, index=True, nullable=False) # e.g. "v1.0-public-canon"
    name = Column(String(64), default="Kalyan", nullable=False)
    archetype = Column(String(128), default="The brutally honest Indian internet friend", nullable=False)
    tagline = Column(String(255), default="Zero corporate sugarcoating, 100% filterless reality.")
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    rules = relationship("CharacterRule", back_populates="character_version", cascade="all, delete-orphan")
    lores = relationship("CharacterLore", back_populates="character_version", cascade="all, delete-orphan")

class CharacterRule(Base):
    __tablename__ = "character_rules"

    id = Column(String(36), primary_key=True, index=True)
    character_version_id = Column(String(36), ForeignKey("character_versions.id", ondelete="CASCADE"), nullable=False)
    rule_type = Column(String(32), nullable=False) # "allowed", "forbidden", "tone", "humor", "language"
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=1)

    character_version = relationship("CharacterVersion", back_populates="rules")

class CharacterLore(Base):
    __tablename__ = "character_lore"

    id = Column(String(36), primary_key=True, index=True)
    character_version_id = Column(String(36), ForeignKey("character_versions.id", ondelete="CASCADE"), nullable=False)
    lore_type = Column(String(32), default="canon", nullable=False) # "canon" | "improvisation" | "community"
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(64), default="origin") # origin, friends, rival, food, habits
    is_verified_canon = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    character_version = relationship("CharacterVersion", back_populates="lores")
