import fitz  # PyMuPDF
import re
from typing import Optional, List, Tuple

def extrair_valor_total(caminho_pdf: str) -> Optional[float]:
    """
    Extrai o valor total de um PDF financeiro utilizando heurísticas avançadas
    e específicas para faturas (energia, água, etc.).
    Retorna o valor em float ou None se nenhum valor confiável for encontrado.
    """
    doc = fitz.open(caminho_pdf)
    candidatos = []  # Lista de tuplas (valor_float, score, contexto)

    for pagina_num, pagina in enumerate(doc):
        blocos = pagina.get_text("dict")["blocks"]
        texto_pagina = pagina.get_text()
        largura_pagina = pagina.rect.width
        altura_pagina = pagina.rect.height

        for bloco in blocos:
            if "lines" not in bloco:
                continue

            for linha in bloco["lines"]:
                for span in linha["spans"]:
                    texto = span["text"].strip()
                    # Expressão regular para valores monetários
                    padrao_valor = r"(?:R?\$\s*)?([\d]{1,3}(?:\.\d{3})*,\d{2})"
                    matches = re.finditer(padrao_valor, texto, re.IGNORECASE)

                    for match in matches:
                        valor_str = match.group(1)
                        try:
                            valor_float = float(valor_str.replace(".", "").replace(",", "."))
                        except ValueError:
                            continue

                        # Contexto estendido (500 caracteres)
                        inicio = max(0, match.start() - 300)
                        fim = min(len(texto_pagina), match.end() + 300)
                        contexto = texto_pagina[inicio:fim].lower()

                        score = 0

                        # 1. Presença de R$ ou $ no contexto próximo
                        if "r$" in contexto or "$" in contexto:
                            score += 30
                        # Bônus extra se o cifrão está imediatamente antes (ex: "R$ 169,51")
                        if re.search(r"R\$\s*" + re.escape(valor_str), texto, re.IGNORECASE):
                            score += 15

                        # 2. Palavras fortes de valor total
                        palavras_fortes = ["total a pagar", "valor a pagar", "total da fatura", "vcto",
                                           "vencimento", "pagar até", "total:", "total r$"]
                        for palavra in palavras_fortes:
                            if palavra in contexto:
                                score += 20

                        # 3. Penalidades severas
                        palavras_penalidade = {
                            "kwh": -20,
                            "consumo": -15,
                            "energia ativa": -20,
                            "parcela": -25,
                            "entrada": -20,
                            "desconto": -15,
                            "juros": -15,
                            "multa": -15,
                            "icms": -30,
                            "pis": -30,
                            "cofins": -30,
                            "tributo": -30,
                            "ajuste": -15,
                        }
                        for palavra, penalidade in palavras_penalidade.items():
                            if palavra in contexto:
                                score += penalidade

                        # 4. Tamanho da fonte
                        font_size = span["size"]
                        if font_size > 12:
                            score += (font_size - 12) * 3

                        # 5. Negrito
                        if "bold" in span["font"].lower():
                            score += 15

                        # 6. Posição na página (terço inferior direito)
                        bbox = span["bbox"]
                        centro_x = (bbox[0] + bbox[2]) / 2
                        centro_y = (bbox[1] + bbox[3]) / 2
                        if centro_x > largura_pagina * 0.5 and centro_y > altura_pagina * 0.7:
                            score += 25
                        elif centro_y > altura_pagina * 0.5:
                            score += 10

                        # 7. Última página
                        if pagina_num == len(doc) - 1:
                            score += 15

                        # 8. Valor muito pequeno
                        if valor_float < 1.0:
                            score -= 50

                        candidatos.append((valor_float, score, contexto, pagina_num, centro_y))

    if not candidatos:
        return None

    # Ordena por score decrescente
    candidatos.sort(key=lambda x: x[1], reverse=True)
    melhor = candidatos[0]

    # Pós-processamento: se há um valor com R$ explícito no final da última página,
    # podemos dar preferência mesmo que o score seja ligeiramente menor.
    for cand in candidatos:
        if cand[1] >= melhor[1] * 0.7:  # score pelo menos 70% do melhor
            contexto = cand[2]
            if "r$" in contexto and cand[3] == len(doc) - 1 and cand[4] > doc[-1].rect.height * 0.6:
                # Valor com cifrão no final da última página: prioridade máxima
                melhor = cand
                break

    melhor_valor = melhor[0]

    # Verifica descontos e acréscimos no texto completo
    texto_completo = ""
    for pagina in doc:
        texto_completo += pagina.get_text()

    desconto = _extrair_valor_associado(texto_completo, ["desconto", "abatimento", "crédito"])
    acrescimo = _extrair_valor_associado(texto_completo, ["acréscimo", "juros", "multa", "encargos"])

    total_final = melhor_valor - desconto + acrescimo
    return round(total_final, 2)


def _extrair_valor_associado(texto: str, palavras_chave: List[str]) -> float:
    total = 0.0
    padrao_valor = r"(?:R?\$\s*)?([\d]{1,3}(?:\.\d{3})*,\d{2})"
    linhas = texto.split("\n")

    for i, linha in enumerate(linhas):
        linha_lower = linha.lower()
        if any(palavra in linha_lower for palavra in palavras_chave):
            match = re.search(padrao_valor, linha, re.IGNORECASE)
            if match:
                try:
                    total += float(match.group(1).replace(".", "").replace(",", "."))
                except ValueError:
                    pass
            else:
                for offset in [-1, 1]:
                    idx = i + offset
                    if 0 <= idx < len(linhas):
                        match = re.search(padrao_valor, linhas[idx], re.IGNORECASE)
                        if match:
                            try:
                                total += float(match.group(1).replace(".", "").replace(",", "."))
                            except ValueError:
                                pass
    return total