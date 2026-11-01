-- =====================================================================
-- 07_operacoes_update_delete.sql — UPDATE e DELETE em processos reais
-- Cenário: manhã de 01/10/2026. O gerente rodou as consultas gerenciais (05)
-- e de auditoria (06) e agora age sobre o que elas mostraram.
-- Cada operação: (1) SELECT do “antes”, (2) alteração dentro de transação,
-- (3) SELECT do “depois”. Nenhum identificador é fixo no código: as linhas
-- são localizadas pelas mesmas regras das consultas, como faria o sistema.
-- Registros operacionais NÃO são apagados (RNF-06, PO-12); DELETE só é
-- usado em dados cadastrais ou planejados que ainda não geraram efeito (OP07, OP08).
-- =====================================================================
USE mercado_boturussu;
SET NAMES utf8mb4;
SET @data_ref = DATE('2026-10-01');

-- ---------------------------------------------------------------------
-- OP01 (UPDATE) — Conferência do lote de ajuste automático do Guaraná (achado A11, RN-40)
-- A contagem no depósito encontrou 10 garrafas além do sistema. Registra-se
-- a entrada do ajuste (INSERT na movimentação) e o lote deixa de estar pendente.
-- ---------------------------------------------------------------------
SET @lote_pend = (SELECT l.id_lote FROM lote l JOIN produto p ON p.id_produto = l.id_produto
                  WHERE l.pendente_conferencia = TRUE AND p.nome_produto LIKE 'Refrigerante Guaraná%' LIMIT 1);
SELECT 'OP01 antes' AS etapa, id_lote, nome_produto, pendente_conferencia, quantidade_atual, data_validade
FROM vw_lote_saldo WHERE id_lote = @lote_pend;

START TRANSACTION;
INSERT INTO movimentacao_estoque (id_lote, id_funcionario, data_hora, tipo, quantidade, motivo)
VALUES (@lote_pend, 1, '2026-10-01 07:40:00', 'AJUSTE_INVENTARIO_ENTRADA', 10,
        'Conferência do ajuste RN-40: 10 garrafas encontradas no depósito');
UPDATE lote
   SET pendente_conferencia = FALSE,
       data_validade = '2027-01-20'          -- validade lida nas garrafas durante a conferência
 WHERE id_lote = @lote_pend;
COMMIT;

SELECT 'OP01 depois' AS etapa, id_lote, nome_produto, pendente_conferencia, quantidade_atual, data_validade
FROM vw_lote_saldo WHERE id_lote = @lote_pend;

-- ---------------------------------------------------------------------
-- OP02 (UPDATE) — Lote de margarina sem validade (achado A05, RN-15)
-- A validade foi lida na embalagem e lançada. O lote passa a aparecer na lista de validades.
-- ---------------------------------------------------------------------
SET @lote_sem_val = (SELECT l.id_lote FROM lote l JOIN produto p ON p.id_produto = l.id_produto
                     WHERE p.controla_validade = TRUE AND l.data_validade IS NULL
                       AND p.nome_produto LIKE 'Margarina%' LIMIT 1);
SELECT 'OP02 antes' AS etapa, id_lote, data_validade FROM lote WHERE id_lote = @lote_sem_val;
UPDATE lote SET data_validade = '2026-10-04' WHERE id_lote = @lote_sem_val;
SELECT 'OP02 depois' AS etapa, id_lote, data_validade FROM lote WHERE id_lote = @lote_sem_val;

-- ---------------------------------------------------------------------
-- OP03 (UPDATE) — Justificar as diferenças de caixa sem explicação (achado A06, RN-30)
-- ---------------------------------------------------------------------
SELECT 'OP03 antes' AS etapa, id_sessao, numero_caixa, diferenca_dinheiro, diferenca_eletronica, justificativa_diferenca
FROM vw_sessao_conferencia
WHERE situacao = 'FECHADA' AND (diferenca_dinheiro <> 0 OR diferenca_eletronica <> 0) AND justificativa_diferenca IS NULL;

