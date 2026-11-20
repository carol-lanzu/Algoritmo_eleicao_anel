# anel.py — Algoritmo de Eleição em Anel
# Grupo 8 — Sistemas Distribuídos — UFSC Araranguá
# Uso: python anel.py
#
# Regra do anel: P1(id=1) → P2(id=2) → ... → P5(id=5) → P1
# Nome do processo == valor do ID.
# Tipos de mensagem:
#   ELEIÇÃO(x)     — candidato com ID x circula pelo anel
#   COORDENADOR(x) — confirma que o processo de ID x é o novo líder

import tkinter as tk
from tkinter import scrolledtext
import math

NUM_PROCESSOS = 5
DELAY_PADRAO = 800   # ms entre passos da animação (padrão)


# ─────────────────────────── Lógica do Algoritmo ────────────────────────────

class Processo:
    def __init__(self, pid):
        self.id    = pid          # ID == nome (P1 tem id=1, P2 tem id=2, ...)
        self.nome  = f"P{pid}"
        self.ativo = True
        self.lider = None         # None = sem líder conhecido


class Anel:
    def __init__(self, num):
        # Cria processos P1, P2, ..., Pn com id == número
        self.processos = [Processo(i) for i in range(1, num + 1)]

    def proximo_ativo(self, pid):
        """Retorna o próximo processo ativo no anel a partir de pid.
        P1(id=1) é o índice 0, logo o próximo de Pk é o índice k % n."""
        n   = len(self.processos)
        idx = pid % n                # índice do processo seguinte a pid
        for _ in range(n):
            proc = self.processos[idx]
            if proc.ativo:
                return proc
            idx = (idx + 1) % n
        return None                  # todos inativos


# ──────────────────────────────── Interface ──────────────────────────────────

