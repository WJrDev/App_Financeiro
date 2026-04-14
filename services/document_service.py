import os
import re
from datetime import datetime
from data.database import Session, Documento

def adicionar_documento(caminho, categoria="gastos", valor_extraido=None):
    session = Session()
    nome = os.path.basename(caminho)

    if valor_extraido is not None:
        valor = valor_extraido
    else:
        match = re.search(r"(\d+[\.,]\d{2})", nome)
        valor = float(match.group(1).replace(",", ".")) if match else 0.0

    doc = Documento(
        nome=nome,
        caminho=caminho,
        categoria=categoria,
        valor=valor,
        data=datetime.now().strftime("%Y-%m-%d")
    )
    session.add(doc)
    session.commit()
    return doc