# 🗄️ Esquema do Banco de Dados - Unificado

Este documento detalha a estrutura do banco de dados, relacionamentos entre tabelas e responsabilidades de cada entidade no sistema **Unificado**.

## 📊 Visão Geral do Schema

O banco de dados está organizado em dois domínios principais:

1. **Domínio Acadêmico**: Cursos, disciplinas e pré-requisitos
2. **Domínio de Usuários**: Autenticação flexível, perfis de estudantes e professores com soft delete

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     COURSES     │    │      USERS      │    │   DISCIPLINES   │
│                 │    │                 │    │                 │
│ • id            │    │ • id            │    │ • id            │
│ • name          │    │ • username      │    │ • name          │
│                 │    │ • email         │    │ • course_id (FK)│
└─────────┬───────┘    │ • password_hash │    └─────────┬───────┘
          │            │ • role          │              │
          │            │ • is_active     │              │
          │            └─────────┬───────┘              │
          │                      │                      │
          │              ┌───────┴───────┐              │
          │              │               │              │
          └──────────────┼───────────────┼──────────────┘
                         │               │
          ┌─────────────────┐    ┌─────────────────┐
          │ STUDENT_PROFILES│    │ TEACHER_PROFILES│
          │                 │    │                 │
          │ • id            │    │ • id            │
          │ • user_id (FK)  │    │ • user_id (FK)  │
          │ • enrollment_#  │    │ • employee_#    │
          └─────────────────┘    └─────────────────┘

                    ┌─────────────────────────┐
                    │ DISCIPLINE_PREREQUISITES│
                    │                         │
                    │ • discipline_id (FK)    │
                    │ • prerequisite_id (FK)  │
                    └─────────────────────────┘
