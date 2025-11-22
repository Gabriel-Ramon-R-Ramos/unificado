"""Módulo de análises de grade/disciplinas usando grafos (networkx).

Fornece funções que constroem um grafo de pré-requisitos a partir do
banco e geram insights úteis para administradores: detecção de ciclos,
importância de disciplinas, recomendações, caminho até a formatura e
visualização leve do progresso do estudante.

As funções usam uma sessão SQLAlchemy (do `get_session`) ou uma `Session`
passada pelo caller.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, cast

import networkx as nx
import sqlalchemy as sa
from sqlalchemy.orm import Session

from unificado.models import (
    Discipline,
    StudentProfile,
    discipline_prerequisites,
    students_disciplines,
)


def build_prereq_graph(db: Session) -> nx.DiGraph:
    """Constrói e retorna um DiGraph de disciplinas com arestas de
    pré-requisito -> disciplina.

    Nós possuem atributos:
    - `name`: nome da disciplina
    - `id`: id inteiro

    Retorna:
        networkx.DiGraph
    """
    G = nx.DiGraph()

    # Carregar disciplinas
    disciplines = db.execute(sa.select(Discipline.id, Discipline.name)).all()
    for did, name in disciplines:
        G.add_node(did, name=name)

    # Carregar pré-requisitos (discipline_id, prerequisite_id)
    rows = db.execute(
        sa.select(
            discipline_prerequisites.c.discipline_id,
            discipline_prerequisites.c.prerequisite_id,
        )
    ).all()
    for disc_id, prereq_id in rows:
        # Aresta do pré-requisito para a disciplina dependente
        if prereq_id is None or disc_id is None:
            continue
        if not G.has_node(prereq_id):
            G.add_node(prereq_id, name=str(prereq_id))
        if not G.has_node(disc_id):
            G.add_node(disc_id, name=str(disc_id))
        G.add_edge(prereq_id, disc_id)

    return G


def detect_cycles(db: Session) -> List[List[int]]:
    """Detecta ciclos no grafo de pré-requisitos. Retorna uma lista de
    ciclos, cada ciclo é uma lista de ids de disciplinas na ordem do ciclo.
    """
    G = build_prereq_graph(db)
    try:
        # se é DAG, topological_sort funciona, sem exceção
        list(nx.topological_sort(G))
        return []
    except nx.NetworkXUnfeasible:
        cycles = list(nx.simple_cycles(G))
        return cycles


def analyze_importance(db: Session) -> List[Dict[str, object]]:
    """Calcula métricas de importância / influência para cada disciplina.

    Retorna uma lista de dicionários com keys:
    - id, name, out_degree (número de disciplinas diretamente desbloqueadas),
      descendants (total desbloqueadas indiretamente), betweenness (float).
    """
    G = build_prereq_graph(db)
    result: List[Dict[str, object]] = []

    # Betweenness centrality (normalizado)
    if len(G) > 0:
        bet = nx.betweenness_centrality(G)
    else:
        bet = {}

    for node in G.nodes():
        name = G.nodes[node].get('name')
        out_deg = G.out_degree(node)
        descendants = len(nx.descendants(G, node))
        result.append({
            'id': node,
            'name': name,
            'out_degree': out_deg,
            'descendants': descendants,
            'betweenness': float(bet.get(node, 0.0)),
        })

    # Ordenar por importância (descendants, betweenness)
    result.sort(
        key=lambda x: (x['descendants'], x['betweenness']),
        reverse=True,
    )
    return result


def _get_student_profile_id(db: Session, user_id: int) -> Optional[int]:
    row = db.execute(
        sa.select(StudentProfile.id).where(StudentProfile.user_id == user_id)
    ).first()
    return row[0] if row else None


def recommend_disciplines_for_student(
    db: Session, user_id: int
) -> List[Dict[str, object]]:
    """Recomenda disciplinas que o estudante já pode cursar com base nas
    disciplinas concluídas.

    Lógica:
    - Buscar disciplinas com todos os pré-requisitos presentes no conjunto
      de disciplinas com status 'concluido'.
    - Excluir disciplinas já concluidas.
    - Retornar lista com disciplina id, name e lista de prereq ids.
    """
    sp_id = _get_student_profile_id(db, user_id)
    if sp_id is None:
        return []

    # Disciplinas concluídas pelo estudante
    concluded_rows = db.execute(
        sa.select(students_disciplines.c.discipline_id).where(
            students_disciplines.c.student_id == sp_id,
            students_disciplines.c.status == 'concluido',
        )
    ).fetchall()
    concluded = {r[0] for r in concluded_rows}

    G = build_prereq_graph(db)
    recommendations: List[Dict[str, object]] = []

    for node in G.nodes():
        if node in concluded:
            continue
        prereqs = set(G.predecessors(node))
        if prereqs.issubset(concluded):
            recommendations.append({
                'id': node,
                'name': G.nodes[node].get('name'),
                'prereqs': list(prereqs),
            })

    # Ordenar por número de prereqs (preferir com menos pré-reqs)
    recommendations.sort(key=lambda x: len(cast(list, x.get('prereqs') or [])))
    return recommendations


def calculate_graduation_path(
    db: Session, user_id: int, required_ids: Iterable[int]
) -> List[int]:
    """Calcula uma ordem viável (topológica) para cursar as disciplinas
    restantes até a formatura, considerando pré-requisitos.

        - `required_ids` deve ser um iterable com os ids das
            disciplinas obrigatórias.
    - Retorna uma lista de disciplina ids na ordem sugerida (exclui já
      concluidas pelo estudante).
    """
    sp_id = _get_student_profile_id(db, user_id)
    if sp_id is None:
        return []

    concluded_rows = db.execute(
        sa.select(students_disciplines.c.discipline_id).where(
            students_disciplines.c.student_id == sp_id,
            students_disciplines.c.status == 'concluido',
        )
    ).fetchall()
    concluded = {r[0] for r in concluded_rows}

    G = build_prereq_graph(db)

    required_set = set(required_ids)
    remaining = required_set - concluded
    sub = G.subgraph(required_set).copy()

    # Remover nós já concluídos para simplificar
    sub.remove_nodes_from(concluded & set(sub.nodes()))

    # Garantir que temos um DiGraph para as operações topológicas
    sub_dg = nx.DiGraph(sub)

    try:
        order_nodes = list(nx.topological_sort(sub_dg))
        # filtrar para apenas os restantes e garantir ints
        order = [int(n) for n in order_nodes if n in remaining]
        return order
    except nx.NetworkXUnfeasible:
        # Ciclos detectados — retornar vazio para sinalizar problema
        return []


def visualize_student_progress(db: Session, user_id: int) -> Dict[str, object]:
    """Gera uma representação leve do progresso do estudante no grafo.

    Retorna um dicionário com:
    - `positions`: mapping node -> (x, y) floats (spring_layout)
        - `statuses`: mapping node -> one of:
            'concluido'|'cursando'|'pendente'|'nao_associada'
    - `labels`: mapping node -> disciplina nome

    Observação: não gera imagens; consumidor pode usar as posições e cores para
    desenhar no frontend.
    """
    sp_id = _get_student_profile_id(db, user_id)
    if sp_id is None:
        return {'positions': {}, 'statuses': {}, 'labels': {}}

    # Buscar todos os status do estudante
    rows = db.execute(
        sa.select(
            students_disciplines.c.discipline_id,
            students_disciplines.c.status,
        ).where(students_disciplines.c.student_id == sp_id)
    ).fetchall()
    status_map = {r[0]: r[1] for r in rows}

    G = build_prereq_graph(db)
    labels = {n: G.nodes[n].get('name') for n in G.nodes()}

    # Mapear status por nó
    statuses = {}
    for n in G.nodes():
        statuses[n] = status_map.get(n, 'nao_associada')

    # Calcular posições (determinístico com seed)
    if len(G) > 0:
        raw_positions = nx.spring_layout(G, seed=42)
    else:
        raw_positions = {}

    # Converter posições (ndarray) em listas de floats serializáveis por JSON
    positions: Dict[int, List[float]] = {}
    for node, coord in raw_positions.items():
        try:
            # coord pode ser numpy.ndarray ou tuple
            coord_list = list(coord)
            positions[int(node)] = [float(coord_list[0]), float(coord_list[1])]
        except Exception:
            # Fallback seguro: armazenar como lista vazia
            positions[int(node)] = []

    return {'positions': positions, 'statuses': statuses, 'labels': labels}
