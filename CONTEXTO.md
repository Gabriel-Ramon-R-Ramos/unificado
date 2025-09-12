## Rede de Conhecimento: Visualizando Dependências Curriculares

Este documento contextualiza a ideia por trás da Rede de Conhecimento, uma aplicação focada em resolver o desafio da **compreensão clara das dependências curriculares** em cursos universitários, utilizando uma abordagem baseada em grafos.

---

## Objetivo do Projeto

O principal objetivo da Rede de Conhecimento é **simplificar e tornar visualmente acessível a estrutura de pré-requisitos de disciplinas** de um curso universitário. Ao representar as disciplinas como nós e as relações de dependência como arestas em um grafo, buscamos proporcionar a alunos e professores uma ferramenta intuitiva para:

* **Visualizar o fluxo de aprendizado:** Entender a sequência lógica ideal para cursar as matérias.
* **Identificar gargalos e oportunidades:** Perceber disciplinas que são cruciais ou que bloqueiam o progresso.
* **Planejar a trajetória acadêmica:** Facilitar a escolha de disciplinas futuras com base nos pré-requisitos já cumpridos.

Em suma, queremos transformar a complexidade curricular em uma visão clara e navegável.

---

## Guia de Desenvolvimento

Este guia oferece direcionamentos técnicos para o desenvolvimento da Rede de Conhecimento, focando em **como fazer** em vez de um passo a passo exato do que fazer.

### 1. Backend (Python)

Para o desenvolvimento do backend, a linguagem escolhida é o **Python**. Sua sintaxe clara e o rico ecossistema de bibliotecas o tornam ideal para este projeto.

* **Estrutura de Pastas:** Adote uma estrutura inspirada na **Arquitetura Limpa**, separando responsabilidades em camadas como `core` (entidades, casos de uso, serviços) e `infra` (banco de dados, API). Utilize um arquivo `main.py` para inicialização da aplicação e `config.py` para configurações.
* **Gerenciamento de Dependências:** Utilize um ambiente virtual (`venv`) e gerencie as dependências com o arquivo `requirements.txt`.
* **API:** Para a construção da API RESTful, utilize o framework **FastAPI**. Ele oferece alta performance, validação automática de dados com Pydantic e documentação interativa (Swagger UI/ReDoc) por padrão.
    * Defina os endpoints em `infra/api/routes.py`.
    * Utilize Pydantic em `infra/data/schemas.py` para definir os modelos de requisição e resposta, garantindo a validação dos dados.
* **Banco de Dados:** Para a persistência dos dados (disciplinas, pré-requisitos), utilize o **SQLAlchemy**. Ele é um ORM (Object-Relational Mapper) poderoso que abstrai as interações com o banco de dados.
    * Configure a conexão com o banco de dados em `app/config.py`.
    * Defina os modelos de dados do ORM em `infra/data/models.py`.
    * Implemente a lógica de acesso aos dados (CRUD) na camada `infra/database/repositories.py`.
* **Manipulação de Grafos:** A biblioteca **`NetworkX`** em Python será a espinha dorsal para a criação e manipulação do grafo.
    * Encapsule a lógica de criação, adição e consulta de nós (disciplinas) e arestas (pré-requisitos) em um `GraphService` na camada `core/services/graph_service.py`.