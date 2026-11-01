# -*- coding: utf-8 -*-
"""Fonte única do modelo conceitual revisado (Entrega 1 – revisão).
Tudo que aparece no dicionário, no quadro de chaves, nos relacionamentos,
nas cardinalidades e no DER é gerado a partir daqui, para garantir coerência."""

# ---------------------------------------------------------------- módulos
MODULES = {
    "PE": "Produtos e Estoque",
    "CF": "Compras e Fornecedores",
    "VC": "Vendas e Caixa",
    "FF": "Financeiro e Fiado",
    "PA": "Pessoas e Acesso",
}

# ---------------------------------------------------------------- entidades
# attr = (nome, descrição, classificação, regra)
# classificações usadas: PK | PK, FK | FK | FK (opcional) | AK | AK (opcional)
# | Simples | Simples (opcional) | Composto (opcional) | Multivalorado e composto | Derivado
E = {}

def ent(name, mod, tipo, desc, why, attrs, new=False, changed=False):
    E[name] = dict(name=name, mod=mod, tipo=tipo, desc=desc, why=why,
                   attrs=attrs, new=new, changed=changed)

# ---------- Produtos e Estoque
ent("CATEGORIA", "PE", "Forte",
    "Setor/agrupamento de produtos do mercado (hortifruti, bebidas, limpeza, alimentos básicos, congelados, carnes).",
    "O mercado se organiza por setores (hortifruti, bebidas, limpeza, alimentos básicos, congelados, carnes) e há política de validade diferente por setor. Sem ela, o prazo de alerta teria de ser repetido em cada produto.",
    [
     ("codigo_categoria", "Sigla do setor", "PK", "Código curto controlado pelo mercado e imutável (ex.: HORTI, BEBID). Separado do nome para que renomear o setor não altere a chave"),
     ("nome", "Nome do setor", "AK", "Obrigatório e único. Ex.: 'Hortifruti', 'Bebidas'"),
     ("controle_validade_rigoroso", "Indica se os produtos do setor exigem vigilância maior de validade", "Simples", "Sim/Não. Ex.: alimentos básicos = Sim (entrevista 2.15)"),
     ("dias_alerta_validade_padrao", "Antecedência padrão (em dias) para alertar vencimento", "Simples (opcional)", "Usado quando o produto não define o seu próprio prazo"),
    ], changed=True)

ent("PRODUTO", "PE", "Forte",
    "Item comercializado, independentemente da embalagem em que é vendido. É a unidade de controle de estoque.",
    "É a unidade de controle de estoque, de compra e de análise de giro. Concentra o que não varia com a forma de venda: nome, marca, unidade base, política de validade e estoque mínimo.",
    [
     ("id_produto", "Identificador do produto", "PK", "Gerado pelo sistema, sem significado e imutável (ver D-13)"),
     ("codigo_categoria", "Setor ao qual o produto pertence", "FK", "Referencia CATEGORIA. Obrigatório (RN-01)"),
     ("nome_produto", "Nome completo e padronizado (tipo, marca e variação)", "AK", "Obrigatório e único. Ex.: 'Arroz Tio João Tipo 1 5 kg'. Pode ser corrigido sem afetar vendas e lotes"),
     ("marca", "Marca do produto", "Simples (opcional)", "Pode não existir (ex.: hortifruti)"),
     ("unidade_base", "Unidade em que o estoque é contado", "Simples", "Domínio: UN ou KG"),
     ("vendido_por_peso", "Indica venda fracionada pesada na balança", "Simples", "Sim/Não. Carnes, frutas e verduras = Sim"),
     ("controla_validade", "Indica se o produto exige data de validade no lote", "Simples", "Se Sim, todo lote deve ter data de validade (RN-15)"),
     ("dias_alerta_validade", "Antecedência (dias) para alerta de vencimento", "Simples (opcional)", "Sobrepõe o padrão da categoria"),
     ("estoque_minimo", "Quantidade mínima desejada, na unidade base", "Simples", "Obrigatório, >= 0. Dispara alerta de reposição"),
     ("margem_referencia", "Margem de lucro de referência (%)", "Simples (opcional)", "Apoio à formação de preço (35–40% em itens comuns)"),
     ("ativo", "Indica se o produto está em comercialização", "Simples", "Produto inativo não pode ser vendido"),
     ("estoque_atual", "Quantidade disponível na unidade base", "Derivado", "Soma da quantidade_atual dos lotes do produto"),
    ], changed=True)

ent("EMBALAGEM", "PE", "Forte",
    "Forma de venda de um produto (lata, fardo, pacote, quilo), com código de leitura e preço próprios.",
    "O mesmo produto é vendido em formas diferentes (lata e fardo, unidade e quilo), cada uma com código e preço próprios. Sem essa entidade, ou se perde o preço por forma, ou o estoque de lata e fardo fica incoerente.",
    [
     ("id_embalagem", "Identificador da forma de venda", "PK", "Gerado pelo sistema (ver D-13)"),
     ("id_produto", "Produto ao qual a forma de venda pertence", "FK", "Referencia PRODUTO. Obrigatório (RN-03)"),
     ("codigo_barras", "GTIN/EAN impresso pelo fabricante ou código interno", "AK (opcional)", "Único quando existir. Item sem código de fábrica recebe código interno de circulação restrita (prefixo 2) (RN-04)"),
     ("codigo_balanca", "Código do item na balança (PLU)", "AK (opcional)", "Único quando existir. Obrigatório para itens pesados: a etiqueta da balança traz o prefixo 2 + este código + preço ou peso, por isso o código lido muda a cada etiqueta (RN-04)"),
     ("descricao", "Descrição da forma de venda", "Simples", "Obrigatório. Ex.: 'Lata 350 ml', 'Fardo 12 un', 'Quilo'"),
     ("fator_conversao", "Quantas unidades base a embalagem representa", "Simples", "Obrigatório, > 0. Fardo 12 un = 12; Quilo = 1"),
     ("preco_venda", "Preço de venda vigente", "Simples", "Obrigatório, > 0. Toda alteração gera HISTORICO_PRECO (RN-06)"),
     ("ativa", "Indica se a embalagem pode ser vendida", "Simples", "Sim/Não. Embalagem com vendas nunca é excluída, só inativada"),
    ], changed=True)

ent("HISTORICO_PRECO", "PE", "Forte",
    "Registro de cada alteração de preço de venda (auditoria e análise).",
    "O preço muda com frequência e por motivos distintos (reajuste do fornecedor, vencimento próximo, correção). Guardar apenas o preço atual apagaria a informação — e a autoria — de cada alteração.",
    [
     ("id_historico", "Identificador da alteração", "PK", "Gerado pelo sistema"),
     ("id_embalagem", "Embalagem cujo preço foi alterado", "FK", "Referencia EMBALAGEM. Obrigatório"),
     ("id_funcionario", "Funcionário que alterou o preço", "FK", "Referencia FUNCIONARIO. Obrigatório (RN-07)"),
     ("data_hora", "Momento da alteração", "Simples", "Automático"),
     ("preco_anterior", "Preço antes da alteração", "Simples", "Obrigatório"),
     ("preco_novo", "Preço após a alteração", "Simples", "Obrigatório, > 0"),
     ("motivo", "Razão da alteração", "Simples", "Domínio: REAJUSTE_FORNECEDOR, PROXIMO_VENCIMENTO, PROMOCAO, CORRECAO"),
    ], changed=True)

