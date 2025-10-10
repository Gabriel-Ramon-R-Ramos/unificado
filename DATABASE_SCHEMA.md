# 🗄️ Esquema do Banco de Dados - Unificado

Este documento detalha a estrutura do banco de dados, relacionamentos entre tabelas e responsabilidades de cada entidade no sistema **Unificado**.

## 📊 Visão Geral do Schema

O banco de dados está organizado em dois domínios principais:

1. **Domínio Acadêmico**: Cursos, disciplinas e pré-requisitos
2. **Domínio de Usuários**: Autenticação, perfis de estudantes e professores

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
**Responsabilidade**: Sistema de autenticação e autorização central.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária |
| `username` | VARCHAR(100) | Nome de usuário único |
| `email` | VARCHAR(255) | Email (único, opcional) |
| `password_hash` | VARCHAR | Hash da senha |
| `role` | VARCHAR(20) | Tipo de usuário (`student`, `teacher`, `admin`) |
| `is_active` | BOOLEAN | Status ativo/inativo |

**Relacionamentos**:
- **1:1** com `student_profiles` (opcional)
- **1:1** com `teacher_profiles` (opcional)

**Índices**:
- `ix_users_username` - Login
- `uq_users_email` - Unicidade de email

### 🎒 **STUDENT_PROFILES** (Perfis de Estudantes)
**Responsabilidade**: Dados específicos de estudantes.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária |
| `user_id` | INTEGER | FK para `users.id` (única) |
| `enrollment_number` | VARCHAR(50) | Matrícula do estudante |

**Relacionamentos**:
- **1:1** com `users` - Cada perfil pertence a um usuário
- **Cascade DELETE** - Removido quando usuário é deletado

### 👨‍🏫 **TEACHER_PROFILES** (Perfis de Professores)
**Responsabilidade**: Dados específicos de professores.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Chave primária |
| `user_id` | INTEGER | FK para `users.id` (única) |
| `employee_number` | VARCHAR(50) | Número de funcionário |

**Relacionamentos**:
- **1:1** com `users` - Cada perfil pertence a um usuário
- **Cascade DELETE** - Removido quando usuário é deletado

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

### 3. **User ↔ Student Profile** (1:1)
```sql
-- Dados completos do estudante
SELECT u.username, u.email, sp.enrollment_number
FROM users u
JOIN student_profiles sp ON u.id = sp.user_id
WHERE u.role = 'student';
```

### 4. **User ↔ Teacher Profile** (1:1)
```sql
-- Dados completos do professor
SELECT u.username, u.email, tp.employee_number
FROM users u
JOIN teacher_profiles tp ON u.id = tp.user_id
WHERE u.role = 'teacher';
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

## 🎯 Cenários de Uso

### Caso 1: Cadastro de Novo Estudante
```python
# 1. Criar usuário
user = User(username="joao123", email="joao@email.com", role="student")

# 2. Criar perfil de estudante
profile = StudentProfile(user_id=user.id, enrollment_number="2024001")
```

### Caso 2: Definir Pré-requisitos
```python
# Disciplina "Estruturas de Dados" tem pré-requisito "Algoritmos"
algoritmos = session.get(Discipline, 1)
estruturas = session.get(Discipline, 2)

estruturas.prerequisites.append(algoritmos)
```

### Caso 3: Validar Matrícula
```python
# Verificar se estudante pode se matricular em disciplina
def pode_matricular(student_id, discipline_id):
    # Verificar se completou todos os pré-requisitos
    discipline = session.get(Discipline, discipline_id)
    completed = get_completed_disciplines(student_id)
    
    for prereq in discipline.prerequisites:
        if prereq.id not in completed:
            return False
    return True
```

## 🔄 Fluxo de Migrations

### Migration 1: `339dbadfaddc` - Schema Acadêmico
- Cria `courses`
- Cria `disciplines`
- Cria `discipline_prerequisites`

### Migration 2: `0001` - Sistema de Usuários
- Cria `users`
- Cria `student_profiles`
- Cria `teacher_profiles`
- Insere usuário `admin` padrão

## 📈 Considerações de Performance

### Índices Importantes
- `disciplines.course_id` - Filtragem por curso
- `disciplines.name` - Busca textual
- `users.username` - Login frequente
- `users.email` - Autenticação alternativa

### Queries Otimizadas
```sql
-- Buscar disciplinas com pré-requisitos (evita N+1)
SELECT d.*, array_agg(p.name) as prerequisites
FROM disciplines d
LEFT JOIN discipline_prerequisites dp ON d.id = dp.discipline_id
LEFT JOIN disciplines p ON dp.prerequisite_id = p.id
GROUP BY d.id;
```

## 🎛️ Configuração SQLAlchemy

Os relacionamentos são configurados com:
- **`back_populates`**: Navegação bidirecional
- **`cascade="all, delete-orphan"`**: Para perfis de usuário
- **`lazy="select"`**: Carregamento sob demanda
- **`uselist=False`**: Para relacionamentos 1:1

Este schema oferece flexibilidade para expansão futura, mantendo a integridade referencial e performance adequada para uma aplicação educacional.