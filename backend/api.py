import peewee
from datetime import datetime
from typing import Annotated, Dict, List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from models import *
from database.db import User, Role, db, Disciplines, Group, Grade, StudentProfile, SessionPeriod, Teacher, Admin
from dependencies.auth_utils import create_jwt_token
from config import settings
from dependencies.current_user import get_current_user

app = FastAPI()


@app.post("/register/",tags=["system"])
async def create_user(user: UserRegister):
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
async def add_teacher(teacher: TeacherInfo, current_user: Annotated[User, Depends(get_current_user)]) -> Dict[str, str]:
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


@app.post("/create-group/", tags=["Админ"])
async def create_group(current_user: Annotated[User, Depends(get_current_user)],group_name: str):
    try:
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
            
            Group.create(name=group_name)
            return {"message":f"Группа {group_name} была успешна создана"}
    except peewee.IntegrityError as exc:
        raise HTTPException(
            status_code=400,
            detail="Группа с таким названием уже существует"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при создании группы"
        ) from exc


@app.post("/create-studentprofile/", tags=["Админ"])
async def create_studentprofile(current_user: Annotated[User, Depends(get_current_user)], student_profile: StudentprofileCreate):
    try:
        with db:
            if current_user.role.name != "Сотрудник учебного отдела":
                raise HTTPException(
                    status_code=403,
                    detail="У вас недостаточно прав"
                )
            
            try:
                student = User.get(User.username == student_profile.username)
            except User.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail=f"Студент с именем {student_profile.username} не найден"
                )
            
            try:
                group = Group.get(Group.name == student_profile.group)
            except Group.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail=f"Группа {student_profile.group} не найдена"
                )
            
            if student.role.name != "Студент":
                raise HTTPException(
                    status_code=400,
                    detail="Пользователь не является студентом"
                )
            
            StudentProfile.create(user=student,group=group, full_name=student_profile.full_name)
            return {"message":"Профиль студента успешно создан"}
    except peewee.IntegrityError as exc:
        raise HTTPException(status_code=400,
            detail="Профиль для этого студента уже существует"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при создании профиля студента"
        ) from exc

        
@app.post("/fill_discipline/", tags=["Админ"])
async def fill_name_discipline(name_disciplines: List[str], current_user: Annotated[User, Depends(get_current_user)]):
    try:
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
            
            created_count = 0
            for discipline in name_disciplines:
                dis = Disciplines(name=discipline.strip())
                dis.save()
                created_count += 1
            return {
                "message": f"Успешно создано {created_count} дисциплин",
                "created_count": created_count
            }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при добавлении дисциплин"
        ) from exc


@app.patch("/put_grade",tags=["Админ/учитель"])
async def put_grade(current_user: Annotated[User,Depends(get_current_user)],grade_put: GradePutRequest):
    try:
        with db:
            if current_user.role.name == "Преподаватель":
                try:
                    student = StudentProfile.get(StudentProfile.full_name == grade_put.student_full_name)
                    discipline = Disciplines.get(Disciplines.name == grade_put.discipline)
                    session = SessionPeriod.get(SessionPeriod.name_session == grade_put.session)
                    teacher = Teacher.get(
                    (Teacher.user == current_user) &  
                    (Teacher.discipline == discipline))
                except (StudentProfile.DoesNotExist, Disciplines.DoesNotExist, SessionPeriod.DoesNotExist, Teacher.DoesNotExist):
                    raise HTTPException(
                        status_code=404,
                        detail="Студент, дисциплина, сессия или преподаватель не найдены"
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
                    grade.save()
                return {
                    "message": "Оценка создана" if created else "Оценка обновлена",
                    "student": student.full_name,
                    "discipline": discipline.name, 
                    "grade": grade_put.grade
                    }
            
            elif current_user.role.name == "Сотрудник учебного отдела":
                try:
                    student = StudentProfile.get(StudentProfile.full_name == grade_put.student_full_name)
                    discipline = Disciplines.get(Disciplines.name == grade_put.discipline)
                    session = SessionPeriod.get(SessionPeriod.name_session == grade_put.session)
                    admin = Admin.get(Admin.name == current_user)
                except (StudentProfile.DoesNotExist, Disciplines.DoesNotExist, SessionPeriod.DoesNotExist, Admin.DoesNotExist):
                    raise HTTPException(
                        status_code=404,
                        detail="Студент, дисциплина, сессия или администратор не найдены"
                    )
                    
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
                detail="У вас нет прав"  
                    )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при сохранении оценки"
        ) from exc


