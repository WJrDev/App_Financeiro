from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///dados.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    caminho = Column(String)
    categoria = Column(String)
    valor = Column(Float)
    data = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))

def init_db():
    Base.metadata.create_all(engine)