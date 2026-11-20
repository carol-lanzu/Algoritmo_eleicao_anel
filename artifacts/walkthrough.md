# 🛠️ Progresso da Implementação — Algoritmo de Eleição em Anel

| # | Tarefa | Status |
|---|--------|--------|
| 1 | Estrutura base (`Processo` + `Anel`) | ✅ Concluído |
| 2 | Lógica de eleição (`ELEIÇÃO` + `COORDENADOR`) | ✅ Concluído |
| 3 | Simulação de falha (derrubar processo + reeleição) | ✅ Concluído |
| 4 | Interface gráfica (canvas + animação + log) | ✅ Concluído |
| 5 | Integração final (GUI + algoritmo) | ✅ Concluído |
| 6 | Teste e validação | ✅ Lógica validada — GUI pendente de `python3-tk` |

---

## Arquivo gerado

**[anel.py](file:///home/carol-lanzu/Documents/distribuidos/T2_eleicao_anel/anel.py)** — único arquivo, ~300 linhas, sem dependências externas além de `tkinter`.

## Validação da Lógica (testes sem GUI)

Três cenários testados com sucesso:

| Cenário | Resultado |
|---------|-----------|
| Anel completo: P1→P2→P3→P4→P5→P1 | ✅ Encadeamento correto |
| P5 cai → eleição a partir de P1 → P4 vence | ✅ P4 eleito corretamente |
| P4 cai → eleição a partir de P1 → P5 vence | ✅ P5 eleito corretamente |

## Como executar

```bash
# 1. Instalar tkinter (apenas uma vez, requer senha)
sudo apt-get install -y python3-tk

# 2. Rodar
cd ~/Documents/distribuidos/T2_eleicao_anel
python3 anel.py
```

## Estrutura do arquivo

```
anel.py
├── Processo      — classe com id, nome, ativo, lider
├── Anel          — ring com proximo_ativo()
└── App (Tkinter)
    ├── _montar_ui()          — constrói canvas, botões, slider, log
    ├── _redesenhar_anel()    — desenha nós e setas no canvas
    ├── _animar_mensagem()    — bolinha animada entre dois nós
    ├── _iniciar_eleicao()    — dispara ELEIÇÃO a partir do primeiro ativo
    ├── _processar()          — lógica: compara IDs, encaminha ou declara vencedor
    ├── _derrubar_processo()  — marca nó como inativo, relança eleição se era líder
    └── _reiniciar()          — reseta tudo para o estado inicial
```

## Decisões de projeto

- **Nome == ID:** P1 tem `id=1`, P2 tem `id=2`, ..., P5 tem `id=5`. O maior ID (P5) sempre vence uma eleição completa.
- **Anel unidirecional:** P1→P2→P3→P4→P5→P1. `proximo_ativo(pid)` pula processos caídos automaticamente.
- **Animação por `root.after()`:** sem threads, sem concorrência — tudo no event loop do Tkinter, simples e didático.
- **Cores:** azul=ativo · verde=líder · vermelho=caído · amarelo=mensagem em trânsito.