from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_role
from app.modules.auth.models import User, UserRole
from app.modules.businesses import service as businesses_service
from app.modules.businesses.schemas import MediaOut, MyBusinessOut
from app.modules.uploads import service

router = APIRouter()


def _to_out(media) -> MediaOut:
    return MediaOut(
        id=media.id,
        url=f"{settings.PUBLIC_BASE_URL}/uploads/{media.path}",
        is_primary=media.is_primary,
        sort_order=media.sort_order,
    )


@router.post("/business/me", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.business_admin)),
) -> MediaOut:
    media = await service.upload_for_my_business(db, current_user, file)
    return _to_out(media)


@router.get("/business/me", response_model=list[MediaOut])
def list_media(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.business_admin)),
) -> list[MediaOut]:
    return [_to_out(m) for m in service.list_my_business_media(db, current_user)]


@router.patch("/media/{media_id}/primary", response_model=MediaOut)
def set_primary(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.business_admin)),
) -> MediaOut:
    media = service.set_primary_media(db, current_user, media_id)
    return _to_out(media)


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.business_admin)),
) -> None:
    service.delete_my_media(db, current_user, media_id)


@router.post("/business/me/logo", response_model=MyBusinessOut)
async def upload_business_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.business_admin)),
) -> MyBusinessOut:
    await service.upload_logo_for_my_business(db, current_user, file)
    view = businesses_service.get_my_business_view(db, current_user)
    assert view is not None
    return view


@router.delete("/business/me/logo", response_model=MyBusinessOut)
def delete_business_logo(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.business_admin)),
) -> MyBusinessOut:
    service.delete_logo_for_my_business(db, current_user)
    view = businesses_service.get_my_business_view(db, current_user)
    assert view is not None
    return view
