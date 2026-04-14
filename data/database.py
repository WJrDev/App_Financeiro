from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "financeiro.db")
engine = create_engine(f"sqlite:///{db_path}", echo=False)

Base = declarative_base()

class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    caminho = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data = Column(String, nullable=False)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)