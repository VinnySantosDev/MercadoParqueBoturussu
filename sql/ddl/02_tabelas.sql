-- =====================================================================
-- 02_tabelas.sql — CREATE TABLE com PK, FK, UNIQUE, CHECK, DEFAULT
-- Gerado a partir de fis.py (fonte única do modelo lógico/físico).
-- Ordem de criação respeita as dependências de chave estrangeira.
-- Nenhuma FK usa CASCADE: registros operacionais não são apagados (RNF-06, PO-12);
-- a exclusão de um registro referenciado é bloqueada (RESTRICT, padrão do MySQL).
-- =====================================================================
SET NAMES utf8mb4;
USE mercado_boturussu;

-- FUNCIONARIO — origem: Entidade FUNCIONARIO
-- Pessoa que trabalha no mercado e usa o sistema; responde “quem fez” em todas as operações.
CREATE TABLE funcionario (
  id_funcionario               INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador do funcionário',
  cpf                          CHAR(11) NOT NULL COMMENT 'CPF, só dígitos',
  login                        VARCHAR(30) NOT NULL COMMENT 'Usuário de acesso ao sistema',
  nome                         VARCHAR(100) NOT NULL COMMENT 'Nome completo',
  telefone                     VARCHAR(15) NULL COMMENT 'Telefone de contato',
  funcao_principal             VARCHAR(20) NOT NULL COMMENT 'Função habitual',
  data_admissao                DATE NULL COMMENT 'Data de admissão',
  ativo                        BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Se pode acessar o sistema',
  CONSTRAINT pk_funcionario PRIMARY KEY (id_funcionario),
  CONSTRAINT uq_funcionario_cpf UNIQUE (cpf),
  CONSTRAINT uq_funcionario_login UNIQUE (login),
  CONSTRAINT ck_funcionario_cpf CHECK (cpf REGEXP '^[0-9]{11}$'),
  CONSTRAINT ck_funcionario_tel CHECK (telefone IS NULL OR telefone REGEXP '^[0-9]{10,11}$'),
  CONSTRAINT ck_funcionario_funcao CHECK (funcao_principal IN ('CAIXA','BALANCA','REPOSICAO','GERENCIA'))
) ENGINE=InnoDB COMMENT='Pessoa que trabalha no mercado e usa o sistema; responde “quem fez” em todas as operações.';

-- PERMISSAO — origem: Entidade PERMISSAO
-- Operação sensível liberada individualmente (PO-01, PO-02, PO-11, PO-13, PO-14).
CREATE TABLE permissao (
  codigo_permissao             VARCHAR(30) NOT NULL COMMENT 'Código da permissão',
  descricao                    VARCHAR(150) NOT NULL COMMENT 'O que a permissão libera',
  CONSTRAINT pk_permissao PRIMARY KEY (codigo_permissao)
) ENGINE=InnoDB COMMENT='Operação sensível liberada individualmente (PO-01, PO-02, PO-11, PO-13, PO-14).';

-- FUNCIONARIO_PERMISSAO — origem: Relacionamento N:N POSSUI (R52) → tabela associativa
-- Quais permissões cada funcionário tem e desde quando.
CREATE TABLE funcionario_permissao (
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Funcionário',
  codigo_permissao             VARCHAR(30) NOT NULL COMMENT 'Permissão concedida',
  data_concessao               DATE NOT NULL DEFAULT (CURRENT_DATE) COMMENT 'Data da concessão',
  data_revogacao               DATE NULL COMMENT 'Data em que a permissão foi retirada',
  CONSTRAINT pk_funcionario_permissao PRIMARY KEY (id_funcionario, codigo_permissao, data_concessao),
  CONSTRAINT fk_fp_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT fk_fp_permissao FOREIGN KEY (codigo_permissao) REFERENCES permissao (codigo_permissao),
  CONSTRAINT ck_fp_periodo CHECK (data_revogacao IS NULL OR data_revogacao >= data_concessao)
) ENGINE=InnoDB COMMENT='Quais permissões cada funcionário tem e desde quando.';

-- CATEGORIA — origem: Entidade CATEGORIA
-- Setor do mercado; define o prazo padrão de alerta de validade.
CREATE TABLE categoria (
  codigo_categoria             VARCHAR(10) NOT NULL COMMENT 'Sigla do setor',
  nome                         VARCHAR(50) NOT NULL COMMENT 'Nome do setor',
  controle_validade_rigoroso   BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Exige vigilância maior de validade',
  dias_alerta_validade_padrao  SMALLINT UNSIGNED NULL COMMENT 'Antecedência padrão do alerta de validade, em dias',
  CONSTRAINT pk_categoria PRIMARY KEY (codigo_categoria),
  CONSTRAINT uq_categoria_nome UNIQUE (nome)
) ENGINE=InnoDB COMMENT='Setor do mercado; define o prazo padrão de alerta de validade.';

-- PRODUTO — origem: Entidade PRODUTO
-- Item comercializado; unidade de controle de estoque.
CREATE TABLE produto (
  id_produto                   INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador do produto',
  codigo_categoria             VARCHAR(10) NOT NULL COMMENT 'Setor do produto',
  nome_produto                 VARCHAR(120) NOT NULL COMMENT 'Nome padronizado (tipo, marca, variação)',
  marca                        VARCHAR(60) NULL COMMENT 'Marca',
  unidade_base                 CHAR(2) NOT NULL COMMENT 'Unidade de contagem do estoque',
  vendido_por_peso             BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Vendido fracionado na balança',
  controla_validade            BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Exige data de validade no lote',
  dias_alerta_validade         SMALLINT UNSIGNED NULL COMMENT 'Antecedência do alerta, em dias',
  estoque_minimo               DECIMAL(12,3) NOT NULL DEFAULT 0 COMMENT 'Estoque mínimo, na unidade base',
  margem_referencia            DECIMAL(5,2) NULL COMMENT 'Margem de referência (%)',
  ativo                        BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Em comercialização',
  CONSTRAINT pk_produto PRIMARY KEY (id_produto),
  CONSTRAINT uq_produto_nome UNIQUE (nome_produto),
  CONSTRAINT fk_produto_categoria FOREIGN KEY (codigo_categoria) REFERENCES categoria (codigo_categoria),
  CONSTRAINT ck_produto_unidade CHECK (unidade_base IN ('UN','KG')),
  CONSTRAINT ck_produto_peso_kg CHECK (vendido_por_peso = FALSE OR unidade_base = 'KG'),
  CONSTRAINT ck_produto_estoque_min CHECK (estoque_minimo >= 0),
  CONSTRAINT ck_produto_margem CHECK (margem_referencia IS NULL OR margem_referencia BETWEEN 0 AND 300)
) ENGINE=InnoDB COMMENT='Item comercializado; unidade de controle de estoque.';