START TRANSACTION;
UPDATE sessao_caixa s
JOIN vw_sessao_conferencia sc ON sc.id_sessao = s.id_sessao
   SET s.justificativa_diferenca = 'Sobra de R$ 1,00: moeda deixada por cliente; conferido pelo gerente em 01/10'
 WHERE sc.diferenca_dinheiro = 1.00 AND s.justificativa_diferenca IS NULL;
UPDATE sessao_caixa s
JOIN vw_sessao_conferencia sc ON sc.id_sessao = s.id_sessao
   SET s.justificativa_diferenca = 'Venda de R$ 15,00 passada no débito e registrada como dinheiro; corrigido no relatório'
 WHERE sc.diferenca_eletronica = 15.00 AND s.justificativa_diferenca IS NULL;
COMMIT;

SELECT 'OP03 depois' AS etapa, COUNT(*) AS sessoes_sem_justificativa
FROM vw_sessao_conferencia
WHERE situacao = 'FECHADA' AND (diferenca_dinheiro <> 0 OR diferenca_eletronica <> 0) AND justificativa_diferenca IS NULL;

-- ---------------------------------------------------------------------
-- OP04 (INSERT + efeito no saldo) — Quitar a parcela vencida do frigorífico com juros (achado A09, RN-38)
-- O pagamento sai do banco: primeiro o movimento financeiro, depois o pagamento que aponta para ele.
-- ---------------------------------------------------------------------
SET @conta_vencida = (SELECT id_conta FROM vw_conta_pagar_situacao
                      WHERE situacao = 'ABERTA' AND data_vencimento < @data_ref AND credor LIKE 'Frigorífico%'
                      ORDER BY data_vencimento LIMIT 1);
SELECT 'OP04 antes' AS etapa, id_conta, credor, data_vencimento, valor_original, saldo_em_aberto, situacao
FROM vw_conta_pagar_situacao WHERE id_conta = @conta_vencida;

START TRANSACTION;
SET @saldo = (SELECT saldo_em_aberto FROM vw_conta_pagar_situacao WHERE id_conta = @conta_vencida);
SET @juros = ROUND(@saldo * (0.02 + 0.00033 * DATEDIFF(@data_ref,
                  (SELECT data_vencimento FROM conta_pagar WHERE id_conta = @conta_vencida))), 2);
INSERT INTO movimento_financeiro (id_conta_financeira, id_funcionario, data_movimento, natureza, origem,
                                  valor_bruto, valor_taxa, documento_referencia)
VALUES ((SELECT id_conta_financeira FROM conta_financeira WHERE tipo = 'CONTA_BANCARIA' LIMIT 1), 1, @data_ref,
        'DEBITO', 'PAGAMENTO_CONTA', @saldo + @juros, 0, CONCAT('PGTO-', LPAD(@conta_vencida, 4, '0'), '-ATRASO'));
SET @mov = LAST_INSERT_ID();
INSERT INTO pagamento_conta (id_conta, numero_pagamento, id_funcionario, id_movimento_fin, data_pagamento,
                             valor_principal, valor_juros_multa, valor_desconto, observacao)
VALUES (@conta_vencida,
        (SELECT COALESCE(MAX(pc.numero_pagamento), 0) + 1 FROM pagamento_conta pc WHERE pc.id_conta = @conta_vencida),
        1, @mov, @data_ref, @saldo, @juros, 0, 'Quitação com atraso (multa 2% + juros diários)');
COMMIT;

SELECT 'OP04 depois' AS etapa, id_conta, valor_original, valor_principal_pago, encargos_pagos, saldo_em_aberto, situacao
FROM vw_conta_pagar_situacao WHERE id_conta = @conta_vencida;

-- ---------------------------------------------------------------------
-- OP05 (UPDATE com histórico) — Reajuste do leite pela política de preço (RN-05, RN-06, RN-07)
-- Toda alteração de preço grava o histórico NA MESMA TRANSAÇÃO: ou as duas coisas acontecem, ou nenhuma.
-- ---------------------------------------------------------------------
SET @emb_leite = (SELECT e.id_embalagem FROM embalagem e JOIN produto p ON p.id_produto = e.id_produto
                  WHERE p.nome_produto LIKE 'Leite Integral%' AND e.fator_conversao = 1 LIMIT 1);
