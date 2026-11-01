-- =====================================================================
-- 08_testes_restricoes.sql — TESTES NEGATIVOS DAS RESTRIÇÕES
-- Cada comando abaixo DEVE FALHAR. Execute com:
--   mysql -u root --force mercado_boturussu < sql/testes/08_testes_restricoes.sql
-- (--force continua após cada erro). O resultado obtido está em evidencias/07_testes_restricoes.md.
-- Cada teste está entre START TRANSACTION e ROLLBACK: nada é gravado.
-- =====================================================================
USE mercado_boturussu;
SET NAMES utf8mb4;

-- T01 — Cadastrar segundo funcionário com o mesmo CPF
-- Regra: CPF identifica uma única pessoa | Esperado: erro 1062 (uq_funcionario_cpf (UNIQUE))
START TRANSACTION;
INSERT INTO funcionario (cpf, login, nome, funcao_principal) SELECT cpf, 'outro.login', 'Pessoa Duplicada', 'CAIXA' FROM funcionario WHERE id_funcionario = 2;
ROLLBACK;

-- T02 — Produto em categoria que não existe
-- Regra: RN-01: todo produto pertence a um setor existente | Esperado: erro 1452 (fk_produto_categoria (FOREIGN KEY))
START TRANSACTION;
INSERT INTO produto (codigo_categoria, nome_produto, unidade_base) VALUES ('XXXX', 'Produto Fantasma', 'UN');
ROLLBACK;

-- T03 — Produto vendido por peso contado em unidade
-- Regra: RN-02: produto pesado é contado em quilo | Esperado: erro 3819 (ck_produto_peso_kg (CHECK))
START TRANSACTION;
INSERT INTO produto (codigo_categoria, nome_produto, unidade_base, vendido_por_peso) VALUES ('HORTI', 'Mamão (kg)', 'UN', TRUE);
ROLLBACK;

-- T04 — Embalagem sem nenhum código de leitura
-- Regra: RN-04: toda forma de venda é identificável no caixa | Esperado: erro 3819 (ck_embalagem_codigo (CHECK))
START TRANSACTION;
INSERT INTO embalagem (id_produto, descricao, fator_conversao, preco_venda) VALUES (1, 'Pacote sem código', 1, 30.00);
ROLLBACK;

-- T05 — Dois produtos com o mesmo código de barras
-- Regra: O código lido no caixa aponta para uma só embalagem | Esperado: erro 1062 (uq_embalagem_barras (UNIQUE))
START TRANSACTION;
INSERT INTO embalagem (id_produto, codigo_barras, descricao, fator_conversao, preco_venda) SELECT 2, codigo_barras, 'Duplicada', 1, 9.99 FROM embalagem WHERE id_embalagem = 1;
ROLLBACK;

-- T06 — Fator de conversão zero
-- Regra: D-01: vender fardo baixa a quantidade certa | Esperado: erro 3819 (ck_embalagem_fator (CHECK))
START TRANSACTION;
UPDATE embalagem SET fator_conversao = 0 WHERE id_embalagem = 1;
ROLLBACK;

-- T07 — Histórico de preço sem mudança de preço
-- Regra: RN-06: só se registra alteração real | Esperado: erro 3819 (ck_hp_precos (CHECK))
START TRANSACTION;
INSERT INTO historico_preco (id_embalagem, id_funcionario, preco_anterior, preco_novo, motivo) VALUES (1, 2, 32.90, 32.90, 'CORRECAO');
ROLLBACK;

-- T08 — Desconto em item de venda sem autorizador
-- Regra: RN-23: desconto só com autorização registrada | Esperado: erro 3819 (ck_iv_autorizacao (CHECK))
START TRANSACTION;
INSERT INTO item_venda (id_venda, numero_item, id_embalagem, quantidade, preco_unitario_praticado, desconto_unitario) VALUES (1, 99, 1, 1, 32.90, 5.00);
ROLLBACK;

-- T09 — Quantidade vendida negativa
-- Regra: Quantidade não pode ser negativa | Esperado: erro 3819 (ck_iv_qtd (CHECK))
START TRANSACTION;
INSERT INTO item_venda (id_venda, numero_item, id_embalagem, quantidade, preco_unitario_praticado) VALUES (1, 98, 1, -2, 32.90);
ROLLBACK;

-- T10 — Autorizar fiado para cliente sem CPF
-- Regra: RN-24 / PO-04: fiado exige cliente identificado | Esperado: erro 3819 (ck_cliente_fiado_cpf (CHECK))
START TRANSACTION;
INSERT INTO cliente (nome, autorizado_fiado, limite_fiado) VALUES ('Cliente Sem CPF', TRUE, 100.00);
ROLLBACK;

-- T11 — Pagar fiado com a forma FIADO
-- Regra: RN-27: fiado não paga fiado | Esperado: erro 3819 (ck_ab_forma (CHECK))
START TRANSACTION;
INSERT INTO abatimento_fiado (id_cliente, codigo_forma, id_funcionario, data_hora, valor) VALUES (1, 'FIADO', 2, '2026-10-01 10:00:00', 10.00);
ROLLBACK;

