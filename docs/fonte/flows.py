# Fluxogramas F1-F6 e mapa de integração (Figura 1), transcritos da Entrega 1 (seções 3.1 e 9)
import subprocess, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img")
os.makedirs(OUT, exist_ok=True)
FONT = "DejaVu Sans"
INK = "#1F2328"; MUTED = "#6B7280"
STY = {
    "ini": f'shape=ellipse style=filled fillcolor="#F3F4F6"',
    "p":   f'shape=box style="rounded,filled" fillcolor="#FFFFFF"',          # pessoa
    "s":   f'shape=box style=filled fillcolor="#DCEBFA"',                    # sistema
    "d":   f'shape=diamond style=filled fillcolor="#FFF7E0" margin="0.05,0.03"',
    "x":   f'shape=box style="rounded,filled" peripheries=2 fillcolor="#FDE2E1"',  # exceção
}

def legend():
    return ('  subgraph cluster_leg { label=<<b>Legenda</b>> fontsize=11 style="rounded,dashed" color="#9CA3AF" fontcolor="#374151";\n'
            f'    L1 [{STY["ini"]} label="Início / fim" fontsize=10];\n'
            f'    L2 [{STY["p"]} label="Atividade de pessoa" fontsize=10];\n'
            f'    L3 [{STY["s"]} label="Ação do sistema" fontsize=10];\n'
            f'    L4 [{STY["d"]} label="Decisão" fontsize=10];\n'
            f'    L5 [{STY["x"]} label="Exceção" fontsize=10];\n'
            '    L1 -> L2 -> L3 -> L4 -> L5 [style=invis];\n  }')

def flow(fname, title, nodes, edges, legend_on=True):
    L = ["digraph F {",
         f'  graph [rankdir=TB bgcolor="white" pad="0.35" nodesep=0.45 ranksep=0.42 dpi=200 '
         f'fontname="{FONT}" labelloc=t fontsize=16 label=<<b>{title}</b><br/> >];',
         f'  node [fontname="{FONT}" fontsize=11 color="{INK}" fontcolor="{INK}" margin="0.18,0.07"];',
         f'  edge [color="{INK}" fontname="{FONT}" fontsize=10 fontcolor="#374151" arrowsize=0.8];']
    for nid, kind, text in nodes:
        L.append(f'  {nid} [{STY[kind]} label="{text}"];')
    for e in edges:
        a, b = e[0], e[1]
        lab = e[2] if len(e) > 2 else ""
        extra = e[3] if len(e) > 3 else ""
        L.append(f'  {a} -> {b} [label="{(" " + lab + " ") if lab else ""}" {extra}];')
    if legend_on:
        L.append(legend())
    L.append("}")
    p = f"{OUT}/{fname}"
    open(p + ".dot", "w").write("\n".join(L))
    subprocess.run(["dot", "-Tpng", p + ".dot", "-o", p + ".png"], check=True)
    subprocess.run(["dot", "-Tsvg", p + ".dot", "-o", p + ".svg"], check=True)

# ---------- F1 ----------
flow("figura-02-f1-compra-recebimento", "F1 - Compra e recebimento de mercadoria (P1)", [
    ("a", "ini", "Início"),
    ("b", "s", "Sistema lista produtos\\nabaixo do estoque mínimo"),
    ("c", "p", "Funcionário consulta\\npreços por fornecedor"),
    ("d", "s", "Registrar PEDIDO_COMPRA\\n(WhatsApp / app / vendedor)"),
    ("e", "p", "Mercadoria chega\\ncom nota fiscal"),
    ("f", "d", "Volumes da nota\\n= volumes entregues?"),
    ("g", "p", "Conferir item a item\\n(itens x nota x pedido)"),
    ("h", "d", "Divergência?"),
    ("i", "d", "Muitas\\ndivergências?"),
    ("j", "p", "Aceitar com divergência\\n(registrar faltas / itens\\nnão pedidos)"),
    ("k", "x", "RECUSAR recebimento\\ne contatar fornecedor"),
    ("l", "p", "Informar validade e custo\\nde cada produto aceito"),
    ("m", "s", "Gerar LOTES + movimentação\\nENTRADA_RECEBIMENTO"),
    ("n", "d", "Custo subiu?"),
    ("o", "s", "Sugerir novo preço pela\\nmargem de referência"),
    ("p", "p", "Funcionário autorizado\\naltera preço\\n(HISTORICO_PRECO)"),
    ("q", "s", "Gerar CONTA_PAGAR\\n(à vista ou 7/14/21)"),
    ("r", "s", "Atualizar situação do pedido\\n(parcial / recebido / recusado)"),
    ("z", "ini", "Fim"),
], [
    ("a","b"),("b","c"),("c","d"),("d","e"),("e","f"),
    ("f","g","sim"),("f","i","não"),("g","h"),("h","l","não"),("h","i","sim"),
    ("i","j","não"),("i","k","sim"),("j","l"),("l","m"),("m","n"),
    ("n","o","sim"),("o","p"),("p","q"),("n","q","não"),("q","r"),("k","r"),("r","z"),
])

