from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, Index, String, Integer, DateTime, func, Enum as SAEnum, Boolean
import enum
import uuid
from datetime import datetime
from typing import Optional

from app.db import Base


class FileStatus(str, enum.Enum):
    pending = "pending"
    uploaded = "uploaded"
    failed = "failed"
    deleted = "deleted"


class File(Base):
    __tablename__ = "files"

    __table_args__ = (
        Index("idx_user_id_file_status", "user_id", "status","is_deleted"),
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)

    content_type: Mapped[str] = mapped_column(String(100), nullable=True)

    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)

    s3_bucket: Mapped[str] = mapped_column(String(255))

    s3_key: Mapped[str] = mapped_column(String(512), unique=True)

    status: Mapped[FileStatus] = mapped_column(
        SAEnum(FileStatus, name="file_status", create_type=True),
        default=FileStatus.pending,
        nullable=False
    )
    presigned_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    user: Mapped["User"] = relationship(back_populates="files") # type: ignore[reportUndefinedVariable]

    def __repr__(self) -> str:
        return f"User(id={self.id!r},user_id={self.user_id},original_filename={self.original_filename!r},content_type={self.content_type!r},size_bytes={self.size_bytes!r},s3_bucket={self.s3_bucket!r},s3_key={self.s3_key!r},status={self.status!r},presigned_expires_at={self.presigned_expires_at!r},uploaded_at={self.uploaded_at!r},deleted_at={self.deleted_at!r},is_deleted={self.is_deleted!r},updated_at={self.updated_at!r},created_at={self.created_at!r})"
