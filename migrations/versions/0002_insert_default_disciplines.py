"""insert default disciplines

Revision ID: 0002
Revises: 0001
Create Date: 2025-10-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert default disciplines only (without course relationships)."""
    bind = op.get_bind()
    
    # Temporariamente tornar course_id nullable para permitir inserção de disciplinas
    op.alter_column('disciplines', 'course_id', nullable=True)
    
    # Mapeamento das disciplinas com seus pré-requisitos
    disciplines_with_prerequisites = {
        "Algoritmos e Programação": [],
        "Estrutura de Dados - Desafios de Programação": ["Algoritmos e Programação"],
        "Grafos: Teoria e Programação": ["Estrutura de Dados - Desafios de Programação"],
        "Introdução aos Compiladores": ["Linguagens Formais e Autômatos", "Grafos: Teoria e Programação"],
        "Programação para Internet": ["Estrutura de Dados - Desafios de Programação"],
        "Bancos de Dados Relacionais": ["Programação para Internet"],
        "Banco de Dados NoSQL": ["Bancos de Dados Relacionais"],
        "Cálculo Diferencial e Integral 1": [],
        "Cálculo Diferencial e Integral 2": ["Cálculo Diferencial e Integral 1"],
        "Álgebra Linear": ["Cálculo Diferencial e Integral 1"],
        "Física do Movimento": ["Cálculo Diferencial e Integral 1"],
        "Fenômenos Eletromagnéticos": ["Física do Movimento"],
        "Aplicações de Eletricidade": ["Fenômenos Eletromagnéticos"],
        "Sistemas Operacionais": ["Arquitetura de Computadores"],
        "Redes de Computadores": ["Sistemas Operacionais"],
        "Programação Distribuída e Paralela / Computação em Nuvem": ["Redes de Computadores", "Sistemas Operacionais"],
        "Engenharia de Software - Desenvolvimento Colaborativo Ágil": ["Programação para Internet"],
        "Gerenciamento de Projetos de Engenharia": ["Engenharia de Software - Desenvolvimento Colaborativo Ágil"],
        "Projeto Integrador: Projetos e Software": [],
        "Projeto Integrador: Desafios de Programação": ["Projeto Integrador: Projetos e Software"],
        "Projeto Integrador: Programação com Dispositivos Mobiles": ["Projeto Integrador: Desafios de Programação"],
        "Projeto Integrador: Compiladores e Grafos": ["Projeto Integrador: Programação com Dispositivos Mobiles"],
        "Projeto Integrador: Desenvolvimento Colaborativo e Análise de Dados": ["Projeto Integrador: Compiladores e Grafos"],
        "Projeto Integrador: Sistemas e Comunicação": ["Projeto Integrador: Desenvolvimento Colaborativo e Análise de Dados"],
        "Projeto Integrador: Programação e Gestão": ["Projeto Integrador: Sistemas e Comunicação"],
        "Arquitetura de Computadores": ["Aplicações de Eletricidade"],
        "Engenharia Técnica e Comercial": ["Teoria Econômica"],
        "Teoria Econômica": [],
        "Engenharia e Inovação": ["Engenharia: Tecnologia e Desafios"],
        "Ciências do Ambiente e Sustentabilidade": ["Química Geral e Experimental"],
        "Estatística Experimental": ["Cálculo Diferencial e Integral 2"],
        "Fenômenos de Transporte": ["Física do Movimento", "Cálculo Diferencial e Integral 2"],
        "Ergonomia e Segurança do Trabalho": [],
        "Administração e Gestão de Pessoas": [],
        "Eletiva": [],
        "Vida & Carreira - Comunicação e Liderança": [],
        "Vida & Carreira - Gestão de Tempo e Produtividade": [],
        "Vida & Carreira - Universidade e Transformação Social": [],
        "Vida & Carreira - Cultura Digital e Futuro do Trabalho": [],
        "Vida & Carreira - Ética e Responsabilidade Profissional": [],
        "Vida & Carreira - Empreendedorismo e Inovação": [],
        # Disciplinas adicionais sem pré-requisitos especificados
        "Vida & Carreira - Línguas: Língua Inglesa": [],
        "Linguagens Formais e Autômatos": [],
        "Fundamentos de Prototipagem Digital": [],
        "Engenharia: Tecnologia e Desafios": [],
        "Representações Gráficas": [],
        "Geometria Analítica": [],
        "Ciência e Tecnologia dos Materiais": [],
        "Mecânica dos Sólidos e Resistência dos Materiais": [],
        "Química Geral e Experimental": [],
        "Recursos Computacionais Aplicados ao Cálculo Numérico": [],
        "Desenvolvimento Mobile - Jogos para Dispositivos Móveis": [],
        "Tecnologias de Comunicação": [],
    }
    
    # Primeiro, inserir todas as disciplinas que ainda não existem (SEM course_id)
    for discipline_name in disciplines_with_prerequisites.keys():
        existing = bind.execute(
            sa.text("SELECT id FROM disciplines WHERE name = :name LIMIT 1"), 
            {"name": discipline_name}
        ).first()
        
        if not existing:
            # Inserir SEM course_id para evitar violação de NOT NULL constraint
            bind.execute(
                sa.text("INSERT INTO disciplines (name) VALUES (:name)"),
                {"name": discipline_name}
            )
    
    # Depois, inserir os relacionamentos de pré-requisitos
    for discipline_name, prerequisites in disciplines_with_prerequisites.items():
        if prerequisites:  # Se a disciplina tem pré-requisitos
            # Buscar o ID da disciplina
            discipline_result = bind.execute(
                sa.text("SELECT id FROM disciplines WHERE name = :name LIMIT 1"),
                {"name": discipline_name}
            ).first()
            
            if discipline_result:
                discipline_id = discipline_result[0]
                
                # Para cada pré-requisito, criar o relacionamento
                for prerequisite_name in prerequisites:
                    prerequisite_result = bind.execute(
                        sa.text("SELECT id FROM disciplines WHERE name = :name LIMIT 1"),
                        {"name": prerequisite_name}
                    ).first()
                    
                    if prerequisite_result:
                        prerequisite_id = prerequisite_result[0]
                        
                        # Verificar se o relacionamento já existe
                        existing_relationship = bind.execute(
                            sa.text(
                                "SELECT 1 FROM discipline_prerequisites "
                                "WHERE discipline_id = :discipline_id AND prerequisite_id = :prerequisite_id"
                            ),
                            {"discipline_id": discipline_id, "prerequisite_id": prerequisite_id}
                        ).first()
                        
                        if not existing_relationship:
                            bind.execute(
                                sa.text(
                                    "INSERT INTO discipline_prerequisites (discipline_id, prerequisite_id) "
                                    "VALUES (:discipline_id, :prerequisite_id)"
                                ),
                                {"discipline_id": discipline_id, "prerequisite_id": prerequisite_id}
                            )