ent("LOTE", "PE", "Forte",
    "Porção de um produto com a mesma origem, o mesmo custo unitário e a mesma validade. Base do controle de validade e do custo.",
    "É a entidade que viabiliza a prioridade nº 1 do gerente. Validade e custo não pertencem ao produto: pertencem à porção recebida. Dois lotes do mesmo arroz — inclusive vindos na mesma nota — podem ter validades e custos diferentes.",
    [
     ("id_lote", "Identificador do lote", "PK", "Gerado pelo sistema. Permite vários lotes do mesmo produto na mesma nota (RN-14) e lotes sem nota (inventário inicial, reposição de troca)"),
     ("id_produto", "Produto do lote", "FK", "Referencia PRODUTO. Obrigatório"),
     ("id_recebimento", "Recebimento de origem", "FK (opcional)", "Com numero_item_nota, referencia ITEM_RECEBIMENTO. Obrigatório quando origem = RECEBIMENTO"),
     ("numero_item_nota", "Linha da nota de origem", "FK (opcional)", "Referencia ITEM_RECEBIMENTO (com id_recebimento)"),
     ("id_lote_reposto", "Lote vencido/avariado que este lote repõe", "FK (opcional)", "Referencia LOTE (autorrelacionamento). Preenchido só quando origem = REPOSICAO_FORNECEDOR (RN-19)"),
     ("origem", "Como o lote passou a existir", "Simples", "Domínio: RECEBIMENTO, INVENTARIO_INICIAL, AJUSTE_INVENTARIO, REPOSICAO_FORNECEDOR"),
     ("codigo_lote_fabricante", "Lote impresso pelo fabricante", "Simples (opcional)", "Informativo; não é chave porque nem todo produto o traz"),
     ("data_validade", "Data de vencimento do lote", "Simples (opcional)", "Obrigatória se PRODUTO.controla_validade = Sim (RN-15)"),
     ("data_entrada", "Data em que o lote entrou no estoque", "Simples", "Automático"),
     ("quantidade_inicial", "Quantidade que entrou, na unidade base", "Derivado", "Quantidade da movimentação de entrada que criou o lote (na versão anterior era gravada; ficou redundante com a movimentação). Soma dos lotes de uma linha da nota = quantidade aceita (RN-14)"),
     ("custo_unitario", "Custo por unidade base", "Simples", "Obrigatório e imutável após a entrada (RN-22). Recebimento: valor unitário do item da nota ÷ fator; inventário: último custo de compra; reposição: custo do lote reposto"),
     ("situacao", "Estado do lote", "Simples", "Domínio: DISPONIVEL, SEPARADO_TROCA, TROCADO, DESCARTADO. “Esgotado” deixou de ser situação: é derivado do saldo zero"),
     ("pendente_conferencia", "Lote de ajuste automático aguardando conferência física", "Simples", "Só em lotes AJUSTE_INVENTARIO (RN-40)"),
     ("quantidade_atual", "Saldo atual do lote", "Derivado", "quantidade_inicial + entradas − saídas das movimentações do lote"),
     ("dias_para_vencer", "Dias restantes até a validade", "Derivado", "data_validade − data atual"),
    ], changed=True)

ent("MOVIMENTACAO_ESTOQUE", "PE", "Forte",
    "Toda entrada ou saída de estoque de um lote (kardex). Nada altera o estoque sem gerar uma movimentação.",
    "Representa toda entrada e saída (kardex). É o que garante que o saldo tenha origem verificável, que a perda por vencimento se torne mensurável e que o custo de cada venda seja calculado pelo lote realmente consumido.",
    [
     ("id_movimentacao", "Identificador da movimentação", "PK", "Gerado pelo sistema. Duas baixas do mesmo lote no mesmo instante são movimentações distintas"),
     ("id_lote", "Lote movimentado", "FK", "Referencia LOTE. Obrigatório (RN-16)"),
     ("id_funcionario", "Funcionário que registrou perda, troca ou ajuste", "FK (opcional)", "Referencia FUNCIONARIO. Obrigatório exceto nas baixas automáticas de venda (RN-18)"),
     ("id_venda", "Venda que gerou a baixa", "FK (opcional)", "Com numero_item, referencia ITEM_VENDA. Preenchido só no tipo SAIDA_VENDA"),
     ("numero_item", "Item do cupom que gerou a baixa", "FK (opcional)", "Referencia ITEM_VENDA (com id_venda)"),
     ("id_devolucao", "Devolução que gerou a movimentação", "FK (opcional)", "Referencia DEVOLUCAO. Preenchido nos tipos DEVOLUCAO_CLIENTE e SAIDA_TROCA_CLIENTE"),
     ("data_hora", "Momento da movimentação", "Simples", "Automático"),
     ("tipo", "Natureza da movimentação", "Simples", "Domínio: ENTRADA_RECEBIMENTO, ENTRADA_INVENTARIO, SAIDA_VENDA, DEVOLUCAO_CLIENTE, SAIDA_TROCA_CLIENTE, PERDA_VENCIMENTO, PERDA_AVARIA, TROCA_FORNECEDOR, AJUSTE_INVENTARIO_ENTRADA, AJUSTE_INVENTARIO_SAIDA"),
     ("quantidade", "Quantidade movimentada, na unidade base", "Simples", "Obrigatório, > 0; o tipo define se soma ou subtrai"),
     ("motivo", "Justificativa textual", "Simples (opcional)", "Obrigatório para perdas e ajustes de inventário"),
     ("valor_custo", "Valor de custo da movimentação", "Derivado", "quantidade × LOTE.custo_unitario. Somado por item de venda, dá o custo da mercadoria vendida (RN-22)"),
    ], changed=True)

# ---------- Compras e Fornecedores
ent("FORNECEDOR", "CF", "Forte",
    "Empresa, distribuidor ou produtor que vende mercadorias ao mercado.",
    "O mesmo produto vem de fornecedores diferentes com preços diferentes; além disso, o fornecedor é quem entrega, quem troca o vencido e quem emite o boleto.",
    [
     ("id_fornecedor", "Identificador do fornecedor", "PK", "Gerado pelo sistema (ver D-13)"),
     ("tipo_documento", "Tipo do documento fiscal", "Simples", "Domínio: CNPJ, CPF (produtor rural pessoa física)"),
     ("documento", "CNPJ ou CPF do fornecedor", "AK", "Obrigatório e único. Aceita o CNPJ alfanumérico (vigente desde 07/2026)"),
     ("razao_social", "Nome jurídico", "Simples", "Obrigatório"),
     ("nome_fantasia", "Nome comercial", "Simples (opcional)", "—"),
     ("contatos", "Vendedores/representantes: nome, telefone, WhatsApp", "Multivalorado e composto", "Um fornecedor pode ter vários vendedores (entrevista 3.11)"),
     ("canal_pedido", "Meio usual de pedido", "Simples", "Domínio: WHATSAPP, APLICATIVO, VENDEDOR_VISITA"),
     ("condicao_pagamento_padrao", "Prazo usual de pagamento", "Simples (opcional)", "Ex.: 'À vista', '7/14/21 dias'"),
     ("ativo", "Indica se o fornecedor está em uso", "Simples", "Sim/Não"),
    ], changed=True)

ent("PEDIDO_COMPRA", "CF", "Forte",
    "Solicitação de mercadorias feita a um fornecedor.",
    "O pedido existe antes da mercadoria e é a referência para verificar divergências. Sem ele não é possível responder “veio menos do que pedi?”.",
    [
     ("id_pedido", "Identificador do pedido", "PK", "Gerado pelo sistema (o pedido por WhatsApp não tem número próprio)"),
     ("id_fornecedor", "Fornecedor a quem o pedido foi feito", "FK", "Referencia FORNECEDOR. Obrigatório (RN-10)"),
     ("id_funcionario", "Funcionário que fez o pedido", "FK", "Referencia FUNCIONARIO. Obrigatório (PO-01)"),
     ("data_hora_pedido", "Momento em que o pedido foi feito", "Simples", "Obrigatório"),
     ("canal", "Meio utilizado no pedido", "Simples", "Domínio: WHATSAPP, APLICATIVO, VENDEDOR_VISITA"),
     ("cancelado", "Indica cancelamento do pedido", "Simples", "Sim/Não. Pedido cancelado não recebe mais entregas"),
     ("observacao", "Anotações do pedido", "Simples (opcional)", "—"),
     ("situacao", "Andamento do pedido", "Derivado", "ABERTO, PARCIALMENTE_RECEBIDO, RECEBIDO ou CANCELADO, calculado pela comparação dos itens pedidos com os itens recebidos (RN-11)"),
     ("valor_previsto", "Valor total esperado", "Derivado", "Σ quantidade_pedida × preco_negociado dos itens"),
    ], changed=True)

