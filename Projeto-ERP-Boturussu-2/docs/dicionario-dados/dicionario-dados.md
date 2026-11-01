# Dicionário de dados — banco implementado (`mercado_boturussu`)

Gerado a partir de `ferramentas/gerador_massa/fis.py`, a mesma fonte que gera `sql/ddl/02_tabelas.sql`. 
A conferência automática contra o banco criado está em `evidencias/08_conferencia_dicionario_x_banco.md`.

## funcionario

*Pessoa que trabalha no mercado e usa o sistema; responde “quem fez” em todas as operações.* — origem: Entidade FUNCIONARIO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_funcionario | Identificador do funcionário | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta: evita espalhar o CPF pelas tabelas de operação (RNF-13); AUTO_INCREMENT |
| cpf | CPF, só dígitos | CHAR | 11 | Não | Não | Não permitido | Sim | — | Único; 11 dígitos; CHECK: ck_funcionario_cpf; UNIQUE: uq_funcionario_cpf |
| login | Usuário de acesso ao sistema | VARCHAR | 30 | Não | Não | Não permitido | Sim | — | Único (RNF-01); UNIQUE: uq_funcionario_login |
| nome | Nome completo | VARCHAR | 100 | Não | Não | Não permitido | Não | — | — |
| telefone | Telefone de contato | VARCHAR | 15 | Não | Não | Permitido | Não | — | Só dígitos, 10 ou 11; CHECK: ck_funcionario_tel |
| funcao_principal | Função habitual | VARCHAR | 20 | Não | Não | Não permitido | Não | — | CAIXA, BALANCA, REPOSICAO, GERENCIA. Descritiva: o que pode fazer vem de funcionario_permissao; CHECK: ck_funcionario_funcao |
| data_admissao | Data de admissão | DATE | — | Não | Não | Permitido | Não | — | — |
| ativo | Se pode acessar o sistema | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | Inativo não opera (RNF-06: não se exclui) |

## permissao

*Operação sensível liberada individualmente (PO-01, PO-02, PO-11, PO-13, PO-14).* — origem: Entidade PERMISSAO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| codigo_permissao | Código da permissão | VARCHAR | 30 | Sim | Não | Não permitido | Sim (PK) | — | Chave natural: código fixo definido pelo sistema (D-13) |
| descricao | O que a permissão libera | VARCHAR | 150 | Não | Não | Não permitido | Não | — | — |

## funcionario_permissao

*Quais permissões cada funcionário tem e desde quando.* — origem: Relacionamento N:N POSSUI (R52) → tabela associativa.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_funcionario | Funcionário | INT UNSIGNED | — | Sim | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario |
| codigo_permissao | Permissão concedida | VARCHAR | 30 | Sim | Sim → permissao(codigo_permissao) | Não permitido | Não | — | FK → permissao |
| data_concessao | Data da concessão | DATE | — | Sim | Não | Não permitido | Não | CURRENT_DATE | Atributo do relacionamento; compõe a PK para permitir conceder de novo depois de revogar; CHECK: ck_fp_periodo |
| data_revogacao | Data em que a permissão foi retirada | DATE | — | Não | Não | Permitido | Não | — | Vazio = vigente. Revogar não apaga a linha: a auditoria precisa saber quem podia o quê em cada data (RNF-02); CHECK: ck_fp_periodo |

## categoria

*Setor do mercado; define o prazo padrão de alerta de validade.* — origem: Entidade CATEGORIA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| codigo_categoria | Sigla do setor | VARCHAR | 10 | Sim | Não | Não permitido | Sim (PK) | — | Chave natural controlada pelo mercado (D-13) |
| nome | Nome do setor | VARCHAR | 50 | Não | Não | Não permitido | Sim | — | Único; UNIQUE: uq_categoria_nome |
| controle_validade_rigoroso | Exige vigilância maior de validade | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | Alimentos básicos = verdadeiro (entrevista 2.15) |
| dias_alerta_validade_padrao | Antecedência padrão do alerta de validade, em dias | SMALLINT UNSIGNED | — | Não | Não | Permitido | Não | — | — |

## produto

*Item comercializado; unidade de controle de estoque.* — origem: Entidade PRODUTO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_produto | Identificador do produto | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta (D-13); AUTO_INCREMENT |
| codigo_categoria | Setor do produto | VARCHAR | 10 | Não | Sim → categoria(codigo_categoria) | Não permitido | Não | — | FK → categoria (RN-01) |
| nome_produto | Nome padronizado (tipo, marca, variação) | VARCHAR | 120 | Não | Não | Não permitido | Sim | — | Único (chave alternativa); UNIQUE: uq_produto_nome |
| marca | Marca | VARCHAR | 60 | Não | Não | Permitido | Não | — | Vazio em hortifruti |
| unidade_base | Unidade de contagem do estoque | CHAR | 2 | Não | Não | Não permitido | Não | — | UN ou KG (RN-02); CHECK: ck_produto_unidade, ck_produto_peso_kg |
| vendido_por_peso | Vendido fracionado na balança | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | Se verdadeiro, unidade_base = KG (RN-02); CHECK: ck_produto_peso_kg |
| controla_validade | Exige data de validade no lote | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | RN-15 |
| dias_alerta_validade | Antecedência do alerta, em dias | SMALLINT UNSIGNED | — | Não | Não | Permitido | Não | — | Sobrepõe o padrão da categoria |
| estoque_minimo | Estoque mínimo, na unidade base | DECIMAL | 12,3 | Não | Não | Não permitido | Não | 0 | >= 0; dispara alerta (RF-19); CHECK: ck_produto_estoque_min |
| margem_referencia | Margem de referência (%) | DECIMAL | 5,2 | Não | Não | Permitido | Não | — | 0 a 300 (PO-09); CHECK: ck_produto_margem |
| ativo | Em comercialização | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | — |

## embalagem

