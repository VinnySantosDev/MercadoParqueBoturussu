# -*- coding: utf-8 -*-
"""Grava sql/dados/04_massa_dados.sql a partir da simulação."""
import sys, os, datetime as dt
from decimal import Decimal
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import simula as S
import fis

def lit(v):
    if v is None: return "NULL"
    if isinstance(v, bool): return "TRUE" if v else "FALSE"
    if isinstance(v, (int, Decimal)): return str(v)
    if isinstance(v, dt.datetime): return "'" + v.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(v, dt.date): return "'" + v.isoformat() + "'"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"

def escreve(caminho):
    out = ["-- =====================================================================",
           "-- 04_massa_dados.sql — INSERT da massa de dados de teste",
           "-- Gerado por gen/simula.py (semente 2026): simulação de 30 dias de operação",
           "-- (01/09/2026 a 30/09/2026). Data de referência das consultas: 01/10/2026.",
           "-- Todos os nomes, CPFs, CNPJs, códigos de barras e chaves de NF-e são FICTÍCIOS.",
           "-- Valores derivados (saldos, totais, situações calculadas) NÃO são gravados:",
           "-- são calculados pelas views de 03_views.sql.",
           "-- =====================================================================",
           "USE mercado_boturussu;", "SET NAMES utf8mb4;", "START TRANSACTION;", ""]
    total = 0
    for t in fis.ORDER:
        linhas = S.rows.get(t, [])
        if not linhas: continue
        cols = [c["nome"] for c in fis.T[t]["cols"]]
        for r in linhas:
            assert set(r) == set(cols), (t, set(r) ^ set(cols))
        out.append(f"-- {t}: {len(linhas)} registros")
        for i in range(0, len(linhas), 250):
            bloco = linhas[i:i + 250]
            vals = ",\n".join("(" + ", ".join(lit(r[c]) for c in cols) + ")" for r in bloco)
            out.append(f"INSERT INTO {t} ({', '.join(cols)}) VALUES\n{vals};")
        out.append("")
        total += len(linhas)
    out.append("COMMIT;")
    out.append(f"-- total de registros inseridos: {total}")
    open(caminho, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return total

if __name__ == "__main__":
    n = escreve(sys.argv[1])
    print("registros:", n)
