from typing import Optional

from fastapi import HTTPException, status
from geoalchemy2.shape import to_shape
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.businesses.models import Business, BusinessVisit, Category, Media
from app.modules.businesses.schemas import (
    BusinessCreate,
    BusinessDetail,
    BusinessLocationUpdate,
    BusinessOwnerRow,
    BusinessUpdate,
    CategoryOut,
    MediaOut,
    MyBusinessOut,
    PublicBusinessDetail,
    PublicBusinessSummary,
)
from app.modules.reviews.models import Review
from app.shared.cities import CITIES


def _media_url(path: str) -> str:
    return f"{settings.PUBLIC_BASE_URL}/uploads/{path}"


def _logo_url(business: Business) -> Optional[str]:
    return _media_url(business.logo_path) if business.logo_path else None


def _location_to_lat_lng(location) -> tuple[Optional[float], Optional[float]]:
    if location is None:
        return None, None
    point = to_shape(location)
    return float(point.y), float(point.x)  # POINT stored as (lng, lat) → shapely y=lat, x=lng


def _validate_city(city: str) -> None:
    if city not in CITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"City '{city}' is not allowed. Use one of: {', '.join(CITIES)}",
        )


def _validate_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")
    return category


def _build_my_business_view(db: Session, business: Business) -> MyBusinessOut:
    media_rows = (
        db.execute(
            select(Media)
            .where(Media.business_id == business.id)
            .order_by(Media.is_primary.desc(), Media.sort_order.asc())
        )
        .scalars()
        .all()
    )
    media_out = [
        MediaOut(id=m.id, url=_media_url(m.path), is_primary=m.is_primary, sort_order=m.sort_order)
        for m in media_rows
    ]
    cover_url = next((m.url for m in media_out if m.is_primary), None) or (
        media_out[0].url if media_out else None
    )

    review_count = db.scalar(
        select(func.count(Review.id)).where(Review.business_id == business.id)
    ) or 0
    avg_rating = (
        db.scalar(select(func.coalesce(func.avg(Review.rating), 0.0)).where(Review.business_id == business.id))
        or 0.0
    )
    profile_views = (
        db.scalar(select(func.count(BusinessVisit.id)).where(BusinessVisit.business_id == business.id))
        or 0
    )
    lat, lng = _location_to_lat_lng(business.location)

    return MyBusinessOut(
        id=business.id,
        name=business.name,
        description=business.description,
        city=business.city,
        address=business.address,
        phone=business.phone,
        email=business.email,
        hours=business.hours,
        is_active=business.is_active,
        category=CategoryOut.model_validate(business.category),
        cover_url=cover_url,
        logo_url=_logo_url(business),
        instagram_url=business.instagram_url,
        facebook_url=business.facebook_url,
        media=media_out,
        lat=lat,
        lng=lng,
        average_rating=round(float(avg_rating), 2),
        review_count=int(review_count),
        profile_views=int(profile_views),
    )


def get_my_business(db: Session, current_user: User) -> Business | None:
    return db.scalar(select(Business).where(Business.owner_id == current_user.id))


def get_my_business_view(db: Session, current_user: User) -> MyBusinessOut | None:
    business = get_my_business(db, current_user)
    if business is None:
        return None
    return _build_my_business_view(db, business)