*Forma de venda de um produto, com código de leitura, fator de conversão e preço vigente.* — origem: Entidade EMBALAGEM.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_embalagem | Identificador da forma de venda | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta (D-13); AUTO_INCREMENT |
| id_produto | Produto da embalagem | INT UNSIGNED | — | Não | Sim → produto(id_produto) | Não permitido | Não | — | FK → produto (RN-03) |
| codigo_barras | GTIN/EAN de fábrica ou código interno (prefixo 2) | VARCHAR | 14 | Não | Não | Permitido | Sim | — | Único quando existir (RN-04); CHECK: ck_embalagem_codigo, ck_embalagem_barras_fmt; UNIQUE: uq_embalagem_barras |
| codigo_balanca | Código do item na balança (PLU) | VARCHAR | 6 | Não | Não | Permitido | Sim | — | Único quando existir; usado nos itens pesados (RN-04); CHECK: ck_embalagem_codigo, ck_embalagem_balanca_fmt; UNIQUE: uq_embalagem_balanca |
| descricao | Descrição da forma de venda | VARCHAR | 60 | Não | Não | Não permitido | Não | — | Ex.: 'Lata 350 ml', 'Fardo 12 un', 'Quilo' |
| fator_conversao | Unidades base por embalagem | DECIMAL | 10,3 | Não | Não | Não permitido | Não | — | > 0 (fardo 12 = 12); CHECK: ck_embalagem_fator |
| preco_venda | Preço de venda vigente | DECIMAL | 10,2 | Não | Não | Não permitido | Não | — | > 0; toda alteração gera historico_preco (RN-06); CHECK: ck_embalagem_preco |
| ativa | Pode ser vendida | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | — |

## historico_preco

*Registro de cada alteração do preço de venda de uma embalagem.* — origem: Entidade HISTORICO_PRECO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_historico | Identificador da alteração | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | AUTO_INCREMENT |
| id_embalagem | Embalagem alterada | INT UNSIGNED | — | Não | Sim → embalagem(id_embalagem) | Não permitido | Não | — | FK → embalagem |
| id_funcionario | Quem alterou | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario (RN-07) |
| data_hora | Momento da alteração | DATETIME | — | Não | Não | Não permitido | Não | CURRENT_TIMESTAMP | — |
| preco_anterior | Preço antes da alteração | DECIMAL | 10,2 | Não | Não | Não permitido | Não | — | > 0; CHECK: ck_hp_precos |
| preco_novo | Preço depois da alteração | DECIMAL | 10,2 | Não | Não | Não permitido | Não | — | > 0 e diferente do anterior; CHECK: ck_hp_precos |
| motivo | Razão da alteração | VARCHAR | 25 | Não | Não | Não permitido | Não | — | REAJUSTE_FORNECEDOR, PROXIMO_VENCIMENTO, PROMOCAO, CORRECAO; CHECK: ck_hp_motivo |

## fornecedor

*Empresa, distribuidor ou produtor rural que vende ao mercado.* — origem: Entidade FORNECEDOR.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_fornecedor | Identificador do fornecedor | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta (D-13); AUTO_INCREMENT |
| tipo_documento | Tipo do documento | VARCHAR | 4 | Não | Não | Não permitido | Não | — | CNPJ ou CPF (produtor rural); CHECK: ck_fornecedor_doc |
| documento | CNPJ (numérico ou alfanumérico) ou CPF | VARCHAR | 14 | Não | Não | Não permitido | Sim | — | Único; CHECK: ck_fornecedor_doc; UNIQUE: uq_fornecedor_documento |
| razao_social | Nome jurídico ou nome do produtor | VARCHAR | 120 | Não | Não | Não permitido | Não | — | — |
| nome_fantasia | Nome comercial | VARCHAR | 80 | Não | Não | Permitido | Não | — | — |
| canal_pedido | Meio usual de pedido | VARCHAR | 16 | Não | Não | Não permitido | Não | — | WHATSAPP, APLICATIVO, VENDEDOR_VISITA; CHECK: ck_fornecedor_canal |
| condicao_pagamento_padrao | Condição usual | VARCHAR | 40 | Não | Não | Permitido | Não | — | Ex.: 'À vista', '7/14/21 dias' (PO-10) |
| ativo | Em uso | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | — |

## contato_fornecedor

*Cada vendedor/representante de um fornecedor.* — origem: Atributo multivalorado e composto FORNECEDOR.contatos → tabela (1FN).

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_fornecedor | Fornecedor | INT UNSIGNED | — | Sim | Sim → fornecedor(id_fornecedor) | Não permitido | Não | — | FK → fornecedor |
| numero_contato | Sequência do contato no fornecedor | TINYINT UNSIGNED | — | Sim | Não | Não permitido | Não | — | Discriminador: 1, 2, 3… |
| nome | Nome do vendedor/representante | VARCHAR | 80 | Não | Não | Não permitido | Não | — | — |
| telefone | Telefone | VARCHAR | 15 | Não | Não | Não permitido | Não | — | Só dígitos; CHECK: ck_contato_tel |
| usa_whatsapp | Atende por WhatsApp | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | — |

## produto_fornecedor

*Quais produtos cada fornecedor fornece e com que código no catálogo dele.* — origem: Relacionamento N:N FORNECE (R09) → tabela associativa.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_fornecedor | Fornecedor | INT UNSIGNED | — | Sim | Sim → fornecedor(id_fornecedor) | Não permitido | Não | — | FK → fornecedor |
| id_produto | Produto | INT UNSIGNED | — | Sim | Sim → produto(id_produto) | Não permitido | Não | — | FK → produto |
| codigo_no_fornecedor | Código do item no catálogo do fornecedor | VARCHAR | 30 | Não | Não | Permitido | Não | — | Depende do par (3FN: não fica em item_pedido) |
| ativo | Par ainda em uso | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | — |

## pedido_compra

*Solicitação de mercadorias a um fornecedor.* — origem: Entidade PEDIDO_COMPRA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_pedido | Identificador do pedido | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta: pedido por WhatsApp não tem número; AUTO_INCREMENT |
| id_fornecedor | Fornecedor | INT UNSIGNED | — | Não | Sim → fornecedor(id_fornecedor) | Não permitido | Não | — | FK → fornecedor (RN-10) |
| id_funcionario | Quem fez o pedido | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario (PO-01) |
| data_hora_pedido | Momento do pedido | DATETIME | — | Não | Não | Não permitido | Não | — | — |
| canal | Meio usado | VARCHAR | 16 | Não | Não | Não permitido | Não | — | WHATSAPP, APLICATIVO, VENDEDOR_VISITA; CHECK: ck_pedido_canal |
| cancelado | Pedido cancelado | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | — |
| observacao | Anotações | VARCHAR | 200 | Não | Não | Permitido | Não | — | — |

## item_pedido