-- EMBALAGEM — origem: Entidade EMBALAGEM
-- Forma de venda de um produto, com código de leitura, fator de conversão e preço vigente.
CREATE TABLE embalagem (
  id_embalagem                 INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador da forma de venda',
  id_produto                   INT UNSIGNED NOT NULL COMMENT 'Produto da embalagem',
  codigo_barras                VARCHAR(14) NULL COMMENT 'GTIN/EAN de fábrica ou código interno (prefixo 2)',
  codigo_balanca               VARCHAR(6) NULL COMMENT 'Código do item na balança (PLU)',
  descricao                    VARCHAR(60) NOT NULL COMMENT 'Descrição da forma de venda',
  fator_conversao              DECIMAL(10,3) NOT NULL COMMENT 'Unidades base por embalagem',
  preco_venda                  DECIMAL(10,2) NOT NULL COMMENT 'Preço de venda vigente',
  ativa                        BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Pode ser vendida',
  CONSTRAINT pk_embalagem PRIMARY KEY (id_embalagem),
  CONSTRAINT uq_embalagem_barras UNIQUE (codigo_barras),
  CONSTRAINT uq_embalagem_balanca UNIQUE (codigo_balanca),
  CONSTRAINT fk_embalagem_produto FOREIGN KEY (id_produto) REFERENCES produto (id_produto),
  CONSTRAINT ck_embalagem_codigo CHECK (codigo_barras IS NOT NULL OR codigo_balanca IS NOT NULL),
  CONSTRAINT ck_embalagem_barras_fmt CHECK (codigo_barras IS NULL OR codigo_barras REGEXP '^[0-9]{8,14}$'),
  CONSTRAINT ck_embalagem_balanca_fmt CHECK (codigo_balanca IS NULL OR codigo_balanca REGEXP '^[0-9]{4,6}$'),
  CONSTRAINT ck_embalagem_fator CHECK (fator_conversao > 0),
  CONSTRAINT ck_embalagem_preco CHECK (preco_venda > 0)
) ENGINE=InnoDB COMMENT='Forma de venda de um produto, com código de leitura, fator de conversão e preço vigente.';

-- HISTORICO_PRECO — origem: Entidade HISTORICO_PRECO
-- Registro de cada alteração do preço de venda de uma embalagem.
CREATE TABLE historico_preco (
  id_historico                 INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador da alteração',
  id_embalagem                 INT UNSIGNED NOT NULL COMMENT 'Embalagem alterada',
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Quem alterou',
  data_hora                    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento da alteração',
  preco_anterior               DECIMAL(10,2) NOT NULL COMMENT 'Preço antes da alteração',
  preco_novo                   DECIMAL(10,2) NOT NULL COMMENT 'Preço depois da alteração',
  motivo                       VARCHAR(25) NOT NULL COMMENT 'Razão da alteração',
  CONSTRAINT pk_historico_preco PRIMARY KEY (id_historico),
  CONSTRAINT fk_hp_embalagem FOREIGN KEY (id_embalagem) REFERENCES embalagem (id_embalagem),
  CONSTRAINT fk_hp_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT ck_hp_precos CHECK (preco_anterior > 0 AND preco_novo > 0 AND preco_novo <> preco_anterior),
  CONSTRAINT ck_hp_motivo CHECK (motivo IN ('REAJUSTE_FORNECEDOR','PROXIMO_VENCIMENTO','PROMOCAO','CORRECAO'))
) ENGINE=InnoDB COMMENT='Registro de cada alteração do preço de venda de uma embalagem.';

-- FORNECEDOR — origem: Entidade FORNECEDOR
-- Empresa, distribuidor ou produtor rural que vende ao mercado.
CREATE TABLE fornecedor (
  id_fornecedor                INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador do fornecedor',
  tipo_documento               VARCHAR(4) NOT NULL COMMENT 'Tipo do documento',
  documento                    VARCHAR(14) NOT NULL COMMENT 'CNPJ (numérico ou alfanumérico) ou CPF',
  razao_social                 VARCHAR(120) NOT NULL COMMENT 'Nome jurídico ou nome do produtor',
  nome_fantasia                VARCHAR(80) NULL COMMENT 'Nome comercial',
  canal_pedido                 VARCHAR(16) NOT NULL COMMENT 'Meio usual de pedido',
  condicao_pagamento_padrao    VARCHAR(40) NULL COMMENT 'Condição usual',
  ativo                        BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Em uso',
  CONSTRAINT pk_fornecedor PRIMARY KEY (id_fornecedor),
  CONSTRAINT uq_fornecedor_documento UNIQUE (documento),
  CONSTRAINT ck_fornecedor_doc CHECK ((tipo_documento = 'CPF' AND documento REGEXP '^[0-9]{11}$') OR (tipo_documento = 'CNPJ' AND documento REGEXP '^[0-9A-Z]{12}[0-9]{2}$')),
  CONSTRAINT ck_fornecedor_canal CHECK (canal_pedido IN ('WHATSAPP','APLICATIVO','VENDEDOR_VISITA'))
) ENGINE=InnoDB COMMENT='Empresa, distribuidor ou produtor rural que vende ao mercado.';

-- CONTATO_FORNECEDOR — origem: Atributo multivalorado e composto FORNECEDOR.contatos → tabela (1FN)
-- Cada vendedor/representante de um fornecedor.
CREATE TABLE contato_fornecedor (
  id_fornecedor                INT UNSIGNED NOT NULL COMMENT 'Fornecedor',
  numero_contato               TINYINT UNSIGNED NOT NULL COMMENT 'Sequência do contato no fornecedor',
  nome                         VARCHAR(80) NOT NULL COMMENT 'Nome do vendedor/representante',
  telefone                     VARCHAR(15) NOT NULL COMMENT 'Telefone',
  usa_whatsapp                 BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Atende por WhatsApp',
  CONSTRAINT pk_contato_fornecedor PRIMARY KEY (id_fornecedor, numero_contato),
  CONSTRAINT fk_contato_fornecedor FOREIGN KEY (id_fornecedor) REFERENCES fornecedor (id_fornecedor),
  CONSTRAINT ck_contato_tel CHECK (telefone REGEXP '^[0-9]{10,11}$')
) ENGINE=InnoDB COMMENT='Cada vendedor/representante de um fornecedor.';

-- PRODUTO_FORNECEDOR — origem: Relacionamento N:N FORNECE (R09) → tabela associativa
-- Quais produtos cada fornecedor fornece e com que código no catálogo dele.
CREATE TABLE produto_fornecedor (
  id_fornecedor                INT UNSIGNED NOT NULL COMMENT 'Fornecedor',
  id_produto                   INT UNSIGNED NOT NULL COMMENT 'Produto',
  codigo_no_fornecedor         VARCHAR(30) NULL COMMENT 'Código do item no catálogo do fornecedor',
  ativo                        BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Par ainda em uso',
  CONSTRAINT pk_produto_fornecedor PRIMARY KEY (id_fornecedor, id_produto),
  CONSTRAINT fk_pf_fornecedor FOREIGN KEY (id_fornecedor) REFERENCES fornecedor (id_fornecedor),
  CONSTRAINT fk_pf_produto FOREIGN KEY (id_produto) REFERENCES produto (id_produto)
) ENGINE=InnoDB COMMENT='Quais produtos cada fornecedor fornece e com que código no catálogo dele.';

