from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, func, Integer, Enum as SAEnum, text, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from datetime import datetime
from typing import Optional, List

from app.db import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"
    moderator = "moderator"


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        Index("idx_users_email", "email"),       # fast login lookup
        Index("idx_users_username", "username"),  # fast login lookup
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole", create_type=True), 
        default=UserRole.user, 
        nullable=False
    )
    token_version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    refresh_sessions: Mapped[List["RefreshSession"]] = relationship(  # type: ignore[reportUndefinedVariable]
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r},username={self.username},first_name={self.first_name!r},last_name={self.last_name!r},email={self.email!r},phone_number={self.phone_number!r},role={self.role},is_verified={self.is_verified!r},is_active={self.is_active!r},token_version={self.token_version!r},password_hash=*******,updated_at={self.updated_at!r},created_at={self.created_at!r})"
