# -*- coding: utf-8 -*-
"""Gera: diagramas do modelo lógico (graphviz), dicionário de dados (Markdown + CSV)
e a conferência automática dicionário × banco implementado (information_schema)."""
import os, re, sys, subprocess, csv, html, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "conc"))
import fis, spec

FIG = os.path.join(ROOT, "fig")
MOD = {}
for t, d in fis.T.items():
    c = d["conceito"]
    if c in spec.E: MOD[t] = spec.E[c]["mod"]
    elif c.startswith("POSSUI"): MOD[t] = "PA"
    else: MOD[t] = "CF"
COL = {"PE": "#dbeafe", "CF": "#fde2c8", "VC": "#d9f2e3", "FF": "#ede0f7", "PA": "#e5e7eb"}
F = "DejaVu Sans"

def pk_cols(t): return set(fis.T[t]["pk"])
def fk_cols(t):
    s = set()
    for f in fis.T[t]["fk"]: s |= set(f[1])
    return s
def uq_cols(t):
    s = set()
    for u in fis.T[t]["uq"]: s |= set(u[1])
    return s

def tipo_tam(tp):
    m = re.match(r"([A-Z]+(?: UNSIGNED)?)(?:\(([^)]*)\))?( UNSIGNED)?", tp)
    base = m.group(1) + (m.group(3) or "")
    return base, (m.group(2) or "—")

def node(t, compact=False):
    d = fis.T[t]
    pk, fk, uq = pk_cols(t), fk_cols(t), uq_cols(t)
    rows = [f'<TR><TD COLSPAN="3" BGCOLOR="{COL[MOD[t]]}"><B>{t}</B></TD></TR>']
    for c in d["cols"]:
        marks = []
        if c["nome"] in pk: marks.append("PK")
        if c["nome"] in fk: marks.append("FK")
        if c["nome"] in uq and c["nome"] not in pk: marks.append("UQ")
        nm = html.escape(c["nome"])
        if c["nome"] in pk: nm = f"<U>{nm}</U>"
        if compact and not marks: continue
        nul = "" if not c["nulo"] else " NULL"
        rows.append(f'<TR><TD PORT="{c["nome"]}" ALIGN="LEFT">{nm}</TD><TD ALIGN="LEFT"><FONT POINT-SIZE="8">{html.escape(c["tipo"])}{nul}</FONT></TD>' +
                    (f'<TD ALIGN="LEFT"><FONT POINT-SIZE="8"><B>{",".join(marks)}</B></FONT></TD></TR>' if marks else '<TD> </TD></TR>'))
    lbl = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">' + "".join(rows) + '</TABLE>>'
    return f'"{t}" [shape=plain label={lbl}];'

def edges(tabs, ghost):
    out = []
    for t in tabs:
        for (n, cols, ref, rcols, _) in fis.T[t]["fk"]:
            if ref not in tabs and ref not in ghost: continue
            # cardinalidade lógica: lado referenciado = 1; lado da FK = N (ou 0..1 se UNIQUE)
            obrig = all(not [c for c in fis.T[t]["cols"] if c["nome"] == x][0]["nulo"] for x in cols)
            unico = any(set(u[1]) == set(cols) for u in fis.T[t]["uq"])
            head = "teetee" if obrig else "teeodot"
            tail = ("teeodot" if not unico else "teeodot") if unico else "crowodot"
            out.append(f'"{t}":"{cols[0]}" -> "{ref}":"{rcols[0]}" [arrowhead={head} arrowtail={tail} dir=both color="#4b5563"];')
    return out

def render(name, tabs, title, compact=False, rankdir="LR", dpi=130):
    ghost = set()
    for t in tabs:
        for f in fis.T[t]["fk"]:
            if f[2] not in tabs: ghost.add(f[2])
    L = ["digraph G {", f'graph [rankdir={rankdir} fontname="{F}" fontsize=16 labelloc=t label="{title}" nodesep=0.3 ranksep=0.7 pad=0.3 splines=true];',
         f'node [fontname="{F}" fontsize=9]; edge [fontname="{F}" arrowsize=0.8];']
    for t in tabs: L.append(node(t, compact))
    for g in sorted(ghost):
        L.append(f'"{g}" [shape=box style="rounded,dashed" color="#6b7280" fontcolor="#374151" label="{g}"];')
    L += edges(tabs, ghost)
    L.append("}")
    p = os.path.join(FIG, name + ".dot"); open(p, "w").write("\n".join(L))
    subprocess.run(["dot", "-Tpng", f"-Gdpi={dpi}", p, "-o", os.path.join(FIG, name + ".png")], check=True)
    subprocess.run(["dot", "-Tsvg", p, "-o", os.path.join(FIG, name + ".svg")], check=True)

