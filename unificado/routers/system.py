from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from unificado.database import get_session

router = APIRouter(prefix='/system', tags=['Sistema'])


@router.get('/health')
def health(db: Session = Depends(get_session)):
    try:
        db.execute(text('SELECT 1'))
        return JSONResponse(
            status_code=200, content={'status': 'ok', 'db': True}
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={'status': 'unhealthy', 'db': False, 'error': str(exc)},
        )