ent("ITEM_PEDIDO", "CF", "Associativa",
    "Entidade associativa: cada produto solicitado em um pedido (PEDIDO_COMPRA × PRODUTO).",
    "Era o relacionamento N:N SOLICITA. Precisou virar entidade associativa porque o item pedido tem de se relacionar com o item recebido (R18) — e relacionamento não se relaciona com relacionamento. É o que permite saber o que ainda falta chegar.",
    [
     ("id_pedido", "Pedido ao qual o item pertence", "PK, FK", "Referencia PEDIDO_COMPRA"),
     ("id_produto", "Produto solicitado", "PK, FK", "Referencia PRODUTO. Um produto aparece uma única vez em cada pedido"),
     ("quantidade_pedida", "Quantidade solicitada, na unidade base", "Simples", "> 0"),
     ("preco_negociado", "Preço unitário combinado com o vendedor", "Simples (opcional)", "—"),
     ("quantidade_recebida", "Quanto já chegou", "Derivado", "Σ quantidade aceita dos ITEM_RECEBIMENTO que atendem este item"),
     ("quantidade_pendente", "Quanto ainda falta chegar", "Derivado", "quantidade_pedida − quantidade_recebida (mínimo 0)"),
    ], new=True)

ent("RECEBIMENTO", "CF", "Forte",
    "Chegada física de mercadorias acompanhada de nota fiscal, com o resultado da conferência.",
    "É o evento que hoje não é registrado e do qual dependem estoque, validade, custo e contas a pagar. Distingue-se do pedido porque uma entrega pode atender parte de um pedido, vários pedidos ou nenhum pedido.",
    [
     ("id_recebimento", "Identificador do recebimento", "PK", "Gerado pelo sistema (ver D-13)"),
     ("id_fornecedor", "Fornecedor que emitiu a nota", "FK", "Referencia FORNECEDOR. Obrigatório (RN-12)"),
     ("id_funcionario", "Funcionário que conferiu a entrega", "FK", "Referencia FUNCIONARIO. Obrigatório (PO-05)"),
     ("chave_acesso_nfe", "Chave de acesso de 44 dígitos da NF-e", "AK (opcional)", "Única quando existir; identifica a nota em todo o país"),
     ("modelo_serie_numero", "Modelo, série e número da nota", "Composto", "Obrigatório. (fornecedor + modelo + série + número) é único; o número sozinho não é, pois pode repetir em séries diferentes"),
     ("data_hora", "Momento da chegada", "Simples", "Obrigatório"),
     ("valor_total_nota", "Valor total da nota", "Simples", "Obrigatório; base das contas a pagar"),
     ("volumes_nota", "Quantidade de volumes declarada na nota", "Simples", "Primeira etapa da conferência (entrevista 3.5)"),
     ("volumes_conferidos", "Quantidade de volumes efetivamente recebida", "Simples", "—"),
     ("situacao", "Resultado da conferência", "Simples", "Domínio: ACEITO, ACEITO_COM_DIVERGENCIA, RECUSADO"),
     ("observacao_divergencia", "Descrição geral das divergências", "Simples (opcional)", "Obrigatório se houver divergência"),
    ], changed=True)

ent("ITEM_RECEBIMENTO", "CF", "Fraca",
    "Cada linha (item) da nota fiscal recebida, com o resultado da conferência item a item.",
    "A conferência acontece item a item (entrevista 3.5) e o custo vem da linha da nota. Sem esta entidade não é possível dizer qual item de qual pedido foi atendido, registrar a recusa de um único produto nem dividir uma linha em vários lotes.",
    [
     ("id_recebimento", "Recebimento ao qual a linha pertence", "PK, FK", "Referencia RECEBIMENTO"),
     ("numero_item_nota", "Número da linha na nota fiscal", "PK", "Discriminador natural: o número do item impresso na nota não muda depois de emitida"),
     ("id_produto", "Produto recebido", "FK", "Referencia PRODUTO. Obrigatório"),
     ("id_pedido", "Pedido atendido por esta linha", "FK (opcional)", "Com id_produto, referencia ITEM_PEDIDO. Vazio se não houve pedido (RN-11, RN-12)"),
     ("quantidade_nota", "Quantidade faturada, na unidade da nota", "Simples", "Obrigatório, > 0"),
     ("fator_conversao_compra", "Unidades base por unidade da nota", "Simples", "Ex.: caixa com 12 = 12"),
     ("valor_unitario_nota", "Valor unitário cobrado na nota", "Simples", "Obrigatório, >= 0 (bonificação = 0)"),
     ("quantidade_aceita", "Quantidade aceita, na unidade base", "Simples", "0 a quantidade_nota × fator. 0 = item recusado"),
     ("situacao_item", "Resultado da conferência da linha", "Simples", "Domínio: ACEITO, ACEITO_PARCIAL, RECUSADO, NAO_PEDIDO_DEVOLVIDO"),
     ("custo_unitario_base", "Custo por unidade base", "Derivado", "valor_unitario_nota ÷ fator_conversao_compra; copiado para os lotes gerados"),
    ], new=True)

# ---------- Vendas e Caixa
ent("VENDA", "VC", "Forte",
    "Transação de venda registrada no caixa.",
    "Evento central do negócio: reúne itens, pagamentos, momento, caixa e operador.",
    [
     ("id_venda", "Identificador da venda", "PK", "Gerado pelo sistema; não depende do relógio do caixa, o que permite operar offline (RNF-07)"),
     ("id_sessao", "Sessão de caixa em que a venda ocorreu", "FK", "Referencia SESSAO_CAIXA. Obrigatório (RN-20)"),
     ("id_funcionario", "Funcionário que operou a venda", "FK", "Referencia FUNCIONARIO. Obrigatório (entrevista 5.16)"),
     ("id_cliente", "Cliente identificado", "FK (opcional)", "Referencia CLIENTE. Obrigatório se houver pagamento FIADO (RN-24)"),
     ("numero_cupom", "Número sequencial do cupom no caixa", "Simples", "Impresso no cupom; usado para localizar a venda na devolução"),
     ("data_hora", "Momento da venda", "Simples", "Automático"),
     ("situacao", "Estado da venda", "Simples", "Domínio: CONCLUIDA, CANCELADA"),
     ("valor_bruto", "Soma dos itens sem desconto", "Derivado", "Σ quantidade × preço praticado"),
     ("valor_desconto", "Soma dos descontos", "Derivado", "Σ quantidade × desconto unitário"),
     ("valor_total", "Valor a pagar", "Derivado", "valor_bruto − valor_desconto; deve igualar Σ pagamentos (RN-21)"),
     ("custo_total", "Custo da mercadoria vendida", "Derivado", "Σ custo_total dos itens"),
     ("lucro_bruto", "Resultado bruto da venda", "Derivado", "valor_total − custo_total (RF-38)"),
    ], changed=True)

