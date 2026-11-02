# -*- coding: utf-8 -*-
"""Modelo lógico/físico do Mercado Parque Boturussu — FONTE ÚNICA.
O DDL (sql/ddl/02_tabelas.sql), o dicionário de dados e o diagrama do modelo
lógico são gerados a partir deste arquivo. Assim, SQL e documentação não divergem.
SGBD alvo: MySQL 8.0 (testado em 8.0.46)."""

T = {}          # nome -> dict
ORDER = []      # ordem de criação (respeita dependências de FK)

def C(nome, tipo, nulo, desc, regra="", default=None, ai=False):
    return dict(nome=nome, tipo=tipo, nulo=nulo, desc=desc, regra=regra, default=default, ai=ai)

def table(nome, origem, desc, cols, pk, uq=(), fk=(), ck=(), conceito=""):
    T[nome] = dict(nome=nome, origem=origem, desc=desc, cols=cols, pk=pk,
                   uq=list(uq), fk=list(fk), ck=list(ck), conceito=conceito)
    ORDER.append(nome)

ID = "INT UNSIGNED"
MON = "DECIMAL(12,2)"
QTD = "DECIMAL(12,3)"
CUSTO = "DECIMAL(12,4)"
BOOL = "BOOLEAN"
CPF_RE = "'^[0-9]{11}$'"

# ======================================================================
# PESSOAS E ACESSO
# ======================================================================
table("funcionario", "Entidade FUNCIONARIO",
      "Pessoa que trabalha no mercado e usa o sistema; responde “quem fez” em todas as operações.",
      [C("id_funcionario", ID, False, "Identificador do funcionário", "Chave substituta: evita espalhar o CPF pelas tabelas de operação (RNF-13)", ai=True),
       C("cpf", "CHAR(11)", False, "CPF, só dígitos", "Único; 11 dígitos"),
       C("login", "VARCHAR(30)", False, "Usuário de acesso ao sistema", "Único (RNF-01)"),
       C("nome", "VARCHAR(100)", False, "Nome completo"),
       C("telefone", "VARCHAR(15)", True, "Telefone de contato", "Só dígitos, 10 ou 11"),
       C("funcao_principal", "VARCHAR(20)", False, "Função habitual", "CAIXA, BALANCA, REPOSICAO, GERENCIA. Descritiva: o que pode fazer vem de funcionario_permissao"),
       C("data_admissao", "DATE", True, "Data de admissão"),
       C("ativo", BOOL, False, "Se pode acessar o sistema", "Inativo não opera (RNF-06: não se exclui)", default="TRUE")],
      pk=["id_funcionario"],
      uq=[("uq_funcionario_cpf", ["cpf"], "Um CPF identifica uma única pessoa (impede cadastro duplicado)"),
          ("uq_funcionario_login", ["login"], "Login individual (RNF-01)")],
      ck=[("ck_funcionario_cpf", f"cpf REGEXP {CPF_RE}", "Formato do CPF (11 dígitos)"),
          ("ck_funcionario_tel", "telefone IS NULL OR telefone REGEXP '^[0-9]{10,11}$'", "Telefone só com DDD + número"),
          ("ck_funcionario_funcao", "funcao_principal IN ('CAIXA','BALANCA','REPOSICAO','GERENCIA')", "Domínio da função")],
      conceito="FUNCIONARIO")

table("permissao", "Entidade PERMISSAO",
      "Operação sensível liberada individualmente (PO-01, PO-02, PO-11, PO-13, PO-14).",
      [C("codigo_permissao", "VARCHAR(30)", False, "Código da permissão", "Chave natural: código fixo definido pelo sistema (D-13)"),
       C("descricao", "VARCHAR(150)", False, "O que a permissão libera")],
      pk=["codigo_permissao"], conceito="PERMISSAO")