def diagramas():
    for m, nome in spec.MODULES.items():
        tabs = [t for t in fis.ORDER if MOD[t] == m]
        render(f"logico_{m}", tabs, f"Modelo lógico — {nome}", rankdir="LR")
    render("logico_geral", list(fis.ORDER), "Modelo lógico relacional — visão geral (só PK, FK e UNIQUE)", compact=True, dpi=110)

# ------------------------------------------------------------------ dicionário
def dicionario_linhas():
    out = []
    for t in fis.ORDER:
        d = fis.T[t]
        pk, fk, uq = pk_cols(t), fk_cols(t), uq_cols(t)
        for c in d["cols"]:
            tp, tam = tipo_tam(c["tipo"])
            ref = [f"{f[2]}({f[3][f[1].index(c['nome'])]})" for f in d["fk"] if c["nome"] in f[1]]
            uqs = [u[0] for u in d["uq"] if c["nome"] in u[1]]
            cks = [k[0] for k in d["ck"] if re.search(r"\b" + c["nome"] + r"\b", k[1])]
            regra = c["regra"]
            restr = []
            if cks: restr.append("CHECK: " + ", ".join(cks))
            if uqs: restr.append("UNIQUE: " + ", ".join(uqs))
            if c["ai"]: restr.append("AUTO_INCREMENT")
            out.append(dict(tabela=t, atributo=c["nome"], descricao=c["desc"], tipo=tp, tamanho=tam,
                            pk="Sim" if c["nome"] in pk else "Não",
                            fk=("Sim → " + "; ".join(ref)) if ref else "Não",
                            nulo="Permitido" if c["nulo"] else "Não permitido",
                            unique=("Sim" + (" (composta)" if any(len(u[1]) > 1 for u in d["uq"] if c["nome"] in u[1]) else "")) if uqs else ("Sim (PK)" if c["nome"] in pk and len(d["pk"]) == 1 else "Não"),
                            default=(c["default"] or "—").strip("()'"),
                            regra=("; ".join(x for x in [regra] + restr if x)) or "—"))
    return out

