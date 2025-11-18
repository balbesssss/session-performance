from fastapi import APIRouter, Depends, HTTPException
from database.db import *
from dependencies.current_user import get_current_user
from models import GradePutRequest
from typing import Annotated
from datetime import datetime

router = APIRouter()

@router.patch("/put_grade",tags=["Админ/учитель"])
async def put_grade(current_user: Annotated[User, Depends(get_current_user)], grade_put: GradePutRequest):
    with db:
        if current_user.role.name == "Преподаватель":
            user = User.get(
                (User.last_name == grade_put.last_name)&
                (User.first_name == grade_put.first_name)&
                (User.middle_name == grade_put.middle_name)
                )
            try:
                group = Group.get(Group.name == grade_put.group)
            except Group.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Группа не найдена"
                )
            try:
                student = Student.get(Student.user == user, Student.group == group)
            except Student.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Студент не найден"
                )
            
            try:
                discipline = Disciplines.get(Disciplines.name == grade_put.discipline)
            except Disciplines.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Дисциплина не найдена"
                )
            try:
                session = SessionPeriod.get(SessionPeriod.name_session == grade_put.session)
            except SessionPeriod.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Сессия не найдена"
                )
            try:
                teacher = Teacher.get(
                    (Teacher.user == current_user) &  
                    (Teacher.discipline == discipline))
            except Teacher.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Преподаватель не найден"
                )
            grade, created = Grade.get_or_create(
            student=student,
            discipline=discipline,
            session=session,
            defaults={
               'grade': grade_put.grade,
               'teacher': teacher.user
            })
               
            if not created:
                grade.grade = grade_put.grade
                grade.teacher = teacher.user
                grade.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                grade.save()
            return {
                "message": "Оценка создана" if created else "Оценка обновлена",
                "student": f"{student.user.last_name} {student.user.first_name} {student.user.middle_name}",
                "discipline": discipline.name, 
                "grade": grade_put.grade
                }
   
        elif current_user.role.name == "Сотрудник учебного отдела":
            
            user = User.get(
                (User.last_name == grade_put.last_name)&
                (User.first_name == grade_put.first_name)&
                (User.middle_name == grade_put.middle_name)
                )
            try:
                group = Group.get(Group.name == grade_put.group)
            except Group.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Группа не найдена"
                )
            try:
                student = Student.get(Student.user == user, Student.group == group)
            except Student.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Студент не найден"
                )
            
            try:
                discipline = Disciplines.get(Disciplines.name == grade_put.discipline)
            except Disciplines.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Дисциплина не найдена"
                )
            try:
                session = SessionPeriod.get(SessionPeriod.name_session == grade_put.session)
            except SessionPeriod.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Сессия не найдена"
                )
            try:
                admin = Admin.get(Admin.user == current_user)
            except Admin.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Сотрудник учебного отдела не найден"
                )
            
            grade, created = Grade.get_or_create(
            student=student,
            discipline=discipline,
            session=session,
            defaults={
               'grade': grade_put.grade,
               'teacher': admin.user
           })
                
            if not created:
                grade.grade = grade_put.grade
                grade.teacher = admin.user
                grade.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                grade.save()
            return {
                "message": "Оценка создана" if created else "Оценка обновлена",
                "student": f"{student.user.last_name} {student.user.first_name} {student.user.middle_name}",
                "discipline": discipline.name, 
                "grade": grade_put.grade
                }
            
        else:
            raise HTTPException(
                status_code=403,
                detail="У вас нет прав"  
                    )