SELECT 'OP05 antes' AS etapa, id_embalagem, descricao, preco_venda FROM embalagem WHERE id_embalagem = @emb_leite;

START TRANSACTION;
INSERT INTO historico_preco (id_embalagem, id_funcionario, data_hora, preco_anterior, preco_novo, motivo)
SELECT id_embalagem, 2, '2026-10-01 08:00:00', preco_venda, 6.49, 'REAJUSTE_FORNECEDOR'
FROM embalagem WHERE id_embalagem = @emb_leite;
UPDATE embalagem SET preco_venda = 6.49 WHERE id_embalagem = @emb_leite;
COMMIT;

SELECT 'OP05 depois' AS etapa, e.id_embalagem, e.preco_venda, h.preco_anterior, h.preco_novo, h.motivo, h.data_hora
FROM embalagem e JOIN historico_preco h ON h.id_embalagem = e.id_embalagem
WHERE e.id_embalagem = @emb_leite ORDER BY h.data_hora DESC LIMIT 1;

-- ---------------------------------------------------------------------
-- OP06 (UPDATE) — Gerente reduz o limite de quem nunca pagou o fiado (achado G07, PO-04)
-- Chico comprou fiado, nunca abateu nada e já usa 99% do limite. O gerente baixa o limite para
-- R$ 100,00: a dívida continua registrada, mas novas compras fiadas ficam bloqueadas até ele pagar
-- parte do saldo (RN-25). A autorização não é retirada para não perder o histórico de crédito.
-- ---------------------------------------------------------------------
SELECT 'OP06 antes' AS etapa, id_cliente, nome, apelido, limite_fiado, saldo_devedor, ultimo_abatimento
FROM vw_cliente_saldo WHERE apelido = 'Chico';
UPDATE cliente SET limite_fiado = 100.00 WHERE apelido = 'Chico' AND autorizado_fiado = TRUE;
SELECT 'OP06 depois' AS etapa, id_cliente, nome, apelido, limite_fiado, saldo_devedor,
       CASE WHEN saldo_devedor > limite_fiado THEN 'Acima do limite — novas compras fiadas bloqueadas' ELSE 'Dentro do limite' END AS efeito
FROM vw_cliente_saldo WHERE apelido = 'Chico';

-- ---------------------------------------------------------------------
-- OP07 (DELETE) — Vendedor saiu da distribuidora: remover o contato e cadastrar o novo
-- Contato é dado cadastral (não é histórico operacional), por isso pode ser excluído.
-- ---------------------------------------------------------------------
SELECT 'OP07 antes' AS etapa, cf.* FROM contato_fornecedor cf JOIN fornecedor f ON f.id_fornecedor = cf.id_fornecedor
WHERE f.nome_fantasia = 'Bebidas Leste';
START TRANSACTION;
DELETE cf FROM contato_fornecedor cf JOIN fornecedor f ON f.id_fornecedor = cf.id_fornecedor
WHERE f.nome_fantasia = 'Bebidas Leste' AND cf.nome = 'Fábio Martins';
INSERT INTO contato_fornecedor (id_fornecedor, numero_contato, nome, telefone, usa_whatsapp)
SELECT id_fornecedor, 3, 'Renata Siqueira', '11940010011', TRUE FROM fornecedor WHERE nome_fantasia = 'Bebidas Leste';
COMMIT;
SELECT 'OP07 depois' AS etapa, cf.* FROM contato_fornecedor cf JOIN fornecedor f ON f.id_fornecedor = cf.id_fornecedor
WHERE f.nome_fantasia = 'Bebidas Leste';

