# ==================================================
# APLICAÇÃO FINANCE PRO – VERSÃO MELHORADA
# ==================================================

import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox, Menu
import tkinter.messagebox as msg
import fitz
from PIL import Image, ImageTk
from services.document_service import adicionar_documento
from services.report_service import gerar_relatorio
from services.dashboard_service import listar_documentos, resumo_financeiro
from services.pdf_extractor import extrair_valor_total   # NOVO
from data.database import Session, Documento
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
import os
from tkcalendar import Calendar
import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Finance Pro")
        self.geometry("1100x650")
        self.ganhos_atuais = 0.0
        self.gastos_atuais = 0.0
        self.anim = None
        self.criar_layout()
        self.atualizar_dashboard()

    # ---------- LAYOUT ----------
    def criar_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkButton(self.sidebar, text="Importar PDF", command=self.importar_pdf).pack(pady=10, padx=10)

        self.main = ctk.CTkFrame(self)
        self.main.pack(fill="both", expand=True)

        self.criar_cards()
        self.criar_filtro()
        self.criar_grafico()
        self.criar_tabela()

        self.tabela.tag_configure("ganho", foreground="#00C853")
        self.tabela.tag_configure("gasto", foreground="#FF5252")
        self.tabela.tag_configure("evenrow", background="#3c3c3c")

    # ---------- CARDS ----------
    def criar_cards(self):
        self.cards_frame = ctk.CTkFrame(self.main, fg_color="#1f1f1f")
        self.cards_frame.pack(fill="x", padx=10, pady=10)

        fonte_card = ("Segoe UI", 18, "bold")
        self.card_ganhos = ctk.CTkLabel(
            self.cards_frame, text="Ganhos: R$ 0",
            font=fonte_card, text_color="#8A2BE2"
        )
        self.card_ganhos.pack(side="left", padx=30, pady=10)

        self.card_gastos = ctk.CTkLabel(
            self.cards_frame, text="Gastos: R$ 0",
            font=fonte_card, text_color="#FF6B6B"
        )
        self.card_gastos.pack(side="left", padx=30, pady=10)

    # ---------- FILTRO ----------
    def criar_filtro(self):
        self.filtro = ctk.CTkOptionMenu(
            self.main,
            values=["todos", "ganhos", "gastos"],
            command=lambda _: self.atualizar_dashboard()
        )
        self.filtro.pack(pady=5)

    # ---------- GRÁFICO ----------
    def criar_grafico(self):
        self.frame_grafico = ctk.CTkFrame(self.main)
        self.frame_grafico.pack(fill="x", padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(5, 2.5))
        self.fig.patch.set_facecolor("#2b2b2b")
        self.ax.set_facecolor("#2b2b2b")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico)
        self.canvas.get_tk_widget().pack()

    def atualizar_grafico(self):
        novos_ganhos, novos_gastos = resumo_financeiro()

        if self.anim is None or not self.anim.event_source:
            self.anim = FuncAnimation(
                self.fig, self._animar_grafico,
                frames=np.linspace(0, 1, 20),
                fargs=(novos_ganhos, novos_gastos),
                interval=30, repeat=False, blit=False
            )
            self.canvas.draw()
        else:
            self.anim.event_source.stop()
            self.anim = FuncAnimation(
                self.fig, self._animar_grafico,
                frames=np.linspace(0, 1, 20),
                fargs=(novos_ganhos, novos_gastos),
                interval=30, repeat=False, blit=False
            )
            self.canvas.draw()

    def _animar_grafico(self, t, ganhos_alvo, gastos_alvo):
        self.ax.clear()
        ganhos = self.ganhos_atuais + t * (ganhos_alvo - self.ganhos_atuais)
        gastos = self.gastos_atuais + t * (gastos_alvo - self.gastos_atuais)

        if ganhos + gastos == 0:
            self.ax.text(0.5, 0.5, "Sem dados", ha="center", color="white")
        else:
            cores = ["#8A2BE2", "#FF6B6B"]
            self.ax.pie(
                [ganhos, gastos], labels=["Ganhos", "Gastos"],
                autopct="%1.1f%%", colors=cores, textprops={"color": "white"}
            )
        self.ax.set_facecolor("#2b2b2b")
        self.fig.patch.set_facecolor("#2b2b2b")

        if t == 1.0:
            self.ganhos_atuais = ganhos_alvo
            self.gastos_atuais = gastos_alvo

    # ---------- TABELA ----------
    def criar_tabela(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#2b2b2b", foreground="white",
                        fieldbackground="#2b2b2b", rowheight=30,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background="#1f1f1f", foreground="white",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview",
                  background=[("selected", "#8A2BE2")],
                  foreground=[("selected", "white")])

        self.tabela = ttk.Treeview(
            self.main,
            columns=("PDF", "Nome", "Categoria", "Valor", "Data"),
            show="headings",
            selectmode="extended"
        )
        self.tabela.heading("PDF", text="📄")
        self.tabela.column("PDF", width=50, anchor="center")
        for col in ("Nome", "Categoria", "Valor", "Data"):
            self.tabela.heading(col, text=col)
        self.tabela.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabela.bind("<Button-3>", self.abrir_menu_contexto)
        self.tabela.bind("<Double-1>", self.editar_por_duplo_clique)

        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="✏️ Editar nome", command=self.editar_nome)
        self.menu.add_command(label="🏷️ Editar categoria", command=self.editar_categoria)
        self.menu.add_command(label="💰 Editar valor", command=self.editar_valor)
        self.menu.add_command(label="📅 Editar data", command=self.editar_data)
        self.menu.add_separator()
        self.menu.add_command(label="🗑️ Excluir", command=self.excluir)
        self.menu.add_command(label="📄 Exportar PDF", command=self.exportar_pdf)

    def atualizar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        docs = listar_documentos(self.filtro.get())
        for i, d in enumerate(docs):
            valor_formatado = self.formatar_moeda(d.valor)
            tag_cat = "ganho" if d.categoria == "ganhos" else "gasto"
            tags = (tag_cat,)
            if i % 2 == 0:
                tags += ("evenrow",)
            self.tabela.insert(
                "", "end", iid=str(d.id),
                values=("📄", d.nome, d.categoria, valor_formatado, d.data),
                tags=tags
            )

    def atualizar_cards(self):
        ganhos, gastos = resumo_financeiro()
        self.card_ganhos.configure(text=f"Ganhos: R$ {ganhos:.2f}")
        self.card_gastos.configure(text=f"Gastos: R$ {gastos:.2f}")

    def atualizar_dashboard(self):
        self.atualizar_tabela()
        self.atualizar_cards()
        self.atualizar_grafico()

    def formatar_moeda(self, valor):
        if valor is None:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # ---------- IMPORTAÇÃO PDF ----------
    def importar_pdf(self):
        caminho = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if caminho:
            valor = extrair_valor_total(caminho)
            if valor is None:
                messagebox.showwarning(
                    "PDF sem valor",
                    "Esse PDF não tem valor para poder ser inserido."
                )
                return
            self.escolher_categoria(lambda cat: self.salvar_pdf(caminho, cat, valor))

    def escolher_categoria(self, callback):
        popup = ctk.CTkToplevel(self)
        popup.title("Categoria")
        var = ctk.StringVar(value="gastos")
        menu = ctk.CTkOptionMenu(popup, values=["ganhos", "gastos"], variable=var)
        menu.pack(pady=10)
        def confirmar():
            callback(var.get())
            popup.destroy()
        ctk.CTkButton(popup, text="Salvar", command=confirmar).pack(pady=10)

    def salvar_pdf(self, caminho, categoria, valor_extraido):
        adicionar_documento(caminho, categoria, valor_extraido)
        self.atualizar_dashboard()

    # ---------- EXPORTAR ----------
    def exportar_pdf(self):
        try:
            session = Session()
            docs = session.query(Documento).all()
            if not docs:
                msg.showwarning("Aviso", "Nenhum dado para exportar.")
                return
            gerar_relatorio(docs)
            msg.showinfo("Sucesso", "Relatório gerado como relatorio.pdf")
        except Exception as e:
            msg.showerror("Erro", str(e))

    # ---------- EXCLUIR ----------
    def excluir(self):
        selecionados = self.tabela.selection()
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione pelo menos um item")
            return
        confirm = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja excluir {len(selecionados)} item(ns)?"
        )
        if not confirm:
            return
        session = Session()
        for iid in selecionados:
            doc_id = int(iid)
            doc = session.get(Documento, doc_id)
            if doc:
                session.delete(doc)
        session.commit()
        self.atualizar_dashboard()

    # ---------- EDIÇÃO ----------
    def abrir_menu_contexto(self, event):
        item = self.tabela.identify_row(event.y)
        if item:
            if item not in self.tabela.selection():
                self.tabela.selection_set(item)
            selecionados = self.tabela.selection()
            if len(selecionados) > 1:
                self.menu.entryconfigure("✏️ Editar nome", state="disabled")
                self.menu.entryconfigure("🏷️ Editar categoria", state="disabled")
                self.menu.entryconfigure("💰 Editar valor", state="disabled")
                self.menu.entryconfigure("📅 Editar data", state="disabled")
            else:
                self.menu.entryconfigure("✏️ Editar nome", state="normal")
                self.menu.entryconfigure("🏷️ Editar categoria", state="normal")
                self.menu.entryconfigure("💰 Editar valor", state="normal")
                self.menu.entryconfigure("📅 Editar data", state="normal")
            self.menu.post(event.x_root, event.y_root)

    def editar_por_duplo_clique(self, event):
        item_id = self.tabela.identify_row(event.y)
        col = self.tabela.identify_column(event.x)
        if not item_id:
            return
        col_index = int(col.replace("#", "")) - 1
        valores = self.tabela.item(item_id)["values"]

        # Coluna PDF (índice 0): abre o arquivo
        if col_index == 0:
            doc_id = int(item_id)
            session = Session()
            doc = session.get(Documento, doc_id)
            if doc and os.path.exists(doc.caminho):
                os.startfile(doc.caminho)
            return

        # Colunas editáveis: nome(1), categoria(2), valor(3), data(4)
        if col_index in (1, 2, 3, 4):
            self.editar_celula_especifica(item_id, col_index)

    def editar_celula_especifica(self, item_id, col_index):
        col = f"#{col_index + 1}"
        bbox = self.tabela.bbox(item_id, col)
        if not bbox:
            return
        x, y, width, height = bbox
        valores = list(self.tabela.item(item_id)["values"])
        valor_atual = valores[col_index]

        if col_index == 4:  # data
            self.abrir_calendario(item_id, col_index)
            return

        widget = None
        if col_index == 2:  # categoria
            var = ctk.StringVar(value=valor_atual)
            widget = ctk.CTkOptionMenu(
                self.tabela, values=["ganhos", "gastos"],
                variable=var, width=width, height=height
            )
        elif col_index == 3:  # valor
            try:
                numero = float(valor_atual.replace("R$", "").replace(".", "").replace(",", "."))
            except:
                numero = 0.0
            widget = ctk.CTkEntry(self.tabela, width=width, height=height)
            widget.insert(0, f"{numero:.2f}")
        elif col_index == 1:  # nome
            widget = ctk.CTkEntry(self.tabela, width=width, height=height)
            widget.insert(0, valor_atual)

        if widget is None:
            return
        widget.place(x=x, y=y)
        widget.focus()

        def salvar(event=None):
            try:
                if col_index == 2:
                    novo_valor = widget.get()
                elif col_index == 3:
                    novo_valor = float(widget.get().replace(",", "."))
                else:
                    novo_valor = widget.get()
            except:
                widget.configure(border_color="red")
                return
            widget.destroy()
            valores[col_index] = novo_valor
            self.tabela.item(item_id, values=valores)
            self.atualizar_banco(item_id, valores)

        widget.bind("<Return>", salvar)
        widget.bind("<FocusOut>", salvar)

    def atualizar_banco(self, iid, valores):
        from data.database import Session, Documento
        session = Session()
        doc_id = int(iid)
        doc = session.get(Documento, doc_id)
        if not doc:
            return
        doc.nome = str(valores[1])
        doc.categoria = str(valores[2])
        try:
            doc.valor = float(valores[3])
        except:
            pass
        doc.data = str(valores[4])
        session.commit()

    # Métodos de conveniência para o menu
    def editar_nome(self):
        sel = self.tabela.selection()
        if sel:
            self.editar_celula_especifica(sel[0], 1)

    def editar_categoria(self):
        sel = self.tabela.selection()
        if sel:
            self.editar_celula_especifica(sel[0], 2)

    def editar_valor(self):
        sel = self.tabela.selection()
        if sel:
            self.editar_celula_especifica(sel[0], 3)

    def editar_data(self):
        sel = self.tabela.selection()
        if sel:
            self.abrir_calendario(sel[0], 4)

    # ---------- CALENDÁRIO ----------
    def abrir_calendario(self, item_id, col_index):
        popup = ctk.CTkToplevel(self)
        popup.title("Selecionar Data")
        popup.geometry("300x300")
        cal = Calendar(popup, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(pady=20)

        def selecionar():
            data = cal.get_date()
            valores = list(self.tabela.item(item_id)["values"])
            valores[col_index] = data
            self.tabela.item(item_id, values=valores)
            self.atualizar_banco(item_id, valores)
            popup.destroy()

        ctk.CTkButton(popup, text="Selecionar", command=selecionar).pack(pady=10)