```

## 📋 Tabelas e Responsabilidades

### 🎓 **COURSES** (Cursos)
**Responsabilidade**: Armazenar informações dos cursos oferecidos pela instituição.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária, identificador único |
| `name` | VARCHAR(255) | Nome do curso (único) |

**Relacionamentos**:
- **1:N** com `disciplines` - Um curso pode ter muitas disciplinas

**Exemplos**:
- Ciência da Computação
- Engenharia de Software
- Sistemas de Informação

### 📚 **DISCIPLINES** (Disciplinas)
**Responsabilidade**: Gerenciar as disciplinas de cada curso e seus relacionamentos de dependência.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária |
| `name` | VARCHAR(255) | Nome da disciplina |
| `course_id` | INTEGER | FK para `courses.id` |

**Relacionamentos**:
- **N:1** com `courses` - Cada disciplina pertence a um curso
- **M:N** com `disciplines` (via `discipline_prerequisites`) - Disciplinas podem ter outras como pré-requisitos

**Índices**:
- `ix_disciplines_name` - Busca por nome
- `ix_disciplines_course_id` - Filtragem por curso

### 🔗 **DISCIPLINE_PREREQUISITES** (Pré-requisitos)
**Responsabilidade**: Tabela de associação para relacionamentos muitos-para-muitos entre disciplinas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `discipline_id` | INTEGER | FK para `disciplines.id` (disciplina que tem pré-requisito) |
| `prerequisite_id` | INTEGER | FK para `disciplines.id` (disciplina que é pré-requisito) |

**Chave Primária Composta**: (`discipline_id`, `prerequisite_id`)

**Validações**:
- Previne dependências circulares
- Disciplinas devem pertencer ao mesmo curso
- Auto-relacionamento não permitido

### 👥 **USERS** (Usuários)
**Responsabilidade**: Sistema de autenticação e autorização central com suporte a login flexível e soft delete.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária |
| `username` | VARCHAR(100) | Nome de usuário único |
| `email` | VARCHAR(255) | Email (único, opcional) |
| `password_hash` | VARCHAR | Hash da senha |
| `role` | VARCHAR(20) | Tipo de usuário (`student`, `teacher`, `admin`) |
| `is_active` | BOOLEAN | Status ativo/inativo (soft delete) |

**Funcionalidades de Autenticação**:
- **Login Flexível**: Aceita `username`, `email`, `enrollment_number` ou `employee_number`
- **JWT Tokens**: Inclui `user_id`, `username`, `role`, `email`, `is_active`
- **Soft Delete**: Usuários inativos são preservados mas filtrados das operações
- **Autorização Hierárquica**: Admin > Teacher > Student

**Relacionamentos**:
- **1:1** com `student_profiles` (opcional)
- **1:1** com `teacher_profiles` (opcional)

**Índices**:
- `ix_users_username` - Login
- `uq_users_email` - Unicidade de email

### 🎒 **STUDENT_PROFILES** (Perfis de Estudantes)
**Responsabilidade**: Dados específicos de estudantes com integração ao sistema de autenticação flexível.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária |
| `user_id` | INTEGER | FK para `users.id` (única) |
| `enrollment_number` | VARCHAR(50) | Matrícula do estudante (usado para login) |

**Funcionalidades**:
- **Login por Matrícula**: `enrollment_number` pode ser usado para autenticação
- **Soft Delete Integration**: Apenas estudantes ativos aparecem nas consultas
- **Associação com Disciplinas**: Relacionamento many-to-many para inscrições

**Relacionamentos**:
- **1:1** com `users` - Cada perfil pertence a um usuário
- **CASCADE DELETE** - Removido quando usuário é deletado
- **M:N** com `disciplines` - Estudante pode se inscrever em várias disciplinas

### 👨‍🏫 **TEACHER_PROFILES** (Perfis de Professores)
**Responsabilidade**: Dados específicos de professores com integração ao sistema de autenticação flexível.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária |
| `user_id` | INTEGER | FK para `users.id` (única) |
| `employee_number` | VARCHAR(50) | Número de funcionário (usado para login) |

**Funcionalidades**:
- **Login por Funcionário**: `employee_number` pode ser usado para autenticação
- **Soft Delete Integration**: Apenas professores ativos aparecem nas consultas
- **Associação com Disciplinas**: Relacionamento many-to-many para disciplinas lecionadas

**Relacionamentos**:
- **1:1** com `users` - Cada perfil pertence a um usuário
- **CASCADE DELETE** - Removido quando usuário é deletado
- **M:N** com `disciplines` - Professor pode lecionar várias disciplinas

## 🔄 Relacionamentos Detalhados

### 1. **Course ↔ Disciplines** (1:N)
```sql
-- Um curso tem muitas disciplinas
SELECT c.name AS curso, d.name AS disciplina
FROM courses c
JOIN disciplines d ON c.id = d.course_id
WHERE c.id = 1;
```

### 2. **Discipline ↔ Prerequisites** (M:N)
```sql
-- Buscar pré-requisitos de uma disciplina
SELECT d.name AS disciplina, p.name AS prerequisito
FROM disciplines d
JOIN discipline_prerequisites dp ON d.id = dp.discipline_id
JOIN disciplines p ON dp.prerequisite_id = p.id
WHERE d.id = 5;
```

### 3. **User ↔ Student Profile** (1:1) com Soft Delete
```sql
-- Dados completos do estudante (apenas ativos)
SELECT u.username, u.email, sp.enrollment_number, u.is_active
FROM users u
JOIN student_profiles sp ON u.id = sp.user_id
WHERE u.role = 'student' AND u.is_active = true;
```

### 4. **User ↔ Teacher Profile** (1:1) com Soft Delete
```sql
-- Dados completos do professor (apenas ativos)
SELECT u.username, u.email, tp.employee_number, u.is_active
FROM users u
JOIN teacher_profiles tp ON u.id = tp.user_id
WHERE u.role = 'teacher' AND u.is_active = true;
```

### 5. **Autenticação Flexível**
```sql
-- Login por qualquer identificador (username, email, RA, funcionário)
SELECT u.*, sp.enrollment_number, tp.employee_number
FROM users u
LEFT JOIN student_profiles sp ON u.id = sp.user_id
LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
WHERE (u.username = ? OR u.email = ? OR sp.enrollment_number = ? OR tp.employee_number = ?)
  AND u.is_active = true;
