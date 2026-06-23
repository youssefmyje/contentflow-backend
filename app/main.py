from fastapi import FastAPI

from app.api.routes.health import router as health_router


app = FastAPI(
    title="ContentFlow Backend API",
    description="Backend FastAPI de la plateforme SaaS ContentFlow.",
    version="0.1.0",
)

app.include_router(health_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Bienvenue sur ContentFlow Backend API."
    }