*Cada produto solicitado em um pedido.* — origem: Entidade associativa ITEM_PEDIDO (PEDIDO_COMPRA × PRODUTO).

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_pedido | Pedido | INT UNSIGNED | — | Sim | Sim → pedido_compra(id_pedido) | Não permitido | Não | — | FK → pedido_compra |
| id_produto | Produto solicitado | INT UNSIGNED | — | Sim | Sim → produto(id_produto) | Não permitido | Não | — | FK → produto |
| quantidade_pedida | Quantidade pedida, na unidade base | DECIMAL | 12,3 | Não | Não | Não permitido | Não | — | > 0; CHECK: ck_ip_qtd |
| preco_negociado | Preço unitário combinado | DECIMAL | 12,4 | Não | Não | Permitido | Não | — | >= 0; CHECK: ck_ip_preco |

## recebimento

*Chegada de mercadoria com nota fiscal e resultado da conferência.* — origem: Entidade RECEBIMENTO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_recebimento | Identificador do recebimento | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta (D-13); AUTO_INCREMENT |
| id_fornecedor | Emitente da nota | INT UNSIGNED | — | Não | Sim → fornecedor(id_fornecedor) | Não permitido | Sim (composta) | — | FK → fornecedor (RN-12); UNIQUE: uq_recebimento_nota |
| id_funcionario | Conferente | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario (PO-05) |
| chave_acesso_nfe | Chave de acesso da NF-e | CHAR | 44 | Não | Não | Permitido | Sim | — | Única quando existir; CHECK: ck_receb_nfe_fmt; UNIQUE: uq_recebimento_nfe |
| modelo_nota | Modelo do documento fiscal | CHAR | 2 | Não | Não | Não permitido | Sim (composta) | — | Ex.: 55 (NF-e); CHECK: ck_receb_modelo; UNIQUE: uq_recebimento_nota |
| serie_nota | Série da nota | SMALLINT UNSIGNED | — | Não | Não | Não permitido | Sim (composta) | — | 0 a 999; CHECK: ck_receb_serie; UNIQUE: uq_recebimento_nota |
| numero_nota | Número da nota | INT UNSIGNED | — | Não | Não | Não permitido | Sim (composta) | — | 1 a 999.999.999; CHECK: ck_receb_numero; UNIQUE: uq_recebimento_nota |
| data_hora | Momento da chegada | DATETIME | — | Não | Não | Não permitido | Não | — | — |
| valor_total_nota | Valor total da nota | DECIMAL | 12,2 | Não | Não | Não permitido | Não | — | >= 0; CHECK: ck_receb_valor |
| volumes_nota | Volumes declarados na nota | SMALLINT UNSIGNED | — | Não | Não | Não permitido | Não | — | — |
| volumes_conferidos | Volumes efetivamente contados | SMALLINT UNSIGNED | — | Não | Não | Não permitido | Não | — | — |
| situacao | Resultado da conferência | VARCHAR | 25 | Não | Não | Não permitido | Não | — | ACEITO, ACEITO_COM_DIVERGENCIA, RECUSADO; CHECK: ck_receb_situacao, ck_receb_obs |
| observacao_divergencia | Descrição das divergências | VARCHAR | 300 | Não | Não | Permitido | Não | — | Obrigatória se a situação não for ACEITO; CHECK: ck_receb_obs |

## item_recebimento

*Cada linha da nota fiscal recebida, com a conferência item a item.* — origem: Entidade fraca ITEM_RECEBIMENTO (linha da nota).

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_recebimento | Recebimento (nota) | INT UNSIGNED | — | Sim | Sim → recebimento(id_recebimento) | Não permitido | Sim (composta) | — | FK → recebimento; UNIQUE: uq_ir_lote_ref |
| numero_item_nota | Número da linha na nota | SMALLINT UNSIGNED | — | Sim | Não | Não permitido | Sim (composta) | — | Discriminador natural impresso na nota; UNIQUE: uq_ir_lote_ref |
| id_produto | Produto recebido | INT UNSIGNED | — | Não | Sim → produto(id_produto); item_pedido(id_produto) | Não permitido | Sim (composta) | — | FK → produto; UNIQUE: uq_ir_lote_ref |
| id_pedido | Pedido atendido por esta linha | INT UNSIGNED | — | Não | Sim → item_pedido(id_pedido) | Permitido | Não | — | Com id_produto, FK → item_pedido; vazio se não houve pedido |
| quantidade_nota | Quantidade faturada, na unidade da nota | DECIMAL | 12,3 | Não | Não | Não permitido | Não | — | > 0; CHECK: ck_ir_qtd, ck_ir_aceita |
| fator_conversao_compra | Unidades base por unidade da nota | DECIMAL | 10,3 | Não | Não | Não permitido | Não | 1 | > 0 (caixa com 12 = 12); CHECK: ck_ir_fator, ck_ir_aceita |
| valor_unitario_nota | Valor unitário na nota | DECIMAL | 12,4 | Não | Não | Não permitido | Não | — | >= 0 (bonificação = 0); CHECK: ck_ir_valor |
| quantidade_aceita | Quantidade aceita, na unidade base | DECIMAL | 12,3 | Não | Não | Não permitido | Não | — | 0 = linha recusada; não excede o faturado; CHECK: ck_ir_aceita, ck_ir_situacao |
| situacao_item | Resultado da conferência da linha | VARCHAR | 25 | Não | Não | Não permitido | Não | — | ACEITO, ACEITO_PARCIAL, RECUSADO, NAO_PEDIDO_DEVOLVIDO; CHECK: ck_ir_situacao |

## lote