-- PEDIDO_COMPRA — origem: Entidade PEDIDO_COMPRA
-- Solicitação de mercadorias a um fornecedor.
CREATE TABLE pedido_compra (
  id_pedido                    INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador do pedido',
  id_fornecedor                INT UNSIGNED NOT NULL COMMENT 'Fornecedor',
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Quem fez o pedido',
  data_hora_pedido             DATETIME NOT NULL COMMENT 'Momento do pedido',
  canal                        VARCHAR(16) NOT NULL COMMENT 'Meio usado',
  cancelado                    BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Pedido cancelado',
  observacao                   VARCHAR(200) NULL COMMENT 'Anotações',
  CONSTRAINT pk_pedido_compra PRIMARY KEY (id_pedido),
  CONSTRAINT fk_pedido_fornecedor FOREIGN KEY (id_fornecedor) REFERENCES fornecedor (id_fornecedor),
  CONSTRAINT fk_pedido_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT ck_pedido_canal CHECK (canal IN ('WHATSAPP','APLICATIVO','VENDEDOR_VISITA'))
) ENGINE=InnoDB COMMENT='Solicitação de mercadorias a um fornecedor.';

-- ITEM_PEDIDO — origem: Entidade associativa ITEM_PEDIDO (PEDIDO_COMPRA × PRODUTO)
-- Cada produto solicitado em um pedido.
CREATE TABLE item_pedido (
  id_pedido                    INT UNSIGNED NOT NULL COMMENT 'Pedido',
  id_produto                   INT UNSIGNED NOT NULL COMMENT 'Produto solicitado',
  quantidade_pedida            DECIMAL(12,3) NOT NULL COMMENT 'Quantidade pedida, na unidade base',
  preco_negociado              DECIMAL(12,4) NULL COMMENT 'Preço unitário combinado',
  CONSTRAINT pk_item_pedido PRIMARY KEY (id_pedido, id_produto),
  CONSTRAINT fk_ip_pedido FOREIGN KEY (id_pedido) REFERENCES pedido_compra (id_pedido),
  CONSTRAINT fk_ip_produto FOREIGN KEY (id_produto) REFERENCES produto (id_produto),
  CONSTRAINT ck_ip_qtd CHECK (quantidade_pedida > 0),
  CONSTRAINT ck_ip_preco CHECK (preco_negociado IS NULL OR preco_negociado >= 0)
) ENGINE=InnoDB COMMENT='Cada produto solicitado em um pedido.';

-- RECEBIMENTO — origem: Entidade RECEBIMENTO
-- Chegada de mercadoria com nota fiscal e resultado da conferência.
CREATE TABLE recebimento (
  id_recebimento               INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador do recebimento',
  id_fornecedor                INT UNSIGNED NOT NULL COMMENT 'Emitente da nota',
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Conferente',
  chave_acesso_nfe             CHAR(44) NULL COMMENT 'Chave de acesso da NF-e',
  modelo_nota                  CHAR(2) NOT NULL COMMENT 'Modelo do documento fiscal',
  serie_nota                   SMALLINT UNSIGNED NOT NULL COMMENT 'Série da nota',
  numero_nota                  INT UNSIGNED NOT NULL COMMENT 'Número da nota',
  data_hora                    DATETIME NOT NULL COMMENT 'Momento da chegada',
  valor_total_nota             DECIMAL(12,2) NOT NULL COMMENT 'Valor total da nota',
  volumes_nota                 SMALLINT UNSIGNED NOT NULL COMMENT 'Volumes declarados na nota',
  volumes_conferidos           SMALLINT UNSIGNED NOT NULL COMMENT 'Volumes efetivamente contados',
  situacao                     VARCHAR(25) NOT NULL COMMENT 'Resultado da conferência',
  observacao_divergencia       VARCHAR(300) NULL COMMENT 'Descrição das divergências',
  CONSTRAINT pk_recebimento PRIMARY KEY (id_recebimento),
  CONSTRAINT uq_recebimento_nfe UNIQUE (chave_acesso_nfe),
  CONSTRAINT uq_recebimento_nota UNIQUE (id_fornecedor, modelo_nota, serie_nota, numero_nota),
  CONSTRAINT fk_receb_fornecedor FOREIGN KEY (id_fornecedor) REFERENCES fornecedor (id_fornecedor),
  CONSTRAINT fk_receb_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT ck_receb_nfe_fmt CHECK (chave_acesso_nfe IS NULL OR chave_acesso_nfe REGEXP '^[0-9A-Z]{44}$'),
  CONSTRAINT ck_receb_modelo CHECK (modelo_nota REGEXP '^[0-9]{2}$'),
  CONSTRAINT ck_receb_serie CHECK (serie_nota <= 999),
  CONSTRAINT ck_receb_numero CHECK (numero_nota BETWEEN 1 AND 999999999),
  CONSTRAINT ck_receb_valor CHECK (valor_total_nota >= 0),
  CONSTRAINT ck_receb_situacao CHECK (situacao IN ('ACEITO','ACEITO_COM_DIVERGENCIA','RECUSADO')),
  CONSTRAINT ck_receb_obs CHECK (situacao = 'ACEITO' OR observacao_divergencia IS NOT NULL)
) ENGINE=InnoDB COMMENT='Chegada de mercadoria com nota fiscal e resultado da conferência.';