# ---------- F2 ----------
flow("figura-03-f2-venda-caixa", "F2 - Venda no caixa, incluindo fiado (P3)", [
    ("a", "ini", "Início"),
    ("b", "d", "Sessão de caixa\\naberta?"),
    ("c", "p", "Operador abre sessão\\n(informa fundo de troco)"),
    ("d", "p", "Ler código de barras\\nou pesar o item"),
    ("e", "d", "Código\\nencontrado?"),
    ("f", "p", "Buscar produto por nome\\n(item sem código)"),
    ("g", "d", "Desconto\\nno item?"),
    ("h", "p", "Funcionário com permissão\\nautoriza o desconto"),
    ("i", "s", "Registrar ITEM_VENDA\\n(preço e custo congelados)"),
    ("j", "d", "Mais itens?"),
    ("k", "p", "Escolher forma(s)\\nde pagamento"),
    ("l", "d", "Fiado?"),
    ("m", "d", "Cliente cadastrado,\\nautorizado e dentro\\ndo limite?"),
    ("n", "s", "Vincular CLIENTE à venda\\n(dívida aumenta o saldo)"),
    ("o", "x", "Recusar fiado:\\nescolher outra forma"),
    ("p", "s", "Registrar PAGAMENTO_VENDA\\n(prevê data de crédito)"),
    ("q", "s", "Baixar estoque por lote\\n(FEFO: vence primeiro,\\nsai primeiro)"),
    ("r", "s", "Estoque < mínimo?\\nGerar alerta de reposição"),
    ("z", "ini", "Fim"),
], [
    ("a","b"),("b","c","não"),("b","d","sim"),("c","d"),("d","e"),
    ("e","f","não"),("e","g","sim"),("f","g"),("g","h","sim"),("g","i","não"),("h","i"),
    ("i","j"),("j","d","sim","constraint=false"),("j","k","não"),("k","l"),
    ("l","m","sim"),("l","p","não"),("m","n","sim"),("m","o","não"),("o","k","","constraint=false"),
    ("n","p"),("p","q"),("q","r"),("r","z"),
])

# ---------- F3 ----------
flow("figura-04-f3-validade-perdas", "F3 - Controle de validade e tratamento de perdas (P4)", [
    ("a", "ini", "Início (diário)"),
    ("b", "s", "Sistema lista lotes com\\nvencimento dentro do prazo\\nde alerta (categoria/produto)"),
    ("c", "p", "Funcionário localiza lotes\\nna gôndola/estoque"),
    ("d", "d", "Lote já\\nvenceu?"),
    ("e", "d", "Aplicar\\npromoção?"),
    ("f", "p", "Alterar preço com motivo\\nPROXIMO_VENCIMENTO"),
    ("g", "p", "Retirar da gôndola e\\nseparar para troca"),
    ("h", "s", "Movimentação\\nPERDA_VENCIMENTO\\n(lote = SEPARADO_TROCA)"),
    ("i", "d", "Fornecedor\\ntroca?"),
    ("j", "s", "Movimentação\\nTROCA_FORNECEDOR\\n(novo lote de entrada)"),
    ("k", "s", "Lote = DESCARTADO\\n(perda definitiva)"),
    ("l", "s", "Atualizar relatório de\\nperdas por produto"),
    ("z", "ini", "Fim"),
], [
    ("a","b"),("b","c"),("c","d"),("d","e","não"),("d","g","sim"),
    ("e","f","sim"),("e","l","não"),("f","l"),("g","h"),("h","i"),
    ("i","j","sim"),("i","k","não"),("j","l"),("k","l"),("l","z"),
])

# ---------- F4 ----------
flow("figura-05-f4-caixa", "F4 - Abertura, conferência e fechamento de caixa (P5)", [
    ("a", "ini", "Início"),
    ("a2", "p", "Operador abre SESSAO_CAIXA\\ninformando o fundo de troco"),
    ("b", "d", "Excesso de dinheiro\\nna gaveta durante\\no dia?"),
    ("c", "p", "Registrar SANGRIA\\n(valor, motivo, responsável)"),
    ("d", "p", "Operador encerra\\nas vendas da sessão"),
    ("e", "s", "Sistema calcula valor\\nesperado por forma\\nde pagamento"),
    ("f", "p", "Operador conta o\\ndinheiro físico"),
    ("g", "p", "Conferir cartão/Pix com\\nrelatório das maquininhas"),
    ("h", "d", "Diferença\\n≠ 0?"),
    ("i", "p", "Registrar justificativa\\n(gerente é notificado)"),
    ("j", "s", "Fechar SESSAO_CAIXA\\n(registra quem fechou)"),
    ("k", "s", "Consolidar faturamento\\ne lucro do dia"),
    ("z", "ini", "Fim"),
], [
    ("a","a2"),("a2","b"),("b","c","sim"),("b","d","não"),("c","d"),("d","e"),("e","f"),("f","g"),
    ("g","h"),("h","i","sim"),("h","j","não"),("i","j"),("j","k"),("k","z"),
])

