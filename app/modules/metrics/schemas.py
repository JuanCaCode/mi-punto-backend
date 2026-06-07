from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CityDistribution(BaseModel):
    city: str
    count: int
    percentage: float


class CategoryDistribution(BaseModel):
    category: str
    count: int
    percentage: float


class OwnerMetricsOut(BaseModel):
    total_businesses: int
    active_businesses: int
    inactive_businesses: int
    total_reviews: int
    total_visits: int
    cities: list[CityDistribution]
    categories: list[CategoryDistribution]


class RecentReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_full_name: str
    rating: int
    comment: str
    created_at: datetime
    has_response: bool


class BusinessMetricsOut(BaseModel):
    business_id: int
    profile_views: int
    total_reviews: int
    average_rating: float
    response_rate: float
    pending_responses: int
    recent_reviews: list[RecentReviewOut]
