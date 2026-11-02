# -*- coding: utf-8 -*-
"""Protótipos de painel (BI) gerados a partir do banco implementado."""
import subprocess, os, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "fig")
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, CRIT = "#2a78d6", "#eb6834", "#d03b3b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF})

def q(sql):
    r = subprocess.run(["mysql", "-uroot", "--default-character-set=utf8mb4", "-N", "-B", "mercado_boturussu", "-e",
                        "SET @data_ref = DATE('2026-10-01'); " + sql], capture_output=True, text=True, check=True)
    return [l.split("\t") for l in r.stdout.strip().split("\n") if l]

reais = FuncFormatter(lambda v, _: f"R$ {v:,.0f}".replace(",", "."))

def base(ax, titulo, sub):
    ax.set_title(titulo, loc="left", fontsize=13, color=INK, pad=22, fontweight="bold")
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9, color=INK2)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)

def g1():
    rows = q("SELECT DATE(data_hora), SUM(valor_total - valor_reembolsado), SUM(lucro_bruto) FROM vw_venda_resumo "
             "WHERE situacao='CONCLUIDA' GROUP BY DATE(data_hora) ORDER BY 1")
    d = [dt.date.fromisoformat(r[0]) for r in rows]; f = [float(r[1]) for r in rows]; l = [float(r[2]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.set_xlim(d[0] - dt.timedelta(days=0.5), d[-1] + dt.timedelta(days=3.2))
    ax.plot(d, f, color=BLUE, linewidth=2, marker="o", markersize=4, label="Faturamento")
    ax.plot(d, l, color=ORANGE, linewidth=2, marker="o", markersize=4, label="Lucro bruto")
    ax.text(d[-1] + dt.timedelta(hours=16), f[-1], "Faturamento", color=INK2, va="center", fontsize=9)
    ax.text(d[-1] + dt.timedelta(hours=16), l[-1], "Lucro bruto", color=INK2, va="center", fontsize=9)
    ax.yaxis.set_major_formatter(reais); ax.set_ylim(0, max(f) * 1.15)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
    base(ax, "Faturamento e lucro bruto por dia — setembro/2026",
         f"Domingos (meio período) derrubam o movimento; lucro bruto = {100*sum(l)/sum(f):.1f}% do faturamento no mês".replace(".", ","))
    ax.legend(frameon=False, loc="upper left", ncol=2, fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "bi_faturamento_lucro.png"), dpi=170); plt.close(fig)

def g2():
    # usa exatamente o resultado da consulta G09 (evidência), para o gráfico nunca divergir da consulta
    import json
    g09 = [x for x in json.load(open(os.path.join(ROOT, "tmp", "g.json"), encoding="utf-8")) if x["titulo"].startswith("G09")][0]
    i_dia, i_saldo = g09["cab"].index("dia"), g09["cab"].index("saldo_previsto")
    rows = [(r[i_dia], r[i_saldo]) for r in g09["dados"]]
    d = [dt.date.fromisoformat(r[0]) for r in rows]; v = [float(r[1]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.axhline(0, color=INK2, linewidth=1)
    ax.plot(d, v, color=BLUE, linewidth=2, marker="o", markersize=4)
    neg = [(x, y) for x, y in zip(d, v) if y < 0]
    if neg:
        ax.scatter([x for x, _ in neg], [y for _, y in neg], color=CRIT, s=36, zorder=3)
        x0, y0 = neg[0]
        ax.annotate(f"⚠ Alerta: saldo previsto negativo a partir de {x0.strftime('%d/%m')}", (x0, y0), xytext=(-180, -40),
                    textcoords="offset points", fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=INK2))
    ax.yaxis.set_major_formatter(reais); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
    base(ax, "Previsão de disponibilidade — próximos 21 dias (G09)",
         "Saldo de banco + cofre + recebíveis pela data prevista − contas em aberto pelo vencimento (sem vendas futuras)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "bi_previsao_saldo.png"), dpi=170); plt.close(fig)

def g3():
    rows = q("""SELECT c.nome, SUM(CASE WHEN m.tipo IN ('PERDA_VENCIMENTO','PERDA_AVARIA') THEN m.valor_custo
                WHEN m.tipo='TROCA_FORNECEDOR' THEN -m.valor_custo ELSE 0 END)
                FROM vw_movimentacao_valorizada m JOIN produto p ON p.id_produto=m.id_produto JOIN categoria c ON c.codigo_categoria=p.codigo_categoria
                GROUP BY c.nome ORDER BY 2""")
    n = [r[0] for r in rows]; v = [float(r[1]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.barh(n, v, color=BLUE, height=0.55)
    for i, x in enumerate(v): ax.text(x + max(v) * 0.01, i, f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), va="center", fontsize=9, color=INK)
    ax.xaxis.set_major_formatter(reais); ax.set_xlim(0, max(v) * 1.2)
    base(ax, "Perda líquida por setor — setembro/2026 (G10)", "Vencimento + avaria − o que o fornecedor repôs na troca, a preço de custo")
    ax.grid(axis="x", color=GRID); ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "bi_perdas_setor.png"), dpi=170); plt.close(fig)

def g4():
    rows = q("""SELECT f.descricao, SUM(pv.valor) FROM pagamento_venda pv JOIN venda v ON v.id_venda=pv.id_venda
                JOIN forma_pagamento f ON f.codigo_forma=pv.codigo_forma WHERE v.situacao='CONCLUIDA' GROUP BY f.descricao ORDER BY 2""")
    n = [r[0] for r in rows]; v = [float(r[1]) for r in rows]; tot = sum(v)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.barh(n, v, color=BLUE, height=0.55)
    for i, x in enumerate(v): ax.text(x + tot * 0.005, i, f"{100 * x / tot:.1f}%", va="center", fontsize=9, color=INK)
    ax.xaxis.set_major_formatter(reais); ax.set_xlim(0, max(v) * 1.15)
    base(ax, "Faturamento por forma de pagamento — setembro/2026 (G04)", "Base para negociar taxas e dimensionar o troco")
    ax.grid(axis="x", color=GRID); ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "bi_formas_pagamento.png"), dpi=170); plt.close(fig)

if __name__ == "__main__":
    g1(); g2(); g3(); g4(); print("graficos ok")
