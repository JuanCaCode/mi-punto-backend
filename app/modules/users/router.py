from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import UserOut, UserUpdate
from app.modules.reviews import service as reviews_service
from app.modules.reviews.schemas import MyReviewOut
from app.modules.users import service as users_service

router = APIRouter()


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=UserOut)
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    return await users_service.save_user_avatar(db, current_user, file)


@router.get("/me/reviews", response_model=list[MyReviewOut])
def list_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MyReviewOut]:
    return reviews_service.list_my_reviews(db, current_user)
