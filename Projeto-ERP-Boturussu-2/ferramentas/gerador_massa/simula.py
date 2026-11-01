# -*- coding: utf-8 -*-
"""Gerador da massa de dados: simula 30 dias de operação do mercado
(01 a 30/09/2026) aplicando as regras de negócio do modelo, e grava os
INSERTs em sql/dados/04_massa_dados.sql. Semente fixa: resultado reprodutível.

O gerador NÃO grava valores derivados (saldos, totais, situações calculadas):
eles são calculados pelas views, exatamente como no banco real."""
import random, datetime as dt, sys, os
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import cadastros as K

R = random.Random(2026)
C2 = D("0.01"); C3 = D("0.001"); C4 = D("0.0001")
def m2(x): return D(x).quantize(C2, ROUND_HALF_UP)
def q3(x): return D(x).quantize(C3, ROUND_HALF_UP)
def c4(x): return D(x).quantize(C4, ROUND_HALF_UP)

INICIO = dt.date(2026, 9, 1)
FIM = dt.date(2026, 9, 30)
DATA_REF = dt.date(2026, 10, 1)

rows = defaultdict(list)
seq = defaultdict(int)
def nid(t):
    seq[t] += 1
    return seq[t]
def ts(d, h, m=0, s=0):
    return dt.datetime(d.year, d.month, d.day, h, m, s)

# ------------------------------------------------------------------ cadastros
FUNC_PERM = K.PERM_FUNC
def tem(func, perm): return perm in FUNC_PERM[func]

for f in K.FUNCIONARIOS:
    rows["funcionario"].append(dict(id_funcionario=f[0], cpf=K.cpf(f[2]), login=f[3], nome=f[1], telefone=f[6],
                                    funcao_principal=f[4], data_admissao=f[5], ativo=True))
for p in K.PERMISSOES:
    rows["permissao"].append(dict(codigo_permissao=p[0], descricao=p[1]))
for fid, perms in K.PERM_FUNC.items():
    adm = [f for f in K.FUNCIONARIOS if f[0] == fid][0][5]
    for p in perms:
        rows["funcionario_permissao"].append(dict(id_funcionario=fid, codigo_permissao=p, data_concessao="2026-08-25", data_revogacao=None))

for c in K.CATEGORIAS:
    rows["categoria"].append(dict(codigo_categoria=c[0], nome=c[1], controle_validade_rigoroso=c[2], dias_alerta_validade_padrao=c[3]))

PROD = {}
EMB = {}            # id_embalagem -> dict
EMB_DE = defaultdict(list)
preco = {}          # id_embalagem -> preço vigente (Decimal)
ean_seq = 100
plu_seq = 1001
int_seq = 1
for p in K.PRODUTOS:
    (pid, cat, nome, marca, base, peso, ctrl, vida, custo, margem, emin, pop, forns, embs) = p
    PROD[pid] = dict(id=pid, cat=cat, nome=nome, base=base, peso=peso, ctrl=ctrl, vida=vida, custo=D(str(custo)),
                     emin=D(str(emin)), pop=pop, forns=forns)
    rows["produto"].append(dict(id_produto=pid, codigo_categoria=cat, nome_produto=nome, marca=marca, unidade_base=base,
                                vendido_por_peso=peso, controla_validade=ctrl,
                                dias_alerta_validade=(3 if pid in (24,) else None),
                                estoque_minimo=q3(emin), margem_referencia=m2(margem), ativo=True))
    for (desc, fator, tcod, pr) in embs:
        eid = nid("embalagem")
        cb = cbal = None
        if tcod == "EAN":
            cb = K.ean13("789" + f"{4500000 + ean_seq:09d}"); ean_seq += 7
        elif tcod == "INT":
            cb = K.ean13("2" + f"{int_seq:011d}"); int_seq += 1
        else:
            cbal = str(plu_seq); plu_seq += 1
        e = dict(id_embalagem=eid, id_produto=pid, codigo_barras=cb, codigo_balanca=cbal, descricao=desc,
                 fator_conversao=q3(fator), preco_venda=m2(pr), ativa=True)
        rows["embalagem"].append(e)
        EMB[eid] = dict(id=eid, prod=pid, fator=D(str(fator)), desc=desc)
        EMB_DE[pid].append(eid)
        preco[eid] = m2(pr)

for f in K.FORNECEDORES:
    rows["fornecedor"].append(dict(id_fornecedor=f[0], tipo_documento=f[1], documento=K.doc_fornecedor(f),
                                   razao_social=f[3], nome_fantasia=f[4], canal_pedido=f[5],
                                   condicao_pagamento_padrao=f[6], ativo=True))
    for i, (nome, tel, wpp) in enumerate(f[7], 1):
        rows["contato_fornecedor"].append(dict(id_fornecedor=f[0], numero_contato=i, nome=nome, telefone=tel, usa_whatsapp=wpp))
FORN = {f[0]: f for f in K.FORNECEDORES}
for pid, p in PROD.items():
    for fo in p["forns"]:
        rows["produto_fornecedor"].append(dict(id_fornecedor=fo, id_produto=pid,
                                               codigo_no_fornecedor=f"F{fo}-{pid:04d}", ativo=True))

for n in (1, 2):
    rows["caixa"].append(dict(numero_caixa=n, ativo=True))

CLI = {}
for c in K.CLIENTES:
    rows["cliente"].append(dict(id_cliente=c[0], cpf=(K.cpf(c[3]) if c[3] else None), nome=c[1], apelido=c[2], telefone=c[4],
                                logradouro=c[5], numero_endereco=c[6], complemento=c[7], bairro=c[8],
                                autorizado_fiado=c[9], limite_fiado=(m2(c[10]) if c[10] else None), data_cadastro=c[11]))
    CLI[c[0]] = dict(id=c[0], aut=c[9], lim=(D(str(c[10])) if c[10] else None), saldo=D("0"))

FORMAS = [("DIN", "Dinheiro", 0, "0", False, False), ("DEB", "Cartão de débito", 1, "1.49", False, True),
          ("CRE", "Cartão de crédito", 30, "3.19", False, True), ("PIX", "Pix", 0, "0", False, True),
          ("VALE", "Vale-alimentação", 30, "6.00", False, True), ("FIADO", "Fiado (caderno)", 0, "0", True, False)]
TAXA = {}
for f in FORMAS:
    rows["forma_pagamento"].append(dict(codigo_forma=f[0], descricao=f[1], prazo_credito_dias=f[2], taxa_percentual=D(f[3]),
                                        gera_divida=f[4], exige_conciliacao=f[5], ativa=True))
    TAXA[f[0]] = D(f[3])

BANCO, COFRE = 1, 2
rows["conta_financeira"] += [
    dict(id_conta_financeira=BANCO, nome="Banco Popular – conta PJ 12345-6", tipo="CONTA_BANCARIA", saldo_inicial=m2("9800.00"),
         data_saldo_inicial="2026-09-01", ativa=True),
    dict(id_conta_financeira=COFRE, nome="Cofre da administração", tipo="COFRE", saldo_inicial=m2("1200.00"),
         data_saldo_inicial="2026-09-01", ativa=True)]

def mov_fin(conta, data, natureza, origem, bruto, taxa=D("0"), doc=None, func=None):
    i = nid("movimento_financeiro")
    rows["movimento_financeiro"].append(dict(id_movimento_fin=i, id_conta_financeira=conta, id_funcionario=func,
                                             data_movimento=str(data), natureza=natureza, origem=origem,
                                             valor_bruto=m2(bruto), valor_taxa=m2(taxa), documento_referencia=doc))
    return i

# ------------------------------------------------------------------ estoque
LOTES = {}
def novo_lote(pid, origem, entrada, custo, validade=None, rec=None, item=None, reposto=None, cod=None, pend=False):
    i = nid("lote")
    LOTES[i] = dict(id=i, prod=pid, origem=origem, entrada=entrada, custo=c4(custo), val=validade, saldo=D("0"),
                    sit="DISPONIVEL", rec=rec, item=item, reposto=reposto, cod=cod, pend=pend, forn=None)
    return i

ENTRADAS = {"ENTRADA_RECEBIMENTO", "ENTRADA_INVENTARIO", "TROCA_FORNECEDOR", "DEVOLUCAO_CLIENTE", "AJUSTE_INVENTARIO_ENTRADA"}
def mov(lote, tipo, qtd, quando, func=None, venda=None, item=None, dev=None, motivo=None):
    qtd = q3(qtd)
    assert qtd > 0, (lote, tipo, qtd)
    L = LOTES[lote]
    L["saldo"] += qtd if tipo in ENTRADAS else -qtd
    assert L["saldo"] >= 0, (lote, tipo, qtd, L["saldo"])
    i = nid("movimentacao_estoque")
    rows["movimentacao_estoque"].append(dict(id_movimentacao=i, id_lote=lote, id_funcionario=func, id_venda=venda,
                                             numero_item=item, id_devolucao=dev, data_hora=quando, tipo=tipo,
                                             quantidade=qtd, motivo=motivo))
    return i