```

## 🛡️ Integridade e Constraints

### Chaves Estrangeiras
- `disciplines.course_id` → `courses.id`
- `discipline_prerequisites.discipline_id` → `disciplines.id`
- `discipline_prerequisites.prerequisite_id` → `disciplines.id`
- `student_profiles.user_id` → `users.id` **ON DELETE CASCADE**
- `teacher_profiles.user_id` → `users.id` **ON DELETE CASCADE**

### Constraints Únicos
- `courses.name` - Nome do curso único
- `users.username` - Username único
- `users.email` - Email único (se informado)
- `student_profiles.user_id` - Um usuário = um perfil estudante
- `teacher_profiles.user_id` - Um usuário = um perfil professor

### Validações de Negócio (Aplicação)
- **Dependências Circulares**: Validação para evitar ciclos em pré-requisitos
- **Mesmo Curso**: Pré-requisitos devem ser do mesmo curso
- **Roles Consistentes**: Usuários com `role=student` só podem ter `student_profile`
- **Soft Delete**: Usuários inativos são filtrados mas preservados no banco
- **Autoproteção Admin**: Administradores não podem desativar a si mesmos
- **Login Flexível**: Sistema aceita múltiplos tipos de identificadores

## 🎯 Cenários de Uso

### Caso 1: Cadastro de Novo Estudante com Autenticação Flexível
```python
# 1. Criar usuário (ativo por padrão)
user = User(
    username="joao123", 
    email="joao@email.com", 
    role="student",
    is_active=True
)

# 2. Criar perfil de estudante
profile = StudentProfile(
    user_id=user.id, 
    enrollment_number="2024001"
)
# Agora pode fazer login com: joao123, joao@email.com ou 2024001
```

### Caso 2: Login Flexível
```python
# Sistema aceita qualquer um destes identificadores:
login_attempts = [
    "joao123",           # username
    "joao@email.com",    # email
    "2024001",           # enrollment_number (se for estudante)
    "EMP001"             # employee_number (se for professor)
]

# Todos retornam o mesmo usuário se válidos e ativos
```

### Caso 3: Soft Delete de Usuário
```python
# Admin desativa usuário (soft delete)
user = session.get(User, user_id)
user.is_active = False
session.commit()

# Usuário não aparece mais em consultas normais
# Mas dados são preservados para auditoria
```

### Caso 4: Definir Pré-requisitos
```python
# Disciplina "Estruturas de Dados" tem pré-requisito "Algoritmos"
algoritmos = session.get(Discipline, 1)
estruturas = session.get(Discipline, 2)

estruturas.prerequisites.append(algoritmos)
```

### Caso 5: Validar Matrícula com Usuários Ativos
```python
# Verificar se estudante ATIVO pode se matricular em disciplina
def pode_matricular(student_id, discipline_id):
    # Verificar se estudante está ativo
    student = session.query(StudentProfile).join(User)\
        .filter(StudentProfile.id == student_id, User.is_active.is_(True))\
        .first()
    
    if not student:
        return False
    
    # Verificar se completou todos os pré-requisitos
    discipline = session.get(Discipline, discipline_id)
    completed = get_completed_disciplines(student_id)
    
    for prereq in discipline.prerequisites:
        if prereq.id not in completed:
            return False
    return True
