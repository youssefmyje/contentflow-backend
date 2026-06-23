from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.database import router as database_router
from app.api.routes.health import router as health_router
from app.db.database import Base, engine
from app.models import User


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="ContentFlow Backend API",
    description="Backend FastAPI de la plateforme SaaS ContentFlow.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(database_router)
app.include_router(auth_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Bienvenue sur ContentFlow Backend API."
    }