ent("ITEM_VENDA", "VC", "Associativa",
    "Entidade associativa: cada linha de produto de uma venda (VENDA × EMBALAGEM).",
    "Resolve o N:N entre VENDA e EMBALAGEM e carrega informação que não pertence a nenhuma das duas: quantidade, preço praticado e desconto. Precisa ser entidade porque se relaciona com MOVIMENTACAO_ESTOQUE (baixas por lote) e com DEVOLUCAO.",
    [
     ("id_venda", "Venda do item", "PK, FK", "Referencia VENDA"),
     ("numero_item", "Posição do item no cupom (001, 002…)", "PK", "Discriminador natural impresso no cupom"),
     ("id_embalagem", "Forma de venda lida no scanner/balança", "FK", "Referencia EMBALAGEM. Obrigatório"),
     ("id_funcionario_autorizador", "Funcionário que autorizou o desconto", "FK (opcional)", "Referencia FUNCIONARIO. Obrigatório se houver desconto (RN-23)"),
     ("quantidade", "Quantidade vendida, na unidade da embalagem", "Simples", "> 0; decimal para itens pesados (kg)"),
     ("preco_unitario_praticado", "Preço no momento da venda", "Simples", "Cópia do preço vigente; não muda se o preço mudar depois (RN-22)"),
     ("desconto_unitario", "Desconto concedido por unidade", "Simples", "Padrão 0"),
     ("valor_item", "Valor líquido do item", "Derivado", "quantidade × (preço − desconto)"),
     ("custo_total", "Custo do item vendido", "Derivado", "Σ valor_custo das movimentações SAIDA_VENDA do item, menos o custo das devoluções. Quando o item consome dois lotes de custos diferentes, cada lote entra com o seu custo (RN-22)"),
     ("custo_unitario_medio", "Custo médio por unidade vendida", "Derivado", "custo_total ÷ (quantidade × fator_conversao)"),
    ], changed=True)

ent("FORMA_PAGAMENTO", "VC", "Forte",
    "Meio de pagamento aceito (dinheiro, débito, crédito, Pix, vale, fiado).",
    "Dinheiro, débito, crédito, Pix, vale e fiado têm prazos de crédito e taxas diferentes. É o que permite prever quando o dinheiro estará disponível.",
    [
     ("codigo_forma", "Código da forma de pagamento", "PK", "Código fixo controlado pelo mercado. Ex.: DIN, DEB, CRE, PIX, VALE, FIADO"),
     ("descricao", "Nome exibido no caixa", "Simples", "Obrigatório"),
     ("prazo_credito_dias", "Dias até o dinheiro estar disponível", "Simples", "Dinheiro/Pix = 0; cartões conforme contrato da maquininha"),
     ("taxa_percentual", "Taxa contratada com a operadora", "Simples", "Padrão 0; comparada à taxa realmente descontada na conciliação"),
     ("gera_divida", "Indica se a forma cria dívida do cliente", "Simples", "Somente FIADO = Sim"),
     ("exige_conciliacao", "Indica se o valor cai em conta e precisa ser conciliado", "Simples", "DEB, CRE, PIX, VALE = Sim; DIN e FIADO = Não"),
     ("ativa", "Indica se está disponível no caixa", "Simples", "Sim/Não"),
    ], changed=True)

ent("PAGAMENTO_VENDA", "VC", "Fraca",
    "Cada pagamento recebido em uma venda (permite pagamento dividido e mais de um cartão).",
    "Uma venda pode ser paga em mais de uma forma e até duas vezes na mesma forma (dois cartões). Cada transação tem valor, autorização e data de crédito próprios e precisa ser conciliada individualmente.",
    [
     ("id_venda", "Venda paga", "PK, FK", "Referencia VENDA"),
     ("numero_pagamento", "Sequência do pagamento dentro da venda", "PK", "1, 2, 3… Permite dois pagamentos na mesma forma"),
     ("codigo_forma", "Forma de pagamento utilizada", "FK", "Referencia FORMA_PAGAMENTO. Obrigatório"),
     ("id_movimento_fin", "Crédito em conta que liquidou este pagamento", "FK (opcional)", "Referencia MOVIMENTO_FINANCEIRO. Vazio enquanto não conciliado (RN-36)"),
     ("valor", "Valor aplicado à venda nesta forma", "Simples", "> 0; já líquido de troco"),
     ("valor_entregue", "Valor entregue pelo cliente em dinheiro", "Simples (opcional)", "Só para dinheiro"),
     ("nsu_autorizacao", "NSU/código de autorização da transação", "Simples (opcional)", "Obrigatório para cartão e Pix; é o elo com o relatório da maquininha"),
     ("troco", "Troco devolvido", "Derivado", "valor_entregue − valor"),
     ("data_prevista_credito", "Quando o valor deve cair em conta", "Derivado", "data da venda + prazo_credito_dias da forma"),
     ("valor_liquido_previsto", "Valor esperado após a taxa", "Derivado", "valor × (1 − taxa_percentual)"),
     ("situacao_credito", "Se o valor já foi confirmado em conta", "Derivado", "PENDENTE se não há movimento financeiro vinculado; CONCILIADO se há"),
    ], changed=True)

ent("CAIXA", "VC", "Forte",
    "Ponto de venda físico (o mercado possui 2).",
    "O mercado tem dois pontos de venda físicos e precisa comparar o desempenho e a conferência de cada um.",
    [
     ("numero_caixa", "Número físico do ponto de venda", "PK", "Único. Ex.: 1, 2. Chave natural estável: é o número pintado no próprio PDV"),
     ("ativo", "Indica se o caixa está em uso", "Simples", "Sim/Não"),
    ])

ent("SESSAO_CAIXA", "VC", "Forte",
    "Período entre a abertura e o fechamento de um caixa. É onde acontece o fechamento de caixa (conferência da gaveta e das maquininhas da sessão).",
    "Um mesmo caixa é aberto e fechado várias vezes, por operadores diferentes. A conferência do dinheiro pertence à sessão, não ao caixa.",
    [
     ("id_sessao", "Identificador da sessão", "PK", "Gerado pelo sistema"),
     ("numero_caixa", "Caixa aberto", "FK", "Referencia CAIXA. Obrigatório"),
     ("id_funcionario_abertura", "Funcionário que abriu a sessão", "FK", "Referencia FUNCIONARIO. Obrigatório"),
     ("id_funcionario_fechamento", "Funcionário que fechou a sessão", "FK (opcional)", "Referencia FUNCIONARIO. Vazio enquanto aberta"),
     ("data_hora_abertura", "Momento da abertura", "Simples", "Automático"),
     ("valor_inicial", "Fundo de troco informado na abertura", "Simples", "Obrigatório, >= 0 (não é fixo)"),
     ("data_hora_fechamento", "Momento do fechamento", "Simples (opcional)", "Vazio enquanto a sessão estiver aberta"),
     ("valor_contado", "Dinheiro físico contado no fechamento", "Simples (opcional)", "Obrigatório para fechar"),
     ("total_maquininhas_informado", "Total do relatório das maquininhas no fechamento", "Simples (opcional)", "Digitado pelo operador a partir do relatório da maquininha"),
     ("justificativa_diferenca", "Explicação de sobra ou falta", "Simples (opcional)", "Obrigatória quando houver diferença (RN-30)"),
     ("situacao", "Estado da sessão", "Derivado", "ABERTA se não há data de fechamento; FECHADA caso contrário (antes gravada; dependia de data_hora_fechamento)"),
     ("valor_esperado", "Dinheiro que deveria haver na gaveta", "Derivado", "inicial + Σ pagamentos em dinheiro (já líquidos de troco) + Σ abatimentos em dinheiro + suprimentos − sangrias − reembolsos em dinheiro (o recolhimento ocorre depois da contagem e não entra)"),
     ("diferenca_dinheiro", "Sobra ou falta de dinheiro", "Derivado", "valor_contado − valor_esperado"),
     ("total_eletronico_registrado", "Cartão, Pix e vale registrados no sistema", "Derivado", "Σ PAGAMENTO_VENDA da sessão nessas formas"),
     ("diferenca_eletronica", "Divergência com as maquininhas", "Derivado", "total_maquininhas_informado − total_eletronico_registrado"),
    ], changed=True)

