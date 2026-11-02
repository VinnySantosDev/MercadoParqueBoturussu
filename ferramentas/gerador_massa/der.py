# -*- coding: utf-8 -*-
import subprocess, html, os, sys
import spec

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fig")
os.makedirs(OUT, exist_ok=True)

COL = {"PE": "#dbeafe", "CF": "#fde2c8", "VC": "#d9f2e3", "FF": "#ede0f7", "PA": "#e5e7eb"}
FONT = "DejaVu Sans"

def attr_line(a):
    nome, _, cl, _ = a
    esc = html.escape(nome)
    if cl.startswith("PK"):
        tag = " (PK, FK)" if "FK" in cl else " (PK)"
        return f'<U>{esc}</U>{tag}'
    if cl == "Derivado":
        return f'<I>/{esc}</I>'
    if cl.startswith("Multivalorado"):
        return f'● {{{esc}}}'
    if cl.startswith("Composto"):
        mark = "○" if "opcional" in cl else "●"
        return f'{mark} {esc} (…)'
    opt = "opcional" in cl
    mark = "○" if opt else "●"
    suf = ""
    if cl.startswith("FK"):
        suf = " (FK)"
    elif cl.startswith("AK"):
        suf = " (AK)"
    return f'{mark} {esc}{suf}'

def ent_node(e, with_attrs=True, ghost=False):
    color = COL[e["mod"]]
    tipo = e["tipo"]
    sub = ""
    if tipo == "Associativa":
        sub = '<BR/><FONT POINT-SIZE="8">«entidade associativa»</FONT>'
    elif tipo == "Fraca":
        sub = '<BR/><FONT POINT-SIZE="8">«entidade fraca»</FONT>'
    border = 2 if tipo == "Fraca" else 1
    if ghost:
        return (f'"{e["name"]}" [shape=box style="rounded,dashed" color="#6b7280" fontcolor="#374151" '
                f'fontsize=9 label="{e["name"]}"];')
    rows = [f'<TR><TD BGCOLOR="{color}"><B>{e["name"]}</B>{sub}</TD></TR>']
    if with_attrs:
        body = "<BR ALIGN=\"LEFT\"/>".join(attr_line(a) for a in e["attrs"]) + '<BR ALIGN="LEFT"/>'
        rows.append(f'<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="8">{body}</FONT></TD></TR>')
    if tipo == "Fraca":
        lbl = '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="2" CELLPADDING="0"><TR><TD><TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">%s</TABLE></TD></TR></TABLE>>' % "".join(rows)
    else:
        lbl = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">%s</TABLE>>' % "".join(rows)
    return f'"{e["name"]}" [shape=plain label={lbl}];'

def rel_nodes(r):
    rid = r["id"]
    per = 2 if r["nn"] else 1
    lines = [f'"{rid}" [shape=diamond style=filled fillcolor="#fff7e0" peripheries={per} fontsize=8 '
             f'label="{html.escape(r["verbo"])}\\n{rid}" margin="0.02,0.02"];']
    if r["a"] == r["b"]:
        lines.append(f'"{r["a"]}" -> "{rid}" [dir=none taillabel="{r["ca"]}\\nreposto" fontcolor="#b91c1c" labelfontsize=8 labelfontcolor="#b91c1c" labeldistance=1.8 labelangle=30];')
        lines.append(f'"{rid}" -> "{r["b"]}" [dir=none headlabel="{r["cb"]}\\nreposição" labelfontsize=8 labelfontcolor="#b91c1c" labeldistance=1.8 labelangle=30];')
    else:
        lines.append(f'"{r["a"]}" -> "{rid}" [dir=none taillabel="{r["ca"]}" labelfontsize=8 labelfontcolor="#b91c1c" labeldistance=1.8 labelangle=30];')
        lines.append(f'"{rid}" -> "{r["b"]}" [dir=none headlabel="{r["cb"]}" labelfontsize=8 labelfontcolor="#b91c1c" labeldistance=1.8 labelangle=30];')
    if r["attrs"]:
        nid = rid + "_attrs"
        lines.append(f'"{nid}" [shape=note style=filled fillcolor="#fefce8" fontsize=8 label="atributos de {html.escape(r["verbo"])}\\n{html.escape(r["attrs"])}"];')
        lines.append(f'"{rid}" -> "{nid}" [dir=none style=dashed];')
    return lines