# ---------- F5 ----------
flow("figura-06-f5-contas-pagar", "F5 - Contas a pagar e previsão de caixa (P7)", [
    ("a", "ini", "Início"),
    ("b", "p", "Boleto/conta chega\\n(fornecedor, Simples,\\nfolha, internet...)"),
    ("c", "s", "Registrar CONTA_PAGAR\\n(vencimento, prioridade)"),
    ("d", "s", "Diariamente: somar contas\\na vencer em 7 dias"),
    ("e", "s", "Somar saldo previsto:\\ndinheiro + créditos de cartão/\\nPix a cair no período"),
    ("f", "d", "Saldo previsto\\n< contas a vencer?"),
    ("g", "x", "ALERTA ao gerente:\\nfalta de caixa prevista"),
    ("h", "d", "Conta paga?"),
    ("i", "p", "Registrar pagamento\\n(data, valor pago, juros)"),
    ("z", "ini", "Fim"),
], [
    ("a","b"),("b","c"),("c","d"),("d","e"),("e","f"),("f","g","sim"),("f","h","não"),
    ("g","h"),("h","i","sim"),("h","d","não (próximo dia)","constraint=false"),("i","z"),
])

# ---------- F6 ----------
flow("figura-07-f6-fiado", "F6 - Recebimento de fiado (P6)", [
    ("a", "ini", "Início"),
    ("b", "p", "Cliente vai ao caixa\\npagar o fiado"),
    ("c", "s", "Sistema mostra saldo\\ndevedor e histórico"),
    ("d", "p", "Cliente informa valor\\n(total ou parcial)"),
    ("e", "d", "Valor ≤ saldo?"),
    ("f", "x", "Ajustar valor"),
    ("g", "s", "Registrar ABATIMENTO_FIADO\\n(forma, funcionário, sessão)"),
    ("h", "d", "Saldo = 0?"),
    ("i", "s", "Cliente quitado\\n(histórico preservado)"),
    ("z", "ini", "Fim"),
], [
    ("a","b"),("b","c"),("c","d"),("d","e"),("e","g","sim"),("e","f","não"),
    ("f","d","","constraint=false"),("g","h"),("h","i","sim"),("h","z","não"),("i","z"),
])

# ---------- Figura 1: mapa de integração ----------
P = {
 "P1": "P1 Compra e\\nrecebimento", "P2": "P2 Cadastro e\\npreço de produto",
 "P3": "P3 Venda\\nno caixa", "P4": "P4 Controle de\\nvalidade e perdas",
 "P5": "P5 Abertura/fechamento\\nde caixa", "P6": "P6 Fiado",
 "P7": "P7 Contas\\na pagar", "P8": "P8 Relatórios\\ne decisão",
}
E = [("P1","P2","custo da nota"),("P1","P4","lote com validade"),("P1","P7","boletos 7/14/21"),
     ("P2","P3","preço vigente"),("P3","P4","baixa de estoque (FEFO)"),
     ("P3","P5","vendas por forma\\nde pagamento"),("P3","P6","venda fiada"),
     ("P6","P5","abatimento\\nem dinheiro"),("P4","P2","promoção por\\nvencimento"),
     ("P4","P1","troca e reposição"),("P5","P7","saldo disponível"),
     ("P3","P8",""),("P4","P8",""),("P6","P8",""),("P7","P8","")]
L = ["digraph M {",
     f'  graph [rankdir=LR bgcolor="white" pad="0.4" nodesep=0.6 ranksep=1.1 dpi=200 fontname="{FONT}" '
     f'labelloc=t fontsize=16 label=<<b>Mapa de integração entre os processos de negócio</b><br/> >];',
     f'  node [shape=box style="rounded,filled" fillcolor="#DCEBFA" color="{INK}" fontname="{FONT} Bold" fontsize=12 margin="0.2,0.1"];',
     f'  edge [color="{INK}" fontname="{FONT}" fontsize=10 fontcolor="#B42318" arrowsize=0.8];']
for k, v in P.items():
    fill = ' fillcolor="#E7E1F5"' if k == "P8" else ""
    L.append(f'  {k} [label="{v}"{fill}];')
for a, b, t in E:
    extra = ' constraint=false' if (a, b) in [("P4","P1"),("P4","P2"),("P6","P5")] else ""
    lab = f'taillabel="{t}" labeldistance=3.2 labelangle=-40 labelfontcolor="#B42318" labelfontsize=10' if (a, b) == ("P6","P5") else f'label="{t}"'
    L.append(f'  {a} -> {b} [{lab}{extra}];')
L.append('  {rank=same; P2; P4} {rank=same; P5; P6}')
L.append("}")
p = f"{OUT}/figura-01-integracao-processos"
open(p + ".dot", "w").write("\n".join(L))
subprocess.run(["dot", "-Tpng", p + ".dot", "-o", p + ".png"], check=True)
subprocess.run(["dot", "-Tsvg", p + ".dot", "-o", p + ".svg"], check=True)