@app.get("/administrator/all_grades/", tags={"Админ"})
async def grades_all_group(current_user: Annotated[User, Depends(get_current_user)]):
    with db:
        if current_user.role.name == "Сотрудник учебного отдела":
            answer = []
            groups = Group.select()
            for group in groups:
                students = StudentProfile.select().join(Group).where(Group.name == group.name)
                student_grades = dict()
                student_grades["Группа"] = group.name
                student_grades["Информация"] = []
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
                    student_grades["Информация"].append(indo_student)
                answer.append(student_grades)
            return answer


@app.get("/administrator/grades/{group_name}", tags=["Админ"],)
async def grade_group(current_user: Annotated[User,Depends(get_current_user)], group_name: str):
    try:
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
            
            students = StudentProfile.select().join(Group).where(Group.name == group_name)
            
            if not students:
                return {"message": "В группе нет студентов"}
            
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
                    grade_student["Преподаватель"] = grade.teacher.username
                    grade_student["Дата"] = grade.created_at
                    indo_student["Оценки"].append(grade_student)
                answer.append(indo_student)
            return answer
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при получении оценок группы"
        ) from exc


@app.delete("/administrator/delete/{discipline}",tags=["Админ"])
async def delete_discipline(current_user: Annotated[User,Depends(get_current_user)], discipline: str):
    try:
        with db:
            if current_user.role.name == "Сотрудник учебного отдела":
                try: 
                    discipline_for_delete = Disciplines.get(Disciplines.name == discipline)
                except Disciplines.DoesNotExist:
                    raise HTTPException(status_code=400,detail="Не удалось получить дисциплину из таблицы")
                discipline_for_delete.delete_instance()
                return {"message":f"{discipline} была успешно удалена"}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при получении оценок группы"
        ) from exc


@app.get("/teacher/grades/{group_name}",tags=["Учитель"])
async def grade_group(current_user: Annotated[User,Depends(get_current_user)],group_name: str):
    with db:
        if current_user.role.name == "Преподаватель":
            disciplines_teacher = []
            disciplines = Teacher.select().join(User).where(User.username == current_user.username)
            for i in disciplines:
                disciplines_teacher.append(i.discipline.name)
            if not disciplines_teacher:
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
            for discipline_name in disciplines_teacher:
                discipline = Disciplines.get(Disciplines.name == discipline_name)
                all_student_grades = Grade.select().join(Disciplines).switch(Grade).join(StudentProfile, on=Grade.student).join(Group).where((Disciplines.name == discipline_name) & (Group.name == group_name))
                    
                for i in all_student_grades:
                    ans = dict()
                    ans["Студент"] = i.student.full_name
                    ans["Оценка"] = i.grade
                    ans["Дата"] = i.created_at
                    answer.append(ans)
            
            if not answer:
                return {"message": "Нет оценок по вашим дисциплинам в этой группе"}
            
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


@app.patch("/teacher/mass-grades/{group_name}", tags=["Учитель"])        
async def put_mass_grades_group(current_user: Annotated[User,Depends(get_current_user)], mpg: MassPutGrades):
    try:
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
                try:
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

                    for_answer = dict()
                    for_answer["Студент"] = student_name.full_name
                    for_answer["Оценка"] = grade_student  
                    for_answer["Дисциплина"] = discipline.name
                    for_answer["Сессия"] = current_session.name_session
                    for_answer["Дата"] = datetime.now()
                    answer.append(for_answer)
                    stud_grade.save()
                    
                except StudentProfile.DoesNotExist:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Студент {mpg.students[i]} не найден"
                    )
            
            return answer
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при массовом выставлении оценок"
        ) from exc


@app.get("/my_grades", tags=["Студент"])
async def get_grades(current_user: Annotated[User,Depends(get_current_user)]):
    with db:
        if current_user.role.name != "Студент":
            raise HTTPException(
                status_code=403,
                detail="Просматривать оценки могут только студенты"
            )
            
        try:
            student = StudentProfile.get(StudentProfile.user == current_user)
        except StudentProfile.DoesNotExist:
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
            info["Учитель"] = grade.teacher.username
            info["Дата оценки"] = grade.created_at
            answer.append(info)
        return answer


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
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    with db:
        if current_user.role.name == "Студент":
            try:
                group = StudentProfile.get(StudentProfile.user == current_user)
                return InfoStudentResponse(name=current_user.username, password="********", role=current_user.role.name,group=group.group.name)
            except StudentProfile.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Профиль студента не найден"
                )
        else:
            return UserInfo(name=current_user.username,password="********", role=current_user.role.name)
