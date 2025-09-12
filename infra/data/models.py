from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Tabela de associação para representar pré-requisitos
discipline_prerequisites = Table(
    "discipline_prerequisites",
    Base.metadata,
    Column("discipline_id", Integer, ForeignKey("disciplines.id"), primary_key=True),
    Column("prerequisite_id", Integer, ForeignKey("disciplines.id"), primary_key=True)
)


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    disciplines = relationship("Discipline", back_populates="course")


class Discipline(Base):
    __tablename__ = "disciplines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    course = relationship("Course", back_populates="disciplines")
    
    # Relacionamento muitos-para-muitos para pré-requisitos
    prerequisites = relationship(
        "Discipline",
        secondary=discipline_prerequisites,
        primaryjoin=(discipline_prerequisites.c.discipline_id == id),
        secondaryjoin=(discipline_prerequisites.c.prerequisite_id == id),
        backref="required_by"
    )