def header(title, rankdir="TB", extra=""):
    return [ "graph G {" if False else "digraph G {",
            f'graph [rankdir={rankdir} fontname="{FONT}" fontsize=16 labelloc=t label="{title}" nodesep=0.35 ranksep=0.45 pad=0.3 splines=true {extra}];',
            f'node [fontname="{FONT}"]; edge [fontname="{FONT}" color="#374151" arrowhead=none];' ]

def render(name, lines, fmt="png", dpi=170):
    dot = os.path.join(OUT, name + ".dot")
    with open(dot, "w") as f:
        f.write("\n".join(lines + ["}"]))
    subprocess.run(["dot", f"-T{fmt}", f"-Gdpi={dpi}", dot, "-o", os.path.join(OUT, f"{name}.{fmt}")], check=True)

def module_der(mod, title):
    ents = [e for e in spec.E.values() if e["mod"] == mod]
    names = {e["name"] for e in ents}
    rels = [r for r in spec.R if r["mod"] == mod or (r["a"] in names and r["b"] in names)]
    if mod == "PA":
        rels = [r for r in spec.R if r["mod"] == "PA"]
    ghosts = set()
    for r in rels:
        for x in (r["a"], r["b"]):
            if x not in names:
                ghosts.add(x)
    L = header(title, rankdir="LR" if mod == "PA" else "TB")
    for e in ents:
        L.append(ent_node(e, with_attrs=True))
    for g in sorted(ghosts):
        L.append(ent_node(spec.E[g], ghost=True))
    for r in rels:
        L += rel_nodes(r)
    render(f"der_{mod}", L, dpi=150)

def overview(with_attrs=False, name="der_geral", title="DER revisado — visão geral (notação Chen)", skip_pa=True):
    L = header(title, rankdir="LR", extra='concentrate=false')
    for mod in spec.MODULES:
        L.append(f'subgraph cluster_{mod} {{ label="{spec.MODULES[mod]}" style="rounded,dashed" color="#9ca3af" fontsize=12;')
        for e in spec.E.values():
            if e["mod"] == mod:
                L.append(ent_node(e, with_attrs=with_attrs))
        L.append("}")
    for r in spec.R:
        if skip_pa and r["mod"] == "PA" and r["id"] != "R52":
            continue
        L += rel_nodes(r)
    render(name, L, dpi=110 if with_attrs else 140)

def legend():
    L = header("Legenda do DER", rankdir="LR")
    L.append('leg [shape=plain label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5">'
             '<TR><TD><B>Símbolo</B></TD><TD><B>Significado</B></TD></TR>'
             '<TR><TD><U>nome</U> (PK)</TD><TD ALIGN="LEFT">Chave primária (sublinhada)</TD></TR>'
             '<TR><TD>● nome (FK)</TD><TD ALIGN="LEFT">Chave estrangeira</TD></TR>'
             '<TR><TD>● nome (AK)</TD><TD ALIGN="LEFT">Chave alternativa: candidata natural única, mantida como regra de unicidade</TD></TR>'
             '<TR><TD>● / ○</TD><TD ALIGN="LEFT">Atributo obrigatório / opcional</TD></TR>'
             '<TR><TD>nome (…)  {nome}  <I>/nome</I></TD><TD ALIGN="LEFT">Composto / multivalorado / derivado</TD></TR>'
             '<TR><TD>Retângulo de borda dupla</TD><TD ALIGN="LEFT">Entidade fraca (identificada pela entidade dona + discriminador)</TD></TR>'
             '<TR><TD>«entidade associativa»</TD><TD ALIGN="LEFT">Relacionamento N:N promovido a entidade</TD></TR>'
             '<TR><TD>Losango / losango duplo</TD><TD ALIGN="LEFT">Relacionamento / relacionamento N:N</TD></TR>'
             '<TR><TD>(min,max) em vermelho</TD><TD ALIGN="LEFT">Cardinalidade, junto da entidade a que se refere (convenção do manual)</TD></TR>'
             '<TR><TD>Caixa tracejada</TD><TD ALIGN="LEFT">Entidade de outro módulo, exibida só para contexto</TD></TR>'
             '</TABLE>>];')
    render("der_legenda", L, dpi=150)

if __name__ == "__main__":
    for mod, t in spec.MODULES.items():
        module_der(mod, f"DER — módulo {t}")
    overview()
    overview(with_attrs=True, name="der_completo", title="DER revisado completo, com atributos")
    legend()
    print("ok")