-- T12 — Pagamento por Pix sem NSU/ID da transação
-- Regra: RN-36: transação eletrônica precisa ser conciliável | Esperado: erro 3819 (ck_pv_nsu (CHECK))
START TRANSACTION;
INSERT INTO pagamento_venda (id_venda, numero_pagamento, codigo_forma, valor) VALUES (1, 9, 'PIX', 5.00);
ROLLBACK;

-- T13 — Registrar duas vezes a mesma transação de cartão
-- Regra: Impede duplicidade de recebíveis | Esperado: erro 1062 (uq_pv_nsu (UNIQUE))
START TRANSACTION;
INSERT INTO pagamento_venda (id_venda, numero_pagamento, codigo_forma, valor, nsu_autorizacao) SELECT 1, 9, codigo_forma, 1.00, nsu_autorizacao FROM pagamento_venda WHERE nsu_autorizacao IS NOT NULL LIMIT 1;
ROLLBACK;

-- T14 — Lançar a mesma nota fiscal duas vezes
-- Regra: RN-12: nota identificada por emitente, modelo, série e número | Esperado: erro 1062 (uq_recebimento_nota (UNIQUE))
START TRANSACTION;
INSERT INTO recebimento (id_fornecedor, id_funcionario, modelo_nota, serie_nota, numero_nota, data_hora, valor_total_nota, volumes_nota, volumes_conferidos, situacao) SELECT id_fornecedor, id_funcionario, modelo_nota, serie_nota, numero_nota, data_hora, valor_total_nota, volumes_nota, volumes_conferidos, situacao FROM recebimento WHERE id_recebimento = 1;
ROLLBACK;

-- T15 — Aceitar mais do que a nota faturou
-- Regra: RN-14: não se aceita mais do que foi faturado | Esperado: erro 3819 (ck_ir_aceita (CHECK))
START TRANSACTION;
UPDATE item_recebimento SET quantidade_aceita = quantidade_nota * fator_conversao_compra + 1 WHERE id_recebimento = 1 AND numero_item_nota = 1;
ROLLBACK;

-- T16 — Lote apontando para linha de nota de OUTRO produto
-- Regra: R19: produto do lote = produto da linha da nota | Esperado: erro 1452 (fk_lote_item_receb (FOREIGN KEY composta))
START TRANSACTION;
INSERT INTO lote (id_produto, id_recebimento, numero_item_nota, origem, data_entrada, custo_unitario) SELECT CASE WHEN ir.id_produto = 1 THEN 2 ELSE 1 END, ir.id_recebimento, ir.numero_item_nota, 'RECEBIMENTO', NOW(), 1.00 FROM item_recebimento ir WHERE ir.quantidade_aceita > 0 LIMIT 1;
ROLLBACK;

-- T17 — Lote de recebimento sem a linha da nota
-- Regra: RN-14: lote de nota nasce de uma linha | Esperado: erro 3819 (ck_lote_origem_nota (CHECK))
START TRANSACTION;
INSERT INTO lote (id_produto, origem, data_entrada, custo_unitario) VALUES (1, 'RECEBIMENTO', NOW(), 24.90);
ROLLBACK;

-- T18 — Linha da nota atendendo pedido de outro produto
-- Regra: R18: linha só atende item pedido do mesmo produto | Esperado: erro 1452 (fk_ir_item_pedido (FOREIGN KEY composta))
START TRANSACTION;
UPDATE item_recebimento SET id_pedido = (SELECT MIN(pc.id_pedido) FROM pedido_compra pc WHERE pc.id_pedido NOT IN (SELECT id_pedido FROM item_pedido WHERE id_produto = 38)) WHERE (id_recebimento, numero_item_nota) IN (SELECT * FROM (SELECT id_recebimento, numero_item_nota FROM item_recebimento WHERE id_produto = 38 LIMIT 1) x);
ROLLBACK;

-- T19 — Perda registrada sem responsável
-- Regra: RN-18: perda exige funcionário responsável | Esperado: erro 3819 (ck_me_responsavel (CHECK))
START TRANSACTION;
INSERT INTO movimentacao_estoque (id_lote, data_hora, tipo, quantidade, motivo) VALUES (1, NOW(), 'PERDA_AVARIA', 1, 'Quebrou');
ROLLBACK;

-- T20 — Baixa de venda sem apontar o item vendido
-- Regra: RN-17: toda baixa de venda aponta para o item | Esperado: erro 3819 (ck_me_venda (CHECK))
START TRANSACTION;
INSERT INTO movimentacao_estoque (id_lote, data_hora, tipo, quantidade) VALUES (1, NOW(), 'SAIDA_VENDA', 1);
ROLLBACK;

-- T21 — Fechar sessão sem contar o dinheiro
-- Regra: RN-30: fechamento exige contagem e responsável | Esperado: erro 3819 (ck_sessao_fechamento (CHECK))
START TRANSACTION;
INSERT INTO sessao_caixa (numero_caixa, id_funcionario_abertura, data_hora_abertura, valor_inicial, data_hora_fechamento) VALUES (1, 2, '2026-10-01 07:00:00', 150.00, '2026-10-01 14:00:00');
ROLLBACK;

