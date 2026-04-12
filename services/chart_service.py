import matplotlib.pyplot as plt
from services.dashboard_service import resumo_financeiro

import matplotlib.pyplot as plt

def grafico_pizza(ganhos, gastos):
    labels = ["Ganhos", "Gastos"]
    valores = [ganhos, gastos]

    if sum(valores) == 0:
        return

    fig, ax = plt.subplots()

    wedges, texts, autotexts = ax.pie(
        valores,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops=dict(width=0.4),  # 👈 estilo donut
    )

    ax.set_title("Distribuição Financeira")
    ax.set_facecolor("#121212")  # fundo dark
    fig.patch.set_facecolor("#121212")

    plt.show()