def lotes_vendaveis(pid, dia):
    ls = [L for L in LOTES.values() if L["prod"] == pid and L["sit"] == "DISPONIVEL" and L["saldo"] > 0
          and (L["val"] is None or L["val"] >= dia)]
    ls.sort(key=lambda L: (L["val"] or dt.date(2099, 1, 1), L["entrada"], L["id"]))
    return ls

def estoque(pid, dia):
    return sum((L["saldo"] for L in lotes_vendaveis(pid, dia)), D("0"))

consumo = defaultdict(lambda: defaultdict(D))   # pid -> dia -> qtd base vendida

# ------------------------------------------------------------------ implantação: inventário inicial (RN-41)
DIA0 = ts(INICIO, 6, 30)
for pid, p in PROD.items():
    perecivel = p["vida"] is not None and p["vida"] <= 10
    dias_estoque = R.uniform(2, 3.5) if perecivel else R.uniform(6, 11)
    qtd = D(str(p["pop"])) * D(str(round(dias_estoque, 2)))
    qtd = q3(qtd) if p["base"] == "KG" else D(int(qtd) + 1)
    partes = [qtd] if p["vida"] is None or p["vida"] < 30 or qtd < 6 else [q3(qtd * D("0.4")), qtd - q3(qtd * D("0.4"))]
    if p["base"] == "UN":
        partes = [D(int(x)) for x in partes]
        partes[-1] += qtd - sum(partes)
    for k, parte in enumerate(partes):
        if parte <= 0: continue
        val = None
        if p["ctrl"]:
            if p["vida"] <= 10:
                val = INICIO + dt.timedelta(days=max(2, int(p["vida"] * R.uniform(0.5, 0.9))))
            else:
                ini = 0.08 if k == 0 else 0.45
                val = INICIO + dt.timedelta(days=max(3, int(p["vida"] * R.uniform(ini, ini + 0.35))))
        if pid == 4 and k == 0:          # lentilha de giro lento vence durante o mês (vigilância de validade)
            val = dt.date(2026, 9, 18)
        if pid == 24 and k == 0:
            val = dt.date(2026, 9, 6)
        lid = novo_lote(pid, "INVENTARIO_INICIAL", DIA0, p["custo"], val)
        if pid == 27 and k == 0:          # falha de digitação na implantação: lote sem validade (auditoria A05)
            LOTES[lid]["val"] = None
        mov(lid, "ENTRADA_INVENTARIO", parte, DIA0, func=1, motivo="Carga inicial do estoque por contagem física (RN-41)")

# ------------------------------------------------------------------ preços
def muda_preco(eid, novo, func, quando, motivo):
    novo = m2(novo)
    hid = nid("historico_preco")
    rows["historico_preco"].append(dict(id_historico=hid, id_embalagem=eid, id_funcionario=func, data_hora=quando,
                                        preco_anterior=preco[eid], preco_novo=novo, motivo=motivo))
    preco[eid] = novo

EVENTOS_PRECO = [  # (data, hora, min, id_produto, índice embalagem, novo, func, motivo)
    (dt.date(2026, 9, 8), 9, 15, 8, 0, "23.90", 3, "REAJUSTE_FORNECEDOR"),
    (dt.date(2026, 9, 17), 10, 30, 23, 0, "6.29", 2, "REAJUSTE_FORNECEDOR"),
    (dt.date(2026, 9, 17), 8, 10, 14, 0, "1.99", 3, "REAJUSTE_FORNECEDOR"),   # erro de digitação (deveria ser 11,99)
    (dt.date(2026, 9, 17), 11, 40, 14, 0, "11.99", 2, "CORRECAO"),
    (dt.date(2026, 9, 22), 9, 0, 33, 0, "64.90", 1, "REAJUSTE_FORNECEDOR"),
    (dt.date(2026, 9, 26), 9, 30, 30, 0, "46.90", 1, "REAJUSTE_FORNECEDOR"),
]
custo_atual = {}   # (forn, pid) -> custo por unidade base
for pid, p in PROD.items():
    for fo in p["forns"]:
        custo_atual[(fo, pid)] = D(str(K.CUSTO_FORN.get((fo, pid), p["custo"])))
MUDA_CUSTO = {dt.date(2026, 9, 8): [((2, 8), "17.60")], dt.date(2026, 9, 16): [((3, 23), "4.69")],
              dt.date(2026, 9, 22): [((4, 33), "46.80")], dt.date(2026, 9, 25): [((4, 30), "33.40")]}

# ------------------------------------------------------------------ compras e recebimentos
AGENDA = {  # fornecedor -> (dias da semana do pedido 0=seg, prazo em dias, hora da entrega)
    1: ([0, 3], 1, 10), 2: ([1, 4], 1, 11), 3: ([0, 2, 4], 1, 9), 4: ([1, 3, 5], 1, 8),
    6: ([2, 5], 0, 14), 7: ([2], 1, 10),
}
VISITA_ANTONIO = [0, 3]          # produtor rural passa seg/qui e entrega na hora, sem pedido
pedidos_pendentes = []           # (data_entrega, id_pedido)
contas_geradas = []
num_nota = defaultdict(lambda: 1000)
nota_cnf = 10000000

def demanda(pid, dia):
    hist = [consumo[pid][dia - dt.timedelta(days=k)] for k in range(1, 8) if dia - dt.timedelta(days=k) >= INICIO]
    est = D(str(PROD[pid]["pop"]))
    if len(hist) >= 3:
        est = (sum(hist, D("0")) / len(hist)) * D("0.7") + est * D("0.3")
    return est

def qtd_compra(pid, fo, dia, ciclo):
    p = PROD[pid]
    if p["vida"] is not None and p["vida"] <= 10:      # perecível: comprar pouco e com frequência
        alvo = demanda(pid, dia) * D(str(ciclo + 1)) + p["emin"] / 2
    else:
        alvo = demanda(pid, dia) * D(str(ciclo + 2)) + p["emin"]
    atual = estoque(pid, dia) + pendente_pedido(pid)
    if atual >= alvo * D("0.75"):
        return D("0")
    falta = alvo - atual
    mult = D(str(K.FATOR_COMPRA.get(pid, 1)))
    if p["base"] == "KG":
        return (falta / 5).to_integral_value(ROUND_CEILING) * 5
    return (falta / mult).to_integral_value(ROUND_CEILING) * mult

PED_ITENS = {}  # id_pedido -> [(pid, qtd)]
def pendente_pedido(pid):
    tot = D("0")
    for _, ped in pedidos_pendentes:
        for (p_, q_) in PED_ITENS[ped]:
            if p_ == pid: tot += q_
    return tot

def cria_pedido(fo, quando, itens, func=2, canal=None):
    pid_ = nid("pedido_compra")
    rows["pedido_compra"].append(dict(id_pedido=pid_, id_fornecedor=fo, id_funcionario=func, data_hora_pedido=quando,
                                      canal=canal or FORN[fo][5], cancelado=False, observacao=None))
    PED_ITENS[pid_] = []
    for (p_, q_) in itens:
        rows["item_pedido"].append(dict(id_pedido=pid_, id_produto=p_, quantidade_pedida=q3(q_),
                                        preco_negociado=c4(custo_atual[(fo, p_)])))
        PED_ITENS[pid_].append((p_, q_))
    return pid_

def validade_nova(pid, dia):
    p = PROD[pid]
    if not p["ctrl"]: return None
    return dia + dt.timedelta(days=max(2, int(p["vida"] * R.uniform(0.75, 0.95))))

