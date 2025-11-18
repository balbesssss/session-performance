from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from database.db import *
from dependencies.auth_utils import create_jwt_token
from models import Token
from config import settings


router = APIRouter()

@router.post("/token", response_model=Token, tags=["system"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        parts = form_data.username.split(' ')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Неверный формат имени")
        
        last_name, first_name, middle_name = parts
        user = User.get(
            (User.last_name == last_name) &
            (User.first_name == first_name) & 
            (User.middle_name == middle_name)
        )
        
        if not user.check_password(form_data.password):
            raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
        
        token = await create_jwt_token(data={"user_id": user.id}, expires_minutes=settings.access_token_expire_minutes)
        return Token(access_token=token, token_type="bearer")
        
    except User.DoesNotExist:
        raise HTTPException(status_code=401, detail="Пользователя нет в базе данных")
