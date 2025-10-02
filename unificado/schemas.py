from typing import List, Optional

from pydantic import BaseModel, model_validator


class DisciplineSchema(BaseModel):
    name: str


class DisciplineCreate(DisciplineSchema):
    course_id: int
    prerequisites: Optional[List[int]] = []


class DisciplinePublic(DisciplineSchema):
    id: int
    course_id: int
    prerequisites: List[int] = []  # Lista de IDs das disciplinas pré-requisito

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_prerequisites_ids(cls, values):
        # Se é um objeto ORM, extrair dados corretamente
        if hasattr(values, '__dict__'):
            prerequisites_list = []
            if hasattr(values, 'prerequisites') and values.prerequisites:
                prerequisites_list = [
                    prereq.id for prereq in values.prerequisites
                ]

            return {
                'id': values.id,
                'name': values.name,
                'course_id': values.course_id,
                'prerequisites': prerequisites_list,
            }
        return values


class CourseBase(BaseModel):
    name: str


class CourseCreate(CourseBase):
    pass


class CoursePublic(CourseBase):
    id: int

    class Config:
        from_attributes = True
