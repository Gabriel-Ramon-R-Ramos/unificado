from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from unificado.routers import (
    auth,
    course,
    discipline,
    students,
    system,
    teachers,
    users,
)

app = FastAPI(
    openapi_prefix='/api/v1',
    title='Rede de Conhecimento',
    description='API para gerenciamento de cursos, disciplinas e usuários',
    version='1.0.0',
    # Configuração de segurança para Swagger UI
    swagger_ui_parameters={
        'persistAuthorization': True,  # Mantém o token após refresh
    },
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',  # React padrão
        'http://localhost:5173',  # Vite padrão
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(system.router)
app.include_router(users.router)
app.include_router(course.router)
app.include_router(discipline.router)
app.include_router(students.router)
app.include_router(teachers.router)


@app.get('/')
def read_root():
    return {'message': 'Rede de Conhecimento API funcionando!'}
