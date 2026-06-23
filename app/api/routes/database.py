from fastapi import APIRouter
from sqlalchemy import text

from app.db.database import engine


router = APIRouter(
    prefix="/database",
    tags=["Database"],
)


@router.get("/health")
def database_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "status": "ok",
        "database": "PostgreSQL",
        "test_result": value,
    }