-- ITEM_RECEBIMENTO — origem: Entidade fraca ITEM_RECEBIMENTO (linha da nota)
-- Cada linha da nota fiscal recebida, com a conferência item a item.
CREATE TABLE item_recebimento (
  id_recebimento               INT UNSIGNED NOT NULL COMMENT 'Recebimento (nota)',
  numero_item_nota             SMALLINT UNSIGNED NOT NULL COMMENT 'Número da linha na nota',
  id_produto                   INT UNSIGNED NOT NULL COMMENT 'Produto recebido',
  id_pedido                    INT UNSIGNED NULL COMMENT 'Pedido atendido por esta linha',
  quantidade_nota              DECIMAL(12,3) NOT NULL COMMENT 'Quantidade faturada, na unidade da nota',
  fator_conversao_compra       DECIMAL(10,3) NOT NULL DEFAULT 1 COMMENT 'Unidades base por unidade da nota',
  valor_unitario_nota          DECIMAL(12,4) NOT NULL COMMENT 'Valor unitário na nota',
  quantidade_aceita            DECIMAL(12,3) NOT NULL COMMENT 'Quantidade aceita, na unidade base',
  situacao_item                VARCHAR(25) NOT NULL COMMENT 'Resultado da conferência da linha',
  CONSTRAINT pk_item_recebimento PRIMARY KEY (id_recebimento, numero_item_nota),
  CONSTRAINT uq_ir_lote_ref UNIQUE (id_recebimento, numero_item_nota, id_produto),
  CONSTRAINT fk_ir_recebimento FOREIGN KEY (id_recebimento) REFERENCES recebimento (id_recebimento),
  CONSTRAINT fk_ir_produto FOREIGN KEY (id_produto) REFERENCES produto (id_produto),
  CONSTRAINT fk_ir_item_pedido FOREIGN KEY (id_pedido, id_produto) REFERENCES item_pedido (id_pedido, id_produto),
  CONSTRAINT ck_ir_qtd CHECK (quantidade_nota > 0),
  CONSTRAINT ck_ir_fator CHECK (fator_conversao_compra > 0),
  CONSTRAINT ck_ir_valor CHECK (valor_unitario_nota >= 0),
  CONSTRAINT ck_ir_aceita CHECK (quantidade_aceita >= 0 AND quantidade_aceita <= quantidade_nota * fator_conversao_compra),
  CONSTRAINT ck_ir_situacao CHECK ((situacao_item IN ('RECUSADO','NAO_PEDIDO_DEVOLVIDO') AND quantidade_aceita = 0) OR (situacao_item IN ('ACEITO','ACEITO_PARCIAL') AND quantidade_aceita > 0))
) ENGINE=InnoDB COMMENT='Cada linha da nota fiscal recebida, com a conferência item a item.';

-- LOTE — origem: Entidade LOTE
-- Porção de um produto com mesma origem, custo e validade. Base de validade, FEFO e custo.
CREATE TABLE lote (
  id_lote                      INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador do lote',
  id_produto                   INT UNSIGNED NOT NULL COMMENT 'Produto do lote',
  id_recebimento               INT UNSIGNED NULL COMMENT 'Recebimento de origem',
  numero_item_nota             SMALLINT UNSIGNED NULL COMMENT 'Linha da nota de origem',
  id_lote_reposto              INT UNSIGNED NULL COMMENT 'Lote trocado que este lote repõe',
  origem                       VARCHAR(25) NOT NULL COMMENT 'Como o lote surgiu',
  codigo_lote_fabricante       VARCHAR(30) NULL COMMENT 'Lote impresso pelo fabricante',
  data_validade                DATE NULL COMMENT 'Validade',
  data_entrada                 DATETIME NOT NULL COMMENT 'Entrada no estoque',
  custo_unitario               DECIMAL(12,4) NOT NULL COMMENT 'Custo por unidade base',
  situacao                     VARCHAR(15) NOT NULL DEFAULT 'DISPONIVEL' COMMENT 'Estado do lote',
  pendente_conferencia         BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Lote de ajuste automático aguardando conferência física',
  CONSTRAINT pk_lote PRIMARY KEY (id_lote),
  CONSTRAINT fk_lote_produto FOREIGN KEY (id_produto) REFERENCES produto (id_produto),
  CONSTRAINT fk_lote_item_receb FOREIGN KEY (id_recebimento, numero_item_nota, id_produto) REFERENCES item_recebimento (id_recebimento, numero_item_nota, id_produto),
  CONSTRAINT fk_lote_reposto FOREIGN KEY (id_lote_reposto) REFERENCES lote (id_lote),
  CONSTRAINT ck_lote_origem CHECK (origem IN ('RECEBIMENTO','INVENTARIO_INICIAL','AJUSTE_INVENTARIO','REPOSICAO_FORNECEDOR')),
  CONSTRAINT ck_lote_origem_nota CHECK ((origem = 'RECEBIMENTO' AND id_recebimento IS NOT NULL AND numero_item_nota IS NOT NULL) OR (origem <> 'RECEBIMENTO' AND id_recebimento IS NULL AND numero_item_nota IS NULL)),
  CONSTRAINT ck_lote_origem_reposicao CHECK ((origem = 'REPOSICAO_FORNECEDOR') = (id_lote_reposto IS NOT NULL)),
  CONSTRAINT ck_lote_custo CHECK (custo_unitario >= 0),
  CONSTRAINT ck_lote_situacao CHECK (situacao IN ('DISPONIVEL','SEPARADO_TROCA','TROCADO','DESCARTADO')),
  CONSTRAINT ck_lote_pendente CHECK (pendente_conferencia = FALSE OR origem = 'AJUSTE_INVENTARIO')
) ENGINE=InnoDB COMMENT='Porção de um produto com mesma origem, custo e validade. Base de validade, FEFO e custo.';

-- CAIXA — origem: Entidade CAIXA
-- Ponto de venda físico.
CREATE TABLE caixa (
  numero_caixa                 TINYINT UNSIGNED NOT NULL COMMENT 'Número pintado no PDV',
  ativo                        BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Em uso',
  CONSTRAINT pk_caixa PRIMARY KEY (numero_caixa),
  CONSTRAINT ck_caixa_numero CHECK (numero_caixa >= 1)
) ENGINE=InnoDB COMMENT='Ponto de venda físico.';

-- SESSAO_CAIXA — origem: Entidade SESSAO_CAIXA
-- Período entre abertura e fechamento de um caixa; onde ocorre o fechamento de caixa.
CREATE TABLE sessao_caixa (
  id_sessao                    INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador da sessão',
  numero_caixa                 TINYINT UNSIGNED NOT NULL COMMENT 'Caixa aberto',
  id_funcionario_abertura      INT UNSIGNED NOT NULL COMMENT 'Quem abriu',
  id_funcionario_fechamento    INT UNSIGNED NULL COMMENT 'Quem fechou',
  data_hora_abertura           DATETIME NOT NULL COMMENT 'Abertura',
  valor_inicial                DECIMAL(10,2) NOT NULL COMMENT 'Fundo de troco',
  data_hora_fechamento         DATETIME NULL COMMENT 'Fechamento',
  valor_contado                DECIMAL(10,2) NULL COMMENT 'Dinheiro contado no fechamento',
  total_maquininhas_informado  DECIMAL(12,2) NULL COMMENT 'Total do relatório das maquininhas',
  justificativa_diferenca      VARCHAR(200) NULL COMMENT 'Explicação de sobra/falta',
  CONSTRAINT pk_sessao_caixa PRIMARY KEY (id_sessao),
  CONSTRAINT fk_sessao_caixa FOREIGN KEY (numero_caixa) REFERENCES caixa (numero_caixa),
  CONSTRAINT fk_sessao_abertura FOREIGN KEY (id_funcionario_abertura) REFERENCES funcionario (id_funcionario),
  CONSTRAINT fk_sessao_fechamento FOREIGN KEY (id_funcionario_fechamento) REFERENCES funcionario (id_funcionario),
  CONSTRAINT ck_sessao_valores CHECK (valor_inicial >= 0 AND (valor_contado IS NULL OR valor_contado >= 0) AND (total_maquininhas_informado IS NULL OR total_maquininhas_informado >= 0)),
  CONSTRAINT ck_sessao_fechamento CHECK ((data_hora_fechamento IS NULL AND id_funcionario_fechamento IS NULL AND valor_contado IS NULL) OR (data_hora_fechamento IS NOT NULL AND id_funcionario_fechamento IS NOT NULL AND valor_contado IS NOT NULL)),
  CONSTRAINT ck_sessao_datas CHECK (data_hora_fechamento IS NULL OR data_hora_fechamento > data_hora_abertura)
) ENGINE=InnoDB COMMENT='Período entre abertura e fechamento de um caixa; onde ocorre o fechamento de caixa.';

