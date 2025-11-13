from typing import Annotated
from fastapi import Depends
from dependencies.auth_utils import verify_jwt_token
from database.db import User
from fastapi.security import OAuth2PasswordBearer

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(OAUTH2_SCHEME)]) -> User:
    user = await verify_jwt_token(token)
    return user
