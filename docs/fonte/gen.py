import subprocess, os, html
from model import E, R, MODULES

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "der")
os.makedirs(OUT, exist_ok=True)
FONT = "DejaVu Sans"
FONTC = "DejaVu Sans Condensed"
INK = "#1F2328"
MUTED = "#6B7280"

def attr_row(name, kind):
    n = html.escape(name)
    if kind == "pk":   s = f"<u>{n}</u> (PK)"
    elif kind == "pkfk": s = f"<u>{n}</u> (PK, FK)"
    elif kind == "fk": s = f"● {n} (FK)"
    elif kind == "fko": s = f"○ {n} (FK)"
    elif kind == "req": s = f"● {n}"
    elif kind == "opt": s = f"○ {n}"
    elif kind == "der": s = f"<i>/{n}</i>"
    elif kind == "comp": s = f"○ {n} (logradouro, numero,<br align='left'/>      complemento, bairro)"
    elif kind == "mv": s = f"● {{{n}}} (nome, telefone,<br align='left'/>      whatsapp)"
    return f'<tr><td align="left" balign="left">{s}</td></tr>'

def ent_node(name, mode):
    """mode: full | name | ctx"""
    mod = E[name]["mod"]
    color = MODULES[mod][1]
    nid = name
    if mode == "ctx":
        return (f'  {nid} [shape=box style="dashed,rounded" color="{MUTED}" fontcolor="{MUTED}" '
                f'fontname="{FONT} Bold" fontsize=12 label="{name}" margin="0.15,0.06"];')
    if mode == "name":
        return (f'  {nid} [shape=box style="filled" fillcolor="{color}" color="{INK}" penwidth=1.3 '
                f'fontname="{FONT} Bold" fontsize=13 label="{name}" margin="0.18,0.08"];')
    rows = "".join(attr_row(a, k) for a, k in E[name]["attrs"])
    lab = (f'<<table border="1" cellborder="0" cellspacing="0" cellpadding="3" color="{INK}">'
           f'<tr><td bgcolor="{color}" cellpadding="5"><b>{name}</b></td></tr>'
           f'<hr/>'
           f'{rows}</table>>')
    return f'  {nid} [shape=plain fontname="{FONT}" fontsize=10.5 label={lab}];'

def rel_nodes(r, notes=True):
    rid, a, ca, verb, b, cb, nn = r
    out = []
    per = 2 if nn else 1
    out.append(f'  {rid} [shape=diamond style=filled fillcolor="#FFFFFF" color="{INK}" '
               f'peripheries={per} fontname="{FONTC}" fontsize=10 label="{verb}" '
               f'margin="0.02,0.02" width=1.1 height=0.55];')
    if nn and notes:
        lines = [f"<b>atributos de {verb}</b>"] + [html.escape(x) for x in nn]
        body = "<br/>".join(lines)
        out.append(f'  {rid}_n [shape=note style=filled fillcolor="#FFFBEA" color="{MUTED}" '
                   f'fontname="{FONTC}" fontsize=9.5 label=<{body}>];')
        out.append(f'  {rid} -> {rid}_n [style=dashed color="{MUTED}" arrowhead=none weight=5 minlen=1];')
    return out

def rel_edges(r):
    rid, a, ca, verb, b, cb, nn = r
    st = f'dir=none color="{INK}" fontname="{FONT}" fontsize=10 fontcolor="#B42318"'
    return [f'  {a} -> {rid} [{st} label=" {ca} "];',
            f'  {rid} -> {b} [{st} label=" {cb} "];']

def build(fname, full, ctx=(), rels=None, mode="full", rankdir="TB", title=None,
          extra="", dpi=200, legend=False, clusters=False, notes=True, engine="dot"):
    rels = rels if rels is not None else R
    L = ["digraph G {",
         f'  graph [rankdir={rankdir} bgcolor="white" pad="0.4" nodesep=0.45 ranksep=0.55 '
         f'fontname="{FONT}" splines=true dpi={dpi} {extra}];',
         f'  node [fontname="{FONT}" color="{INK}" fontcolor="{INK}"];']
    if title:
        L.append(f'  labelloc=t; fontsize=20; label=<<b>{title}</b><br/> >;')
    if clusters:
        for mk, (mname, col) in MODULES.items():
            L.append(f'  subgraph cluster_{mk} {{ label=<<b>{mname}</b>> fontsize=14 '
                     f'style="rounded,dashed" color="{MUTED}" fontcolor="{MUTED}";')
            for n in full:
                if E[n]["mod"] == mk:
                    L.append(ent_node(n, mode))
            L.append("  }")
    else:
        for n in full:
            L.append(ent_node(n, mode))
    for n in ctx:
        L.append(ent_node(n, "ctx"))
    for r in rels:
        L += rel_nodes(r, notes)
    for r in rels:
        L += rel_edges(r)
    if legend:
        L.append(legend_node())
    if mode == "name":
        L.append(module_key())
    L.append("}")
    dot = "\n".join(L)
    open(f"{OUT}/{fname}.dot", "w").write(dot)
    subprocess.run([engine, "-Tpng", f"{OUT}/{fname}.dot", "-o", f"{OUT}/{fname}.png"], check=True)
    subprocess.run([engine, "-Tsvg", f"{OUT}/{fname}.dot", "-o", f"{OUT}/{fname}.svg"], check=True)
    return f"{OUT}/{fname}.png"

def legend_node():
    rows = [
        ("<u>nome</u> (PK)", "chave primária"),
        ("<u>nome</u> (PK, FK)", "compõe a PK e referencia outra entidade"),
        ("● nome (FK) / ○ nome (FK)", "chave estrangeira obrigatória / opcional"),
        ("● nome / ○ nome", "atributo obrigatório / opcional"),
        ("nome (…)", "composto"),
        ("{nome}", "multivalorado"),
        ("<i>/nome</i>", "derivado"),
        ("losango de borda dupla", "relacionamento N:N (atributos na nota tracejada)"),
        ("(min,max)", "cardinalidade da entidade daquele lado"),
    ]
    tr = "".join(f'<tr><td align="left">{a}</td><td align="left"><font color="{MUTED}">{b}</font></td></tr>'
                 for a, b in rows)
    return (f'  legenda [shape=plain fontname="{FONT}" fontsize=10 label=<<table border="1" '
            f'cellborder="0" cellspacing="0" cellpadding="3" color="{MUTED}">'
            f'<tr><td colspan="2" bgcolor="#F3F4F6"><b>Legenda (notação Chen)</b></td></tr>{tr}</table>>];')

def module(mk):
    full = [n for n in E if E[n]["mod"] == mk]
    rels = [r for r in R if r[1] in full or r[4] in full]
    ctx = []
    for r in rels:
        for x in (r[1], r[4]):
            if x not in full and x not in ctx:
                ctx.append(x)
    return full, ctx, rels

def module_key():
    tr = "".join(f'<td bgcolor="{c}" border="1" cellpadding="6">{n}</td>' for n, c in MODULES.values())
    return (f'  modulos [shape=plain fontname="{FONT}" fontsize=12 label=<<table border="0" cellspacing="6">'
            f'<tr><td><b>Módulos:</b></td>{tr}</tr></table>>];')