def recebe(fo, quando, linhas, func, situacao="ACEITO", obs=None, volumes_falta=0, pedido_txt=None):
    """linhas: dicts com pid, qtd_nota (unid. nota), fator, valor_unit (por unid. nota), aceita (base),
    situacao_item, id_pedido, lotes=[(qtd_base, validade)] opcional"""
    global nota_cnf
    rid = nid("recebimento")
    num_nota[fo] += R.randint(3, 40)
    serie = 1 if fo != 5 else 0
    doc = K.doc_fornecedor(FORN[fo])
    doc14 = doc if len(doc) == 14 else "000" + doc
    nota_cnf += R.randint(1000, 90000)
    chave = K.chave_nfe(quando.strftime("%y%m"), doc14, serie, num_nota[fo], nota_cnf)
    total = sum((m2(l["qtd_nota"] * l["valor_unit"]) for l in linhas), D("0"))
    vol = len(linhas) + R.randint(0, 3)
    rows["recebimento"].append(dict(id_recebimento=rid, id_fornecedor=fo, id_funcionario=func, chave_acesso_nfe=chave,
                                    modelo_nota="55", serie_nota=serie, numero_nota=num_nota[fo], data_hora=quando,
                                    valor_total_nota=total, volumes_nota=vol, volumes_conferidos=vol - volumes_falta,
                                    situacao=situacao, observacao_divergencia=obs))
    valor_aceito = D("0")
    for n, l in enumerate(linhas, 1):
        rows["item_recebimento"].append(dict(id_recebimento=rid, numero_item_nota=n, id_produto=l["pid"],
                                             id_pedido=l.get("id_pedido"), quantidade_nota=q3(l["qtd_nota"]),
                                             fator_conversao_compra=q3(l["fator"]), valor_unitario_nota=c4(l["valor_unit"]),
                                             quantidade_aceita=q3(l["aceita"]), situacao_item=l["situacao_item"]))
        if l["aceita"] > 0:
            custo_base = c4(l["valor_unit"] / l["fator"])
            valor_aceito += m2(l["aceita"] * custo_base)
            partes = l.get("lotes") or [(l["aceita"], validade_nova(l["pid"], quando.date()))]
            for (qb, val) in partes:
                lid = novo_lote(l["pid"], "RECEBIMENTO", quando, custo_base, val, rec=rid, item=n,
                                cod=(f"L{R.randint(10000, 99999)}" if PROD[l["pid"]]["ctrl"] and PROD[l["pid"]]["base"] == "UN" else None))
                LOTES[lid]["forn"] = fo
                mov(lid, "ENTRADA_RECEBIMENTO", qb, quando, func=func)
    if situacao != "RECUSADO" and valor_aceito > 0:
        gera_contas(fo, rid, quando, valor_aceito)
    return rid

def gera_contas(fo, rid, quando, valor):
    nome = FORN[fo][3]
    if FORN[fo][6] == "À vista":
        cid = nova_conta(rid, nome, f"NF {num_nota[fo]}", 1, f"Compra à vista — NF {num_nota[fo]}", "FORNECEDOR",
                         valor, quando.date(), "ALTA")
        contas_avista.append((cid, quando, valor))
    else:
        base = m2(valor / 3)
        partes = [base, base, valor - 2 * base]
        for k, dias in enumerate((7, 14, 21)):
            venc = quando.date() + dt.timedelta(days=dias)
            nova_conta(rid, nome, f"BOL-{rid:04d}-{k+1}", k + 1, f"NF {num_nota[fo]} — parcela {k+1}/3", "FORNECEDOR",
                       partes[k], venc, "ALTA" if fo in (3, 4) else "MEDIA")

CONTAS = {}
contas_avista = []
def nova_conta(rid, credor, doc, parcela, descr, cat, valor, venc, prio):
    cid = nid("conta_pagar")
    rows["conta_pagar"].append(dict(id_conta=cid, id_recebimento=rid, credor=credor, numero_documento=doc,
                                    numero_parcela=parcela, descricao=descr, categoria_despesa=cat,
                                    valor_original=m2(valor), data_vencimento=str(venc), prioridade=prio, cancelada=False))
    CONTAS[cid] = dict(id=cid, valor=m2(valor), venc=venc, pago=D("0"), npag=0, cat=cat, rec=rid, credor=credor)
    if doc == "EN-082026":
        ATRASO[cid] = 2                                     # luz paga 2 dias depois, com juros
    if credor == FORN[2][3] and dt.date(2026, 9, 22) <= venc <= dt.date(2026, 9, 25) and not PARCIAL:
        PARCIAL[cid] = (D("0.5"), venc + dt.timedelta(days=5 if (venc + dt.timedelta(days=5)).weekday() != 6 else 6))
    if credor == FORN[3][3] and dt.date(2026, 9, 28) <= venc <= dt.date(2026, 9, 30) and len(PARCIAL) == 1:
        PARCIAL[cid] = (D("0.4"), dt.date(2026, 10, 9))      # parcial; o saldo só será pago depois da data de referência
    if credor == FORN[4][3] and dt.date(2026, 9, 27) <= venc <= dt.date(2026, 9, 30) and not [k for k, v in ATRASO.items() if v == 99]:
        ATRASO[cid] = 99                                    # parcela vencida e não paga até a data de referência
    return cid

def paga_conta(cid, data, principal, conta_fin, func, juros=D("0"), obs=None):
    c = CONTAS[cid]
    principal = m2(principal); juros = m2(juros)
    mf = mov_fin(conta_fin, data, "DEBITO", "PAGAMENTO_CONTA", principal + juros,
                 doc=f"PGTO-{cid:04d}-{c['npag']+1}", func=func)
    c["npag"] += 1
    c["pago"] += principal
    assert c["pago"] <= c["valor"]
    rows["pagamento_conta"].append(dict(id_conta=cid, numero_pagamento=c["npag"], id_funcionario=func,
                                        id_movimento_fin=mf, data_pagamento=str(data), valor_principal=principal,
                                        valor_juros_multa=juros, valor_desconto=m2("0"), observacao=obs))

# ------------------------------------------------------------------ caixa e vendas
fundo = {1: m2("200.00"), 2: m2("150.00")}
cupom = {1: 0, 2: 0}
sessoes_dia = []
VENDAS_ITENS = defaultdict(list)    # pid -> [(id_venda, numero_item, data, eid, qtd, preço, desconto, forma_principal, cliente)]
pix_seq = 0
nsu_usados = set()
def novo_nsu(forma):
    global pix_seq
    while True:
        if forma == "PIX":
            pix_seq += 1
            v = "E" + f"{R.getrandbits(120):032x}"[:32]
        else:
            v = f"{R.randint(10**11, 10**12 - 1)}"
        if v not in nsu_usados:
            nsu_usados.add(v); return v

transacoes = []   # (data, forma, id_venda, numero_pagamento, valor) para repasses
SUPERVISORES = [1, 2, 3]

def escolhe_produto():
    pids = list(PROD)
    pesos = [PROD[p]["pop"] / (1.0 if PROD[p]["base"] == "UN" else 0.9) for p in pids]
    return R.choices(pids, pesos)[0]

def quantidade_para(pid, eid):
    p = PROD[pid]
    if p["base"] == "KG":
        return q3(R.uniform(0.25, 1.9 if p["cat"] != "HORTI" else 2.4))
    if EMB[eid]["fator"] > 1:
        return D("1")
    if preco[eid] > 12:
        return D(R.choices([1, 2], [85, 15])[0])
    if p["cat"] in ("BEBID",):
        return D(R.choices([1, 2, 3, 4, 6], [55, 22, 9, 8, 6])[0])
    return D(R.choices([1, 2, 3], [72, 22, 6])[0])

def baixa_fefo(pid, qbase, quando, venda, item):
    resto = qbase
    for L in lotes_vendaveis(pid, quando.date()):
        if resto <= 0: break
        tira = min(resto, L["saldo"])
        mov(L["id"], "SAIDA_VENDA", tira, quando, venda=venda, item=item)
        resto -= tira
    assert resto == 0

def rn40(pid, falta, quando, operador, custo):
    """Venda não bloqueada: cria lote de ajuste pendente de conferência (RN-40)."""
    lid = novo_lote(pid, "AJUSTE_INVENTARIO", quando, custo, None, pend=True)
    mov(lid, "AJUSTE_INVENTARIO_ENTRADA", falta, quando, func=operador,
        motivo="Ajuste automático RN-40: saldo do sistema insuficiente na venda; conferir estoque físico")
    return lid

RN40_EVENTOS = {}
FIADO_PROB = 0.03

def ultimo_custo(pid):
    best = None
    for (fo, p_), c in custo_atual.items():
        if p_ == pid and fo in PROD[pid]["forns"][:1]:
            best = c
    return best or PROD[pid]["custo"]

def aplica_precos(ate):
    while PRECO_PEND and PRECO_PEND[0][0] <= ate:
        (q, eid, novo, func, motivo) = PRECO_PEND.pop(0)
        muda_preco(eid, novo, func, q, motivo)

PRECO_PEND = sorted((ts(ev[0], ev[1], ev[2]), EMB_DE[ev[3]][ev[4]], D(ev[5]), ev[6], ev[7]) for ev in EVENTOS_PRECO)

