from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from database.db import *
from dependencies.current_user import get_current_user
from models import MassPutGrades

router = APIRouter(prefix="/teacher")

@router.get("/grades/{group_name}",tags=["Учитель"])
async def grade_group(current_user: Annotated[User, Depends(get_current_user)], group_name: str):
    with db:
        if current_user.role.name == "Преподаватель":
            user_teacher = User.get((User.last_name == current_user.last_name) &
                    (User.first_name == current_user.first_name) & 
                    (User.middle_name == current_user.middle_name))
            teacher = Teacher.get(Teacher.user == user_teacher)
            discipline_teacher = teacher.discipline.name
            if not discipline_teacher:
                raise HTTPException(
                    status_code=400,
                    detail="Пока что вы ничего не преподаете "
                )
            try:
                group = Group.get(Group.name == group_name)
            except Group.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail=f"Группа {group_name} не найдена"
                )

            answer = []
            all_students_this_group = Student.select().join(Group).where(Student.group == group)
            for student in all_students_this_group:

                student_grades = Grade.select().join(Disciplines).where(
                    (Grade.student == student) & 
                    (Disciplines.name == discipline_teacher)
                )

                if student_grades.exists():
                    for grade in student_grades:
                        ans = dict()
                        ans["Студент"] = f"{student.user.last_name} {student.user.first_name} {student.user.middle_name}"
                        ans["Оценка"] = grade.grade
                        ans["Дата"] = grade.created_at
                        answer.append(ans)
                else:
                    ans = dict()
                    ans["Студент"] = f"{student.user.last_name} {student.user.first_name} {student.user.middle_name}"
                    ans["Оценка"] = None
                    ans["Дата"] = None
                    answer.append(ans)
            
            if not answer:
                return {"message": "Нет оценок по вашей дисциплине в этой группе"}
            
            return answer
        
        elif current_user.role.name == "Студент":
            raise HTTPException(
                status_code=403,
                detail="Студенты не могут просматривать оценки групп"
            )
        elif current_user.role.name == "Сотрудник учебного отдела":
            raise HTTPException(
                status_code=303,
                detail="Используйте эндпоинт /administator/grades/{group_name}"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Неизвестная роль пользователя"
            )


@router.patch("/mass-grades/{group_name}", tags=["Учитель"])        
async def put_mass_grades_group(current_user: Annotated[User, Depends(get_current_user)], mpg: MassPutGrades):
    if not mpg.students or not mpg.grades:
        raise HTTPException(
            status_code=400,
            detail="Списки студентов и оценок не могут быть пустыми"
        )
        
    if len(mpg.students) != len(mpg.grades):
        raise HTTPException(
            status_code=400,
            detail="Количество студентов должно совпадать с количеством оценок"
        )
        
    with db:
        if current_user.role.name != "Преподаватель":
            raise HTTPException(
                status_code=403,
                detail="Только преподаватели могут массово выставлять оценки"
            )
            
        answer = []
        try:
            teacher = Teacher.get(Teacher.user == current_user)
            discipline = teacher.discipline
        except Teacher.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail="Информация о преподавателе не найдена"
            )

        try:
            current_session = SessionPeriod.get(SessionPeriod.is_active == True)
        except SessionPeriod.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail="Активная сессия не найдена"
            )

        for i in range(len(mpg.students)):
            last_name,first_name,middle_name = mpg.students[i].split(" ")
            try:
                user = User.get(
                    (User.last_name == last_name) &
                    (User.first_name == first_name) &
                    (User.middle_name == middle_name)
                    )
                
                student_name = Student.get(Student.user == user)
            except (User.DoesNotExist,Student.DoesNotExist):
                raise HTTPException(
                    status_code=404,
                    detail="Студент не найден"
                )
            grade_student = mpg.grades[i]
            stud_grade, created = Grade.get_or_create(
            student=student_name,
            discipline=discipline,
            session=current_session,
            )
            if not created:
                stud_grade.grade = grade_student
                stud_grade.teacher = current_user
                stud_grade.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                stud_grade.save()

            for_answer = dict()
            for_answer["Студент"] = f"{student_name.user.last_name} {student_name.user.first_name} {student_name.user.middle_name}"
            for_answer["Оценка"] = grade_student  
            for_answer["Дисциплина"] = discipline.name
            for_answer["Сессия"] = current_session.name_session
            for_answer["Дата"] = datetime.now()
            answer.append(for_answer)
            stud_grade.save()
                    
        return answer