def create_my_business(db: Session, current_user: User, payload: BusinessCreate) -> MyBusinessOut:
    if get_my_business(db, current_user) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already manage a business; only one per admin is allowed in this MVP.",
        )
    _validate_city(payload.city)
    _validate_category(db, payload.category_id)

    business = Business(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
        city=payload.city,
        address=payload.address,
        phone=payload.phone,
        email=payload.email,
        hours=payload.hours,
        instagram_url=payload.instagram_url,
        facebook_url=payload.facebook_url,
        is_active=True,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return _build_my_business_view(db, business)


def update_my_business(
    db: Session, current_user: User, payload: BusinessUpdate
) -> MyBusinessOut:
    business = get_my_business(db, current_user)
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You do not manage a business yet")

    data = payload.model_dump(exclude_unset=True)
    if "city" in data and data["city"] is not None:
        _validate_city(data["city"])
    if "category_id" in data and data["category_id"] is not None:
        _validate_category(db, data["category_id"])

    for key, value in data.items():
        setattr(business, key, value)
    db.commit()
    db.refresh(business)
    return _build_my_business_view(db, business)


def _cover_url_for_business(db: Session, business_id: int) -> Optional[str]:
    media = db.scalar(
        select(Media)
        .where(Media.business_id == business_id)
        .order_by(Media.is_primary.desc(), Media.sort_order.asc())
    )
    return _media_url(media.path) if media is not None else None


def _aggregate_review(db: Session, business_id: int) -> tuple[int, float]:
    review_count = db.scalar(
        select(func.count(Review.id)).where(Review.business_id == business_id)
    ) or 0
    avg_rating = (
        db.scalar(
            select(func.coalesce(func.avg(Review.rating), 0.0)).where(Review.business_id == business_id)
        )
        or 0.0
    )
    return int(review_count), round(float(avg_rating), 2)


def list_public_businesses(
    db: Session,
    *,
    city: Optional[str] = None,
    category_id: Optional[int] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 24,
) -> list[PublicBusinessSummary]:
    stmt = select(Business).where(Business.is_active.is_(True))
    if city:
        stmt = stmt.where(Business.city == city)
    if category_id:
        stmt = stmt.where(Business.category_id == category_id)
    if q:
        stmt = stmt.where(Business.name.ilike(f"%{q}%"))

    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    stmt = stmt.order_by(Business.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    rows = list(db.execute(stmt).scalars().all())
    return [_to_public_summary(db, business) for business in rows]


def list_nearby_businesses(
    db: Session, *, lat: float, lng: float, radius_km: float, limit: int = 50
) -> list[PublicBusinessSummary]:
    radius_m = max(radius_km, 0) * 1000
    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    distance_expr = func.ST_Distance(
        func.ST_Transform(Business.location, 3857),
        func.ST_Transform(point, 3857),
    )

    stmt = (
        select(Business, distance_expr.label("distance_m"))
        .where(Business.is_active.is_(True))
        .where(Business.location.is_not(None))
        .where(
            func.ST_DWithin(
                func.ST_Transform(Business.location, 3857),
                func.ST_Transform(point, 3857),
                radius_m,
            )
        )
        .order_by(distance_expr.asc())
        .limit(max(min(limit, 100), 1))
    )

    results: list[PublicBusinessSummary] = []
    for business, distance_m in db.execute(stmt).all():
        summary = _to_public_summary(db, business)
        summary.distance_km = round(float(distance_m) / 1000, 2)
        results.append(summary)
    return results


def get_public_business_detail(
    db: Session, business_id: int, *, viewer_id: Optional[int] = None
) -> PublicBusinessDetail:
    business = db.get(Business, business_id)
    if business is None or not business.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business not found")

    # Registramos visita (RF-17). Best-effort: si falla no rompe el GET.
    try:
        db.add(BusinessVisit(business_id=business.id, user_id=viewer_id))
        db.commit()
    except Exception:  # pragma: no cover - defensive
        db.rollback()

    media_rows = (
        db.execute(
            select(Media)
            .where(Media.business_id == business.id)
            .order_by(Media.is_primary.desc(), Media.sort_order.asc())
        )
        .scalars()
        .all()
    )
    media_out = [
        MediaOut(id=m.id, url=_media_url(m.path), is_primary=m.is_primary, sort_order=m.sort_order)
        for m in media_rows
    ]
    cover_url = next((m.url for m in media_out if m.is_primary), None) or (
        media_out[0].url if media_out else None
    )

    review_count, avg_rating = _aggregate_review(db, business.id)
    lat, lng = _location_to_lat_lng(business.location)
    category = db.get(Category, business.category_id)

    return PublicBusinessDetail(
        id=business.id,
        name=business.name,
        description=business.description,
        city=business.city,
        address=business.address,
        phone=business.phone,
        email=business.email,
        hours=business.hours,
        category=CategoryOut.model_validate(category),
        cover_url=cover_url,
        logo_url=_logo_url(business),
        instagram_url=business.instagram_url,
        facebook_url=business.facebook_url,
        media=media_out,
        average_rating=avg_rating,
        review_count=review_count,
        lat=lat,
        lng=lng,
    )


def _to_public_summary(db: Session, business: Business) -> PublicBusinessSummary:
    review_count, avg_rating = _aggregate_review(db, business.id)
    cover_url = _cover_url_for_business(db, business.id)
    lat, lng = _location_to_lat_lng(business.location)
    category = business.category or db.get(Category, business.category_id)

    return PublicBusinessSummary(
        id=business.id,
        name=business.name,
        description=business.description,
        city=business.city,
        address=business.address,
        category=CategoryOut.model_validate(category),
        cover_url=cover_url,
        logo_url=_logo_url(business),
        average_rating=avg_rating,
        review_count=review_count,
        lat=lat,
        lng=lng,
        distance_km=None,
    )


def update_my_business_location(
    db: Session, current_user: User, payload: BusinessLocationUpdate
) -> MyBusinessOut:
    business = get_my_business(db, current_user)
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You do not manage a business yet")

    business.location = f"SRID=4326;POINT({payload.lng} {payload.lat})"
    if payload.address is not None:
        business.address = payload.address
    db.commit()
    db.refresh(business)
    return _build_my_business_view(db, business)


def list_businesses_for_owner(
    db: Session, q: Optional[str], status_filter: Optional[str]
) -> list[BusinessOwnerRow]:
    stmt = (
        select(Business, Category, User)
        .join(Category, Category.id == Business.category_id)
        .join(User, User.id == Business.owner_id)
    )
    if q:
        stmt = stmt.where(Business.name.ilike(f"%{q}%"))
    if status_filter == "active":
        stmt = stmt.where(Business.is_active.is_(True))
    elif status_filter == "inactive":
        stmt = stmt.where(Business.is_active.is_(False))

    stmt = stmt.order_by(Business.created_at.desc())
    rows: list[BusinessOwnerRow] = []
    for business, category, admin in db.execute(stmt).all():
        rows.append(
            BusinessOwnerRow(
                id=business.id,
                name=business.name,
                city=business.city,
                is_active=business.is_active,
                category_name=category.name,
                admin_full_name=admin.full_name,
                admin_email=admin.email,
            )
        )
    return rows


def get_business_for_owner(db: Session, business_id: int) -> BusinessDetail:
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business not found")

    category = db.get(Category, business.category_id)
    admin = db.get(User, business.owner_id)

    media_rows = (
        db.execute(
            select(Media)
            .where(Media.business_id == business.id)
            .order_by(Media.is_primary.desc(), Media.sort_order.asc())
        )
        .scalars()
        .all()
    )
    media_out = [
        MediaOut(id=m.id, url=_media_url(m.path), is_primary=m.is_primary, sort_order=m.sort_order)
        for m in media_rows
    ]
    cover_url = next((m.url for m in media_out if m.is_primary), None) or (
        media_out[0].url if media_out else None
    )

    review_count = db.scalar(
        select(func.count(Review.id)).where(Review.business_id == business.id)
    ) or 0
    avg_rating = (
        db.scalar(select(func.coalesce(func.avg(Review.rating), 0.0)).where(Review.business_id == business.id))
        or 0.0
    )
    profile_views = (
        db.scalar(select(func.count(BusinessVisit.id)).where(BusinessVisit.business_id == business.id))
        or 0
    )

    lat, lng = _location_to_lat_lng(business.location)

    return BusinessDetail(
        id=business.id,
        name=business.name,
        description=business.description,
        city=business.city,
        address=business.address,
        phone=business.phone,
        email=business.email,
        hours=business.hours,
        is_active=business.is_active,
        category=CategoryOut.model_validate(category),
        cover_url=cover_url,
        logo_url=_logo_url(business),
        instagram_url=business.instagram_url,
        facebook_url=business.facebook_url,
        media=media_out,
        average_rating=round(float(avg_rating), 2),
        review_count=int(review_count),
        profile_views=int(profile_views),
        lat=lat,
        lng=lng,
        admin_full_name=admin.full_name if admin else None,
        admin_email=admin.email if admin else None,
        created_at=business.created_at,
    )


def toggle_business(db: Session, business_id: int) -> Business:
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business not found")
    business.is_active = not business.is_active
    db.commit()
    db.refresh(business)
    return business
