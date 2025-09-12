## Rede Acadêmica: Grafo de Disciplinas e Pré-requisitos

### 💡 Visão Geral do Projeto

Este projeto tem como objetivo desenvolver uma **ferramenta web** para universidades que visualiza e gerencia as **relações de pré-requisito entre as disciplinas de um curso**. Ao modelar o currículo como um **grafo**, onde cada disciplina é um nó e os pré-requisitos são as arestas direcionadas, a aplicação visa facilitar a compreensão da trajetória acadêmica e o planejamento de estudos para alunos e professores.

-----

### 🎯 Objetivo Principal

Resolver o problema da **fragmentação e complexidade na visualização das dependências curriculares**. Proporcionar uma interface intuitiva para que alunos entendam sua progressão acadêmica e professores possam gerenciar e comunicar claramente os pré-requisitos das disciplinas.

-----

### 🗺️ Onde Será Aplicado?

A aplicação será voltada para **instituições de ensino superior (faculdades e universidades)**, impactando diretamente:

  * **Estudantes:** Para planejar seus semestres, entender a sequência lógica de aprendizado e identificar as próximas disciplinas elegíveis.
  * **Professores e Coordenadores:** Para ter uma visão clara do currículo, identificar gargalos e gerenciar as informações de pré-requisito de forma eficiente.

-----

### ❓ Por Que Este Projeto?

A navegação por currículos universitários pode ser confusa, com informações de pré-requisitos dispersas em diferentes documentos ou sistemas. Utilizar um **grafo** permite uma representação visual e lógica poderosa dessas relações, tornando o processo de planejamento acadêmico mais transparente e menos propenso a erros.

-----

### 🛠️ Como Será Desenvolvido (Tecnologias e Ferramentas)

Este projeto será desenvolvido utilizando uma abordagem modular, inspirada na Arquitetura Limpa, para garantir manutenibilidade e escalabilidade.

  * **Backend:**

      * **Linguagem:** **Python**. Escolhido pela sua **rapidez de desenvolvimento** e pelo rico ecossistema para manipulação de grafos.
      * **API:** **FastAPI**. Um framework moderno e de alta performance para construir APIs RESTful, com validação automática de dados e documentação interativa.
      * **Banco de Dados:** **PostgreSQL**. Um sistema de gerenciamento de banco de dados relacional robusto, confiável e amplamente utilizado. Para este projeto, ele será utilizado para armazenar as informações das disciplinas e suas relações.
      * **ORM:** **SQLAlchemy**. Uma poderosa biblioteca Python que oferece um kit de ferramentas SQL e um mapeador objeto-relacional (ORM), facilitando a interação com o PostgreSQL.
      * **Manipulação de Grafos:** **NetworkX**. Uma biblioteca Python para a criação, manipulação e estudo da estrutura, dinâmica e funções de redes complexas (grafos). Ela será usada para modelar as relações de pré-requisito.

  * **Frontend:**

      * **Framework:** (A ser definido, mas sugerimos **React** ou **Vue.js**) Para criar uma interface de usuário reativa e interativa.
      * **Visualização de Grafos:** **Vis.js** ou **Cytoscape.js**. Bibliotecas JavaScript robustas para visualização interativa de grafos, que se integram bem com frameworks de frontend.

-----

### ⚙️ Configuração e Setup Inicial

Para iniciar o desenvolvimento localmente:

1.  **Instalar Python:** Certifique-se de ter o Python (versão 3.8+) instalado.
2.  **Instalar PostgreSQL:**
      * **Download:** Baixe o instalador do PostgreSQL para o seu sistema operacional no site oficial ([postgresql.org](https://www.postgresql.org/download/)).
      * **Instalação:** Execute o instalador e siga as instruções. Durante a instalação, defina uma **senha segura** para o usuário `postgres`.
      * **Verificação:** Após a instalação, tente se conectar ao banco de dados. No terminal, execute: `psql -U postgres`. Se for solicitada a senha que você definiu e você conseguir acessar o prompt do `psql`, a instalação foi bem-sucedida.
3.  **Criar um Ambiente Virtual:** No diretório raiz do projeto, execute:
    ```bash
    python -m venv venv
    # No Windows:
    venv\Scripts\activate
    # No macOS/Linux:
    source venv/bin/activate
    ```
4.  **Instalar Dependências:** Crie um arquivo `requirements.txt` com as bibliotecas necessárias (ex: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `networkx`) e execute:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Configurar Banco de Dados:** Crie um arquivo `.env` na raiz do projeto com as credenciais do seu banco de dados:
    ```env
    DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/nome_do_seu_db
    ```
    *Substitua `SUA_SENHA` e `nome_do_seu_db`.* Crie o banco de dados no PostgreSQL (você pode fazer isso usando `createdb nome_do_seu_db` no terminal, ou através de uma ferramenta como o pgAdmin).
6.  **Estrutura de Pastas:** Crie as pastas conforme a estrutura sugerida acima.