def downgrade() -> None:
    """Remove default disciplines and prerequisites."""
    bind = op.get_bind()
    
    # Lista das disciplinas para remover (mesma lista do upgrade)
    disciplines_with_prerequisites = {
        "Algoritmos e Programação": [],
        "Estrutura de Dados - Desafios de Programação": ["Algoritmos e Programação"],
        "Grafos: Teoria e Programação": ["Estrutura de Dados - Desafios de Programação"],
        "Introdução aos Compiladores": ["Linguagens Formais e Autômatos", "Grafos: Teoria e Programação"],
        "Programação para Internet": ["Estrutura de Dados - Desafios de Programação"],
        "Bancos de Dados Relacionais": ["Programação para Internet"],
        "Banco de Dados NoSQL": ["Bancos de Dados Relacionais"],
        "Cálculo Diferencial e Integral 1": [],
        "Cálculo Diferencial e Integral 2": ["Cálculo Diferencial e Integral 1"],
        "Álgebra Linear": ["Cálculo Diferencial e Integral 1"],
        "Física do Movimento": ["Cálculo Diferencial e Integral 1"],
        "Fenômenos Eletromagnéticos": ["Física do Movimento"],
        "Aplicações de Eletricidade": ["Fenômenos Eletromagnéticos"],
        "Sistemas Operacionais": ["Arquitetura de Computadores"],
        "Redes de Computadores": ["Sistemas Operacionais"],
        "Programação Distribuída e Paralela / Computação em Nuvem": ["Redes de Computadores", "Sistemas Operacionais"],
        "Engenharia de Software - Desenvolvimento Colaborativo Ágil": ["Programação para Internet"],
        "Gerenciamento de Projetos de Engenharia": ["Engenharia de Software - Desenvolvimento Colaborativo Ágil"],
        "Projeto Integrador: Projetos e Software": [],
        "Projeto Integrador: Desafios de Programação": ["Projeto Integrador: Projetos e Software"],
        "Projeto Integrador: Programação com Dispositivos Mobiles": ["Projeto Integrador: Desafios de Programação"],
        "Projeto Integrador: Compiladores e Grafos": ["Projeto Integrador: Programação com Dispositivos Mobiles"],
        "Projeto Integrador: Desenvolvimento Colaborativo e Análise de Dados": ["Projeto Integrador: Compiladores e Grafos"],
        "Projeto Integrador: Sistemas e Comunicação": ["Projeto Integrador: Desenvolvimento Colaborativo e Análise de Dados"],
        "Projeto Integrador: Programação e Gestão": ["Projeto Integrador: Sistemas e Comunicação"],
        "Arquitetura de Computadores": ["Aplicações de Eletricidade"],
        "Engenharia Técnica e Comercial": ["Teoria Econômica"],
        "Teoria Econômica": [],
        "Engenharia e Inovação": ["Engenharia: Tecnologia e Desafios"],
        "Ciências do Ambiente e Sustentabilidade": ["Química Geral e Experimental"],
        "Estatística Experimental": ["Cálculo Diferencial e Integral 2"],
        "Fenômenos de Transporte": ["Física do Movimento", "Cálculo Diferencial e Integral 2"],
        "Ergonomia e Segurança do Trabalho": [],
        "Administração e Gestão de Pessoas": [],
        "Eletiva": [],
        "Vida & Carreira - Comunicação e Liderança": [],
        "Vida & Carreira - Gestão de Tempo e Produtividade": [],
        "Vida & Carreira - Universidade e Transformação Social": [],
        "Vida & Carreira - Cultura Digital e Futuro do Trabalho": [],
        "Vida & Carreira - Ética e Responsabilidade Profissional": [],
        "Vida & Carreira - Empreendedorismo e Inovação": [],
        # Disciplinas adicionais sem pré-requisitos especificados
        "Vida & Carreira - Línguas: Língua Inglesa": [],
        "Linguagens Formais e Autômatos": [],
        "Fundamentos de Prototipagem Digital": [],
        "Engenharia: Tecnologia e Desafios": [],
        "Representações Gráficas": [],
        "Geometria Analítica": [],
        "Ciência e Tecnologia dos Materiais": [],
        "Mecânica dos Sólidos e Resistência dos Materiais": [],
        "Química Geral e Experimental": [],
        "Recursos Computacionais Aplicados ao Cálculo Numérico": [],
        "Desenvolvimento Mobile - Jogos para Dispositivos Móveis": [],
        "Tecnologias de Comunicação": [],
    }
    
    # Primeiro, remover relacionamentos de pré-requisitos
    for discipline_name, prerequisites in disciplines_with_prerequisites.items():
        if prerequisites:  # Se a disciplina tem pré-requisitos
            # Buscar o ID da disciplina
            discipline_result = bind.execute(
                sa.text("SELECT id FROM disciplines WHERE name = :name LIMIT 1"),
                {"name": discipline_name}
            ).first()
            
            if discipline_result:
                discipline_id = discipline_result[0]
                
                # Remover todos os pré-requisitos desta disciplina
                bind.execute(
                    sa.text("DELETE FROM discipline_prerequisites WHERE discipline_id = :discipline_id"),
                    {"discipline_id": discipline_id}
                )
    
    # Depois, remover disciplinas
    for discipline_name in disciplines_with_prerequisites.keys():
        bind.execute(
            sa.text("DELETE FROM disciplines WHERE name = :name"),
            {"name": discipline_name}
        )