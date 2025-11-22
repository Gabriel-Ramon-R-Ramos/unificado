# Documentação de `graph_insights`

Este documento descreve cada função exportada pelo módulo `unificado/graph_insights.py` e explica o significado de cada item retornado, como interpretar os resultados e exemplos de uso/práticas recomendadas para visualização.

Todas as funções recebem uma sessão SQLAlchemy (`sqlalchemy.orm.Session`) conectada ao banco da aplicação, e utilizam os identificadores das disciplinas (`disciplines.id`) como nós no grafo.

---

## 1) build_prereq_graph(db: Session) -> networkx.DiGraph

Descrição
- Constrói um grafo direcionado (DiGraph) onde cada nó é o `id` de uma disciplina
  e existe uma aresta do pré-requisito -> disciplina dependente.

Retorno
- `DiGraph` do NetworkX. Nós possuem atributos:
  - `name` (str): nome da disciplina.

Interpretação
- Use este grafo para: detectar ciclos, calcular ordenações topológicas, produzir visualizações e executar algoritmos de centralidade.
- Exemplo prático: um caminho topológico do grafo dá uma ordem válida de cursar disciplinas
  quando não existem ciclos.

Observações de performance
- Carregamento dos nós e arestas é O(N + E) em consultas; a construção em memória depende do tamanho do grafo.

---

## 2) detect_cycles(db: Session) -> List[List[int]]

Descrição
- Detecta ciclos no grafo de pré-requisitos. Retorna uma lista de ciclos; cada ciclo é
  representado como uma lista de IDs de disciplinas que formam esse ciclo.

Retorno
- `List[List[int]]` — lista de ciclos. Exemplo: `[[12, 34, 12]]` (um ciclo 12 -> 34 -> 12).

Interpretação & Ações
- Se a lista estiver vazia (`[]`), o grafo é um DAG (sem ciclos) e uma ordenação topológica existe.
- Se houver ciclos, cada ciclo indica um problema na grade: disciplinas mutuamente dependentes
  que tornam impossível o progresso. Ação recomendada: comunicação com a coordenação para
  revisar/remover dependências erradas.

Como apresentar ao administrador
- Mostre o ciclo com nomes das disciplinas (mapeie ids -> nomes) e links para edição/remoção
  das dependências.

---

## 3) analyze_importance(db: Session) -> List[Dict[str, object]]

Descrição
- Calcula métricas que indicam a importância/influência de cada disciplina no grafo.

Retorno (cada item do array)
- `id` (int): id da disciplina.
- `name` (str): nome da disciplina.
- `out_degree` (int): número de disciplinas diretamente desbloqueadas por esta disciplina (arestas saindo).
- `descendants` (int): número total de disciplinas que são desbloqueadas indiretamente (tamanho do fecho descendente).
- `betweenness` (float): betweenness centrality (quanto o nó atua como ponte em caminhos entre outros nós).

Interpretação
- `out_degree` alto: disciplina com impacto direto (p.ex., uma matéria básica que abre várias outras).
- `descendants` alto: disciplina estratégica com impacto em longo alcance; importante para alocação de recursos.
- `betweenness` alto: disciplina que liga áreas distintas — perder oferta desta matéria pode fragmentar a progressão.

Recomendações administrativas
- Priorizar professores, vagas e horários para as disciplinas com alta `descendants` e/ou `betweenness`.
- Monitorar matrícula/abandono nessas disciplinas.

Exemplo de uso
```json
[
  {"id": 10, "name": "Algoritmos e Programação", "out_degree": 5, "descendants": 20, "betweenness": 0.12},
  ...
]
```

---

## 4) recommend_disciplines_for_student(db: Session, user_id: int) -> List[Dict[str, object]]

Descrição
- Para um estudante (identificado por `user_id`), retorna disciplinas cujos pré-requisitos
  já estão satisfeitos (ou seja, o estudante já concluiu todos os pré-requisitos).

Retorno (cada item)
- `id` (int): id da disciplina recomendada.
- `name` (str): nome da disciplina.
- `prereqs` (List[int]): ids dos pré-requisitos dessa disciplina.

Interpretação
- Cada disciplina listada é aquela que o estudante pode se matricular imediatamente,
  assumindo que apenas pré-requisitos são a barreira.