-- CLIENTE — origem: Entidade CLIENTE
-- Consumidor identificado; exigido apenas para venda fiada.
CREATE TABLE cliente (
  id_cliente                   INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador do cliente',
  cpf                          CHAR(11) NULL COMMENT 'CPF',
  nome                         VARCHAR(100) NOT NULL COMMENT 'Nome',
  apelido                      VARCHAR(40) NULL COMMENT 'Como é conhecido no bairro',
  telefone                     VARCHAR(15) NULL COMMENT 'Telefone',
  logradouro                   VARCHAR(100) NULL COMMENT 'Rua/avenida',
  numero_endereco              VARCHAR(10) NULL COMMENT 'Número do imóvel',
  complemento                  VARCHAR(40) NULL COMMENT 'Complemento',
  bairro                       VARCHAR(50) NULL COMMENT 'Bairro',
  autorizado_fiado             BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Pode comprar fiado',
  limite_fiado                 DECIMAL(10,2) NULL COMMENT 'Limite de dívida em aberto',
  data_cadastro                DATE NOT NULL DEFAULT (CURRENT_DATE) COMMENT 'Data do cadastro',
  CONSTRAINT pk_cliente PRIMARY KEY (id_cliente),
  CONSTRAINT uq_cliente_cpf UNIQUE (cpf),
  CONSTRAINT ck_cliente_cpf CHECK (cpf IS NULL OR cpf REGEXP '^[0-9]{11}$'),
  CONSTRAINT ck_cliente_fiado_cpf CHECK (autorizado_fiado = FALSE OR cpf IS NOT NULL),
  CONSTRAINT ck_cliente_limite CHECK (limite_fiado IS NULL OR limite_fiado >= 0),
  CONSTRAINT ck_cliente_tel CHECK (telefone IS NULL OR telefone REGEXP '^[0-9]{10,11}$')
) ENGINE=InnoDB COMMENT='Consumidor identificado; exigido apenas para venda fiada.';

-- VENDA — origem: Entidade VENDA
-- Transação de venda registrada no caixa.
CREATE TABLE venda (
  id_venda                     INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador da venda',
  id_sessao                    INT UNSIGNED NOT NULL COMMENT 'Sessão de caixa',
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Operador',
  id_cliente                   INT UNSIGNED NULL COMMENT 'Cliente identificado',
  numero_cupom                 INT UNSIGNED NOT NULL COMMENT 'Número do cupom',
  data_hora                    DATETIME NOT NULL COMMENT 'Momento da venda',
  situacao                     VARCHAR(10) NOT NULL DEFAULT 'CONCLUIDA' COMMENT 'Estado',
  CONSTRAINT pk_venda PRIMARY KEY (id_venda),
  CONSTRAINT uq_venda_cupom UNIQUE (id_sessao, numero_cupom),
  CONSTRAINT fk_venda_sessao FOREIGN KEY (id_sessao) REFERENCES sessao_caixa (id_sessao),
  CONSTRAINT fk_venda_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT fk_venda_cliente FOREIGN KEY (id_cliente) REFERENCES cliente (id_cliente),
  CONSTRAINT ck_venda_situacao CHECK (situacao IN ('CONCLUIDA','CANCELADA')),
  CONSTRAINT ck_venda_cupom CHECK (numero_cupom >= 1)
) ENGINE=InnoDB COMMENT='Transação de venda registrada no caixa.';

-- ITEM_VENDA — origem: Entidade associativa ITEM_VENDA (VENDA × EMBALAGEM)
-- Cada linha do cupom: embalagem, quantidade, preço praticado e desconto.
CREATE TABLE item_venda (
  id_venda                     INT UNSIGNED NOT NULL COMMENT 'Venda',
  numero_item                  SMALLINT UNSIGNED NOT NULL COMMENT 'Posição no cupom',
  id_embalagem                 INT UNSIGNED NOT NULL COMMENT 'Embalagem lida',
  id_funcionario_autorizador   INT UNSIGNED NULL COMMENT 'Quem autorizou o desconto',
  quantidade                   DECIMAL(12,3) NOT NULL COMMENT 'Quantidade na unidade da embalagem',
  preco_unitario_praticado     DECIMAL(10,2) NOT NULL COMMENT 'Preço no momento da venda',
  desconto_unitario            DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT 'Desconto por unidade',
  CONSTRAINT pk_item_venda PRIMARY KEY (id_venda, numero_item),
  CONSTRAINT fk_iv_venda FOREIGN KEY (id_venda) REFERENCES venda (id_venda),
  CONSTRAINT fk_iv_embalagem FOREIGN KEY (id_embalagem) REFERENCES embalagem (id_embalagem),
  CONSTRAINT fk_iv_autorizador FOREIGN KEY (id_funcionario_autorizador) REFERENCES funcionario (id_funcionario),
  CONSTRAINT ck_iv_qtd CHECK (quantidade > 0),
  CONSTRAINT ck_iv_preco CHECK (preco_unitario_praticado > 0),
  CONSTRAINT ck_iv_desconto CHECK (desconto_unitario >= 0 AND desconto_unitario < preco_unitario_praticado),
  CONSTRAINT ck_iv_autorizacao CHECK (desconto_unitario = 0 OR id_funcionario_autorizador IS NOT NULL)
) ENGINE=InnoDB COMMENT='Cada linha do cupom: embalagem, quantidade, preço praticado e desconto.';

-- CONTA_FINANCEIRA — origem: Entidade CONTA_FINANCEIRA
-- Onde o dinheiro fica fora da gaveta: banco, conta da maquininha ou cofre.
CREATE TABLE conta_financeira (
  id_conta_financeira          INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador',
  nome                         VARCHAR(60) NOT NULL COMMENT 'Nome da conta',
  tipo                         VARCHAR(16) NOT NULL COMMENT 'Tipo',
  saldo_inicial                DECIMAL(12,2) NOT NULL COMMENT 'Saldo na implantação',
  data_saldo_inicial           DATE NOT NULL COMMENT 'Data do saldo inicial',
  ativa                        BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Em uso',
  CONSTRAINT pk_conta_financeira PRIMARY KEY (id_conta_financeira),
  CONSTRAINT uq_cf_nome UNIQUE (nome),
  CONSTRAINT ck_cf_tipo CHECK (tipo IN ('CONTA_BANCARIA','CONTA_ADQUIRENTE','COFRE'))
) ENGINE=InnoDB COMMENT='Onde o dinheiro fica fora da gaveta: banco, conta da maquininha ou cofre.';