def registra_venda(sessao, caixa, operador, quando, itens_forcados=None, cancelar=False, forma_forcada=None,
                   cliente_forcado=None, autorizador_forcado=None, forcar_rn40=False):
    global cupom
    aplica_precos(quando)
    cupom[caixa] += 1
    vid = nid("venda")
    n_itens = R.choices([1, 2, 3, 4, 5, 6, 8], [30, 24, 17, 11, 8, 6, 4])[0]
    escolhidos = itens_forcados or []
    if not itens_forcados:
        usados = set()
        for _ in range(n_itens):
            pid = escolhe_produto()
            if pid in usados: continue
            usados.add(pid)
            eids = EMB_DE[pid]
            eid = eids[0] if len(eids) == 1 or R.random() > 0.15 else eids[1]
            escolhidos.append((pid, eid, quantidade_para(pid, eid)))
    venda_row = dict(id_venda=vid, id_sessao=sessao, id_funcionario=operador, id_cliente=None,
                     numero_cupom=cupom[caixa], data_hora=quando, situacao="CANCELADA" if cancelar else "CONCLUIDA")
    itens = []
    num = 0
    total = D("0")
    for (pid, eid, q) in escolhidos:
        qb = q3(q * EMB[eid]["fator"])
        disp = estoque(pid, quando.date())
        if qb > disp and not forcar_rn40:
            if PROD[pid]["base"] == "UN" and EMB[eid]["fator"] == 1 and disp >= 1:
                q = D(int(disp)); qb = q
            else:
                continue
        num += 1
        p_unit = preco[eid]
        desc = D("0"); aut = None
        Ls = lotes_vendaveis(pid, quando.date())
        if Ls and Ls[0]["val"] is not None and (Ls[0]["val"] - quando.date()).days <= 1 and PROD[pid]["cat"] in ("FRIOS", "CARNE"):
            desc = m2(p_unit * D("0.25"))
            aut = autorizador_forcado or (operador if tem(operador, "AUTORIZAR_DESCONTO") else R.choice(SUPERVISORES))
        itens.append([pid, eid, q, qb, p_unit, desc, aut, num, forcar_rn40, disp])
        total += m2(q * (p_unit - desc))
    if not itens:
        cupom[caixa] -= 1; seq["venda"] -= 1
        return None
    rows["venda"].append(venda_row)
    for (pid, eid, q, qb, p_unit, desc, aut, num, f40, disp) in itens:
        rows["item_venda"].append(dict(id_venda=vid, numero_item=num, id_embalagem=eid, id_funcionario_autorizador=aut,
                                       quantidade=q3(q), preco_unitario_praticado=p_unit, desconto_unitario=m2(desc)))
    if cancelar:
        return vid
    for (pid, eid, q, qb, p_unit, desc, aut, num, f40, disp) in itens:
        if f40 and qb > disp:
            rn40(pid, qb - disp, quando, operador, ultimo_custo(pid))
            RN40_EVENTOS[quando.date()] = vid
        baixa_fefo(pid, qb, quando, vid, num)
        consumo[pid][quando.date()] += qb
    # pagamento
    pagamentos = []
    cli = cliente_forcado
    forma = forma_forcada
    if cli is None and forma is None and R.random() < FIADO_PROB:
        cand = [c for c in CLI.values() if c["aut"] and c["saldo"] + total <= c["lim"]]
        if cand:
            cli = R.choice(cand)["id"]; forma = "FIADO"
    if forma == "FIADO":
        venda_row["id_cliente"] = cli
        if R.random() < 0.25 and total > 20:
            parte = m2(total * D("0.3"))
            pagamentos = [("DIN", parte), ("FIADO", total - parte)]
        else:
            pagamentos = [("FIADO", total)]
        CLI[cli]["saldo"] += dict(pagamentos)["FIADO"]
    elif forma == "2CRE":
        a = m2(total * D("0.4")); b = m2(total * D("0.3"))
        pagamentos = [("DIN", total - a - b), ("CRE", a), ("CRE", b)]
    elif forma:
        pagamentos = [(forma, total)]
    else:
        f = R.choices(["DIN", "DEB", "CRE", "PIX", "VALE"], [31, 29, 15, 21, 4])[0]
        if R.random() < 0.05 and total > 30:
            parte = m2(total * D(str(round(R.uniform(0.3, 0.6), 2))))
            f2 = R.choice(["PIX", "DEB"])
            pagamentos = [("DIN", parte), (f2, total - parte)]
        else:
            pagamentos = [(f, total)]
    if cli is not None and venda_row["id_cliente"] is None:
        venda_row["id_cliente"] = cli
    for k, (f, v) in enumerate(pagamentos, 1):
        ent = None
        if f == "DIN":
            ent = v
            r = R.random()
            if r < 0.55:
                for nota in (D(2), D(5), D(10), D(20), D(50), D(100), D(200)):
                    if nota >= v and R.random() < 0.7:
                        ent = m2(nota); break
                else:
                    ent = m2((v / 10).to_integral_value(ROUND_CEILING) * 10)
        nsu = None if f in ("DIN", "FIADO") else novo_nsu(f)
        rows["pagamento_venda"].append(dict(id_venda=vid, numero_pagamento=k, codigo_forma=f, id_movimento_fin=None,
                                            valor=m2(v), valor_entregue=ent, nsu_autorizacao=nsu))
        pagamentos[k - 1] = (f, m2(v))
        if f in ("DEB", "CRE", "PIX", "VALE"):
            transacoes.append(dict(data=quando.date(), forma=f, venda=vid, num=k, valor=m2(v), nsu=nsu,
                                   idx=len(rows["pagamento_venda"]) - 1))
    for (pid, eid, q, qb, p_unit, desc, aut, num, f40, disp) in itens:
        VENDAS_ITENS[pid].append((vid, num, quando, eid, q, p_unit, desc, pagamentos[0][0], venda_row["id_cliente"]))
    din = sum((v for (f, v) in pagamentos if f == "DIN"), D("0"))
    return vid, din

def nova_sessao(caixa, abre, func_abre, quando):
    sid = nid("sessao_caixa")
    rows["sessao_caixa"].append(dict(id_sessao=sid, numero_caixa=caixa, id_funcionario_abertura=func_abre,
                                     id_funcionario_fechamento=None, data_hora_abertura=quando, valor_inicial=fundo[caixa],
                                     data_hora_fechamento=None, valor_contado=None, total_maquininhas_informado=None,
                                     justificativa_diferenca=None))
    return sid

def mov_caixa(sid, func, quando, tipo, valor, motivo):
    valor = m2(valor)
    mf = None
    if tipo in ("SANGRIA", "RECOLHIMENTO_FECHAMENTO"):
        mf = mov_fin(COFRE, quando.date(), "CREDITO", "RECOLHIMENTO_GAVETA", valor, doc=f"GAV-{sid:04d}-{seq['movimentacao_caixa']+1}")
    elif tipo == "SUPRIMENTO":
        mf = mov_fin(COFRE, quando.date(), "DEBITO", "SUPRIMENTO_GAVETA", valor, doc=f"GAV-{sid:04d}-{seq['movimentacao_caixa']+1}")
    i = nid("movimentacao_caixa")
    rows["movimentacao_caixa"].append(dict(id_mov_caixa=i, id_sessao=sid, id_funcionario=func, id_movimento_fin=mf,
                                           data_hora=quando, tipo=tipo, valor=valor, motivo=motivo))
    return i

DIF_CAIXA = {  # (data, caixa, turno) -> (diferença no dinheiro, justificativa, diferença maquininha)
    (dt.date(2026, 9, 6), 1, "M"): (D("-2.50"), "Troco dado a mais para cliente (identificado pela operadora)", D("0")),
    (dt.date(2026, 9, 19), 2, "T"): (D("1.00"), None, D("0")),
    (dt.date(2026, 9, 27), 1, "M"): (D("0"), None, D("15.00")),
    (dt.date(2026, 9, 12), 1, "T"): (D("-5.00"), "Nota de R$ 5 rasgada, recusada pelo banco", D("0")),
}

def turnos(dia):
    wd = dia.weekday()
    if wd == 6:
        return [(1, "M", 7, 13, 3, 30)]
    t = [(1, "M", 7, 14, 2 if wd != 5 else 3, 26), (1, "T", 14, 21, 3 if dia.day % 2 else 4, 30),
         (2, "T", 16, 21, 4 if dia.day % 2 else 5, 20)]
    if wd in (4, 5):
        t = [(c, tn, a, f, op, int(n * 1.3)) for (c, tn, a, f, op, n) in t]
    return t