class App:
    COR_NORMAL    = "#89b4fa"   # azul   — processo ativo
    COR_LIDER     = "#a6e3a1"   # verde  — líder eleito
    COR_CAIDO     = "#f38ba8"   # rosa   — processo caído
    COR_ENVIANDO  = "#fab387"   # laranja — animando mensagem
    COR_FUNDO     = "#1e1e2e"
    COR_TEXTO     = "#cdd6f4"

    def __init__(self, root):
        self.root      = root
        self.root.title("Eleição em Anel — Grupo 8 | UFSC")
        self.root.configure(bg=self.COR_FUNDO)
        self.root.resizable(False, False)

        self.anel           = Anel(NUM_PROCESSOS)
        self.velocidade_ms  = DELAY_PADRAO
        self.executando     = False
        self.modo_derrubar  = False
        self.nos_oval       = {}    # pid → id do oval no canvas
        self.nos_texto      = {}    # pid → id do texto no canvas
        self.nos_coords     = {}    # pid → (x, y) no canvas

        self._montar_ui()
        self._redesenhar_anel()

    # ── Construção da UI ──────────────────────────────────────────────────────

    def _montar_ui(self):
        # Cabeçalho
        cabecalho = tk.Frame(self.root, bg=self.COR_FUNDO)
        cabecalho.pack(fill=tk.X, padx=10, pady=(10, 0))
        tk.Label(cabecalho, text="🗳️  Algoritmo de Eleição em Anel",
                 font=("Helvetica", 15, "bold"),
                 fg=self.COR_TEXTO, bg=self.COR_FUNDO).pack(side=tk.LEFT)
        self.lbl_status = tk.Label(cabecalho, text="Aguardando...",
                 font=("Helvetica", 10, "italic"),
                 fg="#f9e2af", bg=self.COR_FUNDO)
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # Área central: canvas + controles
        centro = tk.Frame(self.root, bg=self.COR_FUNDO)
        centro.pack(fill=tk.BOTH, padx=10, pady=10)

        # Canvas do anel
        self.canvas = tk.Canvas(centro, width=460, height=460,
                                bg=self.COR_FUNDO, highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=(0, 10))
        self.canvas.bind("<Button-1>", self._clique_canvas)

        # Painel de controles
        painel = tk.Frame(centro, bg=self.COR_FUNDO)
        painel.grid(row=0, column=1, sticky="n")

        def botao(texto, cmd, cor):
            tk.Button(painel, text=texto, command=cmd,
                      bg=cor, fg=self.COR_FUNDO,
                      font=("Helvetica", 11, "bold"),
                      width=20, relief="flat", cursor="hand2",
                      activebackground=cor).pack(pady=6)

        tk.Label(painel, text="Controles", font=("Helvetica", 12, "bold"),
                 fg=self.COR_TEXTO, bg=self.COR_FUNDO).pack(pady=(0, 10))

        self.btn_iniciar = tk.Button(painel, text="▶  Iniciar Eleição",
                      command=self._iniciar_eleicao,
                      bg="#89b4fa", fg=self.COR_FUNDO,
                      font=("Helvetica", 11, "bold"),
                      width=20, relief="flat", cursor="hand2",
                      activebackground="#89b4fa")
        self.btn_iniciar.pack(pady=6)

        tk.Button(painel, text="💀  Derrubar Processo",
                  command=self._ativar_modo_derrubar,
                  bg="#f38ba8", fg=self.COR_FUNDO,
                  font=("Helvetica", 11, "bold"),
                  width=20, relief="flat", cursor="hand2",
                  activebackground="#f38ba8").pack(pady=6)

        tk.Button(painel, text="🔄  Reiniciar",
                  command=self._reiniciar,
                  bg="#a6e3a1", fg=self.COR_FUNDO,
                  font=("Helvetica", 11, "bold"),
                  width=20, relief="flat", cursor="hand2",
                  activebackground="#a6e3a1").pack(pady=6)

        # Slider de velocidade (esquerda = lento, direita = rápido)
        tk.Label(painel, text="\nVelocidade da Animação",
                 fg=self.COR_TEXTO, bg=self.COR_FUNDO,
                 font=("Helvetica", 10)).pack()
        tk.Label(painel, text="Lento  ◀─────────▶  Rápido",
                 fg="#6c7086", bg=self.COR_FUNDO,
                 font=("Helvetica", 8)).pack()
        # from_=alto→lento, to=baixo→rápido  (valor = delay em ms)
        self.slider = tk.Scale(painel, from_=1800, to=200,
                               orient=tk.HORIZONTAL,
                               showvalue=False,
                               command=self._atualizar_velocidade,
                               bg=self.COR_FUNDO, fg=self.COR_TEXTO,
                               troughcolor="#313244", sliderlength=20,
                               length=170, highlightthickness=0)
        self.slider.set(DELAY_PADRAO)
        self.slider.pack()

        # Legenda de cores
        tk.Label(painel, text="\nLegenda", font=("Helvetica", 10, "bold"),
                 fg=self.COR_TEXTO, bg=self.COR_FUNDO).pack()
        for cor, desc in [
            (self.COR_NORMAL,   "Processo ativo"),
            (self.COR_LIDER,    "Líder eleito"),
            (self.COR_CAIDO,    "Processo caído"),
            ("#f9e2af",         "Mensagem em trânsito"),
        ]:
            linha = tk.Frame(painel, bg=self.COR_FUNDO)
            linha.pack(anchor="w", padx=10)
            tk.Label(linha, text="●", fg=cor, bg=self.COR_FUNDO,
                     font=("Helvetica", 14)).pack(side=tk.LEFT)
            tk.Label(linha, text=desc, fg=self.COR_TEXTO, bg=self.COR_FUNDO,
                     font=("Helvetica", 9)).pack(side=tk.LEFT, padx=4)

        # Log de mensagens
        log_frame = tk.Frame(self.root, bg=self.COR_FUNDO)
        log_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 10))
        tk.Label(log_frame, text="📋 Log de Mensagens",
                 fg=self.COR_TEXTO, bg=self.COR_FUNDO,
                 font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.log = scrolledtext.ScrolledText(
            log_frame, height=9, bg="#181825",
            fg=self.COR_TEXTO, font=("Courier", 9),
            state="disabled", relief="flat", insertbackground=self.COR_TEXTO)
        self.log.pack(fill=tk.BOTH, expand=True)

    # ── Desenho do Anel ───────────────────────────────────────────────────────

    def _calcular_coords(self):
        n = len(self.anel.processos)
        cx, cy, raio_anel = 230, 230, 160
        for i, proc in enumerate(self.anel.processos):
            ang = math.radians(-90 + 360 * i / n)
            self.nos_coords[proc.id] = (
                cx + raio_anel * math.cos(ang),
                cy + raio_anel * math.sin(ang),
            )

    def _redesenhar_anel(self):
        self.canvas.delete("all")
        self.nos_oval.clear()
        self.nos_texto.clear()
        self._calcular_coords()
        self._desenhar_setas()
        for proc in self.anel.processos:
            self._desenhar_no(proc)

    def _desenhar_setas(self):
        n   = len(self.anel.processos)
        r_no = 26
        for i, proc in enumerate(self.anel.processos):
            prox = self.anel.processos[(i + 1) % n]
            x1, y1 = self.nos_coords[proc.id]
            x2, y2 = self.nos_coords[prox.id]
            dx, dy  = x2 - x1, y2 - y1
            dist    = math.hypot(dx, dy)
            if dist == 0:
                continue
            # Recua do centro de cada nó até a borda do círculo
            sx  = x1 + r_no * dx / dist
            sy  = y1 + r_no * dy / dist
            ex  = x2 - r_no * dx / dist
            ey  = y2 - r_no * dy / dist
            cor = "#45475a" if proc.ativo else "#2a2a3e"
            self.canvas.create_line(sx, sy, ex, ey,
                                    fill=cor, width=2,
                                    arrow=tk.LAST, arrowshape=(10, 13, 4),
                                    tags="seta")

    def _cor_no(self, proc):
        if not proc.ativo:
            return self.COR_CAIDO
        if proc.lider == proc.id:
            return self.COR_LIDER
        return self.COR_NORMAL

    def _desenhar_no(self, proc):
        x, y = self.nos_coords[proc.id]
        r    = 26
        cor  = self._cor_no(proc)

        if proc.id in self.nos_oval:
            self.canvas.delete(self.nos_oval[proc.id])
            self.canvas.delete(self.nos_texto[proc.id])

        oid = self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                      fill=cor, outline="#cdd6f4", width=2)
        tid = self.canvas.create_text(x, y, text=proc.nome,
                                      fill=self.COR_FUNDO,
                                      font=("Helvetica", 11, "bold"))
        self.nos_oval[proc.id]  = oid
        self.nos_texto[proc.id] = tid

    # ── Animação de Mensagem ──────────────────────────────────────────────────

    def _animar_mensagem(self, remetente, destinatario, tipo, valor, callback):
        """Anima uma bolinha de remetente → destinatario e chama callback ao chegar."""
        x1, y1 = self.nos_coords[remetente.id]
        x2, y2 = self.nos_coords[destinatario.id]
        bolinha = self.canvas.create_oval(-12, -12, -6, -6,
                                          fill="#f9e2af",
                                          outline="#fab387", width=2)
        passos  = 25
        delay   = max(8, self.velocidade_ms // passos)

        def mover(step):
            if step > passos:
                self.canvas.delete(bolinha)
                callback()
                return
            t = step / passos
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            self.canvas.coords(bolinha, x - 7, y - 7, x + 7, y + 7)
            self.root.after(delay, mover, step + 1)

        mover(0)

    # ── Lógica de Eleição ─────────────────────────────────────────────────────

    def _iniciar_eleicao(self):
        if self.executando:
            return
        iniciador = next((p for p in self.anel.processos if p.ativo), None)
        if not iniciador:
            self._log("⚠️  Nenhum processo ativo para iniciar eleição.")
            return

        for proc in self.anel.processos:
            proc.lider = None
        self._redesenhar_anel()

        self.executando = True
        self.btn_iniciar.config(state="disabled")
        self._atualizar_status("Eleição em andamento...")
        self._log("=" * 42)
        self._log(f"🚀 {iniciador.nome} inicia a eleição!")

        proximo = self.anel.proximo_ativo(iniciador.id)
        self._enviar(iniciador, proximo, "ELEIÇÃO", iniciador.id)

    def _enviar(self, remetente, destinatario, tipo, valor):
        rotulo = f"ELEIÇÃO({valor})" if tipo == "ELEIÇÃO" else f"COORDENADOR({valor})"
        self._log(f"   {remetente.nome} ──{rotulo}──▶ {destinatario.nome}")

        def ao_chegar():
            self._processar(destinatario, tipo, valor)

        self._animar_mensagem(remetente, destinatario, tipo, valor, ao_chegar)

    def _processar(self, destinatario, tipo, valor):
        dest = destinatario

        if tipo == "ELEIÇÃO":
            if valor > dest.id:
                self._log(f"   {dest.nome}: {valor} > {dest.id} → passa adiante")
                self._encaminhar(dest, "ELEIÇÃO", valor)

            elif valor < dest.id:
                self._log(f"   {dest.nome}: {dest.id} > {valor} → substitui por ELEIÇÃO({dest.id})")
                self._encaminhar(dest, "ELEIÇÃO", dest.id)

            else:  # valor == dest.id → meu próprio ID voltou: sou o vencedor
                self._log(f"   🏆 {dest.nome} recebeu ELEIÇÃO({valor}) de volta → SOU O LÍDER!")
                dest.lider = dest.id
                self._desenhar_no(dest)
                self._atualizar_status(f"🏆 {dest.nome} é o novo líder!")
                self.root.after(300, lambda: self._encaminhar(dest, "COORDENADOR", dest.id))

        elif tipo == "COORDENADOR":
            if valor == dest.id:
                self._log(f"   ✅ {dest.nome}: mensagem voltou ao líder → eleição concluída!")
                self._concluir_eleicao()
            else:
                dest.lider = valor
                self._log(f"   {dest.nome} reconhece P{valor} como líder")
                self._desenhar_no(dest)
                self._encaminhar(dest, "COORDENADOR", valor)

    def _encaminhar(self, proc, tipo, valor):
        proximo = self.anel.proximo_ativo(proc.id)
        if proximo:
            self.root.after(80, lambda: self._enviar(proc, proximo, tipo, valor))
        else:
            self._log("⚠️  Nenhum próximo ativo encontrado. Eleição abortada.")
            self._concluir_eleicao()

    def _concluir_eleicao(self):
        self.executando = False
        self.btn_iniciar.config(state="normal")
        self._log("=" * 42)
        lider = next((p for p in self.anel.processos if p.lider == p.id), None)
        if lider:
            self._log(f"🎉 Eleição encerrada! Líder: {lider.nome} (id={lider.id})")
        else:
            self._log("Eleição encerrada sem líder definido.")

    # ── Derrubar Processo ─────────────────────────────────────────────────────

    def _ativar_modo_derrubar(self):
        if self.executando:
            return
        self.modo_derrubar = True
        self.root.config(cursor="crosshair")
        self._atualizar_status("Clique em um processo para derrubá-lo")
        self._log("💀 Modo derrubar ativado. Clique em um processo.")

    def _clique_canvas(self, event):
        if not self.modo_derrubar:
            return
        for proc in self.anel.processos:
            x, y = self.nos_coords[proc.id]
            if math.hypot(event.x - x, event.y - y) < 30 and proc.ativo:
                self._derrubar_processo(proc)
                self.modo_derrubar = False
                self.root.config(cursor="")
                return

    def _derrubar_processo(self, proc):
        era_lider = (proc.lider == proc.id)
        proc.ativo = False
        proc.lider = None
        self._log(f"💀 {proc.nome} foi derrubado!")
        self._redesenhar_anel()
        self._atualizar_status(f"{proc.nome} caiu")
        if era_lider:
            self._log("O líder caiu! Iniciando nova eleição automaticamente...")
            self.root.after(600, self._iniciar_eleicao)

    # ── Reiniciar ─────────────────────────────────────────────────────────────

    def _reiniciar(self):
        if self.executando:
            return
        self.anel          = Anel(NUM_PROCESSOS)
        self.executando    = False
        self.modo_derrubar = False
        self.root.config(cursor="")
        self.btn_iniciar.config(state="normal")
        self._redesenhar_anel()
        self._atualizar_status("Reiniciado. Aguardando...")
        self._log("─" * 42)
        self._log("🔄 Sistema reiniciado.")

    # ── Utilitários ───────────────────────────────────────────────────────────

    def _atualizar_velocidade(self, val):
        self.velocidade_ms = int(val)

    def _atualizar_status(self, texto):
        self.lbl_status.config(text=texto)

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")


# ─────────────────────────────── Ponto de entrada ────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app  = App(root)
    root.mainloop()
