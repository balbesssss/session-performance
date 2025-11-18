from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from database.db import *
from dependencies.current_user import get_current_user


router = APIRouter(prefix='/student')

@router.get("/my_grades", tags=["Студент"])
async def get_grades(current_user: Annotated[User, Depends(get_current_user)]): 
    with db:
        if current_user.role.name != "Студент":
            raise HTTPException(
                status_code=403,
                detail="Просматривать оценки могут только студенты"
            )
            
        try:
            student = Student.get(Student.user == current_user)
        except Student.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail="Профиль студента не найден"
                )
            
        grades = Grade.select().where(Grade.student == student)
            
        if not grades:
            return {"message": "У вас пока нет оценок"}
            
        answer = []
        for grade in grades:
            info = dict()
            info["Дисциплина"] = grade.discipline.name
            info["Оценка"] = grade.grade
            info["Учитель"] = f"{grade.teacher.last_name} {grade.teacher.first_name} {grade.teacher.middle_name}"
            info["Дата оценки"] = grade.created_at
            answer.append(info)
        return answer

@router.get("/edit-password",tags=["Студент"])
async def edit_password(current_user: Annotated[User, Depends(get_current_user)], password: str):
    with db:
        if current_user.role.name == "Студент":
            try:
                user = User.get(
                    (User.last_name == current_user.last_name) &
                    (User.first_name == current_user.first_name) &
                    (User.middle_name == current_user.middle_name)&
                    (User.role == current_user.role)
                )
            except User.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Студент не найден"
                )
            
            user.set_password(password)
            user.save()
            return {"message":"Пароль изменен"}