ent("MOVIMENTACAO_CAIXA", "VC", "Forte",
    "Retirada ou reforço de dinheiro na gaveta que não é venda (sangria, suprimento, recolhimento, reembolso).",
    "Sangrias, suprimentos e reembolsos alteram o dinheiro da gaveta sem serem vendas. Sem registrá-los, o valor esperado no fechamento nunca fecha.",
    [
     ("id_mov_caixa", "Identificador da movimentação de caixa", "PK", "Gerado pelo sistema"),
     ("id_sessao", "Sessão em que ocorreu", "FK", "Referencia SESSAO_CAIXA. Obrigatório"),
     ("id_funcionario", "Funcionário que executou", "FK", "Referencia FUNCIONARIO. Obrigatório (RN-29)"),
     ("id_movimento_fin", "Lançamento no cofre/conta gerado", "FK (opcional)", "Referencia MOVIMENTO_FINANCEIRO. Sangria e recolhimento entram no COFRE; suprimento sai dele (RN-37)"),
     ("data_hora", "Momento da movimentação", "Simples", "Automático"),
     ("tipo", "Natureza da movimentação", "Simples", "Domínio: SANGRIA, SUPRIMENTO, RECOLHIMENTO_FECHAMENTO, REEMBOLSO_DEVOLUCAO"),
     ("valor", "Valor movimentado", "Simples", "> 0"),
     ("motivo", "Justificativa", "Simples", "Obrigatório"),
    ], changed=True)

ent("DEVOLUCAO", "VC", "Forte",
    "Devolução ou troca de um item vendido, feita pelo cliente.",
    "A devolução é um fato com data, motivo, quantidade, destino do produto, forma de reembolso e autorizador. Ela precisa estornar o estoque no lote certo (e portanto o custo), tirar dinheiro da gaveta quando há reembolso e, se a venda foi fiada, reduzir a dívida. Um simples tipo de movimentação não carrega essas informações.",
    [
     ("id_devolucao", "Identificador da devolução", "PK", "Gerado pelo sistema"),
     ("id_venda", "Venda de origem", "FK", "Com numero_item, referencia ITEM_VENDA. Obrigatório (só se devolve o que foi vendido)"),
     ("numero_item", "Item devolvido", "FK", "Referencia ITEM_VENDA"),
     ("id_funcionario", "Funcionário que autorizou", "FK", "Referencia FUNCIONARIO. Obrigatório (PO-13)"),
     ("id_mov_caixa", "Saída de dinheiro do reembolso", "FK (opcional)", "Referencia MOVIMENTACAO_CAIXA. Obrigatório quando forma_reembolso = DINHEIRO"),
     ("id_movimento_fin", "Estorno em conta", "FK (opcional)", "Referencia MOVIMENTO_FINANCEIRO. Obrigatório quando forma_reembolso = ESTORNO_ELETRONICO"),
     ("data_hora", "Momento da devolução", "Simples", "Automático"),
     ("quantidade_devolvida", "Quantidade devolvida, na unidade da embalagem", "Simples", "> 0 e <= quantidade vendida menos devoluções anteriores do item"),
     ("motivo", "Por que o cliente devolveu", "Simples", "Domínio: DEFEITO, VENCIDO (RN-28)"),
     ("destino", "O que acontece com o produto", "Simples", "Domínio: REVENDA, SEPARADO_TROCA, DESCARTE"),
     ("forma_reembolso", "Como o cliente é ressarcido", "Simples", "Domínio: TROCA_MESMO_PRODUTO, DINHEIRO, ESTORNO_ELETRONICO, ABATER_FIADO"),
     ("valor_reembolsado", "Valor devolvido ao cliente", "Simples", ">= 0; limitado ao valor pago pelo item. 0 na troca pelo mesmo produto"),
    ], new=True)

# ---------- Financeiro e Fiado
ent("CLIENTE", "FF", "Forte",
    "Consumidor identificado. O cadastro só é exigido para venda fiada.",
    "Só é necessário para o fiado — a maioria das vendas é anônima. Existe porque a dívida precisa de titular, saldo e histórico, substituindo o caderno.",
    [
     ("id_cliente", "Identificador do cliente", "PK", "Gerado pelo sistema (ver D-13)"),
     ("cpf", "Documento do cliente", "AK (opcional)", "Único quando informado; obrigatório para autorizar fiado (PO-04, premissa a validar)"),
     ("nome", "Nome do cliente", "Simples", "Obrigatório"),
     ("apelido", "Como o cliente é conhecido no bairro", "Simples (opcional)", "Facilita a identificação no balcão"),
     ("telefone", "Telefone de contato", "Simples (opcional)", "—"),
     ("endereco", "Logradouro, número, complemento, bairro", "Composto (opcional)", "—"),
     ("autorizado_fiado", "Indica se pode comprar fiado", "Simples", "Somente o gerente altera (PO-04)"),
     ("limite_fiado", "Valor máximo de dívida em aberto", "Simples (opcional)", "Se informado, bloqueia fiado acima do limite"),
     ("data_cadastro", "Data do cadastro", "Simples", "Automático"),
     ("saldo_devedor", "Quanto o cliente deve hoje", "Derivado", "Σ pagamentos FIADO − Σ abatimentos − Σ devoluções com reembolso ABATER_FIADO (RN-26)"),
    ], changed=True)

ent("ABATIMENTO_FIADO", "FF", "Forte",
    "Pagamento (total ou parcial) feito pelo cliente para reduzir sua dívida de fiado.",
    "O cliente paga aos poucos e sem vincular o pagamento a uma compra específica. Cada pagamento é um fato com data, valor, forma e responsável.",
    [
     ("id_abatimento", "Identificador do abatimento", "PK", "Gerado pelo sistema"),
     ("id_cliente", "Cliente que pagou", "FK", "Referencia CLIENTE. Obrigatório"),
     ("codigo_forma", "Forma usada no pagamento", "FK", "Referencia FORMA_PAGAMENTO. Não pode ser FIADO (RN-27)"),
     ("id_funcionario", "Funcionário que recebeu", "FK", "Referencia FUNCIONARIO. Obrigatório"),
     ("id_sessao", "Sessão em que o dinheiro entrou", "FK (opcional)", "Referencia SESSAO_CAIXA. Obrigatório quando pago em dinheiro no caixa"),
     ("id_movimento_fin", "Crédito em conta que liquidou o abatimento", "FK (opcional)", "Referencia MOVIMENTO_FINANCEIRO. Usado em Pix/cartão (RN-36)"),
     ("data_hora", "Momento do pagamento", "Simples", "Automático"),
     ("valor", "Valor pago", "Simples", "> 0 e <= saldo devedor do cliente"),
     ("observacao", "Anotação livre", "Simples (opcional)", "—"),
    ], changed=True)

