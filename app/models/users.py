from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, func, Integer, Enum as SAEnum,text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from uuid import uuid4
from typing import Optional

from app.db import Base
from app.schemas import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default=None)
    last_name: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default=None)
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole", create_type=True, native_enum=False), default=UserRole.user, nullable=False)
    token_version: Mapped[int] = mapped_column(
        Integer, server_default=text("1"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"User(id={self.id!r},first_name={self.first_name!r},email={self.email!r},created_at={self.created_at!r})"
