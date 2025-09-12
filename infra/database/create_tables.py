from infra.database.database import engine, Base

# Dropar todas as tabelas
Base.metadata.drop_all(bind=engine)

# Criação das tabelas no banco de dados
Base.metadata.create_all(bind=engine)
print("Tabelas criadas com sucesso!")
