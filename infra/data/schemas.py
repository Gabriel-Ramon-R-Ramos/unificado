from pydantic import BaseModel, model_validator
from typing import List, Optional

class DisciplineBase(BaseModel):
    name: str

class DisciplineCreate(DisciplineBase):
    course_id: int  # Adicionar este campo obrigatório
    prerequisites: Optional[List[int]] = []

class DisciplineRead(DisciplineBase):
    id: int
    course_id: int
    prerequisites: List[int] = []  # Lista de IDs dos pré-requisitos
    warnings: Optional[List[str]] = []  # Lista de avisos, se houver
    
    class Config:
        from_attributes = True  # Substitui orm_mode no Pydantic v2
        
    @model_validator(mode='before')
    @classmethod
    def extract_prerequisites_ids(cls, values):
        # Se é um objeto ORM, extrair dados corretamente
        if hasattr(values, '__dict__'):
            prerequisites_list = []
            if hasattr(values, 'prerequisites') and values.prerequisites:
                prerequisites_list = [prereq.id for prereq in values.prerequisites]
            
            return {
                'id': values.id,
                'name': values.name,
                'course_id': values.course_id,
                'prerequisites': prerequisites_list
            }
        return values

class CourseBase(BaseModel):
    name: str

class CourseCreate(CourseBase):
    pass

class CourseRead(CourseBase):
    id: int

    class Config:
        from_attributes = True  # Substitui orm_mode no Pydantic v2