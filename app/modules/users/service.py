from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024


def _extension_for_content_type(content_type: str) -> str:
    if content_type == "image/jpeg":
        return ".jpg"
    if content_type == "image/png":
        return ".png"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Solo se permiten imágenes JPG y PNG",
    )


def _remove_file_if_exists(relative_path: str | None) -> None:
    if not relative_path:
        return
    path = settings.upload_path / relative_path
    if path.is_file():
        path.unlink()


async def save_user_avatar(db: Session, user: User, file: UploadFile) -> User:
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten imágenes JPG y PNG",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen no puede superar 2 MB",
        )

    ext = _extension_for_content_type(content_type)
    relative_path = f"avatars/user_{user.id}{ext}"
    destination: Path = settings.upload_path / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)

    if user.avatar_path and user.avatar_path != relative_path:
        _remove_file_if_exists(user.avatar_path)

    destination.write_bytes(content)
    user.avatar_path = relative_path
    db.commit()
    db.refresh(user)
    return user