-- MOVIMENTO_FINANCEIRO — origem: Entidade MOVIMENTO_FINANCEIRO
-- Entrada ou saída efetiva de dinheiro numa conta financeira (linha do extrato ou do cofre).
CREATE TABLE movimento_financeiro (
  id_movimento_fin             INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador',
  id_conta_financeira          INT UNSIGNED NOT NULL COMMENT 'Conta',
  id_funcionario               INT UNSIGNED NULL COMMENT 'Quem lançou',
  data_movimento               DATE NOT NULL COMMENT 'Data em que o valor entrou/saiu',
  natureza                     VARCHAR(7) NOT NULL COMMENT 'Sentido',
  origem                       VARCHAR(20) NOT NULL COMMENT 'O que gerou',
  valor_bruto                  DECIMAL(12,2) NOT NULL COMMENT 'Valor antes da taxa',
  valor_taxa                   DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT 'Taxa descontada',
  documento_referencia         VARCHAR(60) NULL COMMENT 'Identificação no extrato',
  CONSTRAINT pk_movimento_financeiro PRIMARY KEY (id_movimento_fin),
  CONSTRAINT uq_mf_documento UNIQUE (id_conta_financeira, documento_referencia),
  CONSTRAINT fk_mf_conta FOREIGN KEY (id_conta_financeira) REFERENCES conta_financeira (id_conta_financeira),
  CONSTRAINT fk_mf_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT ck_mf_natureza CHECK (natureza IN ('CREDITO','DEBITO')),
  CONSTRAINT ck_mf_origem CHECK ((natureza = 'CREDITO' AND origem IN ('REPASSE_CARTAO','PIX_RECEBIDO','RECOLHIMENTO_GAVETA','DEPOSITO','AJUSTE')) OR (natureza = 'DEBITO' AND origem IN ('SUPRIMENTO_GAVETA','DEPOSITO','PAGAMENTO_CONTA','ESTORNO_DEVOLUCAO','TARIFA','AJUSTE'))),
  CONSTRAINT ck_mf_valores CHECK (valor_bruto > 0 AND valor_taxa >= 0 AND valor_taxa <= valor_bruto),
  CONSTRAINT ck_mf_manual CHECK (origem NOT IN ('DEPOSITO','TARIFA','AJUSTE') OR id_funcionario IS NOT NULL)
) ENGINE=InnoDB COMMENT='Entrada ou saída efetiva de dinheiro numa conta financeira (linha do extrato ou do cofre).';

-- FORMA_PAGAMENTO — origem: Entidade FORMA_PAGAMENTO
-- Meio de pagamento com prazo e taxa de crédito.
CREATE TABLE forma_pagamento (
  codigo_forma                 VARCHAR(5) NOT NULL COMMENT 'Código',
  descricao                    VARCHAR(40) NOT NULL COMMENT 'Nome exibido',
  prazo_credito_dias           SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Dias até o crédito',
  taxa_percentual              DECIMAL(5,2) NOT NULL DEFAULT 0 COMMENT 'Taxa contratada (%)',
  gera_divida                  BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Cria dívida do cliente',
  exige_conciliacao            BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Valor cai em conta e deve ser conciliado',
  ativa                        BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Disponível no caixa',
  CONSTRAINT pk_forma_pagamento PRIMARY KEY (codigo_forma),
  CONSTRAINT ck_fp_taxa CHECK (taxa_percentual BETWEEN 0 AND 100),
  CONSTRAINT ck_fp_divida CHECK (NOT (gera_divida AND exige_conciliacao))
) ENGINE=InnoDB COMMENT='Meio de pagamento com prazo e taxa de crédito.';

-- PAGAMENTO_VENDA — origem: Entidade fraca PAGAMENTO_VENDA
-- Cada transação de pagamento de uma venda.
CREATE TABLE pagamento_venda (
  id_venda                     INT UNSIGNED NOT NULL COMMENT 'Venda paga',
  numero_pagamento             TINYINT UNSIGNED NOT NULL COMMENT 'Sequência na venda',
  codigo_forma                 VARCHAR(5) NOT NULL COMMENT 'Forma',
  id_movimento_fin             INT UNSIGNED NULL COMMENT 'Crédito que liquidou a transação',
  valor                        DECIMAL(10,2) NOT NULL COMMENT 'Valor aplicado à venda',
  valor_entregue               DECIMAL(10,2) NULL COMMENT 'Dinheiro entregue pelo cliente',
  nsu_autorizacao              VARCHAR(36) NULL COMMENT 'NSU / ID da transação',
  CONSTRAINT pk_pagamento_venda PRIMARY KEY (id_venda, numero_pagamento),
  CONSTRAINT uq_pv_nsu UNIQUE (nsu_autorizacao),
  CONSTRAINT fk_pv_venda FOREIGN KEY (id_venda) REFERENCES venda (id_venda),
  CONSTRAINT fk_pv_forma FOREIGN KEY (codigo_forma) REFERENCES forma_pagamento (codigo_forma),
  CONSTRAINT fk_pv_movimento FOREIGN KEY (id_movimento_fin) REFERENCES movimento_financeiro (id_movimento_fin),
  CONSTRAINT ck_pv_valor CHECK (valor > 0),
  CONSTRAINT ck_pv_entregue CHECK ((codigo_forma = 'DIN' AND (valor_entregue IS NULL OR valor_entregue >= valor)) OR (codigo_forma <> 'DIN' AND valor_entregue IS NULL)),
  CONSTRAINT ck_pv_nsu CHECK (codigo_forma IN ('DIN','FIADO') OR nsu_autorizacao IS NOT NULL),
  CONSTRAINT ck_pv_liquidacao CHECK (id_movimento_fin IS NULL OR codigo_forma NOT IN ('DIN','FIADO'))
) ENGINE=InnoDB COMMENT='Cada transação de pagamento de uma venda.';

