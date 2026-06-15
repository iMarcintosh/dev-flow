from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(500), nullable=False, server_default="Untitled")
    content = Column(Text, nullable=False, server_default="")
    tags = Column(ARRAY(String), nullable=False, server_default="{}")
    is_pinned = Column(Boolean, nullable=False, server_default="false")
    chroma_indexed = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notes")

    __table_args__ = (
        Index('ix_notes_user_id_is_pinned', 'user_id', 'is_pinned'),
        Index('ix_notes_user_id_updated_at', 'user_id', 'updated_at'),
    )

