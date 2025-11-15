import peewee
from datetime import datetime
from typing import Annotated, Dict, List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from models import *
from database.db import User, Role, db, Disciplines, Group, Grade, Student, SessionPeriod, Teacher, Admin
from dependencies.auth_utils import create_jwt_token
from config import settings
from dependencies.current_user import get_current_user

app = FastAPI()


@app.post("/register/", tags=["system"])
async def create_user(user: UserRegister):
    with db:
        student_role = Role.get(Role.name == 'Студент')
        try:
            get_user = User.get(
                (User.last_name == user.last_name) &
                (User.first_name == user.first_name) &
                (User.middle_name == user.middle_name) &
                (User.role == student_role)
            )
            raise HTTPException(status_code=400,detail="Пользователь уже есть в базе данных")
        except User.DoesNotExist:
            new_user = User(
                last_name=user.last_name,
                first_name=user.first_name,
                middle_name=user.middle_name,
                role=student_role
            )
            new_user.set_password(user.password)
            new_user.save()
            return {"message": "Пользователь успешно создан"}
                

@app.post("/add_teacher/", response_model=Dict[str, str], tags=["Админ"])
async def add_teacher(teacher: TeacherInfo, discipline_name: str, current_user: Annotated[User, Depends(get_current_user)]) -> Dict[str, str]:
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


@app.post("/create-group/", tags=["Админ"])
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


@app.post("/create-student/", tags=["Админ"])
async def create_student(current_user: Annotated[User, Depends(get_current_user)], student_profile: StudentprofileCreate):
    with db:
        if current_user.role.name != "Сотрудник учебного отдела":
            raise HTTPException(
                status_code=403,
                detail="У вас недостаточно прав"
            )
        
        try:
            student = User.get(
                (User.last_name == student_profile.last_name) &
                (User.first_name == student_profile.first_name) & 
                (User.middle_name == student_profile.middle_name)
            )
        except User.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail=f"Студент не найден"
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
        try:
            student_get = Student.get(user=student,group=group)
            raise HTTPException(
                status_code=404,
                detail=f"Студент с такими данными уже есть"
            )
        except Student.DoesNotExist:
            Student.create(user=student,group=group)
            return {"message":"Профиль студента успешно создан"}

        
@app.post("/fill_discipline/", tags=["Админ"])
async def fill_name_discipline(name_disciplines: List[str], current_user: Annotated[User, Depends(get_current_user)]):
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


@app.patch("/put_grade",tags=["Админ/учитель"])
async def put_grade(current_user: Annotated[User,Depends(get_current_user)],grade_put: GradePutRequest):
    with db:
        if current_user.role.name == "Преподаватель":
            user = User.get(
                (User.last_name == grade_put.last_name)&
                (User.first_name == grade_put.first_name)&
                (User.middle_name == grade_put.middle_name)
                )
            try:
                group = Group.get(Group.name == grade_put.grade)
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
            except SessionPeriod.DowsNotExist:
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
                group = Group.get(Group.name == grade_put.grade)
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
            except SessionPeriod.DowsNotExist:
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
               'teacher': admin.name
           })
                
            if not created:
                grade.grade = grade_put.grade
                grade.teacher = admin.name
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


@app.get("/administrator/all_grades/", tags={"Админ"})
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


@app.get("/administrator/grades/{group_name}", tags=["Админ"],)
async def grade_group(current_user: Annotated[User,Depends(get_current_user)], group_name: str):
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


@app.delete("/administrator/delete/{discipline}",tags=["Админ"])
async def delete_discipline(current_user: Annotated[User,Depends(get_current_user)], discipline: str):
    with db:
        if current_user.role.name == "Сотрудник учебного отдела":
            try: 
                discipline_for_delete = Disciplines.get(Disciplines.name == discipline)
            except Disciplines.DoesNotExist:
                raise HTTPException(status_code=400,detail="Не удалось получить дисциплину из таблицы")
            discipline_for_delete.delete_instance()
            return {"message":f"{discipline} была успешно удалена"}


@app.get("/teacher/grades/{group_name}",tags=["Учитель"])
async def grade_group(current_user: Annotated[User,Depends(get_current_user)],group_name: str):
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


@app.patch("/teacher/mass-grades/{group_name}", tags=["Учитель"])        
async def put_mass_grades_group(current_user: Annotated[User,Depends(get_current_user)], mpg: MassPutGrades):
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


@app.get("/my_grades", tags=["Студент"])
async def get_grades(current_user: Annotated[User,Depends(get_current_user)]):
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


@app.post("/token", response_model=Token, tags=["system"])
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


@app.get("/users/me/", tags=["Пользователи"])
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    with db:
        if current_user.role.name == "Студент":
            try:
                group = Student.get(Student.user == current_user)
                return InfoStudentResponse(name=current_user.full_name, password="********", role=current_user.role.name,group=group.group.name)
            except Student.DoesNotExist:
                raise HTTPException(
                    status_code=404,
                    detail="Профиль студента не найден"
                )
        else:
            return UserInfo(name=current_user.full_name,password="********", role=current_user.role.name)