-- MOVIMENTACAO_CAIXA — origem: Entidade MOVIMENTACAO_CAIXA
-- Dinheiro que entra ou sai da gaveta sem ser venda.
CREATE TABLE movimentacao_caixa (
  id_mov_caixa                 INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador',
  id_sessao                    INT UNSIGNED NOT NULL COMMENT 'Sessão',
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Quem executou',
  id_movimento_fin             INT UNSIGNED NULL COMMENT 'Lançamento no cofre gerado',
  data_hora                    DATETIME NOT NULL COMMENT 'Momento',
  tipo                         VARCHAR(25) NOT NULL COMMENT 'Tipo',
  valor                        DECIMAL(10,2) NOT NULL COMMENT 'Valor',
  motivo                       VARCHAR(200) NOT NULL COMMENT 'Justificativa',
  CONSTRAINT pk_movimentacao_caixa PRIMARY KEY (id_mov_caixa),
  CONSTRAINT uq_mc_movimento UNIQUE (id_movimento_fin),
  CONSTRAINT fk_mc_sessao FOREIGN KEY (id_sessao) REFERENCES sessao_caixa (id_sessao),
  CONSTRAINT fk_mc_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT fk_mc_movimento FOREIGN KEY (id_movimento_fin) REFERENCES movimento_financeiro (id_movimento_fin),
  CONSTRAINT ck_mc_tipo CHECK (tipo IN ('SANGRIA','SUPRIMENTO','RECOLHIMENTO_FECHAMENTO','REEMBOLSO_DEVOLUCAO')),
  CONSTRAINT ck_mc_valor CHECK (valor > 0),
  CONSTRAINT ck_mc_cofre CHECK ((tipo = 'REEMBOLSO_DEVOLUCAO' AND id_movimento_fin IS NULL) OR (tipo <> 'REEMBOLSO_DEVOLUCAO' AND id_movimento_fin IS NOT NULL))
) ENGINE=InnoDB COMMENT='Dinheiro que entra ou sai da gaveta sem ser venda.';

-- DEVOLUCAO — origem: Entidade DEVOLUCAO
-- Devolução ou troca de item vendido.
CREATE TABLE devolucao (
  id_devolucao                 INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador',
  id_venda                     INT UNSIGNED NOT NULL COMMENT 'Venda de origem',
  numero_item                  SMALLINT UNSIGNED NOT NULL COMMENT 'Item devolvido',
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Autorizador',
  id_mov_caixa                 INT UNSIGNED NULL COMMENT 'Saída de dinheiro do reembolso',
  id_movimento_fin             INT UNSIGNED NULL COMMENT 'Estorno em conta',
  data_hora                    DATETIME NOT NULL COMMENT 'Momento',
  quantidade_devolvida         DECIMAL(12,3) NOT NULL COMMENT 'Quantidade, na unidade da embalagem',
  motivo                       VARCHAR(10) NOT NULL COMMENT 'Motivo',
  destino                      VARCHAR(15) NOT NULL COMMENT 'Destino do produto',
  forma_reembolso              VARCHAR(20) NOT NULL COMMENT 'Reembolso',
  valor_reembolsado            DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT 'Valor devolvido',
  CONSTRAINT pk_devolucao PRIMARY KEY (id_devolucao),
  CONSTRAINT uq_dev_mov_caixa UNIQUE (id_mov_caixa),
  CONSTRAINT uq_dev_mov_fin UNIQUE (id_movimento_fin),
  CONSTRAINT fk_dev_item FOREIGN KEY (id_venda, numero_item) REFERENCES item_venda (id_venda, numero_item),
  CONSTRAINT fk_dev_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT fk_dev_mov_caixa FOREIGN KEY (id_mov_caixa) REFERENCES movimentacao_caixa (id_mov_caixa),
  CONSTRAINT fk_dev_mov_fin FOREIGN KEY (id_movimento_fin) REFERENCES movimento_financeiro (id_movimento_fin),
  CONSTRAINT ck_dev_qtd CHECK (quantidade_devolvida > 0),
  CONSTRAINT ck_dev_motivo CHECK (motivo IN ('DEFEITO','VENCIDO')),
  CONSTRAINT ck_dev_destino CHECK (destino IN ('REVENDA','SEPARADO_TROCA','DESCARTE')),
  CONSTRAINT ck_dev_forma CHECK (forma_reembolso IN ('TROCA_MESMO_PRODUTO','DINHEIRO','ESTORNO_ELETRONICO','ABATER_FIADO')),
  CONSTRAINT ck_dev_valor CHECK ((forma_reembolso = 'TROCA_MESMO_PRODUTO' AND valor_reembolsado = 0) OR (forma_reembolso <> 'TROCA_MESMO_PRODUTO' AND valor_reembolsado > 0)),
  CONSTRAINT ck_dev_dinheiro CHECK ((forma_reembolso = 'DINHEIRO') = (id_mov_caixa IS NOT NULL)),
  CONSTRAINT ck_dev_estorno CHECK ((forma_reembolso = 'ESTORNO_ELETRONICO') = (id_movimento_fin IS NOT NULL))
) ENGINE=InnoDB COMMENT='Devolução ou troca de item vendido.';

-- MOVIMENTACAO_ESTOQUE — origem: Entidade MOVIMENTACAO_ESTOQUE
-- Toda entrada ou saída de um lote (kardex). Nenhum saldo muda sem ela.
CREATE TABLE movimentacao_estoque (
  id_movimentacao              INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador',
  id_lote                      INT UNSIGNED NOT NULL COMMENT 'Lote movimentado',
  id_funcionario               INT UNSIGNED NULL COMMENT 'Responsável',
  id_venda                     INT UNSIGNED NULL COMMENT 'Venda que gerou a baixa',
  numero_item                  SMALLINT UNSIGNED NULL COMMENT 'Item do cupom',
  id_devolucao                 INT UNSIGNED NULL COMMENT 'Devolução que gerou',
  data_hora                    DATETIME NOT NULL COMMENT 'Momento',
  tipo                         VARCHAR(30) NOT NULL COMMENT 'Natureza',
  quantidade                   DECIMAL(12,3) NOT NULL COMMENT 'Quantidade na unidade base',
  motivo                       VARCHAR(200) NULL COMMENT 'Justificativa',
  CONSTRAINT pk_movimentacao_estoque PRIMARY KEY (id_movimentacao),
  CONSTRAINT fk_me_lote FOREIGN KEY (id_lote) REFERENCES lote (id_lote),
  CONSTRAINT fk_me_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT fk_me_item_venda FOREIGN KEY (id_venda, numero_item) REFERENCES item_venda (id_venda, numero_item),
  CONSTRAINT fk_me_devolucao FOREIGN KEY (id_devolucao) REFERENCES devolucao (id_devolucao),
  CONSTRAINT ck_me_tipo CHECK (tipo IN ('ENTRADA_RECEBIMENTO','ENTRADA_INVENTARIO','TROCA_FORNECEDOR','DEVOLUCAO_CLIENTE','AJUSTE_INVENTARIO_ENTRADA','SAIDA_VENDA','SAIDA_TROCA_CLIENTE','PERDA_VENCIMENTO','PERDA_AVARIA','AJUSTE_INVENTARIO_SAIDA')),
  CONSTRAINT ck_me_qtd CHECK (quantidade > 0),
  CONSTRAINT ck_me_venda CHECK ((tipo = 'SAIDA_VENDA') = (id_venda IS NOT NULL AND numero_item IS NOT NULL)),
  CONSTRAINT ck_me_venda_par CHECK ((id_venda IS NULL) = (numero_item IS NULL)),
  CONSTRAINT ck_me_devolucao CHECK ((tipo IN ('DEVOLUCAO_CLIENTE','SAIDA_TROCA_CLIENTE')) = (id_devolucao IS NOT NULL)),
  CONSTRAINT ck_me_responsavel CHECK (tipo NOT IN ('PERDA_VENCIMENTO','PERDA_AVARIA','AJUSTE_INVENTARIO_ENTRADA','AJUSTE_INVENTARIO_SAIDA','ENTRADA_INVENTARIO','TROCA_FORNECEDOR') OR id_funcionario IS NOT NULL),
  CONSTRAINT ck_me_motivo CHECK (tipo NOT IN ('PERDA_VENCIMENTO','PERDA_AVARIA','AJUSTE_INVENTARIO_ENTRADA','AJUSTE_INVENTARIO_SAIDA') OR motivo IS NOT NULL)
) ENGINE=InnoDB COMMENT='Toda entrada ou saída de um lote (kardex). Nenhum saldo muda sem ela.';

