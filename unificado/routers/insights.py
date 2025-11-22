from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.graph_insights import (
    analyze_importance,
    build_prereq_graph,
    calculate_graduation_path,
    detect_cycles,
    recommend_disciplines_for_student,
    visualize_student_progress,
)
from unificado.security import require_role

router = APIRouter(prefix='/insights', tags=['Insights'])


def _explain_cycles() -> str:
    return (
        'Detecta ciclos na grade de pré-requisitos. '
        'Vantagem: garante integridade curricular — '
        'ciclos impedem a ordenação '
        'topológica e devem ser corrigidos pela coordenação para evitar '
        'disciplinas impossíveis de cursar.'
    )


def _explain_importance() -> str:
    return (
        'Métricas de importância identificam disciplinas que desbloqueiam '
        'muitas outras (alto alcance) ou que atuam como pontes entre áreas. '
        'Vantagem: priorizar alocação de docentes e recursos nas disciplinas '
        'mais estratégicas melhora throughput acadêmico.'
    )


def _explain_recommendations() -> str:
    return (
        'Recomenda disciplinas que o estudante já pode cursar com base nas '
        'disciplinas concluídas. Vantagem: suporte a aconselhamento acadêmico '
        'personalizado e sugestões de matrícula automatizadas.'
    )


def _explain_graduation_path() -> str:
    return (
        'Gera uma ordem viável (topológica) para concluir disciplinas '
        'obrigatórias, respeitando pré-requisitos. Vantagem: planejar '
        'semestres e estimar tempo até formatura.'
    )


def _explain_progress_visualization() -> str:
    return (
        'Gera uma visão do progresso do estudante sobre o grafo curricular. '
        'Vantagem: painel visual para coordenadores identificarem gargalos '
        'e disciplinas não matriculadas.'
    )


@router.get('/cycles')
def get_cycles(
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_role('admin')),
) -> JSONResponse:
    """Retorna ciclos detectados no grafo de pré-requisitos e explicação."""
    cycles = detect_cycles(db)
    return JSONResponse(
        status_code=200,
        content={
            'insight': 'cycles',
            'explanation': _explain_cycles(),
            'cycles': cycles,
            'cycles_count': len(cycles),
        },
    )


@router.get('/importance')
def get_importance(
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_role('admin')),
) -> JSONResponse:
    """Retorna métricas de importância das disciplinas e explicação."""
    importance = analyze_importance(db)
    return JSONResponse(
        status_code=200,
        content={
            'insight': 'importance',
            'explanation': _explain_importance(),
            'metrics': importance,
        },
    )


@router.get('/graph')
def get_graph(
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_role('admin')),
) -> JSONResponse:
    """Retorna representação simples do grafo (nós e arestas)."""
    G = build_prereq_graph(db)
    nodes = [{'id': n, 'name': G.nodes[n].get('name')} for n in G.nodes()]
    edges = [{'from': u, 'to': v} for u, v in G.edges()]
    return JSONResponse(
        status_code=200,
        content={
            'insight': 'graph',
            'explanation': (
                'Representação de nós e arestas do grafo de pré-requisitos.'
            ),
            'nodes_count': len(nodes),
            'nodes': nodes,
            'edges_count': len(edges),
            'edges': edges,
        },
    )


@router.get('/recommendations/{user_id}')
def get_recommendations(
    user_id: int,
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_role('admin')),
) -> JSONResponse:
    """Recomenda disciplinas para o estudante informado
    e explica a vantagem."""
    recs = recommend_disciplines_for_student(db, user_id)
    return JSONResponse(
        status_code=200,
        content={
            'insight': 'recommendations',
            'explanation': _explain_recommendations(),
            'user_id': user_id,
            'recommendations': recs,
        },
    )


@router.get('/graduation-path/{user_id}')
def get_graduation_path(
    user_id: int,
    required: Optional[str] = Query(
        None, description='Comma-separated discipline ids'
    ),
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_role('admin')),
) -> JSONResponse:
    """Calcula ordem sugerida para concluir as disciplinas obrigatórias.

    Query param `required` deve ser IDs separados por vírgula.
    """
    required_ids: List[int] = []
    if required:
        try:
            required_ids = [
                int(x.strip()) for x in required.split(',') if x.strip()
            ]
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={'detail': 'required must be comma-separated ints'},
            )

    path = calculate_graduation_path(db, user_id, required_ids)
    return JSONResponse(
        status_code=200,
        content={
            'insight': 'graduation_path',
            'explanation': _explain_graduation_path(),
            'user_id': user_id,
            'required_ids': required_ids,
            'path': path,
        },
    )


@router.get('/progress/{user_id}')
def get_progress(
    user_id: int,
    db: Session = Depends(get_session),
    _admin: dict = Depends(require_role('admin')),
) -> JSONResponse:
    """Retorna uma representação leve do progresso do estudante no grafo."""
    progress = visualize_student_progress(db, user_id)
    return JSONResponse(
        status_code=200,
        content={
            'insight': 'progress',
            'explanation': _explain_progress_visualization(),
            'user_id': user_id,
            'progress': progress,
        },
    )
