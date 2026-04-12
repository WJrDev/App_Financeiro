# ========== NOVO MÓDULO: services/pdf_extractor.py ==========
import fitz  # PyMuPDF
import re
from typing import Optional

def extrair_valor_total(caminho_pdf: str) -> Optional[float]:
    """
    Extrai o valor total de um PDF financeiro.
    Prioriza valores com cifrão (R$) e palavras como 'total', 'valor a pagar'.
    Considera descontos e acréscimos se houver.
    Retorna float ou None se não encontrar.
    """
    doc = fitz.open(caminho_pdf)
    texto_completo = ""
    for pagina in doc:
        texto_completo += pagina.get_text()

    # Padrão para valores monetários: R$ 1.234,56 ou 1.234,56
    padrao_valor = r"R?\$?\s*([\d]{1,3}(?:\.\d{3})*,\d{2})"
    matches = re.findall(padrao_valor, texto_completo, re.IGNORECASE)

    if not matches:
        return None

    # Converte para float
    valores_float = []
    for m in matches:
        try:
            val = float(m.replace(".", "").replace(",", "."))
            valores_float.append(val)
        except:
            continue

    if not valores_float:
        return None

    # Procura por palavras-chave para identificar o total
    linhas = texto_completo.lower().split("\n")
    total_candidato = None
    for linha in linhas:
        if any(p in linha for p in ["total", "valor a pagar", "valor total", "líquido"]):
            # Tenta capturar o valor nessa linha
            match = re.search(padrao_valor, linha, re.IGNORECASE)
            if match:
                try:
                    total_candidato = float(match.group(1).replace(".", "").replace(",", "."))
                    break
                except:
                    pass

    # Se não achou um total explícito, usa o maior valor (ou último?)
    if total_candidato is None:
        # Estratégia: maior valor encontrado (presume-se que seja o total)
        total_candidato = max(valores_float)

    # Verifica descontos/acréscimos
    desconto = 0.0
    acrescimo = 0.0
    for linha in linhas:
        if "desconto" in linha:
            m = re.search(padrao_valor, linha, re.IGNORECASE)
            if m:
                try:
                    desconto += float(m.group(1).replace(".", "").replace(",", "."))
                except:
                    pass
        if any(p in linha for p in ["acréscimo", "juros", "multa"]):
            m = re.search(padrao_valor, linha, re.IGNORECASE)
            if m:
                try:
                    acrescimo += float(m.group(1).replace(".", "").replace(",", "."))
                except:
                    pass

    total_final = total_candidato - desconto + acrescimo
    return round(total_final, 2)