def dia_operacao(dia):
    """Todas as sessões do dia rodam em paralelo, em ordem de horário: os
    identificadores e cupons ficam em ordem cronológica, como num sistema real."""
    agenda = []
    for (caixa, turno, h_ini, h_fim, operador, n_vendas) in turnos(dia):
        if operador == 4 and dia.weekday() == 0:
            operador = 5
        st = dict(caixa=caixa, turno=turno, h_ini=h_ini, h_fim=h_fim, operador=operador, sid=None, cancelou=False, gaveta=None)
        agenda.append((h_ini, 0, st, "abre", None))
        agenda += [(R.uniform(h_ini + 0.05, h_fim - 0.1), 1, st, "venda", None) for _ in range(n_vendas)]
        agenda.append((h_fim, -1, st, "fecha", None))
        st["n_vendas"] = n_vendas
    agenda.sort(key=lambda e: (e[0], e[1]))
    i = 0
    while i < len(agenda):
        (t, ordem, st, tipo, fn) = agenda[i]
        i += 1
        caixa, turno, operador = st["caixa"], st["turno"], st["operador"]
        minutos = (t % 1) * 60
        quando = ts(dia, int(t), int(minutos), int((minutos % 1) * 60) if tipo not in ("abre", "fecha") else 0)
        if tipo == "abre":
            st["sid"] = nova_sessao(caixa, None, operador, quando)
            st["gaveta"] = fundo[caixa]
            extra = [(te, 1, st, "esp", f) for (te, f) in ESPECIAIS(dia, caixa, turno, st["sid"], operador, st)]
            agenda = agenda[:i] + sorted(agenda[i:] + extra, key=lambda e: (e[0], e[1]))
            continue
        if tipo == "fecha":
            fecha_sessao(st["sid"], caixa, turno, dia, st["h_fim"], operador)
            continue
        op = operador
        if caixa == 1 and turno == "M" and 12 <= t < 12.75 and dia.weekday() != 6:
            op = 5   # Pedro cobre o almoço no mesmo caixa (R25, T15)
        if tipo == "esp":
            fn(quando, op)
            continue
        cancela = (dia, caixa, turno) in CANCELAR and not st["cancelou"] and t > st["h_ini"] + 2
        res = registra_venda(st["sid"], caixa, op, quando, cancelar=cancela)
        if cancela and res:
            st["cancelou"] = True
        if res and not cancela:
            st["gaveta"] += res[1]
        if st["gaveta"] > D("750"):
            resp = op if tem(op, "REALIZAR_SANGRIA") else 1
            mov_caixa(st["sid"], resp, quando + dt.timedelta(minutes=2), "SANGRIA", D("500"), "Excesso de dinheiro na gaveta")
            st["gaveta"] -= D("500")
    pix_do_dia(dia)

CANCELAR = {(dt.date(2026, 9, 11), 1, "T"), (dt.date(2026, 9, 23), 2, "T")}

def fecha_sessao(sid, caixa, turno, dia, h_fim, operador):
    s = [x for x in rows["sessao_caixa"] if x["id_sessao"] == sid][0]
    din = sum((p["valor"] for p in rows["pagamento_venda"] if p["codigo_forma"] == "DIN" and venda_sessao.get(p["id_venda"]) == sid
               and venda_conc.get(p["id_venda"])), D("0"))
    ele = sum((p["valor"] for p in rows["pagamento_venda"] if p["codigo_forma"] in ("DEB", "CRE", "PIX", "VALE")
               and venda_sessao.get(p["id_venda"]) == sid and venda_conc.get(p["id_venda"])), D("0"))
    ab = sum((a["valor"] for a in rows["abatimento_fiado"] if a["id_sessao"] == sid and a["codigo_forma"] == "DIN"), D("0"))
    mcs = [m for m in rows["movimentacao_caixa"] if m["id_sessao"] == sid]
    sup = sum((m["valor"] for m in mcs if m["tipo"] == "SUPRIMENTO"), D("0"))
    san = sum((m["valor"] for m in mcs if m["tipo"] == "SANGRIA"), D("0"))
    ree = sum((m["valor"] for m in mcs if m["tipo"] == "REEMBOLSO_DEVOLUCAO"), D("0"))
    esperado = s["valor_inicial"] + din + ab + sup - san - ree
    dif, just, dmaq = DIF_CAIXA.get((dia, caixa, turno), (D("0"), None, D("0")))
    contado = m2(esperado + dif)
    fecha = ts(dia, h_fim, 0) - dt.timedelta(minutes=3)
    s.update(id_funcionario_fechamento=operador, data_hora_fechamento=fecha, valor_contado=contado,
             total_maquininhas_informado=m2(ele + dmaq), justificativa_diferenca=just)
    fica = m2(R.choice([150, 150, 200, 180, 120]))
    if contado - fica > 0:
        resp = operador if tem(operador, "REALIZAR_SANGRIA") else 1
        mov_caixa(sid, resp, fecha + dt.timedelta(minutes=1), "RECOLHIMENTO_FECHAMENTO", contado - fica,
                  "Recolhimento do fechamento ao cofre")
    else:
        fica = contado
    fundo[caixa] = fica

venda_sessao = {}
venda_conc = {}
_orig_reg = registra_venda
def registra_venda(sessao, caixa, operador, quando, **kw):
    r = _orig_reg(sessao, caixa, operador, quando, **kw)
    if r:
        vid = r if isinstance(r, int) else r[0]
        venda_sessao[vid] = sessao
        venda_conc[vid] = not kw.get("cancelar", False)
        if isinstance(r, int):
            return (vid, D("0"))
    return r

# ------------------------------------------------------------------ eventos especiais por sessão
def ESPECIAIS(dia, caixa, turno, sid, operador, estado):
    ev = []
    d = dia
    # abatimentos de fiado (caixa 1, turno da tarde)
    if caixa == 1 and turno == "T":
        for cli, dias in PLANO_ABAT.items():
            if d in dias:
                forma = dias[d]
                def f(quando, op, cli=cli, forma=forma):
                    if CLI[cli]["saldo"] <= 0: return
                    v = m2(CLI[cli]["saldo"] * D(str(R.choice([0.4, 0.5, 0.6, 1.0]))))
                    if v > 0:
                        abat(cli, forma, v, op, sid if forma == "DIN" else None, quando)
                ev.append((17 + R.random() * 0.9, f))
    # devoluções
    for dv in DEVOLUCOES:
        if dv["data"] == d and dv["caixa"] == caixa and dv["turno"] == turno:
            ev.append((16.5, lambda quando, op, dv=dv: devolve(dv, sid, op, quando)))
    # dinheiro + dois cartões de crédito (T06)
    if (d, caixa, turno) in DOIS_CARTOES:
        ev.append((18.3 if turno == "T" else 11.3,
                   lambda quando, op: registra_venda(sid, caixa, op, quando, forma_forcada="2CRE")))
    # RN-40: venda com saldo do sistema insuficiente (16/09 Brahma; 30/09 Guaraná)
    if (d, caixa, turno) == (dt.date(2026, 9, 16), 1, "M"):
        ev.append((7.4, lambda quando, op: registra_venda(sid, caixa, op, quando,
                  itens_forcados=[(13, EMB_DE[13][0], D("6"))], forma_forcada="DEB", forcar_rn40=True)))
    if (d, caixa, turno) == (dt.date(2026, 9, 30), 1, "T"):
        def f40(quando, op):
            disp = estoque(15, d)
            registra_venda(sid, caixa, op, quando, itens_forcados=[(15, EMB_DE[15][0], q3(disp + 2))],
                           forma_forcada="PIX", forcar_rn40=True)
        ev.append((19.2, f40))
    # venda durante o preço digitado errado (09:30 de 17/09) — achado da auditoria A15
    if (d, caixa, turno) == (dt.date(2026, 9, 17), 1, "M"):
        ev.append((9.5, lambda quando, op: registra_venda(sid, caixa, op, quando,
                  itens_forcados=[(14, EMB_DE[14][0], D("2")), (2, EMB_DE[2][0], D("1"))], forma_forcada="DEB")))
        ev.append((10.75, lambda quando, op: registra_venda(sid, caixa, op, quando,
                  itens_forcados=[(14, EMB_DE[14][0], D("1"))], forma_forcada="DIN")))
    # suprimento: faltou troco no domingo
    if (d, caixa, turno) == (dt.date(2026, 9, 20), 1, "M"):
        def sup(quando, op):
            mov_caixa(sid, 1, quando, "SUPRIMENTO", D("50"), "Falta de moedas e notas pequenas para troco")
            estado["gaveta"] += D("50")
        ev.append((8.1, sup))
    # desconto autorizado por quem não tem permissão (achado de auditoria)
    if (d, caixa, turno) == (dt.date(2026, 9, 12), 2, "T"):
        def fdesc(quando, op):
            if not lotes_vendaveis(24, d): return
            r = registra_venda(sid, caixa, op, quando, itens_forcados=[(24, EMB_DE[24][0], D("2"))],
                               forma_forcada="DIN", autorizador_forcado=4)
            if not r: return
            iv = [x for x in rows["item_venda"] if x["id_venda"] == r[0]][0]
            if iv["desconto_unitario"] == 0:
                iv["desconto_unitario"] = m2(iv["preco_unitario_praticado"] * D("0.20"))
                iv["id_funcionario_autorizador"] = 4
                ajusta_pagamento(r[0])
        ev.append((19.6, fdesc))
    return ev

def ajusta_pagamento(vid):
    tot = sum((m2(x["quantidade"] * (x["preco_unitario_praticado"] - x["desconto_unitario"])) for x in rows["item_venda"] if x["id_venda"] == vid), D("0"))
    pv = [p for p in rows["pagamento_venda"] if p["id_venda"] == vid]
    assert len(pv) == 1 and pv[0]["codigo_forma"] == "DIN"
    pv[0]["valor"] = tot
    if pv[0]["valor_entregue"] is not None and pv[0]["valor_entregue"] < tot:
        pv[0]["valor_entregue"] = tot

