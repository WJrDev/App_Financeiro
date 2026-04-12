from data.database import Session, Documento

def resumo_financeiro():
    session = Session()
    docs = session.query(Documento).all()

    ganhos = sum(d.valor for d in docs if d.categoria == "ganhos")
    gastos = sum(d.valor for d in docs if d.categoria == "gastos")

    return ganhos, gastos

def listar_documentos(filtro=None):
    session = Session()

    query = session.query(Documento)

    if filtro and filtro != "todos":
        query = query.filter(Documento.categoria == filtro)

    return query.all()