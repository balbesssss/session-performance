from fastapi import FastAPI
from models import *
from routers import students, teachers, admins, admin_teacher, system, users


app = FastAPI()

app.include_router(students.router)
app.include_router(teachers.router) 
app.include_router(admins.router)
app.include_router(admin_teacher.router)
app.include_router(users.router)
app.include_router(system.router) 