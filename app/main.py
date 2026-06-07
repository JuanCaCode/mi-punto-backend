from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.businesses.router import router as businesses_router
from app.modules.categories.router import router as categories_router
from app.modules.metrics.router import router as metrics_router
from app.modules.reviews.router import (
    business_reviews_router,
    reviews_router,
)
from app.modules.uploads.router import router as uploads_router
from app.modules.users.router import router as users_router
from app.shared.cities_router import router as cities_router

app = FastAPI(title="Mi Punto API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.upload_path)), name="uploads")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(businesses_router, prefix="/businesses", tags=["businesses"])
app.include_router(
    business_reviews_router,
    prefix="/businesses/{business_id}/reviews",
    tags=["reviews"],
)
app.include_router(reviews_router, prefix="/reviews", tags=["reviews"])
app.include_router(categories_router, prefix="/categories", tags=["categories"])
app.include_router(cities_router, prefix="/cities", tags=["cities"])
app.include_router(uploads_router, prefix="/uploads-api", tags=["uploads"])
app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])


# se agrega comentario
@app.get("/", tags=["health"])
def root():
    return {"message": "Mi Punto API funcionando", "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
