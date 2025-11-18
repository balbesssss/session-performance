from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from database.db import *
from models import InfoStudentResponse, UserInfo
from dependencies.current_user import get_current_user

router = APIRouter()

@router.get("/users/me/", tags=["Пользователи"])
async def read_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    with db:
        if current_user.role.name == "Студент":
            try:
                group = Student.get(Student.user == current_user)
                return InfoStudentResponse(
                    last_name=current_user.last_name,
                    first_name=current_user.first_name,
                    middle_name=current_user.middle_name,
                    password="********", 
                    role=current_user.role.name,
                    group=group.group.name
                    )
            except Student.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Профиль студента не найден"
                )
        else:
            return UserInfo(
                    last_name=current_user.last_name,
                    first_name=current_user.first_name,
                    middle_name=current_user.middle_name,
                    password="********", 
                    role=current_user.role.name
                    )