ent("CONTA_PAGAR", "FF", "Forte",
    "Obrigação financeira do mercado: parcela de boleto de fornecedor, imposto, folha, internet etc.",
    "Cada parcela de boleto e cada despesa fixa é um compromisso com valor, vencimento e prioridade próprios. É a base da previsão de disponibilidade e do alerta solicitado pelo gerente.",
    [
     ("id_conta", "Identificador da obrigação", "PK", "Gerado pelo sistema (ver D-13)"),
     ("id_recebimento", "Recebimento que gerou a conta", "FK (opcional)", "Referencia RECEBIMENTO. Vazio em despesas fixas (RN-32)"),
     ("credor", "Quem recebe o pagamento", "Simples", "Obrigatório. Ex.: razão social do fornecedor, 'Receita Federal'"),
     ("numero_documento", "Número do boleto, da guia ou competência", "Simples (opcional)", "Ex.: nº do boleto; 'DAS 09/2026'"),
     ("numero_parcela", "Parcela do documento", "Simples", "1 para conta única; 1, 2, 3 no boleto 7/14/21"),
     ("descricao", "Descrição da conta", "Simples", "Obrigatório"),
     ("categoria_despesa", "Tipo de despesa", "Simples", "Domínio: FORNECEDOR, SIMPLES_NACIONAL, FOLHA, INTERNET, AGUA, LUZ, ALUGUEL, OUTROS"),
     ("valor_original", "Valor da obrigação", "Simples", "> 0"),
     ("data_vencimento", "Data de vencimento", "Simples", "Obrigatório"),
     ("prioridade", "Prioridade de pagamento", "Simples", "Domínio: ALTA, MEDIA, BAIXA (entrevista 6.4)"),
     ("cancelada", "Indica cancelamento", "Simples", "Sim/Não"),
     ("valor_principal_pago", "Quanto do valor original já foi quitado", "Derivado", "Σ valor_principal dos PAGAMENTO_CONTA"),
     ("encargos_pagos", "Juros e multa pagos", "Derivado", "Σ valor_juros_multa dos pagamentos"),
     ("saldo_em_aberto", "Quanto ainda falta pagar", "Derivado", "valor_original − valor_principal_pago"),
     ("situacao", "Estado da conta", "Derivado", "ABERTA (nada pago), PARCIALMENTE_PAGA, PAGA (saldo = 0) ou CANCELADA"),
     ("vencida", "Se há saldo em aberto após o vencimento", "Derivado", "saldo_em_aberto > 0 e data atual > data_vencimento"),
    ], changed=True)

ent("PAGAMENTO_CONTA", "FF", "Fraca",
    "Cada pagamento — total ou parcial — feito sobre uma conta a pagar.",
    "Uma mesma obrigação pode ser paga em mais de um momento (parte em dinheiro ao vendedor, parte no banco com juros). Cada pagamento tem data, valor, encargos, origem do dinheiro e responsável próprios — informações que não cabem em um único campo da conta.",
    [
     ("id_conta", "Conta paga", "PK, FK", "Referencia CONTA_PAGAR"),
     ("numero_pagamento", "Sequência do pagamento dentro da conta", "PK", "1, 2, 3…"),
     ("id_funcionario", "Funcionário que registrou o pagamento", "FK", "Referencia FUNCIONARIO. Obrigatório (RN-35)"),
     ("id_movimento_fin", "Saída de dinheiro correspondente", "FK", "Referencia MOVIMENTO_FINANCEIRO. Obrigatório: todo pagamento sai de uma conta financeira (banco ou cofre)"),
     ("data_pagamento", "Data do pagamento", "Simples", "Obrigatório"),
     ("valor_principal", "Parte do valor original quitada", "Simples", "> 0; Σ dos pagamentos <= valor_original (RN-38)"),
     ("valor_juros_multa", "Encargos por atraso pagos neste pagamento", "Simples", ">= 0; padrão 0"),
     ("valor_desconto", "Desconto obtido neste pagamento", "Simples", ">= 0; padrão 0"),
     ("valor_total_pago", "Valor que efetivamente saiu", "Derivado", "valor_principal + juros/multa − desconto"),
     ("observacao", "Anotação livre", "Simples (opcional)", "Ex.: 'pago em dinheiro ao vendedor'"),
    ], new=True)

ent("CONTA_FINANCEIRA", "FF", "Forte",
    "Lugar onde o dinheiro do mercado fica guardado fora da gaveta: conta bancária, conta da maquininha ou cofre.",
    "Sem saber quanto há hoje no banco e no cofre, a previsão de disponibilidade não tem ponto de partida e o alerta de “dinheiro insuficiente” é impossível.",
    [
     ("id_conta_financeira", "Identificador", "PK", "Gerado pelo sistema"),
     ("nome", "Nome da conta", "Simples", "Obrigatório. Ex.: 'Banco X – conta PJ', 'Cofre'"),
     ("tipo", "Tipo de conta", "Simples", "Domínio: CONTA_BANCARIA, CONTA_ADQUIRENTE, COFRE"),
     ("saldo_inicial", "Saldo na data de implantação", "Simples", "Obrigatório"),
     ("data_saldo_inicial", "Data do saldo inicial", "Simples", "Obrigatório"),
     ("ativa", "Indica se está em uso", "Simples", "Sim/Não"),
     ("saldo_atual", "Saldo realizado hoje", "Derivado", "saldo_inicial + Σ créditos − Σ débitos dos movimentos"),
    ], new=True)

ent("MOVIMENTO_FINANCEIRO", "FF", "Forte",
    "Entrada ou saída de dinheiro efetivamente ocorrida em uma conta financeira (linha do extrato do banco/maquininha ou do cofre).",
    "É o “dinheiro realizado”. Separa o que foi vendido (PAGAMENTO_VENDA) do que de fato entrou em conta, permitindo a conciliação (comparar previsto × realizado, taxa contratada × taxa cobrada) e a previsão de disponibilidade a partir de um saldo real.",
    [
     ("id_movimento_fin", "Identificador do movimento", "PK", "Gerado pelo sistema"),
     ("id_conta_financeira", "Conta onde ocorreu", "FK", "Referencia CONTA_FINANCEIRA. Obrigatório"),
     ("id_funcionario", "Funcionário que lançou", "FK (opcional)", "Referencia FUNCIONARIO. Obrigatório em lançamentos manuais (tarifa, ajuste)"),
     ("data_movimento", "Data em que o valor entrou ou saiu", "Simples", "Obrigatório"),
     ("natureza", "Sentido do movimento", "Simples", "Domínio: CREDITO, DEBITO"),
     ("origem", "O que gerou o movimento", "Simples", "Domínio: REPASSE_CARTAO, PIX_RECEBIDO, RECOLHIMENTO_GAVETA, SUPRIMENTO_GAVETA, DEPOSITO, PAGAMENTO_CONTA, ESTORNO_DEVOLUCAO, TARIFA, AJUSTE"),
     ("valor_bruto", "Valor antes de taxas", "Simples", "> 0"),
     ("valor_taxa", "Taxa efetivamente descontada", "Simples", ">= 0; padrão 0"),
     ("documento_referencia", "Identificação no extrato/relatório", "Simples (opcional)", "Ex.: ID do repasse, ID do Pix"),
     ("valor_liquido", "Valor que alterou o saldo", "Derivado", "valor_bruto − valor_taxa"),
     ("valor_previsto_vinculado", "Quanto o sistema esperava receber neste crédito", "Derivado", "Σ valor líquido previsto (valor × (1 − taxa contratada)) dos PAGAMENTO_VENDA e ABATIMENTO_FIADO liquidados por ele"),
     ("diferenca_conciliacao", "Divergência entre esperado e recebido", "Derivado", "valor_liquido − valor_previsto_vinculado (só para créditos de repasse/Pix). Diferente de zero indica transação faltante ou taxa acima da contratada"),
     ("situacao_conciliacao", "Resultado da conciliação", "Derivado", "CONCILIADO (diferença 0), DIVERGENTE ou NAO_SE_APLICA"),
    ], new=True)

# ---------- Pessoas e Acesso
ent("FUNCIONARIO", "PA", "Forte",
    "Pessoa que trabalha no mercado e utiliza o sistema.",
    "Responde “quem fez”, pergunta que hoje o mercado não consegue responder e que o gerente declarou importante para evitar alterações indevidas.",
    [
     ("id_funcionario", "Identificador do funcionário", "PK", "Gerado pelo sistema. Evita espalhar o CPF por todas as tabelas de operação (LGPD, RNF-13)"),
     ("cpf", "Documento do funcionário", "AK", "Obrigatório e único"),
     ("login", "Nome de usuário no sistema", "AK", "Obrigatório e único"),
     ("nome", "Nome completo", "Simples", "Obrigatório"),
     ("telefone", "Telefone de contato", "Simples (opcional)", "—"),
     ("funcao_principal", "Função habitual (caixa, padaria/balança, reposição, gerência)", "Simples", "Descritiva; o que ele PODE fazer é definido por PERMISSAO"),
     ("data_admissao", "Data de admissão", "Simples", "—"),
     ("ativo", "Indica se o funcionário está ativo", "Simples", "Inativo não acessa o sistema"),
    ], changed=True)

