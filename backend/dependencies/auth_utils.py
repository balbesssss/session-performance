import jwt
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from config import settings
from database.db import User
from fastapi import HTTPException

async def create_jwt_token(data: Dict[str, Any], expires_minutes: int = 30) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

async def verify_jwt_token(token: str) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("user_id") 
        if not int(user_id):
            raise HTTPException(status_code=401, detail="Что-то с токеном")
        
        user = User.get(User.id == user_id)
        return user
        
    except User.DoesNotExist:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Что-то с токеном")