table("funcionario_permissao", "Relacionamento N:N POSSUI (R52) → tabela associativa",
      "Quais permissões cada funcionário tem e desde quando.",
      [C("id_funcionario", ID, False, "Funcionário", "FK → funcionario"),
       C("codigo_permissao", "VARCHAR(30)", False, "Permissão concedida", "FK → permissao"),
       C("data_concessao", "DATE", False, "Data da concessão", "Atributo do relacionamento; compõe a PK para permitir conceder de novo depois de revogar", default="(CURRENT_DATE)"),
       C("data_revogacao", "DATE", True, "Data em que a permissão foi retirada", "Vazio = vigente. Revogar não apaga a linha: a auditoria precisa saber quem podia o quê em cada data (RNF-02)")],
      pk=["id_funcionario", "codigo_permissao", "data_concessao"],
      fk=[("fk_fp_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "A permissão pertence a um funcionário existente"),
          ("fk_fp_permissao", ["codigo_permissao"], "permissao", ["codigo_permissao"], "Só se concede permissão cadastrada")],
      ck=[("ck_fp_periodo", "data_revogacao IS NULL OR data_revogacao >= data_concessao", "Não se revoga antes de conceder")],
      conceito="POSSUI (R52)")

# ======================================================================
# PRODUTOS E ESTOQUE
# ======================================================================
table("categoria", "Entidade CATEGORIA",
      "Setor do mercado; define o prazo padrão de alerta de validade.",
      [C("codigo_categoria", "VARCHAR(10)", False, "Sigla do setor", "Chave natural controlada pelo mercado (D-13)"),
       C("nome", "VARCHAR(50)", False, "Nome do setor", "Único"),
       C("controle_validade_rigoroso", BOOL, False, "Exige vigilância maior de validade", "Alimentos básicos = verdadeiro (entrevista 2.15)", default="FALSE"),
       C("dias_alerta_validade_padrao", "SMALLINT UNSIGNED", True, "Antecedência padrão do alerta de validade, em dias")],
      pk=["codigo_categoria"],
      uq=[("uq_categoria_nome", ["nome"], "Dois setores não podem ter o mesmo nome")],
      conceito="CATEGORIA")

table("produto", "Entidade PRODUTO",
      "Item comercializado; unidade de controle de estoque.",
      [C("id_produto", ID, False, "Identificador do produto", "Chave substituta (D-13)", ai=True),
       C("codigo_categoria", "VARCHAR(10)", False, "Setor do produto", "FK → categoria (RN-01)"),
       C("nome_produto", "VARCHAR(120)", False, "Nome padronizado (tipo, marca, variação)", "Único (chave alternativa)"),
       C("marca", "VARCHAR(60)", True, "Marca", "Vazio em hortifruti"),
       C("unidade_base", "CHAR(2)", False, "Unidade de contagem do estoque", "UN ou KG (RN-02)"),
       C("vendido_por_peso", BOOL, False, "Vendido fracionado na balança", "Se verdadeiro, unidade_base = KG (RN-02)", default="FALSE"),
       C("controla_validade", BOOL, False, "Exige data de validade no lote", "RN-15", default="TRUE"),
       C("dias_alerta_validade", "SMALLINT UNSIGNED", True, "Antecedência do alerta, em dias", "Sobrepõe o padrão da categoria"),
       C("estoque_minimo", QTD, False, "Estoque mínimo, na unidade base", ">= 0; dispara alerta (RF-19)", default="0"),
       C("margem_referencia", "DECIMAL(5,2)", True, "Margem de referência (%)", "0 a 300 (PO-09)"),
       C("ativo", BOOL, False, "Em comercialização", default="TRUE")],
      pk=["id_produto"],
      uq=[("uq_produto_nome", ["nome_produto"], "Nome padronizado não se repete (chave alternativa)")],
      fk=[("fk_produto_categoria", ["codigo_categoria"], "categoria", ["codigo_categoria"], "Todo produto pertence a um setor existente (R01, RN-01)")],
      ck=[("ck_produto_unidade", "unidade_base IN ('UN','KG')", "Domínio da unidade base (RN-02)"),
          ("ck_produto_peso_kg", "vendido_por_peso = FALSE OR unidade_base = 'KG'", "Produto pesado é contado em quilo (RN-02)"),
          ("ck_produto_estoque_min", "estoque_minimo >= 0", "Estoque mínimo não pode ser negativo"),
          ("ck_produto_margem", "margem_referencia IS NULL OR margem_referencia BETWEEN 0 AND 300", "Margem plausível (PO-09)")],
      conceito="PRODUTO")

table("embalagem", "Entidade EMBALAGEM",
      "Forma de venda de um produto, com código de leitura, fator de conversão e preço vigente.",
      [C("id_embalagem", ID, False, "Identificador da forma de venda", "Chave substituta (D-13)", ai=True),
       C("id_produto", ID, False, "Produto da embalagem", "FK → produto (RN-03)"),
       C("codigo_barras", "VARCHAR(14)", True, "GTIN/EAN de fábrica ou código interno (prefixo 2)", "Único quando existir (RN-04)"),
       C("codigo_balanca", "VARCHAR(6)", True, "Código do item na balança (PLU)", "Único quando existir; usado nos itens pesados (RN-04)"),
       C("descricao", "VARCHAR(60)", False, "Descrição da forma de venda", "Ex.: 'Lata 350 ml', 'Fardo 12 un', 'Quilo'"),
       C("fator_conversao", "DECIMAL(10,3)", False, "Unidades base por embalagem", "> 0 (fardo 12 = 12)"),
       C("preco_venda", "DECIMAL(10,2)", False, "Preço de venda vigente", "> 0; toda alteração gera historico_preco (RN-06)"),
       C("ativa", BOOL, False, "Pode ser vendida", default="TRUE")],
      pk=["id_embalagem"],
      uq=[("uq_embalagem_barras", ["codigo_barras"], "O mesmo código lido no caixa não pode apontar para duas embalagens"),
          ("uq_embalagem_balanca", ["codigo_balanca"], "Idem para o código da balança")],
      fk=[("fk_embalagem_produto", ["id_produto"], "produto", ["id_produto"], "Cada embalagem é de um único produto (R02)")],
      ck=[("ck_embalagem_codigo", "codigo_barras IS NOT NULL OR codigo_balanca IS NOT NULL", "Toda forma de venda precisa ser identificável no caixa (RN-04)"),
          ("ck_embalagem_barras_fmt", "codigo_barras IS NULL OR codigo_barras REGEXP '^[0-9]{8,14}$'", "GTIN tem de 8 a 14 dígitos"),
          ("ck_embalagem_balanca_fmt", "codigo_balanca IS NULL OR codigo_balanca REGEXP '^[0-9]{4,6}$'", "PLU numérico de 4 a 6 dígitos"),
          ("ck_embalagem_fator", "fator_conversao > 0", "Fator zero ou negativo baixaria estoque errado"),
          ("ck_embalagem_preco", "preco_venda > 0", "Preço de venda positivo")],
      conceito="EMBALAGEM")

table("historico_preco", "Entidade HISTORICO_PRECO",
      "Registro de cada alteração do preço de venda de uma embalagem.",
      [C("id_historico", ID, False, "Identificador da alteração", ai=True),
       C("id_embalagem", ID, False, "Embalagem alterada", "FK → embalagem"),
       C("id_funcionario", ID, False, "Quem alterou", "FK → funcionario (RN-07)"),
       C("data_hora", "DATETIME", False, "Momento da alteração", default="CURRENT_TIMESTAMP"),
       C("preco_anterior", "DECIMAL(10,2)", False, "Preço antes da alteração", "> 0"),
       C("preco_novo", "DECIMAL(10,2)", False, "Preço depois da alteração", "> 0 e diferente do anterior"),
       C("motivo", "VARCHAR(25)", False, "Razão da alteração", "REAJUSTE_FORNECEDOR, PROXIMO_VENCIMENTO, PROMOCAO, CORRECAO")],
      pk=["id_historico"],
      fk=[("fk_hp_embalagem", ["id_embalagem"], "embalagem", ["id_embalagem"], "A alteração refere-se a uma embalagem existente (R03)"),
          ("fk_hp_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Toda alteração tem responsável (R04, RN-07)")],
      ck=[("ck_hp_precos", "preco_anterior > 0 AND preco_novo > 0 AND preco_novo <> preco_anterior", "Registro só existe se o preço de fato mudou"),
          ("ck_hp_motivo", "motivo IN ('REAJUSTE_FORNECEDOR','PROXIMO_VENCIMENTO','PROMOCAO','CORRECAO')", "Domínio do motivo (PO-03)")],
      conceito="HISTORICO_PRECO")

# ======================================================================
# COMPRAS E FORNECEDORES
# ======================================================================
table("fornecedor", "Entidade FORNECEDOR",
      "Empresa, distribuidor ou produtor rural que vende ao mercado.",
      [C("id_fornecedor", ID, False, "Identificador do fornecedor", "Chave substituta (D-13)", ai=True),
       C("tipo_documento", "VARCHAR(4)", False, "Tipo do documento", "CNPJ ou CPF (produtor rural)"),
       C("documento", "VARCHAR(14)", False, "CNPJ (numérico ou alfanumérico) ou CPF", "Único"),
       C("razao_social", "VARCHAR(120)", False, "Nome jurídico ou nome do produtor"),
       C("nome_fantasia", "VARCHAR(80)", True, "Nome comercial"),
       C("canal_pedido", "VARCHAR(16)", False, "Meio usual de pedido", "WHATSAPP, APLICATIVO, VENDEDOR_VISITA"),
       C("condicao_pagamento_padrao", "VARCHAR(40)", True, "Condição usual", "Ex.: 'À vista', '7/14/21 dias' (PO-10)"),
       C("ativo", BOOL, False, "Em uso", default="TRUE")],
      pk=["id_fornecedor"],
      uq=[("uq_fornecedor_documento", ["documento"], "Mesmo CNPJ/CPF não pode ser cadastrado duas vezes")],
      ck=[("ck_fornecedor_doc", "(tipo_documento = 'CPF' AND documento REGEXP '^[0-9]{11}$') OR (tipo_documento = 'CNPJ' AND documento REGEXP '^[0-9A-Z]{12}[0-9]{2}$')",
           "Formato do documento: CPF com 11 dígitos; CNPJ com 12 posições alfanuméricas + 2 dígitos verificadores (formato vigente desde 07/2026)"),
          ("ck_fornecedor_canal", "canal_pedido IN ('WHATSAPP','APLICATIVO','VENDEDOR_VISITA')", "Domínio do canal")],
      conceito="FORNECEDOR")

table("contato_fornecedor", "Atributo multivalorado e composto FORNECEDOR.contatos → tabela (1FN)",
      "Cada vendedor/representante de um fornecedor.",
      [C("id_fornecedor", ID, False, "Fornecedor", "FK → fornecedor"),
       C("numero_contato", "TINYINT UNSIGNED", False, "Sequência do contato no fornecedor", "Discriminador: 1, 2, 3…"),
       C("nome", "VARCHAR(80)", False, "Nome do vendedor/representante"),
       C("telefone", "VARCHAR(15)", False, "Telefone", "Só dígitos"),
       C("usa_whatsapp", BOOL, False, "Atende por WhatsApp", default="FALSE")],
      pk=["id_fornecedor", "numero_contato"],
      fk=[("fk_contato_fornecedor", ["id_fornecedor"], "fornecedor", ["id_fornecedor"], "Contato existe só dentro de um fornecedor (entidade fraca)")],
      ck=[("ck_contato_tel", "telefone REGEXP '^[0-9]{10,11}$'", "Telefone com DDD")],
      conceito="FORNECEDOR.contatos")

table("produto_fornecedor", "Relacionamento N:N FORNECE (R09) → tabela associativa",
      "Quais produtos cada fornecedor fornece e com que código no catálogo dele.",
      [C("id_fornecedor", ID, False, "Fornecedor", "FK → fornecedor"),
       C("id_produto", ID, False, "Produto", "FK → produto"),
       C("codigo_no_fornecedor", "VARCHAR(30)", True, "Código do item no catálogo do fornecedor", "Depende do par (3FN: não fica em item_pedido)"),
       C("ativo", BOOL, False, "Par ainda em uso", default="TRUE")],
      pk=["id_fornecedor", "id_produto"],
      fk=[("fk_pf_fornecedor", ["id_fornecedor"], "fornecedor", ["id_fornecedor"], "Par aponta para fornecedor existente"),
          ("fk_pf_produto", ["id_produto"], "produto", ["id_produto"], "Par aponta para produto existente")],
      conceito="FORNECE (R09)")

table("pedido_compra", "Entidade PEDIDO_COMPRA",
      "Solicitação de mercadorias a um fornecedor.",
      [C("id_pedido", ID, False, "Identificador do pedido", "Chave substituta: pedido por WhatsApp não tem número", ai=True),
       C("id_fornecedor", ID, False, "Fornecedor", "FK → fornecedor (RN-10)"),
       C("id_funcionario", ID, False, "Quem fez o pedido", "FK → funcionario (PO-01)"),
       C("data_hora_pedido", "DATETIME", False, "Momento do pedido"),
       C("canal", "VARCHAR(16)", False, "Meio usado", "WHATSAPP, APLICATIVO, VENDEDOR_VISITA"),
       C("cancelado", BOOL, False, "Pedido cancelado", default="FALSE"),
       C("observacao", "VARCHAR(200)", True, "Anotações")],
      pk=["id_pedido"],
      fk=[("fk_pedido_fornecedor", ["id_fornecedor"], "fornecedor", ["id_fornecedor"], "Pedido dirigido a um fornecedor (R10)"),
          ("fk_pedido_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Pedido tem solicitante (R11)")],
      ck=[("ck_pedido_canal", "canal IN ('WHATSAPP','APLICATIVO','VENDEDOR_VISITA')", "Domínio do canal")],
      conceito="PEDIDO_COMPRA")

table("item_pedido", "Entidade associativa ITEM_PEDIDO (PEDIDO_COMPRA × PRODUTO)",
      "Cada produto solicitado em um pedido.",
      [C("id_pedido", ID, False, "Pedido", "FK → pedido_compra"),
       C("id_produto", ID, False, "Produto solicitado", "FK → produto"),
       C("quantidade_pedida", QTD, False, "Quantidade pedida, na unidade base", "> 0"),
       C("preco_negociado", CUSTO, True, "Preço unitário combinado", ">= 0")],
      pk=["id_pedido", "id_produto"],
      fk=[("fk_ip_pedido", ["id_pedido"], "pedido_compra", ["id_pedido"], "Item pertence a um pedido (R12)"),
          ("fk_ip_produto", ["id_produto"], "produto", ["id_produto"], "Item refere-se a um produto (R13)")],
      ck=[("ck_ip_qtd", "quantidade_pedida > 0", "Não se pede quantidade zero ou negativa"),
          ("ck_ip_preco", "preco_negociado IS NULL OR preco_negociado >= 0", "Preço não negativo")],
      conceito="ITEM_PEDIDO")

table("recebimento", "Entidade RECEBIMENTO",
      "Chegada de mercadoria com nota fiscal e resultado da conferência.",
      [C("id_recebimento", ID, False, "Identificador do recebimento", "Chave substituta (D-13)", ai=True),
       C("id_fornecedor", ID, False, "Emitente da nota", "FK → fornecedor (RN-12)"),
       C("id_funcionario", ID, False, "Conferente", "FK → funcionario (PO-05)"),
       C("chave_acesso_nfe", "CHAR(44)", True, "Chave de acesso da NF-e", "Única quando existir"),
       C("modelo_nota", "CHAR(2)", False, "Modelo do documento fiscal", "Ex.: 55 (NF-e)"),
       C("serie_nota", "SMALLINT UNSIGNED", False, "Série da nota", "0 a 999"),
       C("numero_nota", "INT UNSIGNED", False, "Número da nota", "1 a 999.999.999"),
       C("data_hora", "DATETIME", False, "Momento da chegada"),
       C("valor_total_nota", MON, False, "Valor total da nota", ">= 0"),
       C("volumes_nota", "SMALLINT UNSIGNED", False, "Volumes declarados na nota"),
       C("volumes_conferidos", "SMALLINT UNSIGNED", False, "Volumes efetivamente contados"),
       C("situacao", "VARCHAR(25)", False, "Resultado da conferência", "ACEITO, ACEITO_COM_DIVERGENCIA, RECUSADO"),
       C("observacao_divergencia", "VARCHAR(300)", True, "Descrição das divergências", "Obrigatória se a situação não for ACEITO")],
      pk=["id_recebimento"],
      uq=[("uq_recebimento_nfe", ["chave_acesso_nfe"], "A mesma NF-e não pode ser lançada duas vezes"),
          ("uq_recebimento_nota", ["id_fornecedor", "modelo_nota", "serie_nota", "numero_nota"], "Identificação legal da nota: o número sozinho repete entre séries (RN-12)")],
      fk=[("fk_receb_fornecedor", ["id_fornecedor"], "fornecedor", ["id_fornecedor"], "Toda nota tem emitente (R14)"),
          ("fk_receb_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Todo recebimento tem conferente (R15)")],
      ck=[("ck_receb_nfe_fmt", "chave_acesso_nfe IS NULL OR chave_acesso_nfe REGEXP '^[0-9A-Z]{44}$'", "Chave de acesso tem 44 posições"),
          ("ck_receb_modelo", "modelo_nota REGEXP '^[0-9]{2}$'", "Modelo com 2 dígitos"),
          ("ck_receb_serie", "serie_nota <= 999", "Série de até 3 dígitos"),
          ("ck_receb_numero", "numero_nota BETWEEN 1 AND 999999999", "Número de até 9 dígitos"),
          ("ck_receb_valor", "valor_total_nota >= 0", "Valor não negativo"),
          ("ck_receb_situacao", "situacao IN ('ACEITO','ACEITO_COM_DIVERGENCIA','RECUSADO')", "Domínio da situação"),
          ("ck_receb_obs", "situacao = 'ACEITO' OR observacao_divergencia IS NOT NULL", "Divergência ou recusa precisa ser descrita (RN-13)")],
      conceito="RECEBIMENTO")

table("item_recebimento", "Entidade fraca ITEM_RECEBIMENTO (linha da nota)",
      "Cada linha da nota fiscal recebida, com a conferência item a item.",
      [C("id_recebimento", ID, False, "Recebimento (nota)", "FK → recebimento"),
       C("numero_item_nota", "SMALLINT UNSIGNED", False, "Número da linha na nota", "Discriminador natural impresso na nota"),
       C("id_produto", ID, False, "Produto recebido", "FK → produto"),
       C("id_pedido", ID, True, "Pedido atendido por esta linha", "Com id_produto, FK → item_pedido; vazio se não houve pedido"),
       C("quantidade_nota", QTD, False, "Quantidade faturada, na unidade da nota", "> 0"),
       C("fator_conversao_compra", "DECIMAL(10,3)", False, "Unidades base por unidade da nota", "> 0 (caixa com 12 = 12)", default="1"),
       C("valor_unitario_nota", CUSTO, False, "Valor unitário na nota", ">= 0 (bonificação = 0)"),
       C("quantidade_aceita", QTD, False, "Quantidade aceita, na unidade base", "0 = linha recusada; não excede o faturado"),
       C("situacao_item", "VARCHAR(25)", False, "Resultado da conferência da linha", "ACEITO, ACEITO_PARCIAL, RECUSADO, NAO_PEDIDO_DEVOLVIDO")],
      pk=["id_recebimento", "numero_item_nota"],
      uq=[("uq_ir_lote_ref", ["id_recebimento", "numero_item_nota", "id_produto"], "Superchave que permite a lote referenciar linha + produto juntos (garante produto do lote = produto da linha)")],
      fk=[("fk_ir_recebimento", ["id_recebimento"], "recebimento", ["id_recebimento"], "A linha só existe dentro de uma nota (entidade fraca, R16)"),
          ("fk_ir_produto", ["id_produto"], "produto", ["id_produto"], "Linha refere-se a um produto (R17)"),
          ("fk_ir_item_pedido", ["id_pedido", "id_produto"], "item_pedido", ["id_pedido", "id_produto"], "A linha só atende item pedido do MESMO produto (R18)")],
      ck=[("ck_ir_qtd", "quantidade_nota > 0", "Linha de nota sem quantidade não existe"),
          ("ck_ir_fator", "fator_conversao_compra > 0", "Fator positivo"),
          ("ck_ir_valor", "valor_unitario_nota >= 0", "Valor não negativo"),
          ("ck_ir_aceita", "quantidade_aceita >= 0 AND quantidade_aceita <= quantidade_nota * fator_conversao_compra", "Não se aceita mais do que foi faturado"),
          ("ck_ir_situacao", "(situacao_item IN ('RECUSADO','NAO_PEDIDO_DEVOLVIDO') AND quantidade_aceita = 0) OR (situacao_item IN ('ACEITO','ACEITO_PARCIAL') AND quantidade_aceita > 0)",
           "Situação e quantidade aceita coerentes (RN-14)")],
      conceito="ITEM_RECEBIMENTO")

table("lote", "Entidade LOTE",
      "Porção de um produto com mesma origem, custo e validade. Base de validade, FEFO e custo.",
      [C("id_lote", ID, False, "Identificador do lote", "Chave substituta: permite 2 lotes na mesma linha de nota e lotes sem nota (D-02)", ai=True),
       C("id_produto", ID, False, "Produto do lote", "FK → produto"),
       C("id_recebimento", ID, True, "Recebimento de origem", "Com numero_item_nota e id_produto, FK → item_recebimento"),
       C("numero_item_nota", "SMALLINT UNSIGNED", True, "Linha da nota de origem"),
       C("id_lote_reposto", ID, True, "Lote trocado que este lote repõe", "FK → lote (autorrelacionamento R08)"),
       C("origem", "VARCHAR(25)", False, "Como o lote surgiu", "RECEBIMENTO, INVENTARIO_INICIAL, AJUSTE_INVENTARIO, REPOSICAO_FORNECEDOR"),
       C("codigo_lote_fabricante", "VARCHAR(30)", True, "Lote impresso pelo fabricante"),
       C("data_validade", "DATE", True, "Validade", "Obrigatória se produto.controla_validade (verificada na auditoria A05)"),
       C("data_entrada", "DATETIME", False, "Entrada no estoque"),
       C("custo_unitario", CUSTO, False, "Custo por unidade base", ">= 0; imutável após a entrada (RN-22)"),
       C("situacao", "VARCHAR(15)", False, "Estado do lote", "DISPONIVEL, SEPARADO_TROCA, TROCADO, DESCARTADO", default="'DISPONIVEL'"),
       C("pendente_conferencia", BOOL, False, "Lote de ajuste automático aguardando conferência física", "Só em lotes AJUSTE_INVENTARIO (RN-40)", default="FALSE")],
      pk=["id_lote"],
      fk=[("fk_lote_produto", ["id_produto"], "produto", ["id_produto"], "Lote é de um produto (R05)"),
          ("fk_lote_item_receb", ["id_recebimento", "numero_item_nota", "id_produto"], "item_recebimento", ["id_recebimento", "numero_item_nota", "id_produto"],
           "Lote vem de uma linha de nota existente E do mesmo produto da linha (R19)"),
          ("fk_lote_reposto", ["id_lote_reposto"], "lote", ["id_lote"], "Reposição aponta para o lote trocado (R08)")],
      ck=[("ck_lote_origem", "origem IN ('RECEBIMENTO','INVENTARIO_INICIAL','AJUSTE_INVENTARIO','REPOSICAO_FORNECEDOR')", "Domínio da origem"),
          ("ck_lote_origem_nota", "(origem = 'RECEBIMENTO' AND id_recebimento IS NOT NULL AND numero_item_nota IS NOT NULL) OR (origem <> 'RECEBIMENTO' AND id_recebimento IS NULL AND numero_item_nota IS NULL)",
           "Lote de recebimento tem linha de nota; os outros não (RN-14, RN-41)"),
          ("ck_lote_origem_reposicao", "(origem = 'REPOSICAO_FORNECEDOR') = (id_lote_reposto IS NOT NULL)", "Só lote de reposição aponta para lote trocado (RN-19)"),
          ("ck_lote_custo", "custo_unitario >= 0", "Custo não negativo (bonificação = 0)"),
          ("ck_lote_situacao", "situacao IN ('DISPONIVEL','SEPARADO_TROCA','TROCADO','DESCARTADO')", "Domínio da situação (PO-07)"),
          ("ck_lote_pendente", "pendente_conferencia = FALSE OR origem = 'AJUSTE_INVENTARIO'", "Pendência só existe em lote de ajuste automático (RN-40)")],
      conceito="LOTE")

# ======================================================================
# VENDAS E CAIXA (parte 1)
# ======================================================================
table("caixa", "Entidade CAIXA",
      "Ponto de venda físico.",
      [C("numero_caixa", "TINYINT UNSIGNED", False, "Número pintado no PDV", "Chave natural estável (D-13)"),
       C("ativo", BOOL, False, "Em uso", default="TRUE")],
      pk=["numero_caixa"],
      ck=[("ck_caixa_numero", "numero_caixa >= 1", "Numeração começa em 1")],
      conceito="CAIXA")

table("sessao_caixa", "Entidade SESSAO_CAIXA",
      "Período entre abertura e fechamento de um caixa; onde ocorre o fechamento de caixa.",
      [C("id_sessao", ID, False, "Identificador da sessão", ai=True),
       C("numero_caixa", "TINYINT UNSIGNED", False, "Caixa aberto", "FK → caixa"),
       C("id_funcionario_abertura", ID, False, "Quem abriu", "FK → funcionario"),
       C("id_funcionario_fechamento", ID, True, "Quem fechou", "FK → funcionario; vazio enquanto aberta"),
       C("data_hora_abertura", "DATETIME", False, "Abertura"),
       C("valor_inicial", "DECIMAL(10,2)", False, "Fundo de troco", ">= 0 (não é fixo)"),
       C("data_hora_fechamento", "DATETIME", True, "Fechamento", "Vazio = sessão aberta (a situação é derivada daqui)"),
       C("valor_contado", "DECIMAL(10,2)", True, "Dinheiro contado no fechamento", ">= 0"),
       C("total_maquininhas_informado", MON, True, "Total do relatório das maquininhas", ">= 0"),
       C("justificativa_diferenca", "VARCHAR(200)", True, "Explicação de sobra/falta", "Exigida quando há diferença (auditoria A06)")],
      pk=["id_sessao"],
      fk=[("fk_sessao_caixa", ["numero_caixa"], "caixa", ["numero_caixa"], "Sessão acontece em um caixa existente (R21)"),
          ("fk_sessao_abertura", ["id_funcionario_abertura"], "funcionario", ["id_funcionario"], "Abertura tem responsável (R22)"),
          ("fk_sessao_fechamento", ["id_funcionario_fechamento"], "funcionario", ["id_funcionario"], "Fechamento tem responsável (R23)")],
      ck=[("ck_sessao_valores", "valor_inicial >= 0 AND (valor_contado IS NULL OR valor_contado >= 0) AND (total_maquininhas_informado IS NULL OR total_maquininhas_informado >= 0)", "Valores de dinheiro não negativos"),
          ("ck_sessao_fechamento", "(data_hora_fechamento IS NULL AND id_funcionario_fechamento IS NULL AND valor_contado IS NULL) OR (data_hora_fechamento IS NOT NULL AND id_funcionario_fechamento IS NOT NULL AND valor_contado IS NOT NULL)",
           "Fechar exige data, responsável e contagem juntos (RN-30)"),
          ("ck_sessao_datas", "data_hora_fechamento IS NULL OR data_hora_fechamento > data_hora_abertura", "Fechamento depois da abertura")],
      conceito="SESSAO_CAIXA")

table("cliente", "Entidade CLIENTE",
      "Consumidor identificado; exigido apenas para venda fiada.",
      [C("id_cliente", ID, False, "Identificador do cliente", "Chave substituta (D-13)", ai=True),
       C("cpf", "CHAR(11)", True, "CPF", "Único quando informado; obrigatório para autorizar fiado"),
       C("nome", "VARCHAR(100)", False, "Nome"),
       C("apelido", "VARCHAR(40)", True, "Como é conhecido no bairro"),
       C("telefone", "VARCHAR(15)", True, "Telefone", "Só dígitos"),
       C("logradouro", "VARCHAR(100)", True, "Rua/avenida", "Atributo composto endereço decomposto (1FN)"),
       C("numero_endereco", "VARCHAR(10)", True, "Número do imóvel"),
       C("complemento", "VARCHAR(40)", True, "Complemento"),
       C("bairro", "VARCHAR(50)", True, "Bairro"),
       C("autorizado_fiado", BOOL, False, "Pode comprar fiado", "Só o gerente altera (PO-04)", default="FALSE"),
       C("limite_fiado", "DECIMAL(10,2)", True, "Limite de dívida em aberto", ">= 0"),
       C("data_cadastro", "DATE", False, "Data do cadastro", default="(CURRENT_DATE)")],
      pk=["id_cliente"],
      uq=[("uq_cliente_cpf", ["cpf"], "Um CPF, um cliente")],
      ck=[("ck_cliente_cpf", f"cpf IS NULL OR cpf REGEXP {CPF_RE}", "Formato do CPF"),
          ("ck_cliente_fiado_cpf", "autorizado_fiado = FALSE OR cpf IS NOT NULL", "Fiado exige cliente identificado por CPF (RN-24, PO-04)"),
          ("ck_cliente_limite", "limite_fiado IS NULL OR limite_fiado >= 0", "Limite não negativo"),
          ("ck_cliente_tel", "telefone IS NULL OR telefone REGEXP '^[0-9]{10,11}$'", "Telefone com DDD")],
      conceito="CLIENTE")

table("venda", "Entidade VENDA",
      "Transação de venda registrada no caixa.",
      [C("id_venda", ID, False, "Identificador da venda", "Chave substituta: não depende do relógio, permite caixa offline (RNF-07)", ai=True),
       C("id_sessao", ID, False, "Sessão de caixa", "FK → sessao_caixa (RN-20)"),
       C("id_funcionario", ID, False, "Operador", "FK → funcionario"),
       C("id_cliente", ID, True, "Cliente identificado", "FK → cliente; obrigatório se houver FIADO (auditoria A04)"),
       C("numero_cupom", "INT UNSIGNED", False, "Número do cupom", "Único dentro da sessão"),
       C("data_hora", "DATETIME", False, "Momento da venda"),
       C("situacao", "VARCHAR(10)", False, "Estado", "CONCLUIDA, CANCELADA", default="'CONCLUIDA'")],
      pk=["id_venda"],
      uq=[("uq_venda_cupom", ["id_sessao", "numero_cupom"], "O mesmo cupom não pode ser emitido duas vezes na sessão")],
      fk=[("fk_venda_sessao", ["id_sessao"], "sessao_caixa", ["id_sessao"], "Não há venda fora de sessão (R24, RN-20)"),
          ("fk_venda_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Venda tem operador (R25)"),
          ("fk_venda_cliente", ["id_cliente"], "cliente", ["id_cliente"], "Cliente, quando informado, existe (R26)")],
      ck=[("ck_venda_situacao", "situacao IN ('CONCLUIDA','CANCELADA')", "Domínio da situação"),
          ("ck_venda_cupom", "numero_cupom >= 1", "Cupom numerado a partir de 1")],
      conceito="VENDA")

table("item_venda", "Entidade associativa ITEM_VENDA (VENDA × EMBALAGEM)",
      "Cada linha do cupom: embalagem, quantidade, preço praticado e desconto.",
      [C("id_venda", ID, False, "Venda", "FK → venda"),
       C("numero_item", "SMALLINT UNSIGNED", False, "Posição no cupom", "Discriminador natural impresso no cupom"),
       C("id_embalagem", ID, False, "Embalagem lida", "FK → embalagem"),
       C("id_funcionario_autorizador", ID, True, "Quem autorizou o desconto", "FK → funcionario; obrigatório se houver desconto"),
       C("quantidade", QTD, False, "Quantidade na unidade da embalagem", "> 0; fracionada para peso"),
       C("preco_unitario_praticado", "DECIMAL(10,2)", False, "Preço no momento da venda", "> 0; não muda depois (RN-22)"),
       C("desconto_unitario", "DECIMAL(10,2)", False, "Desconto por unidade", ">= 0 e menor que o preço", default="0")],
      pk=["id_venda", "numero_item"],
      fk=[("fk_iv_venda", ["id_venda"], "venda", ["id_venda"], "Item pertence a uma venda (R27)"),
          ("fk_iv_embalagem", ["id_embalagem"], "embalagem", ["id_embalagem"], "Item é de uma embalagem existente (R28)"),
          ("fk_iv_autorizador", ["id_funcionario_autorizador"], "funcionario", ["id_funcionario"], "Desconto tem autorizador (R29)")],
      ck=[("ck_iv_qtd", "quantidade > 0", "Quantidade positiva"),
          ("ck_iv_preco", "preco_unitario_praticado > 0", "Preço positivo"),
          ("ck_iv_desconto", "desconto_unitario >= 0 AND desconto_unitario < preco_unitario_praticado", "Desconto não pode zerar nem inverter o preço"),
          ("ck_iv_autorizacao", "desconto_unitario = 0 OR id_funcionario_autorizador IS NOT NULL", "Desconto só com autorizador (RN-23)")],
      conceito="ITEM_VENDA")

# ======================================================================
# FINANCEIRO (base) — precisa existir antes dos pagamentos
# ======================================================================
table("conta_financeira", "Entidade CONTA_FINANCEIRA",
      "Onde o dinheiro fica fora da gaveta: banco, conta da maquininha ou cofre.",
      [C("id_conta_financeira", ID, False, "Identificador", ai=True),
       C("nome", "VARCHAR(60)", False, "Nome da conta", "Único"),
       C("tipo", "VARCHAR(16)", False, "Tipo", "CONTA_BANCARIA, CONTA_ADQUIRENTE, COFRE"),
       C("saldo_inicial", MON, False, "Saldo na implantação"),
       C("data_saldo_inicial", "DATE", False, "Data do saldo inicial"),
       C("ativa", BOOL, False, "Em uso", default="TRUE")],
      pk=["id_conta_financeira"],
      uq=[("uq_cf_nome", ["nome"], "Contas distinguíveis pelo nome")],
      ck=[("ck_cf_tipo", "tipo IN ('CONTA_BANCARIA','CONTA_ADQUIRENTE','COFRE')", "Domínio do tipo")],
      conceito="CONTA_FINANCEIRA")

table("movimento_financeiro", "Entidade MOVIMENTO_FINANCEIRO",
      "Entrada ou saída efetiva de dinheiro numa conta financeira (linha do extrato ou do cofre).",
      [C("id_movimento_fin", ID, False, "Identificador", ai=True),
       C("id_conta_financeira", ID, False, "Conta", "FK → conta_financeira"),
       C("id_funcionario", ID, True, "Quem lançou", "FK → funcionario; obrigatório em lançamento manual"),
       C("data_movimento", "DATE", False, "Data em que o valor entrou/saiu"),
       C("natureza", "VARCHAR(7)", False, "Sentido", "CREDITO, DEBITO"),
       C("origem", "VARCHAR(20)", False, "O que gerou", "REPASSE_CARTAO, PIX_RECEBIDO, RECOLHIMENTO_GAVETA, SUPRIMENTO_GAVETA, DEPOSITO, PAGAMENTO_CONTA, ESTORNO_DEVOLUCAO, TARIFA, AJUSTE"),
       C("valor_bruto", MON, False, "Valor antes da taxa", "> 0"),
       C("valor_taxa", MON, False, "Taxa descontada", ">= 0 e <= bruto", default="0"),
       C("documento_referencia", "VARCHAR(60)", True, "Identificação no extrato", "Única por conta")],
      pk=["id_movimento_fin"],
      uq=[("uq_mf_documento", ["id_conta_financeira", "documento_referencia"], "A mesma linha de extrato não pode ser importada duas vezes")],
      fk=[("fk_mf_conta", ["id_conta_financeira"], "conta_financeira", ["id_conta_financeira"], "Movimento ocorre numa conta (R47)"),
          ("fk_mf_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Lançamento manual tem responsável (R51)")],
      ck=[("ck_mf_natureza", "natureza IN ('CREDITO','DEBITO')", "Domínio"),
          ("ck_mf_origem", "(natureza = 'CREDITO' AND origem IN ('REPASSE_CARTAO','PIX_RECEBIDO','RECOLHIMENTO_GAVETA','DEPOSITO','AJUSTE')) OR (natureza = 'DEBITO' AND origem IN ('SUPRIMENTO_GAVETA','DEPOSITO','PAGAMENTO_CONTA','ESTORNO_DEVOLUCAO','TARIFA','AJUSTE'))",
           "Cada origem tem o sentido certo (repasse nunca é débito, pagamento nunca é crédito)"),
          ("ck_mf_valores", "valor_bruto > 0 AND valor_taxa >= 0 AND valor_taxa <= valor_bruto", "Taxa não supera o valor"),
          ("ck_mf_manual", "origem NOT IN ('DEPOSITO','TARIFA','AJUSTE') OR id_funcionario IS NOT NULL", "Lançamento manual exige responsável (RN-35)")],
      conceito="MOVIMENTO_FINANCEIRO")

# ======================================================================
# VENDAS E CAIXA (parte 2)
# ======================================================================
table("forma_pagamento", "Entidade FORMA_PAGAMENTO",
      "Meio de pagamento com prazo e taxa de crédito.",
      [C("codigo_forma", "VARCHAR(5)", False, "Código", "Chave natural fixa: DIN, DEB, CRE, PIX, VALE, FIADO (D-13)"),
       C("descricao", "VARCHAR(40)", False, "Nome exibido"),
       C("prazo_credito_dias", "SMALLINT UNSIGNED", False, "Dias até o crédito", "DIN/PIX = 0", default="0"),
       C("taxa_percentual", "DECIMAL(5,2)", False, "Taxa contratada (%)", "0 a 100", default="0"),
       C("gera_divida", BOOL, False, "Cria dívida do cliente", "Só FIADO", default="FALSE"),
       C("exige_conciliacao", BOOL, False, "Valor cai em conta e deve ser conciliado", "DEB, CRE, PIX, VALE", default="FALSE"),
       C("ativa", BOOL, False, "Disponível no caixa", default="TRUE")],
      pk=["codigo_forma"],
      ck=[("ck_fp_taxa", "taxa_percentual BETWEEN 0 AND 100", "Percentual válido"),
          ("ck_fp_divida", "NOT (gera_divida AND exige_conciliacao)", "Fiado não cai em conta; o que cai em conta não gera dívida")],
      conceito="FORMA_PAGAMENTO")

table("pagamento_venda", "Entidade fraca PAGAMENTO_VENDA",
      "Cada transação de pagamento de uma venda.",
      [C("id_venda", ID, False, "Venda paga", "FK → venda"),
       C("numero_pagamento", "TINYINT UNSIGNED", False, "Sequência na venda", "Permite 2 pagamentos na mesma forma (T06)"),
       C("codigo_forma", "VARCHAR(5)", False, "Forma", "FK → forma_pagamento"),
       C("id_movimento_fin", ID, True, "Crédito que liquidou a transação", "FK → movimento_financeiro; vazio = não conciliado (RN-36)"),
       C("valor", "DECIMAL(10,2)", False, "Valor aplicado à venda", "> 0, já líquido de troco"),
       C("valor_entregue", "DECIMAL(10,2)", True, "Dinheiro entregue pelo cliente", "Só em DIN; >= valor"),
       C("nsu_autorizacao", "VARCHAR(36)", True, "NSU / ID da transação", "Obrigatório em DEB, CRE, PIX, VALE; único")],
      pk=["id_venda", "numero_pagamento"],
      uq=[("uq_pv_nsu", ["nsu_autorizacao"], "A mesma transação de cartão/Pix não pode ser registrada duas vezes")],
      fk=[("fk_pv_venda", ["id_venda"], "venda", ["id_venda"], "Pagamento pertence a uma venda (R31)"),
          ("fk_pv_forma", ["codigo_forma"], "forma_pagamento", ["codigo_forma"], "Forma cadastrada (R32)"),
          ("fk_pv_movimento", ["id_movimento_fin"], "movimento_financeiro", ["id_movimento_fin"], "Liquidação aponta para crédito real (R48)")],
      ck=[("ck_pv_valor", "valor > 0", "Pagamento positivo"),
          ("ck_pv_entregue", "(codigo_forma = 'DIN' AND (valor_entregue IS NULL OR valor_entregue >= valor)) OR (codigo_forma <> 'DIN' AND valor_entregue IS NULL)", "Troco só existe em dinheiro"),
          ("ck_pv_nsu", "codigo_forma IN ('DIN','FIADO') OR nsu_autorizacao IS NOT NULL", "Transação eletrônica precisa de NSU para ser conciliada"),
          ("ck_pv_liquidacao", "id_movimento_fin IS NULL OR codigo_forma NOT IN ('DIN','FIADO')", "Dinheiro e fiado não são liquidados por crédito em conta")],
      conceito="PAGAMENTO_VENDA")

table("movimentacao_caixa", "Entidade MOVIMENTACAO_CAIXA",
      "Dinheiro que entra ou sai da gaveta sem ser venda.",
      [C("id_mov_caixa", ID, False, "Identificador", ai=True),
       C("id_sessao", ID, False, "Sessão", "FK → sessao_caixa"),
       C("id_funcionario", ID, False, "Quem executou", "FK → funcionario (RN-29)"),
       C("id_movimento_fin", ID, True, "Lançamento no cofre gerado", "FK → movimento_financeiro; único"),
       C("data_hora", "DATETIME", False, "Momento"),
       C("tipo", "VARCHAR(25)", False, "Tipo", "SANGRIA, SUPRIMENTO, RECOLHIMENTO_FECHAMENTO, REEMBOLSO_DEVOLUCAO"),
       C("valor", "DECIMAL(10,2)", False, "Valor", "> 0"),
       C("motivo", "VARCHAR(200)", False, "Justificativa", "Obrigatório (RN-29)")],
      pk=["id_mov_caixa"],
      uq=[("uq_mc_movimento", ["id_movimento_fin"], "Um lançamento no cofre corresponde a uma única movimentação (1:1, R50)")],
      fk=[("fk_mc_sessao", ["id_sessao"], "sessao_caixa", ["id_sessao"], "Pertence a uma sessão (R33)"),
          ("fk_mc_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Tem responsável (R34)"),
          ("fk_mc_movimento", ["id_movimento_fin"], "movimento_financeiro", ["id_movimento_fin"], "Sangria/suprimento aparece no cofre (R50)")],
      ck=[("ck_mc_tipo", "tipo IN ('SANGRIA','SUPRIMENTO','RECOLHIMENTO_FECHAMENTO','REEMBOLSO_DEVOLUCAO')", "Domínio"),
          ("ck_mc_valor", "valor > 0", "Valor positivo"),
          ("ck_mc_cofre", "(tipo = 'REEMBOLSO_DEVOLUCAO' AND id_movimento_fin IS NULL) OR (tipo <> 'REEMBOLSO_DEVOLUCAO' AND id_movimento_fin IS NOT NULL)",
           "Todo dinheiro que sai da gaveta para o cofre (ou volta dele) fica registrado no cofre (RN-37)")],
      conceito="MOVIMENTACAO_CAIXA")

table("devolucao", "Entidade DEVOLUCAO",
      "Devolução ou troca de item vendido.",
      [C("id_devolucao", ID, False, "Identificador", ai=True),
       C("id_venda", ID, False, "Venda de origem", "Com numero_item, FK → item_venda"),
       C("numero_item", "SMALLINT UNSIGNED", False, "Item devolvido"),
       C("id_funcionario", ID, False, "Autorizador", "FK → funcionario (PO-13)"),
       C("id_mov_caixa", ID, True, "Saída de dinheiro do reembolso", "FK → movimentacao_caixa; obrigatória se DINHEIRO"),
       C("id_movimento_fin", ID, True, "Estorno em conta", "FK → movimento_financeiro; obrigatório se ESTORNO_ELETRONICO"),
       C("data_hora", "DATETIME", False, "Momento"),
       C("quantidade_devolvida", QTD, False, "Quantidade, na unidade da embalagem", "> 0; não excede o vendido (auditoria A12)"),
       C("motivo", "VARCHAR(10)", False, "Motivo", "DEFEITO, VENCIDO (RN-28)"),
       C("destino", "VARCHAR(15)", False, "Destino do produto", "REVENDA, SEPARADO_TROCA, DESCARTE"),
       C("forma_reembolso", "VARCHAR(20)", False, "Reembolso", "TROCA_MESMO_PRODUTO, DINHEIRO, ESTORNO_ELETRONICO, ABATER_FIADO"),
       C("valor_reembolsado", "DECIMAL(10,2)", False, "Valor devolvido", "0 na troca; > 0 nos demais", default="0")],
      pk=["id_devolucao"],
      uq=[("uq_dev_mov_caixa", ["id_mov_caixa"], "Uma saída de gaveta paga uma única devolução"),
          ("uq_dev_mov_fin", ["id_movimento_fin"], "Um estorno corresponde a uma única devolução")],
      fk=[("fk_dev_item", ["id_venda", "numero_item"], "item_venda", ["id_venda", "numero_item"], "Só se devolve o que foi vendido (R35)"),
          ("fk_dev_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Devolução tem autorizador (R36)"),
          ("fk_dev_mov_caixa", ["id_mov_caixa"], "movimentacao_caixa", ["id_mov_caixa"], "Reembolso em dinheiro sai da gaveta (R38)"),
          ("fk_dev_mov_fin", ["id_movimento_fin"], "movimento_financeiro", ["id_movimento_fin"], "Estorno sai da conta (R39)")],
      ck=[("ck_dev_qtd", "quantidade_devolvida > 0", "Quantidade positiva"),
          ("ck_dev_motivo", "motivo IN ('DEFEITO','VENCIDO')", "Só por defeito ou vencido (RN-28)"),
          ("ck_dev_destino", "destino IN ('REVENDA','SEPARADO_TROCA','DESCARTE')", "Domínio"),
          ("ck_dev_forma", "forma_reembolso IN ('TROCA_MESMO_PRODUTO','DINHEIRO','ESTORNO_ELETRONICO','ABATER_FIADO')", "Domínio"),
          ("ck_dev_valor", "(forma_reembolso = 'TROCA_MESMO_PRODUTO' AND valor_reembolsado = 0) OR (forma_reembolso <> 'TROCA_MESMO_PRODUTO' AND valor_reembolsado > 0)", "Troca não devolve dinheiro; reembolso devolve"),
          ("ck_dev_dinheiro", "(forma_reembolso = 'DINHEIRO') = (id_mov_caixa IS NOT NULL)", "Reembolso em dinheiro registrado na gaveta (RN-28, RN-37)"),
          ("ck_dev_estorno", "(forma_reembolso = 'ESTORNO_ELETRONICO') = (id_movimento_fin IS NOT NULL)", "Estorno registrado na conta")],
      conceito="DEVOLUCAO")

table("movimentacao_estoque", "Entidade MOVIMENTACAO_ESTOQUE",
      "Toda entrada ou saída de um lote (kardex). Nenhum saldo muda sem ela.",
      [C("id_movimentacao", ID, False, "Identificador", "Chave substituta: duas baixas no mesmo instante não colidem (T05)", ai=True),
       C("id_lote", ID, False, "Lote movimentado", "FK → lote (RN-16)"),
       C("id_funcionario", ID, True, "Responsável", "FK → funcionario; obrigatório em perdas, ajustes, inventário e troca (RN-18)"),
       C("id_venda", ID, True, "Venda que gerou a baixa", "Com numero_item, FK → item_venda; só em SAIDA_VENDA"),
       C("numero_item", "SMALLINT UNSIGNED", True, "Item do cupom"),
       C("id_devolucao", ID, True, "Devolução que gerou", "FK → devolucao; só em DEVOLUCAO_CLIENTE e SAIDA_TROCA_CLIENTE"),
       C("data_hora", "DATETIME", False, "Momento"),
       C("tipo", "VARCHAR(30)", False, "Natureza", "Entradas: ENTRADA_RECEBIMENTO, ENTRADA_INVENTARIO, TROCA_FORNECEDOR, DEVOLUCAO_CLIENTE, AJUSTE_INVENTARIO_ENTRADA. Saídas: SAIDA_VENDA, SAIDA_TROCA_CLIENTE, PERDA_VENCIMENTO, PERDA_AVARIA, AJUSTE_INVENTARIO_SAIDA"),
       C("quantidade", QTD, False, "Quantidade na unidade base", "> 0; o tipo define o sinal"),
       C("motivo", "VARCHAR(200)", True, "Justificativa", "Obrigatória em perdas e ajustes")],
      pk=["id_movimentacao"],
      fk=[("fk_me_lote", ["id_lote"], "lote", ["id_lote"], "Toda movimentação afeta um lote (R06)"),
          ("fk_me_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Responsável (R07)"),
          ("fk_me_item_venda", ["id_venda", "numero_item"], "item_venda", ["id_venda", "numero_item"], "Baixa por venda aponta para o item (R30)"),
          ("fk_me_devolucao", ["id_devolucao"], "devolucao", ["id_devolucao"], "Retorno aponta para a devolução (R37)")],
      ck=[("ck_me_tipo", "tipo IN ('ENTRADA_RECEBIMENTO','ENTRADA_INVENTARIO','TROCA_FORNECEDOR','DEVOLUCAO_CLIENTE','AJUSTE_INVENTARIO_ENTRADA','SAIDA_VENDA','SAIDA_TROCA_CLIENTE','PERDA_VENCIMENTO','PERDA_AVARIA','AJUSTE_INVENTARIO_SAIDA')", "Domínio (RF-16)"),
          ("ck_me_qtd", "quantidade > 0", "Quantidade positiva; o sinal vem do tipo"),
          ("ck_me_venda", "(tipo = 'SAIDA_VENDA') = (id_venda IS NOT NULL AND numero_item IS NOT NULL)", "Só baixa de venda aponta para item vendido, e toda baixa de venda aponta (RN-17)"),
          ("ck_me_venda_par", "(id_venda IS NULL) = (numero_item IS NULL)", "Item de venda informado por inteiro"),
          ("ck_me_devolucao", "(tipo IN ('DEVOLUCAO_CLIENTE','SAIDA_TROCA_CLIENTE')) = (id_devolucao IS NOT NULL)", "Retorno e troca ao cliente apontam para a devolução"),
          ("ck_me_responsavel", "tipo NOT IN ('PERDA_VENCIMENTO','PERDA_AVARIA','AJUSTE_INVENTARIO_ENTRADA','AJUSTE_INVENTARIO_SAIDA','ENTRADA_INVENTARIO','TROCA_FORNECEDOR') OR id_funcionario IS NOT NULL", "Perdas, ajustes, inventário e troca têm responsável (RN-18)"),
          ("ck_me_motivo", "tipo NOT IN ('PERDA_VENCIMENTO','PERDA_AVARIA','AJUSTE_INVENTARIO_ENTRADA','AJUSTE_INVENTARIO_SAIDA') OR motivo IS NOT NULL", "Perdas e ajustes têm motivo (RN-18)")],
      conceito="MOVIMENTACAO_ESTOQUE")

table("abatimento_fiado", "Entidade ABATIMENTO_FIADO",
      "Pagamento total ou parcial da dívida de fiado.",
      [C("id_abatimento", ID, False, "Identificador", ai=True),
       C("id_cliente", ID, False, "Cliente", "FK → cliente"),
       C("codigo_forma", "VARCHAR(5)", False, "Forma usada", "FK → forma_pagamento; nunca FIADO (RN-27)"),
       C("id_funcionario", ID, False, "Quem recebeu", "FK → funcionario"),
       C("id_sessao", ID, True, "Sessão em que o dinheiro entrou", "FK → sessao_caixa; obrigatória em DIN"),
       C("id_movimento_fin", ID, True, "Crédito que liquidou", "FK → movimento_financeiro; só em formas eletrônicas"),
       C("data_hora", "DATETIME", False, "Momento"),
       C("valor", "DECIMAL(10,2)", False, "Valor pago", "> 0"),
       C("observacao", "VARCHAR(200)", True, "Anotação")],
      pk=["id_abatimento"],
      fk=[("fk_ab_cliente", ["id_cliente"], "cliente", ["id_cliente"], "Abatimento é de um cliente (R40)"),
          ("fk_ab_forma", ["codigo_forma"], "forma_pagamento", ["codigo_forma"], "Forma cadastrada (R41)"),
          ("fk_ab_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Quem recebeu (R42)"),
          ("fk_ab_sessao", ["id_sessao"], "sessao_caixa", ["id_sessao"], "Dinheiro na gaveta (R43)"),
          ("fk_ab_movimento", ["id_movimento_fin"], "movimento_financeiro", ["id_movimento_fin"], "Liquidação (R49)")],
      ck=[("ck_ab_valor", "valor > 0", "Valor positivo"),
          ("ck_ab_forma", "codigo_forma <> 'FIADO'", "Fiado não paga fiado (RN-27)"),
          ("ck_ab_sessao", "codigo_forma <> 'DIN' OR id_sessao IS NOT NULL", "Dinheiro recebido entra na conferência de uma sessão"),
          ("ck_ab_liquidacao", "id_movimento_fin IS NULL OR codigo_forma <> 'DIN'", "Dinheiro não é liquidado por crédito em conta")],
      conceito="ABATIMENTO_FIADO")

table("conta_pagar", "Entidade CONTA_PAGAR",
      "Obrigação do mercado: parcela de boleto, imposto, folha, internet etc.",
      [C("id_conta", ID, False, "Identificador", "Chave substituta (D-13)", ai=True),
       C("id_recebimento", ID, True, "Recebimento de origem", "FK → recebimento; vazio em despesas fixas"),
       C("credor", "VARCHAR(120)", False, "Quem recebe"),
       C("numero_documento", "VARCHAR(40)", True, "Nº do boleto/guia/competência"),
       C("numero_parcela", "TINYINT UNSIGNED", False, "Parcela", ">= 1", default="1"),
       C("descricao", "VARCHAR(150)", False, "Descrição"),
       C("categoria_despesa", "VARCHAR(18)", False, "Categoria", "FORNECEDOR, SIMPLES_NACIONAL, FOLHA, INTERNET, AGUA, LUZ, ALUGUEL, OUTROS"),
       C("valor_original", MON, False, "Valor da obrigação", "> 0"),
       C("data_vencimento", "DATE", False, "Vencimento"),
       C("prioridade", "VARCHAR(5)", False, "Prioridade", "ALTA, MEDIA, BAIXA (PO-06)", default="'MEDIA'"),
       C("cancelada", BOOL, False, "Cancelada", default="FALSE")],
      pk=["id_conta"],
      uq=[("uq_cp_parcela", ["id_recebimento", "numero_parcela"], "Uma nota não gera a mesma parcela duas vezes")],
      fk=[("fk_cp_recebimento", ["id_recebimento"], "recebimento", ["id_recebimento"], "Conta de fornecedor nasce de um recebimento (R20)")],
      ck=[("ck_cp_categoria", "categoria_despesa IN ('FORNECEDOR','SIMPLES_NACIONAL','FOLHA','INTERNET','AGUA','LUZ','ALUGUEL','OUTROS')", "Domínio"),
          ("ck_cp_valor", "valor_original > 0", "Valor positivo"),
          ("ck_cp_parcela", "numero_parcela >= 1", "Parcela a partir de 1"),
          ("ck_cp_prioridade", "prioridade IN ('ALTA','MEDIA','BAIXA')", "Domínio (PO-06)"),
          ("ck_cp_origem", "categoria_despesa = 'FORNECEDOR' OR id_recebimento IS NULL", "Só conta de fornecedor aponta para nota (RN-32)")],
      conceito="CONTA_PAGAR")

table("pagamento_conta", "Entidade fraca PAGAMENTO_CONTA",
      "Cada pagamento (total ou parcial) de uma conta.",
      [C("id_conta", ID, False, "Conta paga", "FK → conta_pagar"),
       C("numero_pagamento", "TINYINT UNSIGNED", False, "Sequência na conta", "1, 2, 3…"),
       C("id_funcionario", ID, False, "Quem registrou", "FK → funcionario (RN-35)"),
       C("id_movimento_fin", ID, False, "Saída de dinheiro", "FK → movimento_financeiro; única (1:1)"),
       C("data_pagamento", "DATE", False, "Data"),
       C("valor_principal", MON, False, "Parte do valor original quitada", "> 0; soma <= valor original (auditoria A09)"),
       C("valor_juros_multa", MON, False, "Encargos", ">= 0", default="0"),
       C("valor_desconto", MON, False, "Desconto obtido", ">= 0", default="0"),
       C("observacao", "VARCHAR(200)", True, "Anotação")],
      pk=["id_conta", "numero_pagamento"],
      uq=[("uq_pc_movimento", ["id_movimento_fin"], "Cada pagamento corresponde a uma única saída de dinheiro (R46)")],
      fk=[("fk_pc_conta", ["id_conta"], "conta_pagar", ["id_conta"], "Pagamento existe só dentro de uma conta (entidade fraca, R44)"),
          ("fk_pc_funcionario", ["id_funcionario"], "funcionario", ["id_funcionario"], "Responsável (R45)"),
          ("fk_pc_movimento", ["id_movimento_fin"], "movimento_financeiro", ["id_movimento_fin"], "Dinheiro saiu de alguma conta (R46)")],
      ck=[("ck_pc_valores", "valor_principal > 0 AND valor_juros_multa >= 0 AND valor_desconto >= 0", "Valores coerentes"),
          ("ck_pc_desconto", "valor_desconto < valor_principal + valor_juros_multa", "Desconto não anula o pagamento")],
      conceito="PAGAMENTO_CONTA")

# ordem de criação já respeita dependências: verificação automática
def check_order():
    seen = set()
    for t in ORDER:
        for f in T[t]["fk"]:
            ref = f[2]
            assert ref in seen or ref == t, f"{t} referencia {ref} antes de criá-la"
        seen.add(t)
check_order()

# ----------------------------------------------------------------------
def col_sql(c):
    s = f"  {c['nome']:<28} {c['tipo']}"
    s += " NOT NULL" if not c["nulo"] else " NULL"
    if c["ai"]:
        s += " AUTO_INCREMENT"
    if c["default"] is not None:
        s += f" DEFAULT {c['default']}"
    s += f" COMMENT '{c['desc'].replace(chr(39), chr(39)*2)}'"
    return s

def ddl_table(t):
    d = T[t]
    lines = [col_sql(c) for c in d["cols"]]
    lines.append(f"  CONSTRAINT pk_{t} PRIMARY KEY ({', '.join(d['pk'])})")
    for n, cols, _ in d["uq"]:
        lines.append(f"  CONSTRAINT {n} UNIQUE ({', '.join(cols)})")
    for n, cols, ref, rcols, _ in d["fk"]:
        lines.append(f"  CONSTRAINT {n} FOREIGN KEY ({', '.join(cols)}) REFERENCES {ref} ({', '.join(rcols)})")
    for n, expr, _ in d["ck"]:
        lines.append(f"  CONSTRAINT {n} CHECK ({expr})")
    head = f"-- {t.upper()} — origem: {d['origem']}\n-- {d['desc']}\n"
    return head + f"CREATE TABLE {t} (\n" + ",\n".join(lines) + \
        f"\n) ENGINE=InnoDB COMMENT='{d['desc'].replace(chr(39), chr(39)*2)}';\n"

def ddl_all():
    out = ["-- =====================================================================",
           "-- 02_tabelas.sql — CREATE TABLE com PK, FK, UNIQUE, CHECK, DEFAULT",
           "-- Gerado a partir de fis.py (fonte única do modelo lógico/físico).",
           "-- Ordem de criação respeita as dependências de chave estrangeira.",
           "-- Nenhuma FK usa CASCADE: registros operacionais não são apagados (RNF-06, PO-12);",
           "-- a exclusão de um registro referenciado é bloqueada (RESTRICT, padrão do MySQL).",
           "-- =====================================================================",
           "SET NAMES utf8mb4;", "USE mercado_boturussu;", ""]
    for t in ORDER:
        out.append(ddl_table(t))
    return "\n".join(out)

if __name__ == "__main__":
    print(len(T), "tabelas,", sum(len(T[t]['cols']) for t in T), "colunas,",
          sum(len(T[t]['fk']) for t in T), "FKs,", sum(len(T[t]['ck']) for t in T), "CHECKs,",
          sum(len(T[t]['uq']) for t in T), "UNIQUEs")
