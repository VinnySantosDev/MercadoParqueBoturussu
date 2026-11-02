# -*- coding: utf-8 -*-
"""Executa um arquivo de consultas bloco a bloco (G01, G02… / A01, A02…) e grava a evidência
com o título de cada consulta, o número de linhas e o resultado."""
import re, subprocess, sys, json

def blocos(path):
    txt = open(path, encoding="utf-8").read()
    pre = "\n".join(l for l in txt.split("\n") if l.startswith(("SET @", "USE ", "SET NAMES")))
    partes = re.split(r"\n-- -{20,}\n(?=-- [AG]\d\d )", txt)
    out = []
    for p in partes[1:]:
        linhas = p.split("\n")
        tit = linhas[0][3:].strip()
        coment = [l[3:] for l in linhas[1:] if l.startswith("-- ") and not l.startswith("-- ---")]
        sql = "\n".join(l for l in linhas if not l.startswith("--")).strip()
        out.append((tit, coment, sql))
    return pre, out

def roda(path, saida, json_out=None):
    pre, bs = blocos(path)
    res = []
    with open(saida, "w", encoding="utf-8") as o:
        o.write(f"Resultado da execução de {path.split('/')[-1]} — data de referência 01/10/2026\n\n")
        for (tit, com, sql) in bs:
            r = subprocess.run(["mysql", "-uroot", "--default-character-set=utf8mb4", "-t", "mercado_boturussu", "-e",
                                pre + "\n" + sql], capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(f"erro em {tit}: {r.stderr}")
            n = max(0, len([l for l in r.stdout.split("\n") if l.startswith("|")]) - 1)
            o.write("=" * 100 + f"\n{tit}\n" + "\n".join(com) + f"\nLinhas retornadas: {n}"
                    + (" (nenhuma ocorrência: regra respeitada)" if n == 0 and tit.startswith("A") else "") + "\n\n")
            o.write(r.stdout + "\n")
            r2 = subprocess.run(["mysql", "-uroot", "--default-character-set=utf8mb4", "-B", "mercado_boturussu", "-e",
                                 pre + "\n" + sql], capture_output=True, text=True)
            rows = [l.split("\t") for l in r2.stdout.strip().split("\n") if l]
            res.append(dict(titulo=tit, comentario=com, sql=sql, linhas=n, cab=rows[0] if rows else [], dados=rows[1:]))
    if json_out:
        json.dump(res, open(json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res

if __name__ == "__main__":
    roda(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