ent("PERMISSAO", "PA", "Forte",
    "Operação sensível do sistema que precisa ser liberada individualmente.",
    "As funções se sobrepõem e não correspondem a cargos fixos; o que define o que cada um pode fazer é a permissão concedida individualmente.",
    [
     ("codigo_permissao", "Código da permissão", "PK", "Código fixo definido pelo sistema. Ex.: OPERAR_CAIXA, CADASTRAR_PRODUTO, ALTERAR_PRECO, RECEBER_MERCADORIA, REGISTRAR_PERDA, AJUSTAR_ESTOQUE, AUTORIZAR_DESCONTO, AUTORIZAR_DEVOLUCAO, CONCEDER_FIADO, REALIZAR_SANGRIA, GERENCIAR_FINANCEIRO, GERENCIAR_USUARIOS"),
     ("descricao", "O que a permissão libera", "Simples", "Obrigatório"),
    ], changed=True)

# ---------------------------------------------------------------- relacionamentos
# (id, A, cardA, verbo, B, cardB, atributos, justificativa, regra, modulo, status)
# convenção do manual: A (min,max) — verbo — B (min,max); o par junto de A
# indica com quantas ocorrências de B uma ocorrência de A se relaciona.
R = []
def rel(a, ca, verbo, b, cb, just, regra, mod, status="mantido", attrs=None, ida=None, volta=None, nn=False):
    R.append(dict(id=f"R{len(R)+1:02d}", a=a, ca=ca, verbo=verbo, b=b, cb=cb,
                  just=just, regra=regra, mod=mod, status=status, attrs=attrs, nn=nn))

