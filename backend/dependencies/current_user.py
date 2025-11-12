from typing import Annotated
from fastapi import Depends
from backend.dependencies.auth_utils import verify_jwt_token
from database.db import User
from fastapi.security import OAuth2PasswordBearer

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(OAUTH2_SCHEME)]) -> User:
    return await verify_jwt_token(token)


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
