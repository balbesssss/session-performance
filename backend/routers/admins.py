from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from database.db import *
from dependencies.current_user import get_current_user
from models import TeacherInfo, StudentCreate


router = APIRouter(prefix='/administrator')

@router.post("/create_teacher/",tags=["Админ"])
async def create_teacher(current_user: Annotated[User, Depends(get_current_user)], teacher: TeacherInfo, discipline_name: str):
    with db:
        if current_user.role.name != "Сотрудник учебного отдела":
            raise HTTPException(
                status_code=403,
                detail="Только сотрудники учебного отдела могут добавлять преподавателей",
            )
        teacher_role = Role.get(Role.name == "Преподаватель")
        try:
            get_teacher = User.get(
                (User.last_name == teacher.last_name) &
                (User.first_name == teacher.first_name) &
                (User.middle_name == teacher.middle_name) &
                (User.role == teacher_role)
            )
            raise HTTPException(status_code=400,detail="Преподаватель уже есть в базе данных")
        except User.DoesNotExist:
            try:
                discipline = Disciplines.get(Disciplines.name == discipline_name)
            except Disciplines.DoesNotExist:
                raise HTTPException(
                    status_code=400,
                    detail="Дисциплина не найдены"
                )
            new_teacher = User(
                last_name=teacher.last_name,
                first_name=teacher.first_name,
                middle_name=teacher.middle_name,
                role=teacher_role
            )
            new_teacher.set_password(teacher.password)
            new_teacher.save()
            Teacher.create(user=new_teacher,discipline=discipline)
            return {'message':f"{new_teacher.last_name} {new_teacher.first_name} {new_teacher.middle_name} теперь преподает {discipline_name}"}


@router.post("/create-group/", tags=["Админ"])
async def create_group(current_user: Annotated[User, Depends(get_current_user)],group_name: str):
    with db:
        if current_user.role.name != "Сотрудник учебного отдела":
            raise HTTPException(
                status_code=403,
                detail="У вас недостаточно прав"
            )
        if not group_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Название группы не может быть пустым"
            )
        try:
            group = Group.get(Group.name == group_name)
            raise HTTPException(
                status_code=404,
                detail=f"Группа {group_name} с таким названием уже есть"
            )
        except Group.DoesNotExist:
            Group.create(name=group_name)
            return {"message":f"Группа {group_name} была успешна создана"}


@router.post("/create-student/", tags=["Админ"])
async def create_student(current_user: Annotated[User, Depends(get_current_user)], student: StudentCreate):
    with db:
        if current_user.role.name != "Сотрудник учебного отдела":
            raise HTTPException(
                status_code=403,
                detail="У вас недостаточно прав"
            )
        student_role = Role.get(Role.name == "Студент")
        try:
            student_get = User.get(
                (User.last_name == student.last_name) &
                (User.first_name == student.first_name) & 
                (User.middle_name == student.middle_name) &
                (User.role == student_role)
            )
            return {"message": "Студент с такими данными уже существует"}
        except User.DoesNotExist:
            try:
                group = Group.get(Group.name == student.group)
            except Group.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail=f"Группа {student.group} не найдена"
                )
            
            new_student = User(
                last_name=student.last_name,
                first_name=student.first_name,
                middle_name=student.middle_name,
                role=student_role
                )
            new_student.set_password("123")
            new_student.save()

            Student.create(user=new_student,group=group)
            return {"message":"Студент успешно создан"}

        
@router.post("/fill_discipline/", tags=["Админ"])
async def fill_name_discipline(current_user: Annotated[User, Depends(get_current_user)],name_disciplines: list[str]):
    if not name_disciplines:
        raise HTTPException(
            status_code=400,
            detail="Пожалуйста введите хотябы одну дисциплину"
        )
    
    with db:
        if current_user.role.name != "Сотрудник учебного отдела":
            raise HTTPException(
                status_code=403,
                detail="У вас нет прав((("
            )
        
        created_count_discipline = 0
        for discipline in name_disciplines:
            try:
                get_discipline = Disciplines.get(name=discipline.strip())
                raise HTTPException(status_code=400,detail=f"{discipline} уже есть в базе данных")
            except Disciplines.DoesNotExist:
                dis = Disciplines(name=discipline.strip())
                dis.save()
                created_count_discipline += 1
        return {
                "message": f"Успешно создано {created_count_discipline} дисциплины",
                "created_count": created_count_discipline
            }


@router.get("/administrator/all_grades/", tags={"Админ"})
async def grades_all_group(current_user: Annotated[User, Depends(get_current_user)]):
    with db:
        if current_user.role.name == "Сотрудник учебного отдела":
            answer = []
            groups = Group.select()
            for group in groups:
                students = Student.select().join(Group).where(Group.name == group.name)
                student_grades = dict()
                student_grades["Группа"] = group.name
                student_grades["Информация"] = []
                for student in students:
                    grades = Grade.select().where(Grade.student == student)
                    info_student = dict()
                    info_student["Студент"] = f"{student.user.last_name} {student.user.first_name} {student.user.middle_name}"
                    info_student["Оценки"] = []
                    for grade in grades:
                        grade_student = dict()
                        grade_student["Дисциплина"] = grade.discipline.name
                        grade_student["Оценка"] = grade.grade
                        info_student["Оценки"].append(grade_student)
                    student_grades["Информация"].append(info_student)
                answer.append(student_grades)
            return answer
        else:
            raise HTTPException(
                status_code=403,
                detail="Вы не админ"
            )


@router.get("/administrator/grades/{group_name}", tags=["Админ"],)
async def grade_group(current_user: Annotated[User, Depends(get_current_user)], group_name: str):
    with db:
        if current_user.role.name != "Сотрудник учебного отдела":
            raise HTTPException(
                status_code=403,
                detail="У вас нет прав для просмотра оценок группы"
            )
            
        try:
            group = Group.get(Group.name == group_name)
        except Group.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail=f"Группа {group_name} не найдена"
            )
            
        students = Student.select().join(Group).where(Group.name == group_name)
            
        if not students:
            return {"message": "В группе нет студентов"}
          
        answer = []
        for student in students:
            grades = Grade.select().where(Grade.student == student)
            info_student = dict()
            info_student["Студент"] = f"{student.user.last_name} {student.user.first_name} {student.user.middle_name}"
            info_student["Оценки"] = []
            for grade in grades:
                grade_student = dict()
                grade_student["Дисциплина"] = grade.discipline.name
                grade_student["Оценка"] = grade.grade
                grade_student["Преподаватель"] = f"{grade.teacher.last_name} {grade.teacher.first_name} {grade.teacher.middle_name}"
                grade_student["Дата"] = grade.created_at
                info_student["Оценки"].append(grade_student)
            answer.append(info_student)
        return answer


@router.delete("/administrator/delete/{discipline}",tags=["Админ"])
async def delete_discipline(current_user: Annotated[User, Depends(get_current_user)], discipline: str):
    with db:
        if current_user.role.name == "Сотрудник учебного отдела":
            try: 
                discipline_for_delete = Disciplines.get(Disciplines.name == discipline)
            except Disciplines.DoesNotExist:
                raise HTTPException(status_code=400,detail="Не удалось получить дисциплину из таблицы")
            discipline_for_delete.delete_instance()
            return {"message":f"{discipline} была успешно удалена"}