import re
import fitz  # PyMuPDF

def extrair_dados_pdf(caminho):
    doc = fitz.open(caminho)
    texto = ""

    for page in doc:
        texto += page.get_text()

    # tenta achar valor tipo R$ 123,45
    match = re.search(r'R\$\s?(\d+[.,]\d+)', texto)

    valor = None
    if match:
        valor = float(match.group(1).replace(",", "."))

    # heurística simples
    categoria = "gastos"

    if any(p in texto.lower() for p in ["salário", "deposito", "pix recebido"]):
        categoria = "ganhos"

    return valor, categoria

def classificar(texto):
    texto = texto.lower()

    palavras_gasto = [
        "pagamento", "compra", "boleto", "fatura",
        "debito", "supermercado", "loja"
    ]

    palavras_ganho = [
        "salario", "pix recebido", "credito",
        "transferencia recebida", "rendimento"
    ]

    score_gasto = sum(p in texto for p in palavras_gasto)
    score_ganho = sum(p in texto for p in palavras_ganho)

    if score_ganho > score_gasto:
        return "ganhos"
    else:
        return "gastos"