```

## 🔄 Fluxo de Migrations

### Migration 1: `0001_create_users_and_profiles_and_admin` - Sistema de Usuários Base
- Cria `users` com campos base
- Cria `student_profiles`
- Cria `teacher_profiles`
- Insere usuário `admin` padrão

### Migration 2: `339dbadfaddc_create_discipline_and_courses_tables` - Schema Acadêmico
- Cria `courses`
- Cria `disciplines`
- Cria `discipline_prerequisites`

### Migration 3: `3aa3a204d952_relacionando_disciplinas_professores_` - Relacionamentos Avançados
- Adiciona relacionamentos many-to-many entre professores e disciplinas
- Adiciona relacionamentos many-to-many entre estudantes e disciplinas
- Implementa constraints de integridade referencial

### Funcionalidades Implementadas via Aplicação:
- **Autenticação Flexível**: Login por username, email, RA ou número de funcionário
- **JWT com Dados Completos**: Tokens incluem role, is_active e dados do usuário
- **Soft Delete**: Filtragem automática de usuários inativos
- **Autorização Hierárquica**: Admin → Teacher → Student
- **Endpoints Administrativos**: Ativação/desativação de usuários

## 📈 Considerações de Performance

### Índices Importantes
- `disciplines.course_id` - Filtragem por curso
- `disciplines.name` - Busca textual
- `users.username` - Login frequente
- `users.email` - Autenticação alternativa
- `users.is_active` - Filtro soft delete (recomendado)
- `student_profiles.enrollment_number` - Login por matrícula
- `teacher_profiles.employee_number` - Login por funcionário

### Queries Otimizadas
```sql
-- Buscar disciplinas com pré-requisitos (evita N+1)
SELECT d.*, array_agg(p.name) as prerequisites
FROM disciplines d
LEFT JOIN discipline_prerequisites dp ON d.id = dp.discipline_id
LEFT JOIN disciplines p ON dp.prerequisite_id = p.id
GROUP BY d.id;

-- Autenticação flexível otimizada
SELECT u.id, u.username, u.email, u.role, u.is_active,
       sp.enrollment_number, tp.employee_number
FROM users u
LEFT JOIN student_profiles sp ON u.id = sp.user_id
LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
WHERE u.is_active = true
  AND (u.username = ? OR u.email = ? OR sp.enrollment_number = ? OR tp.employee_number = ?)
LIMIT 1;

-- Listagem de usuários ativos com paginação
SELECT u.*, sp.enrollment_number, tp.employee_number
FROM users u
LEFT JOIN student_profiles sp ON u.id = sp.user_id AND u.role = 'student'
LEFT JOIN teacher_profiles tp ON u.id = tp.user_id AND u.role = 'teacher'
WHERE u.is_active = true
ORDER BY u.username
LIMIT ? OFFSET ?;
```

## 🎛️ Configuração SQLAlchemy

Os relacionamentos são configurados com:
- **`back_populates`**: Navegação bidirecional
- **`cascade="all, delete-orphan"`**: Para perfis de usuário
- **`lazy="select"`**: Carregamento sob demanda
- **`uselist=False`**: Para relacionamentos 1:1

## 🔐 Sistema de Autenticação e Autorização

### Funcionalidades Implementadas

#### 1. **Autenticação Flexível**
- **Múltiplos Identificadores**: Username, email, RA (estudantes), número de funcionário (professores)
- **JWT Tokens**: Incluem dados completos do usuário (`user_id`, `username`, `role`, `email`, `is_active`)
- **Validação de Status**: Apenas usuários ativos podem fazer login

#### 2. **Autorização Hierárquica**
```python
# Hierarquia de permissões:
admin     # Acesso total (CRUD usuários, visualizar inativos)
teacher   # Acesso limitado (apenas próprios dados e estudantes)
student   # Acesso restrito (apenas próprios dados)
```

#### 3. **Soft Delete**
- **Preservação de Dados**: Usuários são marcados como `is_active=False`
- **Filtragem Automática**: Endpoints filtram usuários inativos por padrão
- **Controle Administrativo**: Apenas admins podem ativar/desativar usuários
- **Autoproteção**: Admins não podem desativar a si mesmos

#### 4. **Endpoints de Segurança**
```http
POST /api/v1/auth/login          # Login flexível
GET  /api/v1/me                  # Dados do usuário atual
GET  /api/v1/users               # Listar usuários (admin)
PATCH /api/v1/users/{id}/toggle-active  # Ativar/desativar (admin)
```

#### 5. **Swagger UI Integration**
- **Bearer Token**: Autenticação via JWT no Swagger
- **Documentação Automática**: Endpoints protegidos marcados adequadamente
- **Teste Interativo**: Login e teste de endpoints diretamente no Swagger

Este schema oferece flexibilidade para expansão futura, mantendo a integridade referencial, performance adequada e segurança robusta para uma aplicação educacional moderna.