*Porção de um produto com mesma origem, custo e validade. Base de validade, FEFO e custo.* — origem: Entidade LOTE.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_lote | Identificador do lote | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta: permite 2 lotes na mesma linha de nota e lotes sem nota (D-02); AUTO_INCREMENT |
| id_produto | Produto do lote | INT UNSIGNED | — | Não | Sim → produto(id_produto); item_recebimento(id_produto) | Não permitido | Não | — | FK → produto |
| id_recebimento | Recebimento de origem | INT UNSIGNED | — | Não | Sim → item_recebimento(id_recebimento) | Permitido | Não | — | Com numero_item_nota e id_produto, FK → item_recebimento; CHECK: ck_lote_origem_nota |
| numero_item_nota | Linha da nota de origem | SMALLINT UNSIGNED | — | Não | Sim → item_recebimento(numero_item_nota) | Permitido | Não | — | CHECK: ck_lote_origem_nota |
| id_lote_reposto | Lote trocado que este lote repõe | INT UNSIGNED | — | Não | Sim → lote(id_lote) | Permitido | Não | — | FK → lote (autorrelacionamento R08); CHECK: ck_lote_origem_reposicao |
| origem | Como o lote surgiu | VARCHAR | 25 | Não | Não | Não permitido | Não | — | RECEBIMENTO, INVENTARIO_INICIAL, AJUSTE_INVENTARIO, REPOSICAO_FORNECEDOR; CHECK: ck_lote_origem, ck_lote_origem_nota, ck_lote_origem_reposicao, ck_lote_pendente |
| codigo_lote_fabricante | Lote impresso pelo fabricante | VARCHAR | 30 | Não | Não | Permitido | Não | — | — |
| data_validade | Validade | DATE | — | Não | Não | Permitido | Não | — | Obrigatória se produto.controla_validade (verificada na auditoria A05) |
| data_entrada | Entrada no estoque | DATETIME | — | Não | Não | Não permitido | Não | — | — |
| custo_unitario | Custo por unidade base | DECIMAL | 12,4 | Não | Não | Não permitido | Não | — | >= 0; imutável após a entrada (RN-22); CHECK: ck_lote_custo |
| situacao | Estado do lote | VARCHAR | 15 | Não | Não | Não permitido | Não | DISPONIVEL | DISPONIVEL, SEPARADO_TROCA, TROCADO, DESCARTADO; CHECK: ck_lote_situacao |
| pendente_conferencia | Lote de ajuste automático aguardando conferência física | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | Só em lotes AJUSTE_INVENTARIO (RN-40); CHECK: ck_lote_pendente |

## caixa

*Ponto de venda físico.* — origem: Entidade CAIXA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| numero_caixa | Número pintado no PDV | TINYINT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave natural estável (D-13); CHECK: ck_caixa_numero |
| ativo | Em uso | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | — |

## sessao_caixa

*Período entre abertura e fechamento de um caixa; onde ocorre o fechamento de caixa.* — origem: Entidade SESSAO_CAIXA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_sessao | Identificador da sessão | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | AUTO_INCREMENT |
| numero_caixa | Caixa aberto | TINYINT UNSIGNED | — | Não | Sim → caixa(numero_caixa) | Não permitido | Não | — | FK → caixa |
| id_funcionario_abertura | Quem abriu | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario |
| id_funcionario_fechamento | Quem fechou | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Permitido | Não | — | FK → funcionario; vazio enquanto aberta; CHECK: ck_sessao_fechamento |
| data_hora_abertura | Abertura | DATETIME | — | Não | Não | Não permitido | Não | — | CHECK: ck_sessao_datas |
| valor_inicial | Fundo de troco | DECIMAL | 10,2 | Não | Não | Não permitido | Não | — | >= 0 (não é fixo); CHECK: ck_sessao_valores |
| data_hora_fechamento | Fechamento | DATETIME | — | Não | Não | Permitido | Não | — | Vazio = sessão aberta (a situação é derivada daqui); CHECK: ck_sessao_fechamento, ck_sessao_datas |
| valor_contado | Dinheiro contado no fechamento | DECIMAL | 10,2 | Não | Não | Permitido | Não | — | >= 0; CHECK: ck_sessao_valores, ck_sessao_fechamento |
| total_maquininhas_informado | Total do relatório das maquininhas | DECIMAL | 12,2 | Não | Não | Permitido | Não | — | >= 0; CHECK: ck_sessao_valores |
| justificativa_diferenca | Explicação de sobra/falta | VARCHAR | 200 | Não | Não | Permitido | Não | — | Exigida quando há diferença (auditoria A06) |

## cliente

*Consumidor identificado; exigido apenas para venda fiada.* — origem: Entidade CLIENTE.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_cliente | Identificador do cliente | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta (D-13); AUTO_INCREMENT |
| cpf | CPF | CHAR | 11 | Não | Não | Permitido | Sim | — | Único quando informado; obrigatório para autorizar fiado; CHECK: ck_cliente_cpf, ck_cliente_fiado_cpf; UNIQUE: uq_cliente_cpf |
| nome | Nome | VARCHAR | 100 | Não | Não | Não permitido | Não | — | — |
| apelido | Como é conhecido no bairro | VARCHAR | 40 | Não | Não | Permitido | Não | — | — |
| telefone | Telefone | VARCHAR | 15 | Não | Não | Permitido | Não | — | Só dígitos; CHECK: ck_cliente_tel |
| logradouro | Rua/avenida | VARCHAR | 100 | Não | Não | Permitido | Não | — | Atributo composto endereço decomposto (1FN) |
| numero_endereco | Número do imóvel | VARCHAR | 10 | Não | Não | Permitido | Não | — | — |
| complemento | Complemento | VARCHAR | 40 | Não | Não | Permitido | Não | — | — |
| bairro | Bairro | VARCHAR | 50 | Não | Não | Permitido | Não | — | — |
| autorizado_fiado | Pode comprar fiado | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | Só o gerente altera (PO-04); CHECK: ck_cliente_fiado_cpf |
| limite_fiado | Limite de dívida em aberto | DECIMAL | 10,2 | Não | Não | Permitido | Não | — | >= 0; CHECK: ck_cliente_limite |
| data_cadastro | Data do cadastro | DATE | — | Não | Não | Não permitido | Não | CURRENT_DATE | — |

## venda

*Transação de venda registrada no caixa.* — origem: Entidade VENDA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_venda | Identificador da venda | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta: não depende do relógio, permite caixa offline (RNF-07); AUTO_INCREMENT |
| id_sessao | Sessão de caixa | INT UNSIGNED | — | Não | Sim → sessao_caixa(id_sessao) | Não permitido | Sim (composta) | — | FK → sessao_caixa (RN-20); UNIQUE: uq_venda_cupom |
| id_funcionario | Operador | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario |
| id_cliente | Cliente identificado | INT UNSIGNED | — | Não | Sim → cliente(id_cliente) | Permitido | Não | — | FK → cliente; obrigatório se houver FIADO (auditoria A04) |
| numero_cupom | Número do cupom | INT UNSIGNED | — | Não | Não | Não permitido | Sim (composta) | — | Único dentro da sessão; CHECK: ck_venda_cupom; UNIQUE: uq_venda_cupom |
| data_hora | Momento da venda | DATETIME | — | Não | Não | Não permitido | Não | — | — |
| situacao | Estado | VARCHAR | 10 | Não | Não | Não permitido | Não | CONCLUIDA | CONCLUIDA, CANCELADA; CHECK: ck_venda_situacao |

## item_venda

