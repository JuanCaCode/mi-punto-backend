from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.businesses.models import Business, Media

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
EXT_BY_MIME = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_BYTES = 5 * 1024 * 1024  # 5 MiB

# HU-01: el logo se acepta sólo en JPG/PNG y con un tope más bajo (2 MiB).
LOGO_ALLOWED_MIME = {"image/jpeg", "image/png"}
LOGO_MAX_BYTES = 2 * 1024 * 1024


def _get_owned_business(db: Session, current_user: User) -> Business:
    business = db.scalar(select(Business).where(Business.owner_id == current_user.id))
    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You do not manage a business yet",
        )
    return business


def _media_url(path: str) -> str:
    return f"{settings.PUBLIC_BASE_URL}/uploads/{path}"


async def upload_for_my_business(db: Session, current_user: User, file: UploadFile) -> Media:
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Allowed types: {', '.join(sorted(ALLOWED_MIME))}",
        )

    business = _get_owned_business(db, current_user)
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large; max {MAX_BYTES // (1024 * 1024)} MiB",
        )

    business_dir = settings.upload_path / "businesses" / str(business.id)
    business_dir.mkdir(parents=True, exist_ok=True)

    ext = EXT_BY_MIME[file.content_type]
    filename = f"{uuid4().hex}{ext}"
    target = business_dir / filename
    target.write_bytes(contents)

    relative_path = f"businesses/{business.id}/{filename}"

    has_existing = db.scalar(
        select(func.count(Media.id)).where(Media.business_id == business.id)
    ) or 0

    next_sort = (
        db.scalar(
            select(func.coalesce(func.max(Media.sort_order), -1)).where(
                Media.business_id == business.id
            )
        )
        or -1
    )

    media = Media(
        business_id=business.id,
        path=relative_path,
        is_primary=has_existing == 0,
        sort_order=next_sort + 1,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def list_my_business_media(db: Session, current_user: User) -> list[Media]:
    business = _get_owned_business(db, current_user)
    return list(
        db.execute(
            select(Media)
            .where(Media.business_id == business.id)
            .order_by(Media.is_primary.desc(), Media.sort_order.asc())
        )
        .scalars()
        .all()
    )


def set_primary_media(db: Session, current_user: User, media_id: int) -> Media:
    business = _get_owned_business(db, current_user)
    media = db.get(Media, media_id)
    if media is None or media.business_id != business.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media not found")

    others = db.execute(
        select(Media).where(Media.business_id == business.id, Media.is_primary.is_(True))
    ).scalars().all()
    for m in others:
        m.is_primary = False
    media.is_primary = True
    db.commit()
    db.refresh(media)
    return media


async def upload_logo_for_my_business(
    db: Session, current_user: User, file: UploadFile
) -> Business:
    if file.content_type not in LOGO_ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato no permitido. Use JPG o PNG.",
        )

    business = _get_owned_business(db, current_user)
    contents = await file.read()
    if len(contents) > LOGO_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El logo supera {LOGO_MAX_BYTES // (1024 * 1024)} MiB.",
        )
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío.",
        )

    business_dir = settings.upload_path / "businesses" / str(business.id)
    business_dir.mkdir(parents=True, exist_ok=True)

    ext = EXT_BY_MIME[file.content_type]
    filename = f"logo-{uuid4().hex}{ext}"
    target = business_dir / filename
    target.write_bytes(contents)

    previous = business.logo_path
    business.logo_path = f"businesses/{business.id}/{filename}"
    db.commit()
    db.refresh(business)

    if previous:
        old_file = settings.upload_path / previous
        try:
            if old_file.is_file():
                old_file.unlink()
        except OSError:
            pass

    return business


def delete_logo_for_my_business(db: Session, current_user: User) -> Business:
    business = _get_owned_business(db, current_user)
    previous = business.logo_path
    business.logo_path = None
    db.commit()
    db.refresh(business)

    if previous:
        old_file = settings.upload_path / previous
        try:
            if old_file.is_file():
                old_file.unlink()
        except OSError:
            pass

    return business


def delete_my_media(db: Session, current_user: User, media_id: int) -> None:
    business = _get_owned_business(db, current_user)
    media = db.get(Media, media_id)
    if media is None or media.business_id != business.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media not found")

    file_path = settings.upload_path / media.path
    db.delete(media)
    db.commit()

    try:
        if file_path.is_file():
            file_path.unlink()
    except OSError:
        # No bloqueamos por errores de filesystem.
        pass

    if media.is_primary:
        # Promover otra imagen como principal si quedan.
        replacement = db.scalar(
            select(Media)
            .where(Media.business_id == business.id)
            .order_by(Media.sort_order.asc())
        )
        if replacement is not None:
            replacement.is_primary = True
            db.commit()