DOIS_CARTOES = {(dt.date(2026, 9, 5), 1, "T"), (dt.date(2026, 9, 19), 1, "T"), (dt.date(2026, 9, 26), 2, "T")}

def abat(cli, forma, v, func, sid, quando):
    mf = None
    nsu_doc = None
    if forma == "PIX":
        mf = mov_fin(BANCO, quando.date(), "CREDITO", "PIX_RECEBIDO", v, doc=f"PIX-{novo_nsu('PIX')}")
    i = nid("abatimento_fiado")
    rows["abatimento_fiado"].append(dict(id_abatimento=i, id_cliente=cli, codigo_forma=forma, id_funcionario=func,
                                         id_sessao=sid, id_movimento_fin=mf, data_hora=quando, valor=m2(v),
                                         observacao=("Pagamento total" if v >= CLI[cli]["saldo"] else "Pagamento parcial")))
    CLI[cli]["saldo"] -= m2(v)

PLANO_ABAT = {
    1: {dt.date(2026, 9, 9): "DIN", dt.date(2026, 9, 18): "PIX", dt.date(2026, 9, 28): "DIN"},
    2: {dt.date(2026, 9, 11): "DIN", dt.date(2026, 9, 25): "DIN"},
    3: {dt.date(2026, 9, 14): "PIX", dt.date(2026, 9, 29): "PIX"},
    4: {dt.date(2026, 9, 10): "DIN", dt.date(2026, 9, 17): "DIN", dt.date(2026, 9, 24): "DIN"},
    5: {dt.date(2026, 9, 21): "PIX"},
    10: {dt.date(2026, 9, 26): "DIN"},
    # cliente 6 (Chico) não paga nada no mês: aparece na análise de risco
}

DEVOLUCOES = [
    dict(data=dt.date(2026, 9, 9), caixa=1, turno="T", pid=14, motivo="DEFEITO", destino="SEPARADO_TROCA", forma="DINHEIRO"),
    dict(data=dt.date(2026, 9, 16), caixa=1, turno="T", pid=24, motivo="VENCIDO", destino="DESCARTE", forma="TROCA_MESMO_PRODUTO"),
    dict(data=dt.date(2026, 9, 22), caixa=1, turno="T", pid=2, motivo="DEFEITO", destino="DESCARTE", forma="ABATER_FIADO"),
    dict(data=dt.date(2026, 9, 26), caixa=1, turno="T", pid=12, motivo="DEFEITO", destino="SEPARADO_TROCA", forma="ESTORNO_ELETRONICO"),
]

def devolve(dv, sid, func_op, quando):
    pids = [dv["pid"]] + [p for p in PROD if p != dv["pid"] and PROD[p]["base"] == "UN"]
    for pid in pids:
        cand = [x for x in VENDAS_ITENS[pid] if x[2].date() < dv["data"] and (dv["data"] - x[2].date()).days <= 6
                and venda_conc.get(x[0]) and EMB[x[3]]["fator"] == 1]
        if dv["forma"] == "ABATER_FIADO":
            cand = [x for x in cand if x[8] is not None and x[7] == "FIADO"]
        elif dv["forma"] == "ESTORNO_ELETRONICO":
            cand = [x for x in cand if x[7] == "PIX"]
        if cand and (dv["forma"] != "TROCA_MESMO_PRODUTO" or lotes_vendaveis(pid, dv["data"])):
            break
    dv["pid_real"] = pid
    assert cand, dv
    (vid, num, quando_v, eid, q, p_unit, desc, f0, cli) = cand[-1]
    autor = func_op if tem(func_op, "AUTORIZAR_DEVOLUCAO") else 1
    qdev = D("1")
    valor = m2(qdev * (p_unit - desc)) if dv["forma"] != "TROCA_MESMO_PRODUTO" else m2("0")
    mc = mf = None
    if dv["forma"] == "DINHEIRO":
        mc = mov_caixa(sid, autor, quando, "REEMBOLSO_DEVOLUCAO", valor, f"Reembolso da devolução do cupom (venda {vid})")
    if dv["forma"] == "ESTORNO_ELETRONICO":
        mf = mov_fin(BANCO, dv["data"], "DEBITO", "ESTORNO_DEVOLUCAO", valor, doc=f"EST-PIX-{vid}")
    did = nid("devolucao")
    rows["devolucao"].append(dict(id_devolucao=did, id_venda=vid, numero_item=num, id_funcionario=autor, id_mov_caixa=mc,
                                  id_movimento_fin=mf, data_hora=quando, quantidade_devolvida=q3(qdev), motivo=dv["motivo"],
                                  destino=dv["destino"], forma_reembolso=dv["forma"], valor_reembolsado=valor))
    if dv["forma"] == "ABATER_FIADO":
        CLI[cli]["saldo"] -= valor
    # retorno ao lote de onde saiu (último lote baixado pelo item)
    saidas = [m for m in rows["movimentacao_estoque"] if m["id_venda"] == vid and m["numero_item"] == num]
    lote_orig = saidas[-1]["id_lote"]
    mov(lote_orig, "DEVOLUCAO_CLIENTE", qdev, quando, dev=did)
    if dv["destino"] != "REVENDA":
        tipo = "PERDA_VENCIMENTO" if dv["motivo"] == "VENCIDO" else "PERDA_AVARIA"
        mov(lote_orig, tipo, qdev, quando + dt.timedelta(minutes=1), func=autor,
            motivo=f"Produto devolvido pelo cliente (devolução {did}) — destino {dv['destino']}")
    if dv["forma"] == "TROCA_MESMO_PRODUTO":
        Ls = lotes_vendaveis(pid, dv["data"])
        mov(Ls[0]["id"], "SAIDA_TROCA_CLIENTE", qdev, quando + dt.timedelta(minutes=2), dev=did)

# ------------------------------------------------------------------ rotinas diárias de estoque
def rotina_validade(dia):
    func = 6 if dia.weekday() != 6 else 5
    quando = ts(dia, 7, 30)
    for L in list(LOTES.values()):
        if L["sit"] == "DISPONIVEL" and L["val"] is not None and L["val"] < dia and L["saldo"] > 0:
            mov(L["id"], "PERDA_VENCIMENTO", L["saldo"], quando, func=func,
                motivo=f"Vencido em {L['val'].strftime('%d/%m/%Y')}; separado para troca")
            L["sit"] = "SEPARADO_TROCA"; L["sep"] = dia

def rotina_hortifruti(dia):
    if dia.day % 2: return
    quando = ts(dia, 20, 30)
    for L in list(LOTES.values()):
        p = PROD[L["prod"]]
        if p["cat"] != "HORTI" or L["sit"] != "DISPONIVEL" or L["saldo"] <= 0: continue
        idade = (dia - L["entrada"].date()).days
        if idade > p["vida"]:
            mov(L["id"], "PERDA_AVARIA", L["saldo"], quando, func=5, motivo="Hortifruti deteriorado: fim da vida útil")
            L["sit"] = "DESCARTADO"
        elif idade >= 3:
            perda = q3(L["saldo"] * D(str(round(R.uniform(0.03, 0.08), 3)))) if p["base"] == "KG" else D(int(L["saldo"] * D("0.08")))
            if perda > 0:
                mov(L["id"], "PERDA_AVARIA", perda, quando, func=5, motivo="Deterioração (fruta/verdura passada)")

def trocas_fornecedor(dia, fo, func, quando):
    for L in list(LOTES.values()):
        if L["sit"] == "SEPARADO_TROCA" and L.get("sep") and L["sep"] < dia:
            forn_lote = L.get("forn") or PROD[L["prod"]]["forns"][0]
            if forn_lote != fo: continue
            perdido = sum((m["quantidade"] for m in rows["movimentacao_estoque"] if m["id_lote"] == L["id"]
                           and m["tipo"] == "PERDA_VENCIMENTO"), D("0"))
            if fo in (1, 3) and perdido > 0:
                nl = novo_lote(L["prod"], "REPOSICAO_FORNECEDOR", quando, L["custo"], validade_nova(L["prod"], dia), reposto=L["id"])
                LOTES[nl]["forn"] = fo
                mov(nl, "TROCA_FORNECEDOR", perdido, quando, func=func,
                    motivo=f"Reposição do lote {L['id']} vencido, trocado pelo fornecedor")
                L["sit"] = "TROCADO"
            elif (dia - L["sep"]).days >= 3:
                L["sit"] = "DESCARTADO"

def descarta_sem_troca(dia):
    for L in LOTES.values():
        if L["sit"] == "SEPARADO_TROCA" and L.get("sep"):
            fo = L.get("forn") or PROD[L["prod"]]["forns"][0]
            if fo not in (1, 3) and (dia - L["sep"]).days >= 4:
                L["sit"] = "DESCARTADO"

