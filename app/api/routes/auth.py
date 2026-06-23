from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user

import base64
from urllib.parse import urlencode

import httpx
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.oauth_state import consume_oauth_state, create_oauth_state

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

from app.core.security import hash_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cette adresse email.",
        )

    new_user = User(
        first_name=user_data.first_name.strip(),
        last_name=user_data.last_name.strip(),
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
        auth_provider="email",
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == login_data.email.lower())
        .first()
    )

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé.",
        )

    password_is_valid = verify_password(
        login_data.password,
        user.password_hash,
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.get("/notion/login")
def login_with_notion():
    state = create_oauth_state()

    params = {
        "client_id": settings.notion_client_id,
        "response_type": "code",
        "owner": "user",
        "redirect_uri": settings.notion_redirect_uri,
        "state": state,
    }

    authorization_url = (
        "https://api.notion.com/v1/oauth/authorize?"
        + urlencode(params)
    )

    return RedirectResponse(url=authorization_url)

@router.get("/notion/callback")
async def notion_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Autorisation Notion refusée : {error}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code ou état OAuth Notion manquant.",
        )

    if not consume_oauth_state(state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="État OAuth invalide ou expiré.",
        )

    credentials = (
        f"{settings.notion_client_id}:"
        f"{settings.notion_client_secret}"
    )

    basic_token = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.notion.com/v1/oauth/token",
            headers={
                "Authorization": f"Basic {basic_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2026-03-11",
            },
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.notion_redirect_uri,
            },
            timeout=20,
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de récupérer le token Notion.",
        )

    notion_data = response.json()

    owner = notion_data.get("owner") or {}
    notion_user = owner.get("user") or {}
    person = notion_user.get("person") or {}

    notion_user_id = notion_user.get("id")
    notion_email = person.get("email")
    notion_name = notion_user.get("name") or "Utilisateur Notion"

    if not notion_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notion n'a pas retourné l'identifiant utilisateur.",
        )

    user = (
        db.query(User)
        .filter(User.notion_user_id == notion_user_id)
        .first()
    )

    if user is None and notion_email:
        user = (
            db.query(User)
            .filter(User.email == notion_email.lower())
            .first()
        )

    if user is None:
        name_parts = notion_name.strip().split(maxsplit=1)

        first_name = name_parts[0] if name_parts else "Utilisateur"
        last_name = name_parts[1] if len(name_parts) > 1 else "Notion"

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=notion_email or f"{notion_user_id}@notion.local",
            password_hash=None,
            auth_provider="notion",
            notion_user_id=notion_user_id,
            notion_workspace_id=notion_data.get("workspace_id"),
            notion_access_token=notion_data.get("access_token"),
            notion_refresh_token=notion_data.get("refresh_token"),
            notion_email=notion_email,
            is_active=True,
        )

        db.add(user)

    else:
        user.auth_provider = "notion"
        user.notion_user_id = notion_user_id
        user.notion_workspace_id = notion_data.get("workspace_id")
        user.notion_access_token = notion_data.get("access_token")
        user.notion_refresh_token = notion_data.get("refresh_token")
        user.notion_email = notion_email

    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id)

    return RedirectResponse(
        url=(
            f"{settings.notion_frontend_redirect_uri}"
            f"?access_token={access_token}"
        )
    )