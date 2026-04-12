import os
from data.database import Session, Documento
from services.pdf_service import extrair_valor
from services.ai_service import classificar
from services.pdf_service import extrair_texto

def adicionar_documento(caminho, categoria=None):
    session = Session()

    nome = os.path.basename(caminho)

    texto = extrair_texto(caminho)
    categoria_auto = classificar(texto)

    # usa categoria manual se tiver, senão usa IA
    categoria_final = categoria if categoria else categoria_auto

    valor = extrair_valor(caminho)

    doc = Documento(
        nome=nome,
        caminho=caminho,
        categoria=categoria_final,
        valor=valor
    )

    session.add(doc)
    session.commit()

    return doc