# ------------------------------------------------------------------ compras do dia
CENARIOS = {}
def compras(dia):
    wd = dia.weekday()
    # entregas de pedidos feitos antes
    for (d_ent, ped) in list(pedidos_pendentes):
        if d_ent == dia:
            entrega_pedido(ped, dia)
            pedidos_pendentes.remove((d_ent, ped))
    for fo, (dias, prazo, hora) in AGENDA.items():
        if wd not in dias or wd == 6: continue
        itens = []
        for pid in PROD:
            if PROD[pid]["forns"][0] != fo: continue
            if pid == 13 and dt.date(2026, 9, 15) <= dia < dt.date(2026, 9, 21):
                continue   # pedido de Brahma suspenso após contagem errada (ver RN-40)
            q = qtd_compra(pid, fo, dia, 3 if len(dias) >= 2 else 7)
            if q > 0: itens.append((pid, q))
        if fo == 2 and dia == dt.date(2026, 9, 8):
            itens = [(p, q) for (p, q) in itens if p != 6] + [(6, D("60"))]   # cenário do pedido parcial: óleo
        if not itens: continue
        func = 2 if wd in (0, 2, 4) else 3
        ped = cria_pedido(fo, ts(dia, 8, R.randint(0, 40)), itens, func=func)
        entrega = dia + dt.timedelta(days=prazo)
        if entrega.weekday() == 6: entrega += dt.timedelta(days=1)
        if fo == 4 and dia == dt.date(2026, 9, 17):
            CENARIOS["recusa"] = ped
        pedidos_pendentes.append((entrega, ped))
    # Nova Rota: compra-teste de leite e arroz (comparação de fornecedores)
    if dia == dt.date(2026, 9, 14):
        ped = cria_pedido(8, ts(dia, 9, 0), [(23, D("48")), (1, D("10"))], func=1, canal="APLICATIVO")
        pedidos_pendentes.append((dia + dt.timedelta(days=1), ped))
    # produtor rural passa e entrega na hora, sem pedido (RF-11)
    if wd in VISITA_ANTONIO:
        linhas = []
        for pid in (34, 35, 36, 37, 38):
            q = qtd_compra(pid, 5, dia, 3)
            if q > 0:
                linhas.append(dict(pid=pid, qtd_nota=q, fator=D("1"), valor_unit=custo_atual[(5, pid)],
                                   aceita=q, situacao_item="ACEITO"))
        if linhas:
            recebe(5, ts(dia, 9, 30), linhas, func=5)
    trocas_fornecedor(dia, 3, 2, ts(dia, 9, 5))
    trocas_fornecedor(dia, 1, 3, ts(dia, 10, 5))
    descarta_sem_troca(dia)

def entrega_pedido(ped, dia):
    fo = [p for p in rows["pedido_compra"] if p["id_pedido"] == ped][0]["id_fornecedor"]
    hora = AGENDA.get(fo, (None, None, 10))[2]
    quando = ts(dia, hora, R.randint(0, 30))
    func = R.choice([2, 3, 5, 6])
    for (d_, c) in MUDA_CUSTO.items():
        if d_ <= dia:
            for (k, v) in c: custo_atual[k] = D(v)
    linhas = []
    sit = "ACEITO"; obs = None; vol_falta = 0
    for (pid, q) in PED_ITENS[ped]:
        fator = D(str(K.FATOR_COMPRA.get(pid, 1)))
        qn = q / fator
        linha = dict(pid=pid, qtd_nota=qn, fator=fator, valor_unit=custo_atual[(fo, pid)] * fator, aceita=q,
                     situacao_item="ACEITO", id_pedido=ped)
        linhas.append(linha)
    # ---- cenários
    if fo == 2 and dia == dt.date(2026, 9, 9):            # T01: óleo não veio; chega em outra nota
        falt = [l for l in linhas if l["pid"] == 6]
        linhas = [l for l in linhas if l["pid"] != 6]
        sit = "ACEITO_COM_DIVERGENCIA"; obs = "Óleo de soja do pedido não veio; vendedor promete entregar em 2 dias"; vol_falta = 0
        CENARIOS["oleo_pendente"] = (ped, falt[0])
    if CENARIOS.get("oleo_pendente") and dia == dt.date(2026, 9, 11) and fo == 2:
        pass
    if fo == 3 and dia == dt.date(2026, 9, 15):           # T03: iogurte com duas validades na mesma linha
        for l in linhas:
            if l["pid"] == 24:
                metade = (l["aceita"] / 2).to_integral_value()
                l["lotes"] = [(metade, dt.date(2026, 9, 28)), (l["aceita"] - metade, dt.date(2026, 10, 6))]
    if fo == 3 and dia == dt.date(2026, 9, 22):           # aceitação parcial: caixa de leite avariada
        for l in linhas:
            if l["pid"] == 23:
                l["aceita"] = l["aceita"] - 12 + 11
                l["situacao_item"] = "ACEITO_PARCIAL"
                sit = "ACEITO_COM_DIVERGENCIA"; obs = "1 caixa de leite amassada e vazando: 11 de 12 unidades aceitas"
    if fo == 1 and dia == dt.date(2026, 9, 4):            # linha não pedida devolvida ao entregador
        linhas.append(dict(pid=15, qtd_nota=D("2"), fator=D("6"), valor_unit=custo_atual[(1, 15)] * 6, aceita=D("0"),
                           situacao_item="NAO_PEDIDO_DEVOLVIDO", id_pedido=None))
        sit = "ACEITO_COM_DIVERGENCIA"; obs = "2 fardos de Guaraná não pedidos: devolvidos ao entregador"
    if fo == 1 and dia == dt.date(2026, 9, 25):           # bonificação (valor zero)
        linhas.append(dict(pid=16, qtd_nota=D("1"), fator=D("12"), valor_unit=D("0"), aceita=D("12"),
                           situacao_item="ACEITO", id_pedido=None))
    if fo == 4 and ped == CENARIOS.get("recusa"):          # T: entrega recusada e reentregue no dia seguinte
        for l in linhas:
            l["aceita"] = D("0"); l["situacao_item"] = "RECUSADO"
        recebe(fo, quando, linhas, func=2, situacao="RECUSADO",
               obs="Carne fora da temperatura (12 °C) e embalagens violadas: entrega recusada; fornecedor acionado")
        nova = [dict(l, aceita=l["qtd_nota"] * l["fator"], situacao_item="ACEITO") for l in linhas]
        recebe(fo, ts(dia + dt.timedelta(days=1), 8, 40), nova, func=3)
        return
    if linhas:
        recebe(fo, quando, linhas, func=func, situacao=sit, obs=obs, volumes_falta=vol_falta)
    if fo == 2 and dia == dt.date(2026, 9, 9):
        pass

def entrega_oleo(dia):
    if dia == dt.date(2026, 9, 11) and CENARIOS.get("oleo_pendente"):
        ped, l = CENARIOS["oleo_pendente"]
        recebe(2, ts(dia, 15, 10), [l], func=3)

# ------------------------------------------------------------------ contas fixas e pagamentos
def contas_fixas():
    fixas = [("Folha de pagamento — 08/2026", "Funcionários", "FOLHA 08/2026", "FOLHA", "13850.00", dt.date(2026, 9, 5), "ALTA"),
             ("Internet fibra — 09/2026", "Vivanet Telecom", "FAT-0926", "INTERNET", "149.90", dt.date(2026, 9, 10), "MEDIA"),
             ("Energia elétrica — 08/2026", "Enel SP", "EN-082026", "LUZ", "1186.40", dt.date(2026, 9, 15), "ALTA"),
             ("Simples Nacional — DAS 08/2026", "Receita Federal", "DAS 08/2026", "SIMPLES_NACIONAL", "4820.00", dt.date(2026, 9, 21), "ALTA"),
             ("Água e esgoto — 08/2026", "Sabesp", "SAB-082026", "AGUA", "212.30", dt.date(2026, 9, 25), "MEDIA"),
             ("Folha de pagamento — 09/2026", "Funcionários", "FOLHA 09/2026", "FOLHA", "13850.00", dt.date(2026, 10, 5), "ALTA"),
             ("Internet fibra — 10/2026", "Vivanet Telecom", "FAT-1026", "INTERNET", "149.90", dt.date(2026, 10, 10), "MEDIA"),
             ("Energia elétrica — 09/2026", "Enel SP", "EN-092026", "LUZ", "1243.10", dt.date(2026, 10, 15), "ALTA"),
             ("Simples Nacional — DAS 09/2026", "Receita Federal", "DAS 09/2026", "SIMPLES_NACIONAL", "5110.00", dt.date(2026, 10, 20), "ALTA"),
             ("Água e esgoto — 09/2026", "Sabesp", "SAB-092026", "AGUA", "205.70", dt.date(2026, 10, 26), "MEDIA")]
    for (descr, credor, doc, cat, v, venc, prio) in fixas:
        nova_conta(None, credor, doc, 1, descr, cat, D(v), venc, prio)

