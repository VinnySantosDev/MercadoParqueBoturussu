# Modelo conceitual do Supermercado Parque Boturussu (Entrega 1, seções 10 a 14)
# kinds: pk, pkfk, fk, fko, req, opt, der, comp, mv

MODULES = {
    "PE": ("Produtos e Estoque", "#DCEBFA"),
    "CF": ("Compras e Fornecedores", "#FBE7CF"),
    "VC": ("Vendas e Caixa", "#DDF2DF"),
    "FF": ("Financeiro e Fiado", "#F6DDE4"),
    "PA": ("Pessoas e Acesso", "#E7E1F5"),
}

E = {}
def ent(name, mod, attrs):
    E[name] = {"mod": mod, "attrs": attrs}

ent("CATEGORIA", "PE", [
    ("nome_categoria", "pk"), ("controle_validade_rigoroso", "req"),
    ("dias_alerta_validade_padrao", "opt")])
ent("PRODUTO", "PE", [
    ("nome_produto", "pk"), ("nome_categoria", "fk"), ("marca", "opt"),
    ("unidade_base", "req"), ("vendido_por_peso", "req"), ("controla_validade", "req"),
    ("dias_alerta_validade", "opt"), ("estoque_minimo", "req"),
    ("margem_referencia", "opt"), ("ativo", "req"), ("estoque_atual", "der")])
ent("EMBALAGEM", "PE", [
    ("codigo_barras", "pk"), ("nome_produto", "fk"), ("descricao", "req"),
    ("fator_conversao", "req"), ("preco_venda", "req"), ("ativa", "req")])
ent("HISTORICO_PRECO", "PE", [
    ("codigo_barras", "pkfk"), ("data_hora", "pk"), ("cpf_funcionario", "fk"),
    ("preco_anterior", "req"), ("preco_novo", "req"), ("motivo", "req")])
ent("LOTE", "PE", [
    ("cnpj_fornecedor", "pkfk"), ("numero_nota", "pkfk"), ("nome_produto", "pkfk"),
    ("quantidade_recebida", "req"), ("custo_unitario", "req"), ("data_validade", "opt"),
    ("situacao", "req"), ("quantidade_atual", "der"), ("dias_para_vencer", "der")])
ent("MOVIMENTACAO_ESTOQUE", "PE", [
    ("cnpj_fornecedor", "pkfk"), ("numero_nota", "pkfk"), ("nome_produto", "pkfk"),
    ("data_hora", "pk"), ("tipo", "req"), ("quantidade", "req"), ("motivo", "opt"),
    ("cpf_responsavel", "fko"), ("numero_caixa_venda", "fko"),
    ("data_hora_venda", "fko"), ("numero_item", "fko")])

ent("FORNECEDOR", "CF", [
    ("cnpj", "pk"), ("razao_social", "req"), ("nome_fantasia", "opt"),
    ("contatos", "mv"), ("canal_pedido", "req"), ("condicao_pagamento_padrao", "opt"),
    ("ativo", "req")])
ent("PEDIDO_COMPRA", "CF", [
    ("cnpj_fornecedor", "pkfk"), ("data_hora_pedido", "pk"), ("cpf_funcionario", "fk"),
    ("canal", "req"), ("situacao", "req"), ("observacao", "opt"), ("valor_previsto", "der")])
ent("RECEBIMENTO", "CF", [
    ("cnpj_fornecedor", "pkfk"), ("numero_nota", "pk"), ("data_hora_pedido", "fko"),
    ("cpf_conferente", "fk"), ("data_hora", "req"), ("valor_total_nota", "req"),
    ("volumes_nota", "req"), ("volumes_conferidos", "req"), ("situacao", "req"),
    ("observacao_divergencia", "opt")])

ent("VENDA", "VC", [
    ("numero_caixa", "pkfk"), ("data_hora", "pk"), ("data_hora_abertura", "fk"),
    ("cpf_operador", "fk"), ("cpf_cliente", "fko"), ("situacao", "req"),
    ("valor_bruto", "der"), ("valor_desconto", "der"), ("valor_total", "der")])