def dicionario_md(caminho, caminho_csv):
    linhas = dicionario_linhas()
    md = ["# Dicionário de dados — banco implementado (`mercado_boturussu`)", "",
          "Gerado a partir de `ferramentas/gerador_massa/fis.py`, a mesma fonte que gera `sql/ddl/02_tabelas.sql`. ",
          "A conferência automática contra o banco criado está em `evidencias/08_conferencia_dicionario_x_banco.md`.", ""]
    for t in fis.ORDER:
        d = fis.T[t]
        md += [f"## {t}", "", f"*{d['desc']}* — origem: {d['origem']}.", "",
               "| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for l in [x for x in linhas if x["tabela"] == t]:
            md.append("| " + " | ".join(str(l[k]).replace("|", "/") for k in
                      ("atributo", "descricao", "tipo", "tamanho", "pk", "fk", "nulo", "unique", "default", "regra")) + " |")
        md.append("")
    md += views_md()
    open(caminho, "w", encoding="utf-8").write("\n".join(md))
    with open(caminho_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(linhas)
    return linhas

def views_info():
    """Lê 03_views.sql: o comentário que antecede cada CREATE VIEW diz quais atributos derivados ela implementa."""
    txt = open(os.path.join(ROOT, "sql_src", "03_views.sql"), encoding="utf-8").read()
    out = []
    for m in re.finditer(r"((?:-- [^\n]*\n)+)-- -+\nCREATE VIEW (\w+)", txt):
        com = " ".join(l[3:].strip() for l in m.group(1).strip().split("\n") if not l.startswith("-- ---"))
        out.append((m.group(2), com))
    r = subprocess.run(["mysql", "-uroot", "-N", "-B", "-e",
        "SELECT table_name, GROUP_CONCAT(column_name ORDER BY ordinal_position SEPARATOR ', ') FROM information_schema.columns "
        "WHERE table_schema='mercado_boturussu' AND table_name LIKE 'vw\\_%' GROUP BY table_name"], capture_output=True, text=True, check=True)
    cols = dict(l.split("\t") for l in r.stdout.strip().split("\n"))
    return [(v, c, cols.get(v, "")) for v, c in out]

def views_md():
    md = ["## Views — atributos derivados (não gravados)", "",
          "Os atributos marcados como derivados no DER não são colunas de tabela: são calculados pelas views abaixo",
          "(`sql/ddl/03_views.sql`). Assim nenhum valor calculável fica gravado em duplicidade (3FN).", "",
          "| View | O que calcula (atributos derivados do DER) | Colunas |", "|---|---|---|"]
    for v, c, cs in views_info():
        md.append(f"| {v} | {c.replace('|', '/')} | {cs} |")
    return md + [""]

def confere_banco(caminho):
    q = ("SELECT table_name, column_name, column_type, is_nullable, column_default, column_key, extra "
         "FROM information_schema.columns WHERE table_schema='mercado_boturussu' AND table_name IN (%s) ORDER BY table_name, ordinal_position"
         % ",".join(f"'{t}'" for t in fis.T))
    r = subprocess.run(["mysql", "-uroot", "--default-character-set=utf8mb4", "-N", "-B", "-e", q], capture_output=True, text=True, check=True)
    banco = {}
    for ln in r.stdout.strip().split("\n"):
        t, c, ct, nul, dfl, key, extra = (ln.split("\t") + [""] * 7)[:7]
        banco[(t, c)] = dict(tipo=ct, nulo=(nul == "YES"), default=dfl, extra=extra)
    divs = []
    norm = lambda s: s.lower().replace("boolean", "tinyint(1)").replace("int unsigned", "int unsigned")
    for t in fis.ORDER:
        for c in fis.T[t]["cols"]:
            b = banco.get((t, c["nome"]))
            if not b: divs.append((t, c["nome"], "coluna ausente no banco")); continue
            esperado = norm(c["tipo"])
            if b["tipo"].lower() != esperado:
                divs.append((t, c["nome"], f"tipo {b['tipo']} ≠ {c['tipo']}"))
            if b["nulo"] != c["nulo"]:
                divs.append((t, c["nome"], "nulidade diferente"))
            if c["ai"] and "auto_increment" not in b["extra"]:
                divs.append((t, c["nome"], "AUTO_INCREMENT ausente"))
    extras = [k for k in banco if not any(c["nome"] == k[1] for c in fis.T[k[0]]["cols"])]
    q2 = ("SELECT table_name, constraint_type, COUNT(*) FROM information_schema.table_constraints "
          "WHERE table_schema='mercado_boturussu' GROUP BY table_name, constraint_type")
    r2 = subprocess.run(["mysql", "-uroot", "-N", "-B", "-e", q2], capture_output=True, text=True, check=True)
    cons = {}
    for ln in r2.stdout.strip().split("\n"):
        t, ty, n = ln.split("\t"); cons[(t, ty)] = int(n)
    cdiv = []
    for t, d in fis.T.items():
        for ty, n in (("PRIMARY KEY", 1), ("FOREIGN KEY", len(d["fk"])), ("UNIQUE", len(d["uq"])), ("CHECK", len(d["ck"]))):
            if cons.get((t, ty), 0) != n: cdiv.append((t, ty, cons.get((t, ty), 0), n))
    md = ["# Evidência — conferência automática: dicionário de dados × banco implementado", "",
          "Compara cada coluna documentada (tipo, nulidade, AUTO_INCREMENT) e a quantidade de PK, FK, UNIQUE e CHECK de cada tabela",
          "com o `information_schema` do banco criado pelo script.", "",
          f"- Tabelas conferidas: {len(fis.T)}",
          f"- Colunas conferidas: {sum(len(d['cols']) for d in fis.T.values())}",
          f"- Restrições conferidas: {sum(1 + len(d['fk']) + len(d['uq']) + len(d['ck']) for d in fis.T.values())}",
          f"- Divergências de coluna: **{len(divs)}**", f"- Colunas no banco sem documentação: **{len(extras)}**",
          f"- Divergências de restrição: **{len(cdiv)}**", ""]
    for x in divs: md.append(f"- {x}")
    for x in cdiv: md.append(f"- {x}")
    if not (divs or extras or cdiv):
        md.append("Resultado: **dicionário e banco idênticos**.")
    open(caminho, "w", encoding="utf-8").write("\n".join(md) + "\n")
    return len(divs) + len(extras) + len(cdiv)

if __name__ == "__main__":
    diagramas()
    os.makedirs(os.path.join(ROOT, "tmp"), exist_ok=True)
    dicionario_md(os.path.join(ROOT, "tmp", "dicionario-dados.md"), os.path.join(ROOT, "tmp", "dicionario-dados.csv"))
    print("divergencias:", confere_banco(os.path.join(ROOT, "tmp", "conferencia.md")))