-- ---------------------------------------------------------------------
-- OP08 (DELETE) — Retirar do pedido em aberto um item que ainda não chegou (RN-11)
-- Motivo: o vendedor avisou que está sem Sabão em Pó Omo; o item sai do pedido para ser comprado de outro fornecedor.
-- Só é permitido porque nenhuma linha de nota atende esse item: a FK
-- fk_ir_item_pedido bloquearia a exclusão de item já recebido.
-- ---------------------------------------------------------------------
SET @ped_aberto = (SELECT id_pedido FROM vw_pedido_situacao WHERE situacao = 'ABERTO' ORDER BY data_hora_pedido DESC LIMIT 1);
SET @prod_retirar = (SELECT x.id_produto FROM vw_item_pedido_pendencia x WHERE x.id_pedido = @ped_aberto
                     AND x.quantidade_recebida = 0 AND x.nome_produto LIKE 'Sabão em Pó%' LIMIT 1);
SELECT 'OP08 antes' AS etapa, id_pedido, nome_produto, quantidade_pedida, quantidade_recebida
FROM vw_item_pedido_pendencia WHERE id_pedido = @ped_aberto;
DELETE FROM item_pedido
 WHERE id_pedido = @ped_aberto AND id_produto = @prod_retirar
   AND NOT EXISTS (SELECT 1 FROM item_recebimento ir WHERE ir.id_pedido = @ped_aberto AND ir.id_produto = @prod_retirar);
SELECT 'OP08 depois' AS etapa, id_pedido, nome_produto, quantidade_pedida, quantidade_recebida
FROM vw_item_pedido_pendencia WHERE id_pedido = @ped_aberto;

-- ---------------------------------------------------------------------
-- OP09 (UPDATE, não DELETE) — Revogar permissão: após o preço errado de 17/09 (achado A15), o gerente
-- decidiu que apenas ele e Mariana alteram preço. A linha NÃO é apagada: grava-se a data de revogação.
-- Motivo (decisão D-24): se a linha fosse excluída, a auditoria A13 passaria a acusar como
-- “sem permissão” as alterações que Rafael fez quando ainda podia — o passado ficaria errado.
-- ---------------------------------------------------------------------
SELECT 'OP09 antes' AS etapa, f.nome, fp.codigo_permissao, fp.data_concessao, fp.data_revogacao
FROM funcionario_permissao fp JOIN funcionario f ON f.id_funcionario = fp.id_funcionario
WHERE fp.codigo_permissao = 'ALTERAR_PRECO';
UPDATE funcionario_permissao fp JOIN funcionario f ON f.id_funcionario = fp.id_funcionario
   SET fp.data_revogacao = @data_ref
 WHERE fp.codigo_permissao = 'ALTERAR_PRECO' AND f.login = 'rafael.dias' AND fp.data_revogacao IS NULL;
SELECT 'OP09 depois' AS etapa, f.nome, fp.codigo_permissao, fp.data_concessao, fp.data_revogacao,
       CASE WHEN fp.data_revogacao IS NULL THEN 'vigente' ELSE 'revogada' END AS situacao
FROM funcionario_permissao fp JOIN funcionario f ON f.id_funcionario = fp.id_funcionario
WHERE fp.codigo_permissao = 'ALTERAR_PRECO';

-- ---------------------------------------------------------------------
-- Reexecução das auditorias afetadas: comprova que as ações resolveram os achados
-- ---------------------------------------------------------------------
SELECT 'A05 depois' AS auditoria, COUNT(*) AS ocorrencias FROM vw_lote_saldo s JOIN produto p ON p.id_produto = s.id_produto
WHERE p.controla_validade = TRUE AND s.data_validade IS NULL AND s.pendente_conferencia = FALSE
UNION ALL
SELECT 'A06 depois', COUNT(*) FROM vw_sessao_conferencia
WHERE situacao = 'FECHADA' AND (diferenca_dinheiro <> 0 OR diferenca_eletronica <> 0) AND justificativa_diferenca IS NULL
UNION ALL
SELECT 'A09 depois (vencidas sem nenhum pagamento)', COUNT(*) FROM vw_conta_pagar_situacao
WHERE situacao = 'ABERTA' AND data_vencimento < @data_ref
UNION ALL
SELECT 'A11 depois', COUNT(*) FROM lote WHERE pendente_conferencia = TRUE;