ent("ITEM_VENDA", "VC", [
    ("numero_caixa", "pkfk"), ("data_hora_venda", "pkfk"), ("numero_item", "pk"),
    ("codigo_barras", "fk"), ("cpf_autorizador", "fko"), ("quantidade", "req"),
    ("preco_unitario_praticado", "req"), ("desconto_unitario", "req"),
    ("custo_unitario_referencia", "req"), ("valor_item", "der")])
ent("FORMA_PAGAMENTO", "VC", [
    ("nome_forma", "pk"), ("prazo_credito_dias", "req"), ("taxa_percentual", "req"),
    ("gera_divida", "req"), ("ativa", "req")])
ent("PAGAMENTO_VENDA", "VC", [
    ("numero_caixa", "pkfk"), ("data_hora_venda", "pkfk"), ("nome_forma", "pkfk"),
    ("valor", "req"), ("valor_entregue", "opt"), ("situacao_credito", "req"),
    ("troco", "der"), ("data_prevista_credito", "der")])
ent("CAIXA", "VC", [("numero_caixa", "pk"), ("ativo", "req")])
ent("SESSAO_CAIXA", "VC", [
    ("numero_caixa", "pkfk"), ("data_hora_abertura", "pk"), ("cpf_abertura", "fk"),
    ("cpf_fechamento", "fko"), ("valor_inicial", "req"), ("data_hora_fechamento", "opt"),
    ("valor_contado", "opt"), ("situacao", "req"), ("valor_esperado", "der"),
    ("diferenca", "der")])
ent("MOVIMENTACAO_CAIXA", "VC", [
    ("numero_caixa", "pkfk"), ("data_hora_abertura", "pkfk"), ("data_hora", "pk"),
    ("cpf_responsavel", "fk"), ("tipo", "req"), ("valor", "req"), ("motivo", "req")])

ent("CLIENTE", "FF", [
    ("cpf", "pk"), ("nome", "req"), ("apelido", "opt"), ("telefone", "opt"),
    ("endereco", "comp"), ("autorizado_fiado", "req"), ("limite_fiado", "opt"),
    ("data_cadastro", "req"), ("saldo_devedor", "der")])
ent("ABATIMENTO_FIADO", "FF", [
    ("cpf_cliente", "pkfk"), ("data_hora", "pk"), ("nome_forma", "fk"),
    ("cpf_recebedor", "fk"), ("numero_caixa", "fko"), ("data_hora_abertura", "fko"),
    ("valor", "req"), ("observacao", "opt")])
ent("CONTA_PAGAR", "FF", [
    ("credor", "pk"), ("numero_documento", "pk"), ("numero_parcela", "pk"),
    ("cnpj_fornecedor", "fko"), ("numero_nota", "fko"), ("cpf_quitante", "fko"),
    ("descricao", "req"), ("categoria_despesa", "req"), ("valor", "req"),
    ("data_vencimento", "req"), ("prioridade", "req"), ("data_pagamento", "opt"),
    ("valor_pago", "opt"), ("situacao", "req"), ("juros_pagos", "der"), ("vencida", "der")])

ent("FUNCIONARIO", "PA", [
    ("cpf", "pk"), ("nome", "req"), ("telefone", "opt"), ("funcao_principal", "req"),
    ("login", "req"), ("data_admissao", "req"), ("ativo", "req")])
ent("PERMISSAO", "PA", [("codigo_permissao", "pk"), ("descricao", "req")])