- Não inclui disciplinas já concluídas.

Como usar operacionalmente
- Mostrar essas recomendações na interface de matrícula (UX), como sugestões "Você já pode
  cursar".
- Integrar com sistemas de recomendação para priorizar disciplinas com menor carga ou mais
  impacto curricular.

Exemplo de saída
```json
[
  {"id": 21, "name": "Estrutura de Dados", "prereqs": [10]},
  {"id": 34, "name": "Programação para Internet", "prereqs": [10, 11]}
]
```

---

## 5) calculate_graduation_path(db: Session, user_id: int, required_ids: Iterable[int]) -> List[int]

Descrição
- Recebe uma lista de disciplinas obrigatórias (`required_ids`) e calcula uma ordem viável (topológica)
  para que o estudante complete essas disciplinas, excluindo as já concluídas.

Retorno
- `List[int]`: sequência de ids na ordem sugerida.

Interpretação
- É uma sugestão que respeita pré-requisitos. Se o retorno for `[]`, pode indicar ciclostidade
  (o grafo tem ciclos) ou que não há um caminho viável (situação anômala).

Como usar
- Exibir esse caminho no planejamento de semestres; dividir em semestres com heurísticas
  (p.ex., balancear carga por número de créditos) para estimar tempo até formatura.

Dica: combinar este resultado com métricas de dificuldade/creditos para criar planos otimizados.

---

## 6) visualize_student_progress(db: Session, user_id: int) -> Dict[str, object]

Descrição
- Produz uma representação leve do grafo com o status do estudante por disciplina e posições
  (layout) para visualização no frontend.

Retorno (estrutura)
- `positions` (Dict[int, List[float]]): mapeamento `discipline_id -> [x, y]` com coordenadas no layout (spring_layout).
- `statuses` (Dict[int, str]): mapeamento `discipline_id -> status` com valores possíveis:
  - `concluido`: estudante concluiu a disciplina.
  - `cursando`: estudante está cursando atualmente.
  - `pendente`: disciplina associada ao estudante, mas não iniciada.
  - `nao_associada`: disciplina não está associada ao estudante (não matriculada/sem registro).
- `labels` (Dict[int, str]): mapeamento `discipline_id -> nome` para rótulos.

Interpretação
- Use as `positions` para desenhar os nós em um canvas; use `statuses` para colorir os nós:
  - `concluido`: cor verde
  - `cursando`: cor amarela
  - `pendente`: cor laranja
  - `nao_associada`: cor cinza

Exemplo de apresentação
- Tamanho do nó: proporcional a `descendants` ou `out_degree` (importância).
- Destaque recomendações (do `recommend_disciplines_for_student`) com borda brilhante.
- Mostrar tooltip com `name`, `status`, e `prereqs` ao passar o mouse.

Considerações técnicas
- `positions` já vem convertida para listas de floats (JSON-serializable).
- O frontend pode reconstruir arestas consultando `/admin/insights/graph` ou mantendo
  um cache local.

---

## Sugestões práticas de visualização

- Color map sugerido (hex):
  - `concluido`: `#2ecc71` (verde)
  - `cursando`: `#f1c40f` (amarelo)
  - `pendente`: `#e67e22` (laranja)
  - `nao_associada`: `#95a5a6` (cinza)

- Layouts:
  - `spring_layout` (usado internamente) é bom para grafos médios; para grafos grandes
    considere `kamada_kawai_layout` ou visualização paginada por subgrafo.

- Anotações:
  - Para dashboards, gere métricas agregadas (número de disciplinas concluídas, média de `descendants` das
    disciplinas concluídas, etc.) e combine com `analyze_importance`.

---

## Integração com API / exemplo de fluxo

1. Admin abre dashboard — frontend requisita `/admin/insights/importance` e `/admin/insights/graph`.
2. Para um estudante específico, o frontend chama `/admin/insights/progress/{user_id}` e `/admin/insights/recommendations/{user_id}`.
3. O frontend desenha o grafo, colorindo nós segundo `statuses` e destacando recomendações.

---

Se desejar, posso gerar exemplos de JSON reais extraídos do seu banco (se rodar `scripts/graph_demo.py`),
ou criar componentes React/Vue que consomem esses endpoints para gerar visualizações interativas.