-- T22 — Sangria que não chega ao cofre
-- Regra: RN-37: dinheiro que sai da gaveta fica registrado no cofre | Esperado: erro 3819 (ck_mc_cofre (CHECK))
START TRANSACTION;
INSERT INTO movimentacao_caixa (id_sessao, id_funcionario, data_hora, tipo, valor, motivo) VALUES (1, 2, '2026-09-01 10:00:00', 'SANGRIA', 300.00, 'Teste');
ROLLBACK;

-- T23 — Usar a mesma saída de dinheiro para dois pagamentos de conta
-- Regra: R46: cada pagamento corresponde a uma saída de dinheiro | Esperado: erro 1062 (uq_pc_movimento (UNIQUE))
START TRANSACTION;
INSERT INTO pagamento_conta (id_conta, numero_pagamento, id_funcionario, id_movimento_fin, data_pagamento, valor_principal) SELECT id_conta, 9, 1, id_movimento_fin, data_pagamento, 1.00 FROM pagamento_conta LIMIT 1;
ROLLBACK;

-- T24 — Repasse de cartão lançado como débito
-- Regra: Coerência entre origem e sentido do movimento | Esperado: erro 3819 (ck_mf_origem (CHECK))
START TRANSACTION;
INSERT INTO movimento_financeiro (id_conta_financeira, data_movimento, natureza, origem, valor_bruto) VALUES (1, '2026-10-01', 'DEBITO', 'REPASSE_CARTAO', 100.00);
ROLLBACK;

-- T25 — Devolução em dinheiro sem registrar a saída da gaveta
-- Regra: RN-28 / RN-37: reembolso em dinheiro aparece no caixa | Esperado: erro 3819 (ck_dev_dinheiro (CHECK))
START TRANSACTION;
INSERT INTO devolucao (id_venda, numero_item, id_funcionario, data_hora, quantidade_devolvida, motivo, destino, forma_reembolso, valor_reembolsado) VALUES (1, 1, 2, NOW(), 1, 'DEFEITO', 'DESCARTE', 'DINHEIRO', 5.00);
ROLLBACK;

-- T26 — Excluir produto que já tem embalagens, lotes e vendas
-- Regra: RNF-06 / PO-12: histórico não é apagado (FK sem CASCADE) | Esperado: erro 1451 (fk_embalagem_produto (RESTRICT))
START TRANSACTION;
DELETE FROM produto WHERE id_produto = 1;
ROLLBACK;

-- T27 — Excluir venda já registrada
-- Regra: RNF-06: venda é histórico; cancela-se por situação | Esperado: erro 1451 (fk_iv_venda (RESTRICT))
START TRANSACTION;
DELETE FROM venda WHERE id_venda = 1;
ROLLBACK;

-- T28 — Excluir item de pedido que já foi recebido
-- Regra: RN-11: o que chegou não some do pedido | Esperado: erro 1451 (fk_ir_item_pedido (RESTRICT))
START TRANSACTION;
DELETE ip FROM item_pedido ip JOIN item_recebimento ir ON ir.id_pedido = ip.id_pedido AND ir.id_produto = ip.id_produto;
ROLLBACK;

-- T29 — Fornecedor com CNPJ em formato inválido
-- Regra: Formato do documento (CNPJ alfanumérico desde 07/2026) | Esperado: erro 3819 (ck_fornecedor_doc (CHECK))
START TRANSACTION;
INSERT INTO fornecedor (tipo_documento, documento, razao_social, canal_pedido) VALUES ('CNPJ', '1234567/000199', 'Teste', 'WHATSAPP');
ROLLBACK;

-- T30 — Conta de despesa fixa apontando para nota de fornecedor
-- Regra: RN-32: só conta de fornecedor nasce de recebimento | Esperado: erro 3819 (ck_cp_origem (CHECK))
START TRANSACTION;
INSERT INTO conta_pagar (id_recebimento, credor, descricao, categoria_despesa, valor_original, data_vencimento) VALUES (1, 'Enel SP', 'Luz', 'LUZ', 100.00, '2026-10-20');
ROLLBACK;

-- T31 — Revogar uma permissão com data anterior à concessão
-- Regra: Histórico de permissões coerente (auditoria A13 depende dele) | Esperado: erro 3819 (ck_fp_periodo (CHECK))
START TRANSACTION;
UPDATE funcionario_permissao SET data_revogacao = DATE_SUB(data_concessao, INTERVAL 1 DAY) WHERE id_funcionario = 1 LIMIT 1;
ROLLBACK;

-- T32 — Linha de nota recusada com quantidade aceita
-- Regra: RN-14: situação da linha coerente com o aceito | Esperado: erro 3819 (ck_ir_situacao (CHECK))
START TRANSACTION;
UPDATE item_recebimento SET situacao_item = 'RECUSADO' WHERE quantidade_aceita > 0 LIMIT 1;
ROLLBACK;

