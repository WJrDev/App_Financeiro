from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

def gerar_relatorio(documentos):
    doc = SimpleDocTemplate("relatorio.pdf")

    dados = [["ID", "Nome", "Categoria", "Valor", "Data"]]

    for d in documentos:
        dados.append([
            d.id,
            d.nome,
            d.categoria,
            f"R$ {d.valor:.2f}",
            d.data
        ])

    tabela = Table(dados)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
    ]))

    doc.build([tabela])