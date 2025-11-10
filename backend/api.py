import peewee
from datetime import datetime
from typing import Annotated, Dict, List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from models import *
from database.db import User, Role, db, Disciplines, Group, Grade, StudentProfile, SessionPeriod, Teacher, Admin
from auth_utils import create_jwt_token
from config import settings
from dependencies.current_user import get_current_active_user

app = FastAPI()


@app.post("/register/",tags=["system"])
async def create_user(user: UserInfo):
    try:
        with db:
            student_role = Role.get(Role.name == 'Студент')
            new_user = User(
                username=user.name,
                role=student_role)
            new_user.set_password(user.password)
            new_user.save()
            return {"message": "Пользователь успешно создан"}
    except peewee.IntegrityError as exc:
        raise HTTPException(
            status_code=400,
            detail="Имя пользователя уже занято"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка"
        ) from exc


@app.post("/add_teacher/", response_model=Dict[str, str], tags=["Админ"])
async def add_teacher(
    teacher: TeacherInfo,
    current_user: Annotated[User, Depends(get_current_active_user)]) -> Dict[str, str]:
    try:
        with db:
            if current_user.role.name != "Сотрудник учебного отдела":
                raise HTTPException(
                    status_code=403,
                    detail="Только сотрудники учебного отдела могут добавлять преподавателей",
                )
            teacher_role = Role.get(Role.name == "Преподаватель")
            new_user = User(
                username=teacher.name,
                role=teacher_role
            )
            new_user.set_password(teacher.password)
            new_user.save()
            return {"message": "Преподаватель успешно добавлен"}
    except peewee.DoesNotExist as exc:
        raise HTTPException(
            status_code=400,
            detail="Роль 'Преподаватель' не найдена") from exc
    except peewee.IntegrityError as exc:
        raise HTTPException(
            status_code=400,
            detail="Имя пользователя уже занято") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Произошла ошибка: {exc}") from exc


@app.post("/fill_discipline/", tags=["Админ"])
async def fill_name_discipline(name_disciplines: List[str], current_user: Annotated[User, Depends(get_current_active_user)]):
    if name_disciplines:
        with db:
            if current_user.role.name == "Сотрудник учебного отдела":
                for discipline in name_disciplines:
                    dis = Disciplines(name=discipline)
                    dis.save()
            else:
                raise HTTPException(
                    status_code=403,
                    detail=f"У вас нет прав (("
                )
    else:
        raise HTTPException(
            status_code=400,
            detail="Пожалуйста введите хотябы одну дисциплину"
        )


@app.patch("/put_grade",tags=["Админ/учитель"])
async def put_grade(current_user: Annotated[User,Depends(get_current_active_user)],grade_put: GradePutRequest):
    with db:
        if current_user.role.name == "Преподаватель":
            student = StudentProfile.get(StudentProfile.full_name == grade_put.student_full_name)
            discipline = Disciplines.get(Disciplines.name == grade_put.discipline)
            session = SessionPeriod.get(SessionPeriod.name_session == grade_put.session)
            teacher = Teacher.get(
            (Teacher.user == current_user) &  
            (Teacher.discipline == discipline))
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
                grade.save()
            return {
                "message": "Оценка создана" if created else "Оценка обновлена",
                "student": student.full_name,
                "discipline": discipline.name, 
                "grade": grade_put.grade
                }
        
        if current_user.role.name == "Сотрудник учебного отдела":
            student = StudentProfile.get(StudentProfile.full_name == grade_put.student_full_name)
            discipline = Disciplines.get(Disciplines.name == grade_put.discipline)
            session = SessionPeriod.get(SessionPeriod.name_session == grade_put.session)
            admin = Admin.get(Admin.name == current_user)
            grade, created = Grade.get_or_create(
            student=student,
            discipline=discipline,
            session=session,
            defaults={
                'grade': grade_put.grade,
                'teacher': admin.name
            })
            
            if not created:
                grade.grade = grade_put.grade
                grade.teacher = admin.name
                grade.save()
            return {
                "message": "Оценка создана" if created else "Оценка обновлена",
                "student": student.full_name,
                "discipline": discipline.name, 
                "grade": grade_put.grade
                }
        
        else:
            raise HTTPException(
              status_code=403,
              detail=f"У вас нет прав (("  
            )

@app.get("/administator/grades/{group_name}", tags=["Админ"],)
async def grade_group(current_user: Annotated[User,Depends(get_current_active_user)], group_name: str):
    with db:
        if current_user.role.name == "Сотрудник учебного отдела":
            students = StudentProfile.select().join(Group).where(Group.name == group_name)
            answer = []
            for student in students:
                grades = Grade.select().where(Grade.student == student)
                indo_student = dict()
                indo_student["Студент"] = student.full_name
                indo_student["Оценки"] = []
                for grade in grades:
                    grade_student = dict()
                    grade_student["Дисциплина"] = grade.discipline.name
                    grade_student["Оценка"] = grade.grade
                    indo_student["Оценки"].append(grade_student)
                answer.append(indo_student)
            return answer
        