-- ABATIMENTO_FIADO — origem: Entidade ABATIMENTO_FIADO
-- Pagamento total ou parcial da dívida de fiado.
CREATE TABLE abatimento_fiado (
  id_abatimento                INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador',
  id_cliente                   INT UNSIGNED NOT NULL COMMENT 'Cliente',
  codigo_forma                 VARCHAR(5) NOT NULL COMMENT 'Forma usada',
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Quem recebeu',
  id_sessao                    INT UNSIGNED NULL COMMENT 'Sessão em que o dinheiro entrou',
  id_movimento_fin             INT UNSIGNED NULL COMMENT 'Crédito que liquidou',
  data_hora                    DATETIME NOT NULL COMMENT 'Momento',
  valor                        DECIMAL(10,2) NOT NULL COMMENT 'Valor pago',
  observacao                   VARCHAR(200) NULL COMMENT 'Anotação',
  CONSTRAINT pk_abatimento_fiado PRIMARY KEY (id_abatimento),
  CONSTRAINT fk_ab_cliente FOREIGN KEY (id_cliente) REFERENCES cliente (id_cliente),
  CONSTRAINT fk_ab_forma FOREIGN KEY (codigo_forma) REFERENCES forma_pagamento (codigo_forma),
  CONSTRAINT fk_ab_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT fk_ab_sessao FOREIGN KEY (id_sessao) REFERENCES sessao_caixa (id_sessao),
  CONSTRAINT fk_ab_movimento FOREIGN KEY (id_movimento_fin) REFERENCES movimento_financeiro (id_movimento_fin),
  CONSTRAINT ck_ab_valor CHECK (valor > 0),
  CONSTRAINT ck_ab_forma CHECK (codigo_forma <> 'FIADO'),
  CONSTRAINT ck_ab_sessao CHECK (codigo_forma <> 'DIN' OR id_sessao IS NOT NULL),
  CONSTRAINT ck_ab_liquidacao CHECK (id_movimento_fin IS NULL OR codigo_forma <> 'DIN')
) ENGINE=InnoDB COMMENT='Pagamento total ou parcial da dívida de fiado.';

-- CONTA_PAGAR — origem: Entidade CONTA_PAGAR
-- Obrigação do mercado: parcela de boleto, imposto, folha, internet etc.
CREATE TABLE conta_pagar (
  id_conta                     INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Identificador',
  id_recebimento               INT UNSIGNED NULL COMMENT 'Recebimento de origem',
  credor                       VARCHAR(120) NOT NULL COMMENT 'Quem recebe',
  numero_documento             VARCHAR(40) NULL COMMENT 'Nº do boleto/guia/competência',
  numero_parcela               TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Parcela',
  descricao                    VARCHAR(150) NOT NULL COMMENT 'Descrição',
  categoria_despesa            VARCHAR(18) NOT NULL COMMENT 'Categoria',
  valor_original               DECIMAL(12,2) NOT NULL COMMENT 'Valor da obrigação',
  data_vencimento              DATE NOT NULL COMMENT 'Vencimento',
  prioridade                   VARCHAR(5) NOT NULL DEFAULT 'MEDIA' COMMENT 'Prioridade',
  cancelada                    BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Cancelada',
  CONSTRAINT pk_conta_pagar PRIMARY KEY (id_conta),
  CONSTRAINT uq_cp_parcela UNIQUE (id_recebimento, numero_parcela),
  CONSTRAINT fk_cp_recebimento FOREIGN KEY (id_recebimento) REFERENCES recebimento (id_recebimento),
  CONSTRAINT ck_cp_categoria CHECK (categoria_despesa IN ('FORNECEDOR','SIMPLES_NACIONAL','FOLHA','INTERNET','AGUA','LUZ','ALUGUEL','OUTROS')),
  CONSTRAINT ck_cp_valor CHECK (valor_original > 0),
  CONSTRAINT ck_cp_parcela CHECK (numero_parcela >= 1),
  CONSTRAINT ck_cp_prioridade CHECK (prioridade IN ('ALTA','MEDIA','BAIXA')),
  CONSTRAINT ck_cp_origem CHECK (categoria_despesa = 'FORNECEDOR' OR id_recebimento IS NULL)
) ENGINE=InnoDB COMMENT='Obrigação do mercado: parcela de boleto, imposto, folha, internet etc.';

-- PAGAMENTO_CONTA — origem: Entidade fraca PAGAMENTO_CONTA
-- Cada pagamento (total ou parcial) de uma conta.
CREATE TABLE pagamento_conta (
  id_conta                     INT UNSIGNED NOT NULL COMMENT 'Conta paga',
  numero_pagamento             TINYINT UNSIGNED NOT NULL COMMENT 'Sequência na conta',
  id_funcionario               INT UNSIGNED NOT NULL COMMENT 'Quem registrou',
  id_movimento_fin             INT UNSIGNED NOT NULL COMMENT 'Saída de dinheiro',
  data_pagamento               DATE NOT NULL COMMENT 'Data',
  valor_principal              DECIMAL(12,2) NOT NULL COMMENT 'Parte do valor original quitada',
  valor_juros_multa            DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT 'Encargos',
  valor_desconto               DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT 'Desconto obtido',
  observacao                   VARCHAR(200) NULL COMMENT 'Anotação',
  CONSTRAINT pk_pagamento_conta PRIMARY KEY (id_conta, numero_pagamento),
  CONSTRAINT uq_pc_movimento UNIQUE (id_movimento_fin),
  CONSTRAINT fk_pc_conta FOREIGN KEY (id_conta) REFERENCES conta_pagar (id_conta),
  CONSTRAINT fk_pc_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionario (id_funcionario),
  CONSTRAINT fk_pc_movimento FOREIGN KEY (id_movimento_fin) REFERENCES movimento_financeiro (id_movimento_fin),
  CONSTRAINT ck_pc_valores CHECK (valor_principal > 0 AND valor_juros_multa >= 0 AND valor_desconto >= 0),
  CONSTRAINT ck_pc_desconto CHECK (valor_desconto < valor_principal + valor_juros_multa)
) ENGINE=InnoDB COMMENT='Cada pagamento (total ou parcial) de uma conta.';