*Cada linha do cupom: embalagem, quantidade, preço praticado e desconto.* — origem: Entidade associativa ITEM_VENDA (VENDA × EMBALAGEM).

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_venda | Venda | INT UNSIGNED | — | Sim | Sim → venda(id_venda) | Não permitido | Não | — | FK → venda |
| numero_item | Posição no cupom | SMALLINT UNSIGNED | — | Sim | Não | Não permitido | Não | — | Discriminador natural impresso no cupom |
| id_embalagem | Embalagem lida | INT UNSIGNED | — | Não | Sim → embalagem(id_embalagem) | Não permitido | Não | — | FK → embalagem |
| id_funcionario_autorizador | Quem autorizou o desconto | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Permitido | Não | — | FK → funcionario; obrigatório se houver desconto; CHECK: ck_iv_autorizacao |
| quantidade | Quantidade na unidade da embalagem | DECIMAL | 12,3 | Não | Não | Não permitido | Não | — | > 0; fracionada para peso; CHECK: ck_iv_qtd |
| preco_unitario_praticado | Preço no momento da venda | DECIMAL | 10,2 | Não | Não | Não permitido | Não | — | > 0; não muda depois (RN-22); CHECK: ck_iv_preco, ck_iv_desconto |
| desconto_unitario | Desconto por unidade | DECIMAL | 10,2 | Não | Não | Não permitido | Não | 0 | >= 0 e menor que o preço; CHECK: ck_iv_desconto, ck_iv_autorizacao |

## conta_financeira

*Onde o dinheiro fica fora da gaveta: banco, conta da maquininha ou cofre.* — origem: Entidade CONTA_FINANCEIRA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_conta_financeira | Identificador | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | AUTO_INCREMENT |
| nome | Nome da conta | VARCHAR | 60 | Não | Não | Não permitido | Sim | — | Único; UNIQUE: uq_cf_nome |
| tipo | Tipo | VARCHAR | 16 | Não | Não | Não permitido | Não | — | CONTA_BANCARIA, CONTA_ADQUIRENTE, COFRE; CHECK: ck_cf_tipo |
| saldo_inicial | Saldo na implantação | DECIMAL | 12,2 | Não | Não | Não permitido | Não | — | — |
| data_saldo_inicial | Data do saldo inicial | DATE | — | Não | Não | Não permitido | Não | — | — |
| ativa | Em uso | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | — |

## movimento_financeiro

*Entrada ou saída efetiva de dinheiro numa conta financeira (linha do extrato ou do cofre).* — origem: Entidade MOVIMENTO_FINANCEIRO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_movimento_fin | Identificador | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | AUTO_INCREMENT |
| id_conta_financeira | Conta | INT UNSIGNED | — | Não | Sim → conta_financeira(id_conta_financeira) | Não permitido | Sim (composta) | — | FK → conta_financeira; UNIQUE: uq_mf_documento |
| id_funcionario | Quem lançou | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Permitido | Não | — | FK → funcionario; obrigatório em lançamento manual; CHECK: ck_mf_manual |
| data_movimento | Data em que o valor entrou/saiu | DATE | — | Não | Não | Não permitido | Não | — | — |
| natureza | Sentido | VARCHAR | 7 | Não | Não | Não permitido | Não | — | CREDITO, DEBITO; CHECK: ck_mf_natureza, ck_mf_origem |
| origem | O que gerou | VARCHAR | 20 | Não | Não | Não permitido | Não | — | REPASSE_CARTAO, PIX_RECEBIDO, RECOLHIMENTO_GAVETA, SUPRIMENTO_GAVETA, DEPOSITO, PAGAMENTO_CONTA, ESTORNO_DEVOLUCAO, TARIFA, AJUSTE; CHECK: ck_mf_origem, ck_mf_manual |
| valor_bruto | Valor antes da taxa | DECIMAL | 12,2 | Não | Não | Não permitido | Não | — | > 0; CHECK: ck_mf_valores |
| valor_taxa | Taxa descontada | DECIMAL | 12,2 | Não | Não | Não permitido | Não | 0 | >= 0 e <= bruto; CHECK: ck_mf_valores |
| documento_referencia | Identificação no extrato | VARCHAR | 60 | Não | Não | Permitido | Sim (composta) | — | Única por conta; UNIQUE: uq_mf_documento |

## forma_pagamento

*Meio de pagamento com prazo e taxa de crédito.* — origem: Entidade FORMA_PAGAMENTO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| codigo_forma | Código | VARCHAR | 5 | Sim | Não | Não permitido | Sim (PK) | — | Chave natural fixa: DIN, DEB, CRE, PIX, VALE, FIADO (D-13) |
| descricao | Nome exibido | VARCHAR | 40 | Não | Não | Não permitido | Não | — | — |
| prazo_credito_dias | Dias até o crédito | SMALLINT UNSIGNED | — | Não | Não | Não permitido | Não | 0 | DIN/PIX = 0 |
| taxa_percentual | Taxa contratada (%) | DECIMAL | 5,2 | Não | Não | Não permitido | Não | 0 | 0 a 100; CHECK: ck_fp_taxa |
| gera_divida | Cria dívida do cliente | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | Só FIADO; CHECK: ck_fp_divida |
| exige_conciliacao | Valor cai em conta e deve ser conciliado | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | DEB, CRE, PIX, VALE; CHECK: ck_fp_divida |
| ativa | Disponível no caixa | BOOLEAN | — | Não | Não | Não permitido | Não | TRUE | — |

## pagamento_venda

*Cada transação de pagamento de uma venda.* — origem: Entidade fraca PAGAMENTO_VENDA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_venda | Venda paga | INT UNSIGNED | — | Sim | Sim → venda(id_venda) | Não permitido | Não | — | FK → venda |
| numero_pagamento | Sequência na venda | TINYINT UNSIGNED | — | Sim | Não | Não permitido | Não | — | Permite 2 pagamentos na mesma forma (T06) |
| codigo_forma | Forma | VARCHAR | 5 | Não | Sim → forma_pagamento(codigo_forma) | Não permitido | Não | — | FK → forma_pagamento; CHECK: ck_pv_entregue, ck_pv_nsu, ck_pv_liquidacao |
| id_movimento_fin | Crédito que liquidou a transação | INT UNSIGNED | — | Não | Sim → movimento_financeiro(id_movimento_fin) | Permitido | Não | — | FK → movimento_financeiro; vazio = não conciliado (RN-36); CHECK: ck_pv_liquidacao |
| valor | Valor aplicado à venda | DECIMAL | 10,2 | Não | Não | Não permitido | Não | — | > 0, já líquido de troco; CHECK: ck_pv_valor, ck_pv_entregue |
| valor_entregue | Dinheiro entregue pelo cliente | DECIMAL | 10,2 | Não | Não | Permitido | Não | — | Só em DIN; >= valor; CHECK: ck_pv_entregue |
| nsu_autorizacao | NSU / ID da transação | VARCHAR | 36 | Não | Não | Permitido | Sim | — | Obrigatório em DEB, CRE, PIX, VALE; único; CHECK: ck_pv_nsu; UNIQUE: uq_pv_nsu |

