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
    last_name = peewee.CharField()
    first_name = peewee.CharField()
    middle_name = peewee.CharField()
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
    user = peewee.ForeignKeyField(User,unique=True)


class Group(BaseModel):
    name = peewee.CharField(unique=True)


class Student(BaseModel):
    user = peewee.ForeignKeyField(User, unique=True)
    group = peewee.ForeignKeyField(Group)
    

class SessionPeriod(BaseModel):
    name_session = peewee.CharField()
    start_date = peewee.DateField()
    end_date = peewee.DateField()
    is_active = peewee.BooleanField(default=False)


class Grade(BaseModel):
    student = peewee.ForeignKeyField(Student)
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
            Student, SessionPeriod, Grade,Admin,Teacher
        ])


def create_test():
    Role.create(name="Студент")
    Role.create(name="Преподаватель")
    Role.create(name="Сотрудник учебного отдела")

    student_role = Role.get(Role.name == "Студент")
    teacher_role = Role.get(Role.name == "Преподаватель")

    student1 = User(last_name="Ухова",first_name="Дарина",middle_name="Олеговна",role=student_role)
    student1.set_password("123")
    student1.save()
    
    student2 = User(last_name="Смирнов",first_name="Максим",middle_name="Константинович",role=student_role)
    student2.set_password("123")
    student2.save()
    
    student3 = User(last_name="Варешков",first_name="Владислав",middle_name="Михайлович",role=student_role)
    student3.set_password("123")
    student3.save()
    
    student4 = User(last_name="Маяков",first_name="Кирилл",middle_name="Миронович",role=student_role)
    student4.set_password("123")
    student4.save()

    student5 = User(last_name="Дата",first_name="Абдул",middle_name="Аманович",role=student_role)
    student5.set_password("123")
    student5.save()

    student6 = User(last_name="Греков",first_name="Денис",middle_name="Владимирович",role=student_role)
    student6.set_password("123")
    student6.save()

    student7 = User(last_name="Махолов",first_name="Сергей",middle_name="Генадьевич",role=student_role)
    student7.set_password("123")
    student7.save()

    student8 = User(last_name="Губнов",first_name="Артем",middle_name="Александрович",role=student_role)
    student8.set_password("123")
    student8.save()

    student9 = User(last_name="Комаров",first_name="Глеб",middle_name="Андреевич",role=student_role)
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

    teacher_user1 = User(last_name="Смирнов", first_name="Павел",middle_name="Леонидович", role=teacher_role)
    teacher_user1.set_password("123")
    teacher_user1.save()
    
    teacher_user2 = User(last_name="Вавилов", first_name="Леонид",middle_name="Миронович", role=teacher_role)
    teacher_user2.set_password("123")
    teacher_user2.save()

    role_admin = Role.get(name="Сотрудник учебного отдела")

    admin_user = User(last_name="админ",first_name="админ",middle_name="админ",role=role_admin)
    admin_user.set_password("123")
    admin_user.save()

    Admin.create(user=admin_user)

    session = SessionPeriod(
        name_session="Осенняя сессия 2024",
        start_date=datetime.date(2024, 9, 1),
        end_date=datetime.date(2024, 12, 31),
        is_active=True
    )
    session.save()
   
    profile1 = Student.create(user=student1, group=group1)
    profile2 = Student.create(user=student2, group=group1) 
    profile3 = Student.create(user=student3, group=group1)
    profile4 = Student.create(user=student4, group=group1)
    profile5 = Student.create(user=student5, group=group1)
    profile6 = Student.create(user=student6, group=group2)
    profile7 = Student.create(user=student7, group=group2)
    profile8 = Student.create(user=student8, group=group2)
    profile9 = Student.create(user=student9, group=group2)
    
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