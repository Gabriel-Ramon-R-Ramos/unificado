from fastapi import FastAPI
from infra.api.routes import router

app = FastAPI(title="Rede de Conhecimento")

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)