## movimentacao_caixa

*Dinheiro que entra ou sai da gaveta sem ser venda.* — origem: Entidade MOVIMENTACAO_CAIXA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_mov_caixa | Identificador | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | AUTO_INCREMENT |
| id_sessao | Sessão | INT UNSIGNED | — | Não | Sim → sessao_caixa(id_sessao) | Não permitido | Não | — | FK → sessao_caixa |
| id_funcionario | Quem executou | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario (RN-29) |
| id_movimento_fin | Lançamento no cofre gerado | INT UNSIGNED | — | Não | Sim → movimento_financeiro(id_movimento_fin) | Permitido | Sim | — | FK → movimento_financeiro; único; CHECK: ck_mc_cofre; UNIQUE: uq_mc_movimento |
| data_hora | Momento | DATETIME | — | Não | Não | Não permitido | Não | — | — |
| tipo | Tipo | VARCHAR | 25 | Não | Não | Não permitido | Não | — | SANGRIA, SUPRIMENTO, RECOLHIMENTO_FECHAMENTO, REEMBOLSO_DEVOLUCAO; CHECK: ck_mc_tipo, ck_mc_cofre |
| valor | Valor | DECIMAL | 10,2 | Não | Não | Não permitido | Não | — | > 0; CHECK: ck_mc_valor |
| motivo | Justificativa | VARCHAR | 200 | Não | Não | Não permitido | Não | — | Obrigatório (RN-29) |

## devolucao

*Devolução ou troca de item vendido.* — origem: Entidade DEVOLUCAO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_devolucao | Identificador | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | AUTO_INCREMENT |
| id_venda | Venda de origem | INT UNSIGNED | — | Não | Sim → item_venda(id_venda) | Não permitido | Não | — | Com numero_item, FK → item_venda |
| numero_item | Item devolvido | SMALLINT UNSIGNED | — | Não | Sim → item_venda(numero_item) | Não permitido | Não | — | — |
| id_funcionario | Autorizador | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario (PO-13) |
| id_mov_caixa | Saída de dinheiro do reembolso | INT UNSIGNED | — | Não | Sim → movimentacao_caixa(id_mov_caixa) | Permitido | Sim | — | FK → movimentacao_caixa; obrigatória se DINHEIRO; CHECK: ck_dev_dinheiro; UNIQUE: uq_dev_mov_caixa |
| id_movimento_fin | Estorno em conta | INT UNSIGNED | — | Não | Sim → movimento_financeiro(id_movimento_fin) | Permitido | Sim | — | FK → movimento_financeiro; obrigatório se ESTORNO_ELETRONICO; CHECK: ck_dev_estorno; UNIQUE: uq_dev_mov_fin |
| data_hora | Momento | DATETIME | — | Não | Não | Não permitido | Não | — | — |
| quantidade_devolvida | Quantidade, na unidade da embalagem | DECIMAL | 12,3 | Não | Não | Não permitido | Não | — | > 0; não excede o vendido (auditoria A12); CHECK: ck_dev_qtd |
| motivo | Motivo | VARCHAR | 10 | Não | Não | Não permitido | Não | — | DEFEITO, VENCIDO (RN-28); CHECK: ck_dev_motivo |
| destino | Destino do produto | VARCHAR | 15 | Não | Não | Não permitido | Não | — | REVENDA, SEPARADO_TROCA, DESCARTE; CHECK: ck_dev_destino |
| forma_reembolso | Reembolso | VARCHAR | 20 | Não | Não | Não permitido | Não | — | TROCA_MESMO_PRODUTO, DINHEIRO, ESTORNO_ELETRONICO, ABATER_FIADO; CHECK: ck_dev_forma, ck_dev_valor, ck_dev_dinheiro, ck_dev_estorno |
| valor_reembolsado | Valor devolvido | DECIMAL | 10,2 | Não | Não | Não permitido | Não | 0 | 0 na troca; > 0 nos demais; CHECK: ck_dev_valor |

## movimentacao_estoque

*Toda entrada ou saída de um lote (kardex). Nenhum saldo muda sem ela.* — origem: Entidade MOVIMENTACAO_ESTOQUE.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_movimentacao | Identificador | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta: duas baixas no mesmo instante não colidem (T05); AUTO_INCREMENT |
| id_lote | Lote movimentado | INT UNSIGNED | — | Não | Sim → lote(id_lote) | Não permitido | Não | — | FK → lote (RN-16) |
| id_funcionario | Responsável | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Permitido | Não | — | FK → funcionario; obrigatório em perdas, ajustes, inventário e troca (RN-18); CHECK: ck_me_responsavel |
| id_venda | Venda que gerou a baixa | INT UNSIGNED | — | Não | Sim → item_venda(id_venda) | Permitido | Não | — | Com numero_item, FK → item_venda; só em SAIDA_VENDA; CHECK: ck_me_venda, ck_me_venda_par |
| numero_item | Item do cupom | SMALLINT UNSIGNED | — | Não | Sim → item_venda(numero_item) | Permitido | Não | — | CHECK: ck_me_venda, ck_me_venda_par |
| id_devolucao | Devolução que gerou | INT UNSIGNED | — | Não | Sim → devolucao(id_devolucao) | Permitido | Não | — | FK → devolucao; só em DEVOLUCAO_CLIENTE e SAIDA_TROCA_CLIENTE; CHECK: ck_me_devolucao |
| data_hora | Momento | DATETIME | — | Não | Não | Não permitido | Não | — | — |
| tipo | Natureza | VARCHAR | 30 | Não | Não | Não permitido | Não | — | Entradas: ENTRADA_RECEBIMENTO, ENTRADA_INVENTARIO, TROCA_FORNECEDOR, DEVOLUCAO_CLIENTE, AJUSTE_INVENTARIO_ENTRADA. Saídas: SAIDA_VENDA, SAIDA_TROCA_CLIENTE, PERDA_VENCIMENTO, PERDA_AVARIA, AJUSTE_INVENTARIO_SAIDA; CHECK: ck_me_tipo, ck_me_venda, ck_me_devolucao, ck_me_responsavel, ck_me_motivo |
| quantidade | Quantidade na unidade base | DECIMAL | 12,3 | Não | Não | Não permitido | Não | — | > 0; o tipo define o sinal; CHECK: ck_me_qtd |
| motivo | Justificativa | VARCHAR | 200 | Não | Não | Permitido | Não | — | Obrigatória em perdas e ajustes; CHECK: ck_me_motivo |