def pagamentos_do_dia(dia):
    # à vista: pagas no ato com dinheiro do cofre
    for (cid, quando, valor) in list(contas_avista):
        if quando.date() == dia:
            paga_conta(cid, dia, valor, COFRE, 1, obs="Pago em dinheiro ao entregador")
            contas_avista.remove((cid, quando, valor))
    if dia.weekday() == 6: return
    for c in sorted(CONTAS.values(), key=lambda c: c["id"]):
        if c["pago"] >= c["valor"]: continue
        venc = c["venc"]
        alvo = venc if venc.weekday() != 6 else venc + dt.timedelta(days=1)
        cid = c["id"]
        if cid in ATRASO:
            alvo = venc + dt.timedelta(days=ATRASO[cid])
            if alvo > FIM: continue
        if c["npag"] == 1 and cid in PARCIAL:
            alvo = PARCIAL[cid][1]
        if alvo != dia: continue
        if cid in PARCIAL and c["npag"] == 0:
            paga_conta(cid, dia, m2(c["valor"] * PARCIAL[cid][0]), BANCO, 1, obs="Pagamento parcial: caixa insuficiente no dia")
        elif cid in PARCIAL:
            saldo = c["valor"] - c["pago"]
            dias = (dia - venc).days
            juros = m2(saldo * (D("0.02") + D("0.00033") * dias))
            paga_conta(cid, dia, saldo, BANCO, 1, juros=juros, obs=f"Quitação do saldo com {dias} dias de atraso (multa 2% + juros)")
        else:
            dias = max(0, (dia - venc).days)
            juros = m2(c["valor"] * (D("0.02") + D("0.00033") * dias)) if dias > 1 else D("0")
            paga_conta(cid, dia, c["valor"], BANCO, 1, juros=juros,
                       obs=(f"Pago com {dias} dias de atraso" if juros else None))

ATRASO = {}
PARCIAL = {}

# ------------------------------------------------------------------ repasses, depósitos e conciliação
DEB_ESQUECIDO = {}
def repasses(dia):
    # débito D+1: um crédito por dia de venda; Pix: um crédito por transação no próprio dia
    ontem = dia - dt.timedelta(days=1)
    deb = [t for t in transacoes if t["data"] == ontem and t["forma"] == "DEB" and venda_conc.get(t["venda"])]
    if ontem == dt.date(2026, 9, 12) and deb:
        DEB_ESQUECIDO["t"] = deb[len(deb) // 2]
        deb = [t for t in deb if t is not DEB_ESQUECIDO["t"]]   # transação não repassada pela adquirente
    if deb and ontem >= INICIO:
        bruto = sum((t["valor"] for t in deb), D("0"))
        taxa_pct = TAXA["DEB"] if ontem != dt.date(2026, 9, 19) else D("1.99")   # taxa cobrada acima da contratada
        taxa = m2(bruto * taxa_pct / 100)
        mf = mov_fin(BANCO, dia, "CREDITO", "REPASSE_CARTAO", bruto, taxa=taxa, doc=f"REP-DEB-{ontem.strftime('%Y%m%d')}")
        for t in deb:
            rows["pagamento_venda"][t["idx"]]["id_movimento_fin"] = mf

def pix_do_dia(dia):
    for t in [t for t in transacoes if t["data"] == dia and t["forma"] == "PIX" and venda_conc.get(t["venda"])]:
        mf = mov_fin(BANCO, dia, "CREDITO", "PIX_RECEBIDO", t["valor"], doc=f"PIX-{t['nsu']}")
        rows["pagamento_venda"][t["idx"]]["id_movimento_fin"] = mf

def deposito(dia):
    if dia.weekday() not in (1, 4): return
    saldo_cofre = saldo_conta(COFRE)
    v = m2((saldo_cofre - D("1000")) / 100) * 100
    v = m2((saldo_cofre - D("1000")).quantize(D("1")) // 100 * 100)
    if v >= 500:
        mov_fin(COFRE, dia, "DEBITO", "DEPOSITO", v, doc=f"DEP-{dia.strftime('%Y%m%d')}-C", func=1)
        mov_fin(BANCO, dia, "CREDITO", "DEPOSITO", v, doc=f"DEP-{dia.strftime('%Y%m%d')}-B", func=1)

def saldo_conta(cf):
    s = [c for c in rows["conta_financeira"] if c["id_conta_financeira"] == cf][0]["saldo_inicial"]
    for m in rows["movimento_financeiro"]:
        if m["id_conta_financeira"] != cf: continue
        s += (m["valor_bruto"] - m["valor_taxa"]) if m["natureza"] == "CREDITO" else -(m["valor_bruto"] + m["valor_taxa"])
    return s

saldo_banco_min = [D("999999"), None]
def tarifa(dia):
    if dia == dt.date(2026, 9, 30):
        mov_fin(BANCO, dia, "DEBITO", "TARIFA", D("39.90"), doc="TAR-092026", func=1)

# ------------------------------------------------------------------ ajustes de inventário (09/15) e RN-40
def ajustes(dia):
    if dia == dt.date(2026, 9, 15):
        quando = ts(dia, 20, 40)
        # Skol: 6 latas a menos na contagem
        Ls = lotes_vendaveis(12, dia)
        mov(Ls[0]["id"], "AJUSTE_INVENTARIO_SAIDA", D("6"), quando, func=1,
            motivo="Contagem física: 6 latas a menos que o sistema (quebra/furto)")
        # Brahma: contagem feita só na gôndola, esquecendo o depósito (erro que gera o RN-40 do dia 16)
        for L in lotes_vendaveis(13, dia):
            mov(L["id"], "AJUSTE_INVENTARIO_SAIDA", L["saldo"], quando, func=1,
                motivo="Contagem física: gôndola sem Brahma 473 (depósito não foi contado)")
        # Sabão em pó: 1 caixa a mais
        L = lotes_vendaveis(19, dia)[-1]
        mov(L["id"], "AJUSTE_INVENTARIO_ENTRADA", D("1"), quando, func=1,
            motivo="Contagem física: 1 caixa a mais (recebimento contado a menos)")
    if dia == dt.date(2026, 9, 17):
        # conferência do lote de ajuste RN-40 de 16/09: depósito tinha mais 18 latas
        aj = [L for L in LOTES.values() if L["origem"] == "AJUSTE_INVENTARIO" and L["pend"]]
        for L in aj:
            mov(L["id"], "AJUSTE_INVENTARIO_ENTRADA", D("18"), ts(dia, 8, 0), func=1,
                motivo="Conferência do ajuste RN-40: 18 latas encontradas no depósito")
            L["pend"] = False
            L["val"] = dt.date(2026, 12, 10)   # validade lida nas latas durante a conferência
    if dia == dt.date(2026, 9, 19):
        L = lotes_vendaveis(14, dia)
        mov(L[0]["id"], "PERDA_AVARIA", D("1"), ts(dia, 15, 10), func=6, motivo="Garrafa caiu da gôndola e quebrou")

# ------------------------------------------------------------------ laço principal
contas_fixas()
dia = INICIO
while dia <= FIM:
    for (d_, c) in MUDA_CUSTO.items():
        if d_ == dia:
            for (k, v) in c: custo_atual[k] = D(v)
    if dia > INICIO:
        rotina_validade(dia)
    compras(dia)
    entrega_oleo(dia)
    ajustes(dia)
    repasses(dia)
    dia_operacao(dia)
    rotina_hortifruti(dia)
    pagamentos_do_dia(dia)
    deposito(dia)
    tarifa(dia)
    sb = saldo_conta(BANCO)
    if sb < saldo_banco_min[0]: saldo_banco_min[:] = [sb, dia]
    dia += dt.timedelta(days=1)

# kardex em ordem cronológica (nenhuma tabela referencia movimentacao_estoque, então renumerar é seguro)
rows["movimentacao_estoque"].sort(key=lambda m: (m["data_hora"], m["id_movimentacao"]))
for i, m in enumerate(rows["movimentacao_estoque"], 1):
    m["id_movimentacao"] = i
aplica_precos(ts(FIM, 23, 59))
for e in rows["embalagem"]:
    e["preco_venda"] = preco[e["id_embalagem"]]
# ------------------------------------------------------------------ estado final dos lotes
for L in LOTES.values():
    rows["lote"].append(dict(id_lote=L["id"], id_produto=L["prod"], id_recebimento=L["rec"], numero_item_nota=L["item"],
                             id_lote_reposto=L["reposto"], origem=L["origem"], codigo_lote_fabricante=L["cod"],
                             data_validade=(str(L["val"]) if L["val"] else None), data_entrada=L["entrada"],
                             custo_unitario=L["custo"], situacao=L["sit"], pendente_conferencia=L["pend"]))

STATS = dict(saldo_banco_min=saldo_banco_min, banco_final=saldo_conta(BANCO), cofre_final=saldo_conta(COFRE),
             deb_esquecido=DEB_ESQUECIDO.get("t"), rn40=RN40_EVENTOS)
