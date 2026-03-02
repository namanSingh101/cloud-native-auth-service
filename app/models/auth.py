from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Index, ForeignKey, String, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from typing import Optional

from app.db import Base


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    __table_args__ = (
        Index("idx_user_active_sessions", "user_id", "is_revoked"),
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    hashed_token: Mapped[str] = mapped_column(String(255), nullable=False)
    device_info: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
   
    user: Mapped["User"] = relationship(back_populates="refresh_sessions") # type: ignore[reportUndefinedVariable]

    def __repr__(self) -> str:
        return f"User(id={self.id!r},user_id={self.user_id},hashed_token=*******,device_info={self.device_info!r},ip_address={self.ip_address!r},expires_at={self.expires_at!r},is_revoked={self.is_revoked!r},updated_at={self.updated_at!r},created_at={self.created_at!r})"