## abatimento_fiado

*Pagamento total ou parcial da dívida de fiado.* — origem: Entidade ABATIMENTO_FIADO.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_abatimento | Identificador | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | AUTO_INCREMENT |
| id_cliente | Cliente | INT UNSIGNED | — | Não | Sim → cliente(id_cliente) | Não permitido | Não | — | FK → cliente |
| codigo_forma | Forma usada | VARCHAR | 5 | Não | Sim → forma_pagamento(codigo_forma) | Não permitido | Não | — | FK → forma_pagamento; nunca FIADO (RN-27); CHECK: ck_ab_forma, ck_ab_sessao, ck_ab_liquidacao |
| id_funcionario | Quem recebeu | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario |
| id_sessao | Sessão em que o dinheiro entrou | INT UNSIGNED | — | Não | Sim → sessao_caixa(id_sessao) | Permitido | Não | — | FK → sessao_caixa; obrigatória em DIN; CHECK: ck_ab_sessao |
| id_movimento_fin | Crédito que liquidou | INT UNSIGNED | — | Não | Sim → movimento_financeiro(id_movimento_fin) | Permitido | Não | — | FK → movimento_financeiro; só em formas eletrônicas; CHECK: ck_ab_liquidacao |
| data_hora | Momento | DATETIME | — | Não | Não | Não permitido | Não | — | — |
| valor | Valor pago | DECIMAL | 10,2 | Não | Não | Não permitido | Não | — | > 0; CHECK: ck_ab_valor |
| observacao | Anotação | VARCHAR | 200 | Não | Não | Permitido | Não | — | — |

## conta_pagar

*Obrigação do mercado: parcela de boleto, imposto, folha, internet etc.* — origem: Entidade CONTA_PAGAR.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_conta | Identificador | INT UNSIGNED | — | Sim | Não | Não permitido | Sim (PK) | — | Chave substituta (D-13); AUTO_INCREMENT |
| id_recebimento | Recebimento de origem | INT UNSIGNED | — | Não | Sim → recebimento(id_recebimento) | Permitido | Sim (composta) | — | FK → recebimento; vazio em despesas fixas; CHECK: ck_cp_origem; UNIQUE: uq_cp_parcela |
| credor | Quem recebe | VARCHAR | 120 | Não | Não | Não permitido | Não | — | — |
| numero_documento | Nº do boleto/guia/competência | VARCHAR | 40 | Não | Não | Permitido | Não | — | — |
| numero_parcela | Parcela | TINYINT UNSIGNED | — | Não | Não | Não permitido | Sim (composta) | 1 | >= 1; CHECK: ck_cp_parcela; UNIQUE: uq_cp_parcela |
| descricao | Descrição | VARCHAR | 150 | Não | Não | Não permitido | Não | — | — |
| categoria_despesa | Categoria | VARCHAR | 18 | Não | Não | Não permitido | Não | — | FORNECEDOR, SIMPLES_NACIONAL, FOLHA, INTERNET, AGUA, LUZ, ALUGUEL, OUTROS; CHECK: ck_cp_categoria, ck_cp_origem |
| valor_original | Valor da obrigação | DECIMAL | 12,2 | Não | Não | Não permitido | Não | — | > 0; CHECK: ck_cp_valor |
| data_vencimento | Vencimento | DATE | — | Não | Não | Não permitido | Não | — | — |
| prioridade | Prioridade | VARCHAR | 5 | Não | Não | Não permitido | Não | MEDIA | ALTA, MEDIA, BAIXA (PO-06); CHECK: ck_cp_prioridade |
| cancelada | Cancelada | BOOLEAN | — | Não | Não | Não permitido | Não | FALSE | — |

## pagamento_conta

*Cada pagamento (total ou parcial) de uma conta.* — origem: Entidade fraca PAGAMENTO_CONTA.

| Atributo | Descrição | Tipo | Tamanho | PK | FK | NULL | UNIQUE | DEFAULT | Regra / restrição |
|---|---|---|---|---|---|---|---|---|---|
| id_conta | Conta paga | INT UNSIGNED | — | Sim | Sim → conta_pagar(id_conta) | Não permitido | Não | — | FK → conta_pagar |
| numero_pagamento | Sequência na conta | TINYINT UNSIGNED | — | Sim | Não | Não permitido | Não | — | 1, 2, 3… |
| id_funcionario | Quem registrou | INT UNSIGNED | — | Não | Sim → funcionario(id_funcionario) | Não permitido | Não | — | FK → funcionario (RN-35) |
| id_movimento_fin | Saída de dinheiro | INT UNSIGNED | — | Não | Sim → movimento_financeiro(id_movimento_fin) | Não permitido | Sim | — | FK → movimento_financeiro; única (1:1); UNIQUE: uq_pc_movimento |
| data_pagamento | Data | DATE | — | Não | Não | Não permitido | Não | — | — |
| valor_principal | Parte do valor original quitada | DECIMAL | 12,2 | Não | Não | Não permitido | Não | — | > 0; soma <= valor original (auditoria A09); CHECK: ck_pc_valores, ck_pc_desconto |
| valor_juros_multa | Encargos | DECIMAL | 12,2 | Não | Não | Não permitido | Não | 0 | >= 0; CHECK: ck_pc_valores, ck_pc_desconto |
| valor_desconto | Desconto obtido | DECIMAL | 12,2 | Não | Não | Não permitido | Não | 0 | >= 0; CHECK: ck_pc_valores, ck_pc_desconto |
| observacao | Anotação | VARCHAR | 200 | Não | Não | Permitido | Não | — | — |

## Views — atributos derivados (não gravados)

Os atributos marcados como derivados no DER não são colunas de tabela: são calculados pelas views abaixo
(`sql/ddl/03_views.sql`). Assim nenhum valor calculável fica gravado em duplicidade (3FN).

