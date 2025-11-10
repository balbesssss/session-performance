import peewee, datetime, bcrypt
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "db.db"
db = peewee.SqliteDatabase(str(DATABASE_PATH))


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Role(BaseModel):
    name = peewee.CharField(unique=True)


class User(BaseModel):
    username = peewee.CharField(unique=True)
    password_hash = peewee.CharField()
    role = peewee.ForeignKeyField(Role)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'),
                                           bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'),
                              self.password_hash.encode('utf-8'))


class Disciplines(BaseModel):
    name = peewee.CharField(unique=True)


class Teacher(BaseModel):
    user = peewee.ForeignKeyField(User)
    discipline = peewee.ForeignKeyField(Disciplines)
    
    class Meta:
        indexes = (
            (('user', 'discipline'), True),
        )


class Admin(BaseModel):
    name = peewee.ForeignKeyField(User,unique=True)


class Group(BaseModel):
    name = peewee.CharField(unique=True)


class StudentProfile(BaseModel):
    user = peewee.ForeignKeyField(User, unique=True)
    group = peewee.ForeignKeyField(Group)
    full_name = peewee.CharField()


class SessionPeriod(BaseModel):
    name_session = peewee.CharField()
    start_date = peewee.DateField()
    end_date = peewee.DateField()
    is_active = peewee.BooleanField(default=False)

class Grade(BaseModel):
    student = peewee.ForeignKeyField(StudentProfile)
    discipline = peewee.ForeignKeyField(Disciplines)
    session = peewee.ForeignKeyField(SessionPeriod)
    grade = peewee.IntegerField(null=True)
    teacher = peewee.ForeignKeyField(User)
    created_at = peewee.DateTimeField(default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def create_tables():
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    with db:
        db.create_tables([
            Role, User, Disciplines, Group, 
            StudentProfile, SessionPeriod, Grade,Admin,Teacher
        ])

def create_test():
    Role.create(name="Студент")
    Role.create(name="Преподаватель")
    Role.create(name="Сотрудник учебного отдела")

    student_role = Role.get(Role.name == "Студент")
    teacher_role = Role.get(Role.name == "Преподаватель")

    student1 = User(username="Дарина", role=student_role)
    student1.set_password("123")
    student1.save()
    
    student2 = User(username="Максим", role=student_role)
    student2.set_password("123")
    student2.save()
    
    student3 = User(username="Владислав", role=student_role)
    student3.set_password("123")
    student3.save()
    
    student4 = User(username="Кирилл", role=student_role)
    student4.set_password("123")
    student4.save()

    student5 = User(username="Абдул", role=student_role)
    student5.set_password("123")
    student5.save()

    student6 = User(username="Денис", role=student_role)
    student6.set_password("123")
    student6.save()

    student7 = User(username="Сергей", role=student_role)
    student7.set_password("123")
    student7.save()

    student8 = User(username="Артем", role=student_role)
    student8.set_password("123")
    student8.save()

    student9 = User(username="Глеб", role=student_role)
    student9.set_password("123")
    student9.save()

    group1 = Group(name="1-1Р9")
    group1.save()
    group2 = Group(name="1-2Р9")
    group2.save()

    math = Disciplines(name="Математика")
    math.save()
    russian = Disciplines(name="Русский язык")  
    russian.save()

    teacher_user1 = User(username="Смирнов Павел Леонидович", role=teacher_role)
    teacher_user1.set_password("123")
    teacher_user1.save()
    
    teacher_user2 = User(username="Вавилов Леонид Миронович", role=teacher_role)
    teacher_user2.set_password("123")
    teacher_user2.save()

    role_admin = Role.get(name="Сотрудник учебного отдела")

    admin_user = User(username="админ",role=role_admin)
    admin_user.set_password("123")
    admin_user.save()

    Admin.create(name=admin_user)

    session = SessionPeriod(
        name_session="Осенняя сессия 2024",
        start_date=datetime.date(2024, 9, 1),
        end_date=datetime.date(2024, 12, 31),
        is_active=True
    )
    session.save()
   
    profile1 = StudentProfile.create(user=student1, group=group1, full_name="Дарина")
    profile2 = StudentProfile.create(user=student2, group=group1, full_name="Максим") 
    profile3 = StudentProfile.create(user=student3, group=group1, full_name="Владислав")
    profile4 = StudentProfile.create(user=student4, group=group1, full_name="Кирилл")
    profile5 = StudentProfile.create(user=student5, group=group1, full_name="Абдул")
    profile6 = StudentProfile.create(user=student6, group=group2, full_name="Денис")
    profile7 = StudentProfile.create(user=student7, group=group2, full_name="Сергей")
    profile8 = StudentProfile.create(user=student8, group=group2, full_name="Артем")
    profile9 = StudentProfile.create(user=student9, group=group2, full_name="Глеб")
    
    Teacher.create(user=teacher_user1, discipline=math)
    Teacher.create(user=teacher_user2, discipline=russian)

    Grade.create(
        student=profile1,
        discipline=math,
        session=session,
        grade=5,
        teacher=teacher_user1 
    )
    
    Grade.create(
        student=profile1,
        discipline=russian,
        session=session,
        grade=4,
        teacher=teacher_user2  
    )

    Grade.create(
        student=profile2,
        discipline=math,
        session=session,
        grade=2,
        teacher=teacher_user1 
    )

    Grade.create(
        student=profile2,
        discipline=russian,
        session=session,
        grade=4,
        teacher=teacher_user2  
    )

    Grade.create(
        student=profile3,
        discipline=math,
        session=session,
        grade=5,
        teacher=teacher_user1  
    )

    Grade.create(
        student=profile4,
        discipline=russian,
        session=session,
        grade=5,
        teacher=teacher_user2  
    )

    Grade.create(
        student=profile4,
        discipline=math,
        session=session,
        grade=5,
        teacher=teacher_user1  
    )

    Grade.create(
        student=profile5,
        discipline=math,
        session=session,
        grade=4,
        teacher=teacher_user1  
    )

    Grade.create(
        student=profile5,
        discipline=russian,
        session=session,
        grade=4,
        teacher=teacher_user2  
    )

    Grade.create(
        student=profile6,
        discipline=math,
        session=session,
        grade=4,
        teacher=teacher_user1  
    )

    Grade.create(
        student=profile6,
        discipline=russian,
        session=session,
        grade=5,
        teacher=teacher_user2  
    )

    Grade.create(
        student=profile7,
        discipline=math,
        session=session,
        grade=5,
        teacher=teacher_user1  
    )

    Grade.create(
        student=profile7,
        discipline=russian,
        session=session,
        grade=2,
        teacher=teacher_user2  
    )

    Grade.create(
        student=profile8,
        discipline=math,
        session=session,
        grade=2,
        teacher=teacher_user1  
    )

    Grade.create(
        student=profile8,
        discipline=russian,
        session=session,
        grade=4,
        teacher=teacher_user2  
    )

    Grade.create(
        student=profile9,
        discipline=math,
        session=session,
        grade=5,
        teacher=teacher_user1  
    )

    Grade.create(
        student=profile9,
        discipline=russian,
        session=session,
        grade=2,
        teacher=teacher_user2  
    )
    

if __name__ == '__main__':
    db.connect()
    create_tables()
    create_test()