@app.get("/teacher/grades/{group_name}",tags=["Учитель"])
async def grade_group(current_user: Annotated[User,Depends(get_current_active_user)],group_name: str):
    with db:
        if current_user.role.name == "Преподаватель":
            disciplines_teacher = []
            disciplines = (Teacher.select().join(User).where(User.username == current_user.username))
            for i in disciplines:
                disciplines_teacher.append(i.discipline.name)
            answer = []
            all_student_grades = Grade.select().join(Disciplines).switch(Grade).join(StudentProfile, on=Grade.student).join(Group).where((Disciplines.name == disciplines_teacher[0]) & (Group.name == group_name))
            for i in all_student_grades:
                ans = dict()
                ans["Студент"] = i.student.full_name
                ans["Оценка"] = i.grade
                ans["Дата"] = i.created_at
                answer.append(ans)
            return answer
        if current_user.role.name == "Студент":
            raise HTTPException(
                status_code=403,
                detail="Такой функцией не может обладать студент"
            )
        if current_user.role.name == "Сотрудник учебного отдела":
            raise HTTPException(
                status_code=303,
                detail="У вас есть своя функция, поищите ее"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Вы кто?"
            )


@app.patch("/teacher/mass-grades/{group_name}", tags=["Учитель"])        
async def put_mass_grades_group(current_user: Annotated[User,Depends(get_current_active_user)], mpg: MassPutGrades):
    if len(mpg.students) == len(mpg.grades):
        with db:
            answer = []
            if current_user.role.name == "Преподаватель":
                
                teacher = Teacher.get(Teacher.user == current_user)
                discipline = teacher.discipline
                current_session = SessionPeriod.get(SessionPeriod.is_active == True)
                for i in range(len(mpg.students)):
                    for_answer = dict()
                    student_name = StudentProfile.get(StudentProfile.full_name == mpg.students[i]) 
                    grade_student = mpg.grades[i]
                    stud_grade, created = Grade.get_or_create(
                        student=student_name,
                        discipline=discipline,
                        session=current_session,
                    )
                    if not created:
                        stud_grade.grade=grade_student
                        stud_grade.teacher=current_user
                        stud_grade.save()



                    for_answer["Студент"] = student_name.full_name
                    for_answer["Оценка"] = grade_student  
                    for_answer["Дисциплина"] = discipline.name
                    for_answer["Сессия"] = current_session.name_session
                    for_answer["Дата"] = datetime.now()
                    answer.append(for_answer)
                    stud_grade.save()
                return answer
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Такой функцией вы не можете обладать"
                )
    else:
        raise HTTPException(
            status_code=400,
            detail="Количество оценок должна быть равно количеству студентов"
        )
            
@app.get("/my_grades", tags=["Студент"])
async def get_grades(current_user: Annotated[User,Depends(get_current_active_user)]):
    with db:
        if current_user.role.name == "Студент":
            student = StudentProfile.get(StudentProfile.full_name == current_user.username)
            grades = Grade.select().where(Grade.student == student)
            answer = []
            for grade in grades:
                info = dict()
                info["Дисциплина"] = grade.discipline.name
                info["Оценка"] = grade.grade
                info["Учитель"] = grade.teacher.username
                info["Дата оценки"] = grade.created_at
                answer.append(info)
            return answer
        else:
            if current_user.role.name:
                raise HTTPException(
                    status_code=403,
                    detail="Оценки просматривать может только студент"
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Вы не авторизированы"
                )


@app.post("/token", response_model=Token, tags=["system"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = User.get(User.username == form_data.username)
        if not user or not user.check_password(form_data.password):
            raise HTTPException(status_code=401, detail="Ошибка! пользователя нет/пароль не совпадает")
        
        token = await create_jwt_token(
            data={"sub": user.username}, 
            expires_minutes=settings.access_token_expire_minutes
        )
        return Token(access_token=token, token_type="bearer")
    except User.DoesNotExist:
        raise HTTPException(status_code=401, detail="Пользователя нет в базе данных")


@app.get("/users/me/", tags=["Пользователи"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    with db:
        try:
            if current_user.role.name == "Студент":
                group = StudentProfile.get(StudentProfile.user == current_user)
                return InfoStudentResponse(name=current_user.username, password="********", role=current_user.role.name,group=group.group.name)
            else:
                return UserInfo(name=current_user.username,password="********", role=current_user.role.name)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении данных пользователя: {exc}") from exc