| View | O que calcula (atributos derivados do DER) | Colunas |
|---|---|---|
| vw_movimentacao_valorizada | Movimentação com sinal e valor de custo (kardex valorizado) Derivado: MOVIMENTACAO_ESTOQUE.valor_custo = quantidade × custo do lote | id_movimentacao, id_lote, id_produto, tipo, data_hora, quantidade, sinal, quantidade_com_sinal, valor_custo, id_venda, numero_item, id_devolucao, id_funcionario, motivo |
| vw_lote_saldo | Saldo por lote. Derivados: LOTE.quantidade_inicial, LOTE.quantidade_atual, "esgotado" (antiga situação ESGOTADO, removida da tabela). | id_lote, id_produto, nome_produto, origem, data_validade, data_entrada, custo_unitario, situacao, pendente_conferencia, id_recebimento, numero_item_nota, quantidade_inicial, quantidade_atual, qtd_movimentacoes |
| vw_estoque_produto | Estoque vendável por produto. Derivado: PRODUTO.estoque_atual Só lotes DISPONIVEL contam (separado para troca não é vendável). | id_produto, nome_produto, codigo_categoria, unidade_base, estoque_minimo, ativo, estoque_atual, valor_estoque_custo, abaixo_minimo |
| vw_item_venda_resultado | Resultado por item vendido. Derivados: ITEM_VENDA.valor_item, ITEM_VENDA.custo_total (soma dos lotes realmente baixados — RN-22), ITEM_VENDA.custo_unitario_medio. custo = saídas por venda − retornos de devolução + saídas de troca ao cliente | id_venda, numero_item, id_embalagem, id_produto, data_hora, situacao_venda, quantidade, fator_conversao, quantidade_base, preco_unitario_praticado, desconto_unitario, valor_item, custo_baixado, custo_devolvido, custo_troca, custo_total, quantidade_devolvida, valor_reembolsado, qtd_lotes_baixados |
| vw_venda_resumo | Resumo por venda. Derivados: VENDA.valor_bruto, valor_desconto, valor_total, custo_total, lucro_bruto. | id_venda, id_sessao, numero_caixa, id_funcionario, id_cliente, numero_cupom, data_hora, situacao, valor_bruto, valor_desconto, valor_total, total_pago, custo_total, valor_reembolsado, lucro_bruto, qtd_itens |
| vw_pagamento_venda_previsao | Recebíveis. Derivados: PAGAMENTO_VENDA.troco, data_prevista_credito, valor_liquido_previsto, situacao_credito. | id_venda, numero_pagamento, codigo_forma, data_venda, situacao_venda, valor, valor_entregue, troco, nsu_autorizacao, data_prevista_credito, valor_liquido_previsto, id_movimento_fin, situacao_credito |
| vw_sessao_conferencia | Conferência da sessão de caixa (FECHAMENTO). Derivados: SESSAO_CAIXA.situacao, valor_esperado, diferenca_dinheiro, total_eletronico_registrado, diferenca_eletronica. valor_esperado = dinheiro que deveria estar na gaveta NO MOMENTO DA CONTAGEM: fundo + vendas em dinheiro (líquidas de troco) + abatimentos em dinheiro + suprimentos − sangrias − reembolsos em dinheiro. O recolhimento acontece depois da contagem e por isso não entra. | id_sessao, numero_caixa, id_funcionario_abertura, id_funcionario_fechamento, data_hora_abertura, data_hora_fechamento, situacao, valor_inicial, vendas_dinheiro, abatimentos_dinheiro, suprimentos, sangrias, reembolsos, recolhido_fechamento, valor_esperado, valor_contado, diferenca_dinheiro, total_eletronico_registrado, total_maquininhas_informado, diferenca_eletronica, justificativa_diferenca |
| vw_cliente_saldo | Conta corrente do fiado. Derivado: CLIENTE.saldo_devedor (RN-26) | id_cliente, nome, apelido, autorizado_fiado, limite_fiado, total_fiado, total_abatido, total_devolvido_fiado, saldo_devedor, primeira_compra_fiado, ultima_compra_fiado, ultimo_abatimento |
| vw_conta_pagar_situacao | Situação das contas a pagar. Derivados: CONTA_PAGAR.valor_principal_pago, encargos_pagos, saldo_em_aberto, situacao (RN-38). | id_conta, id_recebimento, credor, numero_documento, numero_parcela, descricao, categoria_despesa, valor_original, data_vencimento, prioridade, cancelada, valor_principal_pago, encargos_pagos, descontos_obtidos, saldo_em_aberto, qtd_pagamentos, ultimo_pagamento, situacao |
| vw_conta_financeira_saldo | Saldo realizado das contas financeiras. Derivado: CONTA_FINANCEIRA.saldo_atual | id_conta_financeira, nome, tipo, saldo_inicial, data_saldo_inicial, total_creditos, total_debitos, saldo_atual |
| vw_conciliacao | CONCILIAÇÃO. Derivados: MOVIMENTO_FINANCEIRO.valor_liquido, valor_previsto_vinculado, diferenca_conciliacao, situacao_conciliacao (RN-36). previsto = Σ valor − taxa contratada sobre o total das transações liquidadas | id_movimento_fin, id_conta_financeira, data_movimento, origem, documento_referencia, valor_bruto, valor_taxa, valor_liquido, qtd_transacoes, bruto_previsto, taxa_prevista, valor_previsto_vinculado, diferenca_conciliacao, situacao_conciliacao |
| vw_item_pedido_pendencia | Pendências de compra por item. Derivados: ITEM_PEDIDO.quantidade_recebida, quantidade_pendente (RN-11). | id_pedido, id_produto, nome_produto, quantidade_pedida, preco_negociado, quantidade_recebida, quantidade_pendente |
| vw_pedido_situacao | Situação do pedido. Derivados: PEDIDO_COMPRA.situacao (ABERTO, PARCIALMENTE_RECEBIDO, RECEBIDO, CANCELADO) e valor_previsto (RN-11). | id_pedido, id_fornecedor, razao_social, data_hora_pedido, canal, cancelado, qtd_itens, itens_pendentes, valor_previsto, situacao |
| vw_ultimo_custo_fornecedor | Último custo por par fornecedor–produto. Derivados: FORNECE.preco_ultima_compra e data_ultima_compra (antes gravados; removidos da tabela na normalização porque são consequência dos recebimentos). | id_fornecedor, id_produto, data_ultima_compra, preco_ultima_compra |
