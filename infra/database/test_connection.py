from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_connection():
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("Conexão com o banco de dados bem-sucedida!")
    except Exception as e:
        print(f"Erro na conexão: {e}")
    finally:
        if db is not None:
            db.close()

if __name__ == "__main__":
    test_connection()