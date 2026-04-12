import pdfplumber
import re
import pdfplumber

def extrair_texto(caminho):
    try:
        with pdfplumber.open(caminho) as pdf:
            return " ".join([p.extract_text() or "" for p in pdf.pages])
    except:
        return ""
    
def extrair_valor(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""

            # Procura valores tipo 123.45 ou 123,45
            match = re.search(r"\d+[.,]\d{2}", texto)

            if match:
                valor = match.group().replace(",", ".")
                return float(valor)

    except Exception as e:
        print("Erro ao ler PDF:", e)

    return 0.0