# (id, A, cardA, verbo, B, cardB, nn_note)
R = [
    ("R01", "CATEGORIA", "(0,N)", "classifica", "PRODUTO", "(1,1)", None),
    ("R02", "PRODUTO", "(1,N)", "é vendido em", "EMBALAGEM", "(1,1)", None),
    ("R03", "EMBALAGEM", "(0,N)", "registra", "HISTORICO_PRECO", "(1,1)", None),
    ("R04", "FUNCIONARIO", "(0,N)", "altera", "HISTORICO_PRECO", "(1,1)", None),
    ("R05", "FORNECEDOR", "(0,N)", "FORNECE", "PRODUTO", "(0,N)",
     ["PK/FK: cnpj_fornecedor + nome_produto", "● preco_ultima_compra",
      "● data_ultima_compra", "○ codigo_no_fornecedor"]),
    ("R06", "FORNECEDOR", "(0,N)", "atende", "PEDIDO_COMPRA", "(1,1)", None),
    ("R07", "FUNCIONARIO", "(0,N)", "emite", "PEDIDO_COMPRA", "(1,1)", None),
    ("R08", "PEDIDO_COMPRA", "(1,N)", "SOLICITA", "PRODUTO", "(0,N)",
     ["PK/FK: cnpj_fornecedor + data_hora_pedido", "+ nome_produto",
      "● quantidade_pedida", "○ preco_negociado"]),
    ("R09", "PEDIDO_COMPRA", "(0,N)", "é atendido por", "RECEBIMENTO", "(0,1)", None),
    ("R10", "FORNECEDOR", "(0,N)", "entrega", "RECEBIMENTO", "(1,1)", None),
    ("R11", "FUNCIONARIO", "(0,N)", "confere", "RECEBIMENTO", "(1,1)", None),
    ("R12", "RECEBIMENTO", "(0,N)", "origina", "LOTE", "(1,1)", None),
    ("R13", "PRODUTO", "(0,N)", "possui", "LOTE", "(1,1)", None),
    ("R14", "LOTE", "(1,N)", "sofre", "MOVIMENTACAO_ESTOQUE", "(1,1)", None),
    ("R15", "FUNCIONARIO", "(0,N)", "registra", "MOVIMENTACAO_ESTOQUE", "(0,1)", None),
    ("R16", "ITEM_VENDA", "(0,N)", "gera", "MOVIMENTACAO_ESTOQUE", "(0,1)", None),
    ("R17", "RECEBIMENTO", "(0,N)", "gera", "CONTA_PAGAR", "(0,1)", None),
    ("R18", "FUNCIONARIO", "(0,N)", "quita", "CONTA_PAGAR", "(0,1)", None),
    ("R19", "CAIXA", "(0,N)", "possui", "SESSAO_CAIXA", "(1,1)", None),
    ("R20", "FUNCIONARIO", "(0,N)", "abre", "SESSAO_CAIXA", "(1,1)", None),
    ("R21", "FUNCIONARIO", "(0,N)", "fecha", "SESSAO_CAIXA", "(0,1)", None),
    ("R22", "SESSAO_CAIXA", "(0,N)", "registra", "VENDA", "(1,1)", None),
    ("R23", "FUNCIONARIO", "(0,N)", "opera", "VENDA", "(1,1)", None),
    ("R24", "CLIENTE", "(0,N)", "realiza", "VENDA", "(0,1)", None),
    ("R25", "VENDA", "(1,N)", "contém", "ITEM_VENDA", "(1,1)", None),
    ("R26", "EMBALAGEM", "(0,N)", "é vendida em", "ITEM_VENDA", "(1,1)", None),
    ("R27", "FUNCIONARIO", "(0,N)", "autoriza desconto", "ITEM_VENDA", "(0,1)", None),
    ("R28", "VENDA", "(1,N)", "é paga por", "PAGAMENTO_VENDA", "(1,1)", None),
    ("R29", "FORMA_PAGAMENTO", "(0,N)", "é usada em", "PAGAMENTO_VENDA", "(1,1)", None),
    ("R30", "SESSAO_CAIXA", "(0,N)", "registra", "MOVIMENTACAO_CAIXA", "(1,1)", None),
    ("R31", "FUNCIONARIO", "(0,N)", "executa", "MOVIMENTACAO_CAIXA", "(1,1)", None),
    ("R32", "CLIENTE", "(0,N)", "paga", "ABATIMENTO_FIADO", "(1,1)", None),
    ("R33", "FORMA_PAGAMENTO", "(0,N)", "é usada em", "ABATIMENTO_FIADO", "(1,1)", None),
    ("R34", "FUNCIONARIO", "(0,N)", "recebe", "ABATIMENTO_FIADO", "(1,1)", None),
    ("R35", "SESSAO_CAIXA", "(0,N)", "contabiliza", "ABATIMENTO_FIADO", "(0,1)", None),
    ("R36", "FUNCIONARIO", "(0,N)", "POSSUI", "PERMISSAO", "(0,N)",
     ["PK/FK: cpf_funcionario + codigo_permissao", "● data_concessao"]),
]

assert len(E) == 21 and len(R) == 36
