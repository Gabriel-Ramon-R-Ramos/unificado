from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()

# Tabela de associação para relacionamento muitos-para-muitos entre
# disciplinas e pré-requisitos
discipline_prerequisites = Table(
    'discipline_prerequisites',
    table_registry.metadata,
    Column(
        'discipline_id',
        Integer,
        ForeignKey('disciplines.id'),
        primary_key=True,
    ),
    Column(
        'prerequisite_id',
        Integer,
        ForeignKey('disciplines.id'),
        primary_key=True,
    ),
)


@table_registry.mapped_as_dataclass
class Course:
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)

    disciplines: Mapped[list['Discipline']] = relationship(
        back_populates='course', init=False, default_factory=list
    )


@table_registry.mapped_as_dataclass
class Discipline:
    __tablename__ = 'disciplines'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(
        ForeignKey('courses.id'), nullable=False, index=True
    )

    course: Mapped['Course'] = relationship(
        back_populates='disciplines', init=False
    )

    prerequisites: Mapped[list['Discipline']] = relationship(
        secondary=discipline_prerequisites,
        primaryjoin=(
            'Discipline.id == discipline_prerequisites.c.discipline_id'
        ),
        secondaryjoin=(
            'Discipline.id == discipline_prerequisites.c.prerequisite_id'
        ),
        back_populates='dependent_disciplines',
        init=False,
        default_factory=list,
    )

    dependent_disciplines: Mapped[list['Discipline']] = relationship(
        secondary=discipline_prerequisites,
        primaryjoin=(
            'Discipline.id == discipline_prerequisites.c.prerequisite_id'
        ),
        secondaryjoin=(
            'Discipline.id == discipline_prerequisites.c.discipline_id'
        ),
        back_populates='prerequisites',
        init=False,
        default_factory=list,
    )