# Produtos e estoque
rel("CATEGORIA","(0,N)","classifica","PRODUTO","(1,1)","Todo produto pertence a exatamente um setor; um setor recém-criado pode ainda não ter produtos.","RN-01","PE")
rel("PRODUTO","(1,N)","é vendido em","EMBALAGEM","(1,1)","Um produto só é vendável se tiver ao menos uma forma de venda; cada embalagem é de um único produto.","RN-03","PE")
rel("EMBALAGEM","(0,N)","registra","HISTORICO_PRECO","(1,1)","Cada alteração de preço refere-se a uma embalagem; embalagem nova pode não ter alterações.","RN-06","PE")
rel("FUNCIONARIO","(0,N)","altera","HISTORICO_PRECO","(1,1)","Toda alteração de preço tem um responsável identificado.","RN-07","PA")
rel("PRODUTO","(0,N)","possui","LOTE","(1,1)","O estoque do produto é a soma dos saldos dos seus lotes; produto recém-cadastrado pode não ter lote.","RN-14","PE")
rel("LOTE","(1,N)","sofre","MOVIMENTACAO_ESTOQUE","(1,1)","Todo lote nasce com uma movimentação de entrada; cada movimentação afeta um único lote.","RN-16","PE")
rel("FUNCIONARIO","(0,N)","registra","MOVIMENTACAO_ESTOQUE","(0,1)","Perdas, trocas e ajustes manuais exigem responsável; baixas automáticas de venda são rastreadas pelo item de venda.","RN-18","PA")
rel("LOTE","(0,N)","é reposto por","LOTE","(0,1)","Autorrelacionamento: o lote vencido trocado pelo fornecedor (papel “reposto”) pode gerar zero ou mais lotes de reposição; cada lote de reposição repõe no máximo um lote.","RN-19","PE",status="novo")
# Compras
rel("FORNECEDOR","(0,N)","FORNECE","PRODUTO","(0,N)","Um produto pode ser comprado de vários fornecedores e um fornecedor vende vários produtos, com preços diferentes. O preço pertence ao PAR fornecedor-produto.","RN-09","CF",attrs="codigo_no_fornecedor, /preco_ultima_compra, /data_ultima_compra",nn=True)
rel("FORNECEDOR","(0,N)","atende","PEDIDO_COMPRA","(1,1)","Todo pedido é feito a um único fornecedor.","RN-10","CF")
rel("FUNCIONARIO","(0,N)","emite","PEDIDO_COMPRA","(1,1)","Pedidos são feitos por funcionários específicos (entrevista 3.2).","PO-01","PA")
rel("PEDIDO_COMPRA","(1,N)","contém","ITEM_PEDIDO","(1,1)","Um pedido tem ao menos um produto solicitado; cada item é de um único pedido.","RN-10","CF",status="alterado")
rel("PRODUTO","(0,N)","é solicitado em","ITEM_PEDIDO","(1,1)","Um produto aparece em vários pedidos ao longo do tempo; cada item refere-se a um único produto.","RN-10","CF",status="alterado")
rel("FORNECEDOR","(0,N)","entrega","RECEBIMENTO","(1,1)","Todo recebimento tem um fornecedor, mesmo sem pedido prévio.","RN-12","CF")
rel("FUNCIONARIO","(0,N)","confere","RECEBIMENTO","(1,1)","Quem estiver disponível confere (entrevista 3.15); o sistema precisa saber quem foi.","PO-05","PA")
rel("RECEBIMENTO","(1,N)","contém","ITEM_RECEBIMENTO","(1,1)","Toda nota tem ao menos uma linha; as linhas são registradas mesmo na recusa, para documentar o que foi recusado.","RN-13","CF",status="novo")
rel("PRODUTO","(0,N)","é recebido em","ITEM_RECEBIMENTO","(1,1)","Cada linha da nota refere-se a um único produto do cadastro.","RN-13","CF",status="novo")
rel("ITEM_PEDIDO","(0,N)","é atendido por","ITEM_RECEBIMENTO","(0,1)","Um item pedido pode chegar em várias entregas (faltante chega depois) ou em nenhuma (pedido cancelado); uma linha da nota atende no máximo um item pedido e pode não atender nenhum (vendedor que passa e entrega na hora, produto não pedido).","RN-11","CF",status="novo")
rel("ITEM_RECEBIMENTO","(0,N)","origina","LOTE","(0,1)","Uma linha aceita gera um ou mais lotes (um por data de validade); linha recusada gera zero. Um lote pode não vir de nota (inventário inicial, reposição de troca).","RN-14","CF",status="novo")
rel("RECEBIMENTO","(0,N)","gera","CONTA_PAGAR","(0,1)","Uma entrega gera uma conta quitada no ato (à vista), várias parcelas (boleto 7/14/21) ou nenhuma (entrega recusada). Contas como luz e Simples Nacional não vêm de recebimento.","RN-31","CF")
# Vendas e caixa
rel("CAIXA","(0,N)","possui","SESSAO_CAIXA","(1,1)","Cada sessão acontece em um único caixa; um caixa tem várias sessões ao longo do tempo.","RN-30","VC")
rel("FUNCIONARIO","(0,N)","abre","SESSAO_CAIXA","(1,1)","Operadores abrem o caixa (entrevista 5.6).","PO-11","PA")
rel("FUNCIONARIO","(0,N)","fecha","SESSAO_CAIXA","(0,1)","Sessão aberta ainda não foi fechada; o fechamento precisa de responsável (entrevista 5.13).","RN-30","PA")
rel("SESSAO_CAIXA","(0,N)","registra","VENDA","(1,1)","Não existe venda fora de uma sessão de caixa aberta.","RN-20","VC")
rel("FUNCIONARIO","(0,N)","opera","VENDA","(1,1)","Resolve “não conseguimos identificar quem fez a venda” (entrevista 5.16). Fica na VENDA porque quem cobre o almoço opera o mesmo caixa.","RN-35","PA")
rel("CLIENTE","(0,N)","realiza","VENDA","(0,1)","A maioria das vendas é anônima; só a venda fiada exige cliente.","RN-24","FF")
rel("VENDA","(1,N)","contém","ITEM_VENDA","(1,1)","Uma venda tem ao menos um item.","RN-21","VC")
rel("EMBALAGEM","(0,N)","é vendida em","ITEM_VENDA","(1,1)","O item referencia a embalagem lida no scanner ou na balança, que determina preço e fator de conversão.","RN-03","VC")
rel("FUNCIONARIO","(0,N)","autoriza desconto","ITEM_VENDA","(0,1)","Desconto só com autorização de quem tem permissão.","RN-23","PA")
rel("ITEM_VENDA","(0,N)","baixa","MOVIMENTACAO_ESTOQUE","(0,1)","Um item pode baixar mais de um lote (FEFO), gerando uma movimentação por lote — é assim que o custo de cada lote entra no custo da venda. Mínimo 0 só para venda cancelada antes da conclusão (RN-17).","RN-17, RN-22","VC",status="alterado")
rel("VENDA","(0,N)","é paga por","PAGAMENTO_VENDA","(1,1)","Permite pagamento dividido e mais de uma transação na mesma forma (dois cartões). Mínimo 0: a venda cancelada antes do pagamento não tem pagamento; a venda CONCLUÍDA tem ao menos um e a soma fecha o total (RN-21, auditoria A01).","RN-21","VC",status="alterado")
rel("FORMA_PAGAMENTO","(0,N)","é usada em","PAGAMENTO_VENDA","(1,1)","Separa o faturamento por forma de pagamento (hoje não feito, entrevista 5.11).","RN-33","VC")
rel("SESSAO_CAIXA","(0,N)","registra","MOVIMENTACAO_CAIXA","(1,1)","Sangrias, suprimentos, recolhimentos e reembolsos pertencem a uma sessão e entram no valor esperado.","RN-29","VC")
rel("FUNCIONARIO","(0,N)","executa","MOVIMENTACAO_CAIXA","(1,1)","Toda retirada ou reforço de dinheiro tem responsável.","RN-29","PA")
rel("ITEM_VENDA","(0,N)","é devolvido em","DEVOLUCAO","(1,1)","Um item pode ser devolvido nenhuma ou várias vezes (devoluções parciais); toda devolução refere-se a um item vendido.","RN-28","VC",status="novo")
rel("FUNCIONARIO","(0,N)","autoriza","DEVOLUCAO","(1,1)","Devolução movimenta estoque e dinheiro; precisa de autorizador.","PO-13","PA",status="novo")
rel("DEVOLUCAO","(1,N)","gera","MOVIMENTACAO_ESTOQUE","(0,1)","Toda devolução devolve a quantidade ao(s) lote(s) baixado(s) pelo item (estornando o custo); se for troca pelo mesmo produto, gera também a nova saída.","RN-28","VC",status="novo")
rel("DEVOLUCAO","(0,1)","é reembolsada por","MOVIMENTACAO_CAIXA","(0,1)","Reembolso em dinheiro sai da gaveta e precisa entrar na conferência do caixa.","RN-28","VC",status="novo")
rel("DEVOLUCAO","(0,1)","é estornada por","MOVIMENTO_FINANCEIRO","(0,1)","Reembolso por estorno de cartão/Pix sai da conta financeira.","RN-28","FF",status="novo")
# Financeiro e fiado
rel("CLIENTE","(0,N)","paga","ABATIMENTO_FIADO","(1,1)","O cliente paga aos poucos, sem vínculo com uma venda específica (entrevista 4.6).","RN-27","FF")
rel("FORMA_PAGAMENTO","(0,N)","é usada em","ABATIMENTO_FIADO","(1,1)","Cliente pode quitar fiado em dinheiro, Pix ou cartão; a forma FIADO não pode ser usada aqui.","RN-27","FF")
rel("FUNCIONARIO","(0,N)","recebe","ABATIMENTO_FIADO","(1,1)","Quem recebeu o pagamento fica registrado.","RN-35","PA")
rel("SESSAO_CAIXA","(0,N)","contabiliza","ABATIMENTO_FIADO","(0,1)","Abatimento em dinheiro entra na gaveta e na conferência; pagamento por Pix fora do caixa, não.","RN-30","VC")
rel("CONTA_PAGAR","(0,N)","é quitada por","PAGAMENTO_CONTA","(1,1)","Uma obrigação pode ter nenhum pagamento (em aberto), um (quitada de uma vez) ou vários (pagamentos parciais).","RN-38","FF",status="novo")
rel("FUNCIONARIO","(0,N)","registra","PAGAMENTO_CONTA","(1,1)","Todo pagamento tem responsável identificado.","RN-35","PA",status="alterado")
rel("PAGAMENTO_CONTA","(1,1)","gera","MOVIMENTO_FINANCEIRO","(0,1)","Todo pagamento corresponde a exatamente uma saída de dinheiro de uma conta financeira; movimentos de outras origens não têm pagamento de conta.","RN-38","FF",status="novo")
rel("CONTA_FINANCEIRA","(0,N)","registra","MOVIMENTO_FINANCEIRO","(1,1)","Cada movimento ocorre em uma única conta (banco, maquininha ou cofre).","RN-36","FF",status="novo")
rel("MOVIMENTO_FINANCEIRO","(0,N)","liquida","PAGAMENTO_VENDA","(0,1)","Um repasse da maquininha liquida várias transações de uma vez; cada transação é liquidada por no máximo um crédito (dinheiro não passa por aqui).","RN-36","FF",status="novo")
rel("MOVIMENTO_FINANCEIRO","(0,N)","liquida","ABATIMENTO_FIADO","(0,1)","Abatimento pago por Pix ou cartão também precisa ser confirmado em conta.","RN-36","FF",status="novo")
rel("MOVIMENTACAO_CAIXA","(0,1)","gera","MOVIMENTO_FINANCEIRO","(0,1)","Sangria e recolhimento levam o dinheiro da gaveta ao cofre; suprimento faz o caminho inverso. Reembolso de devolução não gera movimento.","RN-37","FF",status="novo")
rel("FUNCIONARIO","(0,N)","lança","MOVIMENTO_FINANCEIRO","(0,1)","Lançamentos manuais (tarifa, ajuste) exigem responsável; créditos importados do extrato não.","RN-35","PA",status="novo")
rel("FUNCIONARIO","(0,N)","POSSUI","PERMISSAO","(0,N)","As funções se sobrepõem (entrevista 7.4). Controle por permissão individual, não por cargo fixo.","RN-35","PA",attrs="data_concessao, data_revogacao",nn=True)

# relacionamentos da versão original que deixaram de existir
REMOVED = [
    ("R08 (antigo)", "PEDIDO_COMPRA (1,N) — SOLICITA — PRODUTO (0,N)", "Convertido na entidade associativa ITEM_PEDIDO (R12 e R13), porque o item pedido precisa se relacionar com o item recebido."),
    ("R09 (antigo)", "PEDIDO_COMPRA (0,N) — é atendido por — RECEBIMENTO (0,1)", "Substituído por ITEM_PEDIDO — é atendido por — ITEM_RECEBIMENTO (R18). No nível do cabeçalho não era possível saber o que faltava chegar nem uma nota atender dois pedidos."),
    ("R12 (antigo)", "RECEBIMENTO (0,N) — origina — LOTE (1,1)", "Substituído por RECEBIMENTO → ITEM_RECEBIMENTO → LOTE (R16 e R19). O mínimo 1 do lado do lote impedia lotes sem nota."),
    ("R18 (antigo)", "FUNCIONARIO (0,N) — quita — CONTA_PAGAR (0,1)", "Substituído por FUNCIONARIO — registra — PAGAMENTO_CONTA (R45): com pagamentos parciais, cada pagamento tem o seu responsável."),
]
