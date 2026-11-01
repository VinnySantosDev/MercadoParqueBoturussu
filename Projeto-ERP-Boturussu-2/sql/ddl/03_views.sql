-- =====================================================================
-- 03_views.sql — VIEWS dos atributos DERIVADOS
-- Decisão de projeto: nenhum valor calculável é gravado em tabela (3FN e
-- ausência de anomalias de atualização). Cada view abaixo implementa
-- atributos marcados como derivados (/nome) no DER.
-- Valores que dependem da data de hoje (dias para vencer, contas vencidas,
-- previsão) ficam nas consultas, que usam a data de referência @data_ref.
-- =====================================================================
SET NAMES utf8mb4;
USE mercado_boturussu;

-- ---------------------------------------------------------------------
-- Movimentação com sinal e valor de custo (kardex valorizado)
-- Derivado: MOVIMENTACAO_ESTOQUE.valor_custo = quantidade × custo do lote
-- ---------------------------------------------------------------------
CREATE VIEW vw_movimentacao_valorizada AS
SELECT m.id_movimentacao, m.id_lote, l.id_produto, m.tipo, m.data_hora,
       m.quantidade,
       CASE WHEN m.tipo IN ('ENTRADA_RECEBIMENTO','ENTRADA_INVENTARIO','TROCA_FORNECEDOR',
                            'DEVOLUCAO_CLIENTE','AJUSTE_INVENTARIO_ENTRADA') THEN 1 ELSE -1 END AS sinal,
       m.quantidade * CASE WHEN m.tipo IN ('ENTRADA_RECEBIMENTO','ENTRADA_INVENTARIO','TROCA_FORNECEDOR',
                            'DEVOLUCAO_CLIENTE','AJUSTE_INVENTARIO_ENTRADA') THEN 1 ELSE -1 END AS quantidade_com_sinal,
       ROUND(m.quantidade * l.custo_unitario, 2) AS valor_custo,
       m.id_venda, m.numero_item, m.id_devolucao, m.id_funcionario, m.motivo
FROM movimentacao_estoque m
JOIN lote l ON l.id_lote = m.id_lote;

-- ---------------------------------------------------------------------
-- Saldo por lote. Derivados: LOTE.quantidade_inicial, LOTE.quantidade_atual,
-- "esgotado" (antiga situação ESGOTADO, removida da tabela).
-- ---------------------------------------------------------------------
CREATE VIEW vw_lote_saldo AS
SELECT l.id_lote, l.id_produto, p.nome_produto, l.origem, l.data_validade, l.data_entrada,
       l.custo_unitario, l.situacao, l.pendente_conferencia, l.id_recebimento, l.numero_item_nota,
       COALESCE(SUM(CASE WHEN (l.origem = 'RECEBIMENTO'          AND m.tipo = 'ENTRADA_RECEBIMENTO')
                           OR (l.origem = 'INVENTARIO_INICIAL'   AND m.tipo = 'ENTRADA_INVENTARIO')
                           OR (l.origem = 'REPOSICAO_FORNECEDOR' AND m.tipo = 'TROCA_FORNECEDOR')
                           OR (l.origem = 'AJUSTE_INVENTARIO'    AND m.tipo = 'AJUSTE_INVENTARIO_ENTRADA')
                         THEN m.quantidade END), 0) AS quantidade_inicial,
       COALESCE(SUM(m.quantidade * CASE WHEN m.tipo IN ('ENTRADA_RECEBIMENTO','ENTRADA_INVENTARIO','TROCA_FORNECEDOR',
                            'DEVOLUCAO_CLIENTE','AJUSTE_INVENTARIO_ENTRADA') THEN 1 ELSE -1 END), 0) AS quantidade_atual,
       COUNT(m.id_movimentacao) AS qtd_movimentacoes
FROM lote l
JOIN produto p ON p.id_produto = l.id_produto
LEFT JOIN movimentacao_estoque m ON m.id_lote = l.id_lote
GROUP BY l.id_lote, l.id_produto, p.nome_produto, l.origem, l.data_validade, l.data_entrada,
         l.custo_unitario, l.situacao, l.pendente_conferencia, l.id_recebimento, l.numero_item_nota;

-- ---------------------------------------------------------------------
-- Estoque vendável por produto. Derivado: PRODUTO.estoque_atual
-- Só lotes DISPONIVEL contam (separado para troca não é vendável).
-- ---------------------------------------------------------------------
CREATE VIEW vw_estoque_produto AS
SELECT p.id_produto, p.nome_produto, p.codigo_categoria, p.unidade_base, p.estoque_minimo, p.ativo,
       COALESCE(SUM(CASE WHEN s.situacao = 'DISPONIVEL' THEN s.quantidade_atual END), 0) AS estoque_atual,
       COALESCE(SUM(CASE WHEN s.situacao = 'DISPONIVEL' THEN s.quantidade_atual * s.custo_unitario END), 0) AS valor_estoque_custo,
       CASE WHEN COALESCE(SUM(CASE WHEN s.situacao = 'DISPONIVEL' THEN s.quantidade_atual END), 0) < p.estoque_minimo
            THEN 1 ELSE 0 END AS abaixo_minimo
FROM produto p
LEFT JOIN vw_lote_saldo s ON s.id_produto = p.id_produto
GROUP BY p.id_produto, p.nome_produto, p.codigo_categoria, p.unidade_base, p.estoque_minimo, p.ativo;

-- ---------------------------------------------------------------------
-- Resultado por item vendido. Derivados: ITEM_VENDA.valor_item,
-- ITEM_VENDA.custo_total (soma dos lotes realmente baixados — RN-22),
-- ITEM_VENDA.custo_unitario_medio.
-- custo = saídas por venda − retornos de devolução + saídas de troca ao cliente
-- ---------------------------------------------------------------------
CREATE VIEW vw_item_venda_resultado AS
SELECT iv.id_venda, iv.numero_item, iv.id_embalagem, e.id_produto, v.data_hora, v.situacao AS situacao_venda,
       iv.quantidade, e.fator_conversao,
       iv.quantidade * e.fator_conversao AS quantidade_base,
       iv.preco_unitario_praticado, iv.desconto_unitario,
       ROUND(iv.quantidade * (iv.preco_unitario_praticado - iv.desconto_unitario), 2) AS valor_item,
       COALESCE(baixa.custo, 0) AS custo_baixado,
       COALESCE(dev.custo_retorno, 0) AS custo_devolvido,
       COALESCE(dev.custo_troca, 0) AS custo_troca,
       COALESCE(baixa.custo, 0) - COALESCE(dev.custo_retorno, 0) + COALESCE(dev.custo_troca, 0) AS custo_total,
       COALESCE(dev.qtd_devolvida, 0) AS quantidade_devolvida,
       COALESCE(dev.valor_reembolsado, 0) AS valor_reembolsado,
       COALESCE(baixa.qtd_lotes, 0) AS qtd_lotes_baixados
FROM item_venda iv
JOIN venda v ON v.id_venda = iv.id_venda
JOIN embalagem e ON e.id_embalagem = iv.id_embalagem
LEFT JOIN (SELECT m.id_venda, m.numero_item, SUM(m.quantidade * l.custo_unitario) AS custo,
                  COUNT(DISTINCT m.id_lote) AS qtd_lotes
           FROM movimentacao_estoque m JOIN lote l ON l.id_lote = m.id_lote
           WHERE m.tipo = 'SAIDA_VENDA'
           GROUP BY m.id_venda, m.numero_item) baixa
       ON baixa.id_venda = iv.id_venda AND baixa.numero_item = iv.numero_item
LEFT JOIN (SELECT d.id_venda, d.numero_item,
                  SUM(d.quantidade_devolvida) AS qtd_devolvida,
                  SUM(d.valor_reembolsado) AS valor_reembolsado,
                  SUM(COALESCE(mv.custo_retorno, 0)) AS custo_retorno,
                  SUM(COALESCE(mv.custo_troca, 0)) AS custo_troca
           FROM devolucao d
           LEFT JOIN (SELECT m.id_devolucao,
                             SUM(CASE WHEN m.tipo = 'DEVOLUCAO_CLIENTE' THEN m.quantidade * l.custo_unitario END) AS custo_retorno,
                             SUM(CASE WHEN m.tipo = 'SAIDA_TROCA_CLIENTE' THEN m.quantidade * l.custo_unitario END) AS custo_troca
                      FROM movimentacao_estoque m JOIN lote l ON l.id_lote = m.id_lote
                      WHERE m.id_devolucao IS NOT NULL
                      GROUP BY m.id_devolucao) mv ON mv.id_devolucao = d.id_devolucao
           GROUP BY d.id_venda, d.numero_item) dev
       ON dev.id_venda = iv.id_venda AND dev.numero_item = iv.numero_item;

-- ---------------------------------------------------------------------
-- Resumo por venda. Derivados: VENDA.valor_bruto, valor_desconto,
-- valor_total, custo_total, lucro_bruto.
-- ---------------------------------------------------------------------
CREATE VIEW vw_venda_resumo AS
SELECT v.id_venda, v.id_sessao, s.numero_caixa, v.id_funcionario, v.id_cliente, v.numero_cupom, v.data_hora, v.situacao,
       r.valor_bruto, r.valor_desconto, r.valor_total, COALESCE(pg.total_pago, 0) AS total_pago,
       r.custo_total, r.valor_reembolsado,
       r.valor_total - r.valor_reembolsado - r.custo_total AS lucro_bruto,
       r.qtd_itens
FROM venda v
JOIN sessao_caixa s ON s.id_sessao = v.id_sessao
JOIN (SELECT id_venda,
             ROUND(SUM(quantidade * preco_unitario_praticado), 2) AS valor_bruto,
             ROUND(SUM(quantidade * desconto_unitario), 2) AS valor_desconto,
             SUM(valor_item) AS valor_total,
             SUM(custo_total) AS custo_total,
             SUM(valor_reembolsado) AS valor_reembolsado,
             COUNT(*) AS qtd_itens
      FROM vw_item_venda_resultado GROUP BY id_venda) r ON r.id_venda = v.id_venda
LEFT JOIN (SELECT id_venda, SUM(valor) AS total_pago FROM pagamento_venda GROUP BY id_venda) pg
       ON pg.id_venda = v.id_venda;

-- ---------------------------------------------------------------------
-- Recebíveis. Derivados: PAGAMENTO_VENDA.troco, data_prevista_credito,
-- valor_liquido_previsto, situacao_credito.
-- ---------------------------------------------------------------------
CREATE VIEW vw_pagamento_venda_previsao AS
SELECT pv.id_venda, pv.numero_pagamento, pv.codigo_forma, v.data_hora AS data_venda, v.situacao AS situacao_venda,
       pv.valor, pv.valor_entregue,
       CASE WHEN pv.valor_entregue IS NULL THEN 0 ELSE pv.valor_entregue - pv.valor END AS troco,
       pv.nsu_autorizacao,
       DATE_ADD(DATE(v.data_hora), INTERVAL f.prazo_credito_dias DAY) AS data_prevista_credito,
       ROUND(pv.valor * (1 - f.taxa_percentual / 100), 2) AS valor_liquido_previsto,
       pv.id_movimento_fin,
       CASE WHEN f.exige_conciliacao = FALSE THEN 'NAO_SE_APLICA'
            WHEN pv.id_movimento_fin IS NULL THEN 'PENDENTE'
            ELSE 'CONCILIADO' END AS situacao_credito
FROM pagamento_venda pv
JOIN venda v ON v.id_venda = pv.id_venda
JOIN forma_pagamento f ON f.codigo_forma = pv.codigo_forma;

-- ---------------------------------------------------------------------
-- Conferência da sessão de caixa (FECHAMENTO). Derivados:
-- SESSAO_CAIXA.situacao, valor_esperado, diferenca_dinheiro,
-- total_eletronico_registrado, diferenca_eletronica.
-- valor_esperado = dinheiro que deveria estar na gaveta NO MOMENTO DA CONTAGEM:
--   fundo + vendas em dinheiro (líquidas de troco) + abatimentos em dinheiro
--   + suprimentos − sangrias − reembolsos em dinheiro.
-- O recolhimento acontece depois da contagem e por isso não entra.
-- ---------------------------------------------------------------------
CREATE VIEW vw_sessao_conferencia AS
SELECT s.id_sessao, s.numero_caixa, s.id_funcionario_abertura, s.id_funcionario_fechamento,
       s.data_hora_abertura, s.data_hora_fechamento,
       CASE WHEN s.data_hora_fechamento IS NULL THEN 'ABERTA' ELSE 'FECHADA' END AS situacao,
       s.valor_inicial,
       COALESCE(vd.dinheiro, 0) AS vendas_dinheiro,
       COALESCE(ab.dinheiro, 0) AS abatimentos_dinheiro,
       COALESCE(mc.suprimentos, 0) AS suprimentos,
       COALESCE(mc.sangrias, 0) AS sangrias,
       COALESCE(mc.reembolsos, 0) AS reembolsos,
       COALESCE(mc.recolhido, 0) AS recolhido_fechamento,
       s.valor_inicial + COALESCE(vd.dinheiro, 0) + COALESCE(ab.dinheiro, 0) + COALESCE(mc.suprimentos, 0)
         - COALESCE(mc.sangrias, 0) - COALESCE(mc.reembolsos, 0) AS valor_esperado,
       s.valor_contado,
       s.valor_contado - (s.valor_inicial + COALESCE(vd.dinheiro, 0) + COALESCE(ab.dinheiro, 0) + COALESCE(mc.suprimentos, 0)
         - COALESCE(mc.sangrias, 0) - COALESCE(mc.reembolsos, 0)) AS diferenca_dinheiro,
       COALESCE(vd.eletronico, 0) AS total_eletronico_registrado,
       s.total_maquininhas_informado,
       s.total_maquininhas_informado - COALESCE(vd.eletronico, 0) AS diferenca_eletronica,
       s.justificativa_diferenca
FROM sessao_caixa s
LEFT JOIN (SELECT v.id_sessao,
                  SUM(CASE WHEN pv.codigo_forma = 'DIN' THEN pv.valor END) AS dinheiro,
                  SUM(CASE WHEN f.exige_conciliacao THEN pv.valor END) AS eletronico
           FROM venda v JOIN pagamento_venda pv ON pv.id_venda = v.id_venda
           JOIN forma_pagamento f ON f.codigo_forma = pv.codigo_forma
           WHERE v.situacao = 'CONCLUIDA'
           GROUP BY v.id_sessao) vd ON vd.id_sessao = s.id_sessao
LEFT JOIN (SELECT id_sessao, SUM(valor) AS dinheiro FROM abatimento_fiado
           WHERE codigo_forma = 'DIN' GROUP BY id_sessao) ab ON ab.id_sessao = s.id_sessao
LEFT JOIN (SELECT id_sessao,
                  SUM(CASE WHEN tipo = 'SUPRIMENTO' THEN valor END) AS suprimentos,
                  SUM(CASE WHEN tipo = 'SANGRIA' THEN valor END) AS sangrias,
                  SUM(CASE WHEN tipo = 'REEMBOLSO_DEVOLUCAO' THEN valor END) AS reembolsos,
                  SUM(CASE WHEN tipo = 'RECOLHIMENTO_FECHAMENTO' THEN valor END) AS recolhido
           FROM movimentacao_caixa GROUP BY id_sessao) mc ON mc.id_sessao = s.id_sessao;

-- ---------------------------------------------------------------------
-- Conta corrente do fiado. Derivado: CLIENTE.saldo_devedor (RN-26)
-- ---------------------------------------------------------------------
CREATE VIEW vw_cliente_saldo AS
SELECT c.id_cliente, c.nome, c.apelido, c.autorizado_fiado, c.limite_fiado,
       COALESCE(fi.total_fiado, 0) AS total_fiado,
       COALESCE(ab.total_abatido, 0) AS total_abatido,
       COALESCE(dv.total_devolvido, 0) AS total_devolvido_fiado,
       COALESCE(fi.total_fiado, 0) - COALESCE(ab.total_abatido, 0) - COALESCE(dv.total_devolvido, 0) AS saldo_devedor,
       fi.primeira_compra_fiado, fi.ultima_compra_fiado, ab.ultimo_abatimento
FROM cliente c
LEFT JOIN (SELECT v.id_cliente, SUM(pv.valor) AS total_fiado, MIN(v.data_hora) AS primeira_compra_fiado, MAX(v.data_hora) AS ultima_compra_fiado
           FROM venda v JOIN pagamento_venda pv ON pv.id_venda = v.id_venda
           WHERE pv.codigo_forma = 'FIADO' AND v.situacao = 'CONCLUIDA'
           GROUP BY v.id_cliente) fi ON fi.id_cliente = c.id_cliente
LEFT JOIN (SELECT id_cliente, SUM(valor) AS total_abatido, MAX(data_hora) AS ultimo_abatimento
           FROM abatimento_fiado GROUP BY id_cliente) ab ON ab.id_cliente = c.id_cliente
LEFT JOIN (SELECT v.id_cliente, SUM(d.valor_reembolsado) AS total_devolvido
           FROM devolucao d JOIN venda v ON v.id_venda = d.id_venda
           WHERE d.forma_reembolso = 'ABATER_FIADO'
           GROUP BY v.id_cliente) dv ON dv.id_cliente = c.id_cliente;

-- ---------------------------------------------------------------------
-- Situação das contas a pagar. Derivados: CONTA_PAGAR.valor_principal_pago,
-- encargos_pagos, saldo_em_aberto, situacao (RN-38).
-- ---------------------------------------------------------------------
CREATE VIEW vw_conta_pagar_situacao AS
SELECT cp.id_conta, cp.id_recebimento, cp.credor, cp.numero_documento, cp.numero_parcela, cp.descricao,
       cp.categoria_despesa, cp.valor_original, cp.data_vencimento, cp.prioridade, cp.cancelada,
       COALESCE(pg.principal, 0) AS valor_principal_pago,
       COALESCE(pg.encargos, 0) AS encargos_pagos,
       COALESCE(pg.descontos, 0) AS descontos_obtidos,
       cp.valor_original - COALESCE(pg.principal, 0) AS saldo_em_aberto,
       COALESCE(pg.qtd, 0) AS qtd_pagamentos,
       pg.ultimo_pagamento,
       CASE WHEN cp.cancelada THEN 'CANCELADA'
            WHEN COALESCE(pg.principal, 0) >= cp.valor_original THEN 'PAGA'
            WHEN COALESCE(pg.principal, 0) > 0 THEN 'PARCIALMENTE_PAGA'
            ELSE 'ABERTA' END AS situacao
FROM conta_pagar cp
LEFT JOIN (SELECT id_conta, SUM(valor_principal) AS principal, SUM(valor_juros_multa) AS encargos,
                  SUM(valor_desconto) AS descontos, COUNT(*) AS qtd, MAX(data_pagamento) AS ultimo_pagamento
           FROM pagamento_conta GROUP BY id_conta) pg ON pg.id_conta = cp.id_conta;

-- ---------------------------------------------------------------------
-- Saldo realizado das contas financeiras. Derivado: CONTA_FINANCEIRA.saldo_atual
-- ---------------------------------------------------------------------
CREATE VIEW vw_conta_financeira_saldo AS
SELECT cf.id_conta_financeira, cf.nome, cf.tipo, cf.saldo_inicial, cf.data_saldo_inicial,
       COALESCE(SUM(CASE WHEN mf.natureza = 'CREDITO' THEN mf.valor_bruto - mf.valor_taxa END), 0) AS total_creditos,
       COALESCE(SUM(CASE WHEN mf.natureza = 'DEBITO' THEN mf.valor_bruto + mf.valor_taxa END), 0) AS total_debitos,
       cf.saldo_inicial
         + COALESCE(SUM(CASE WHEN mf.natureza = 'CREDITO' THEN mf.valor_bruto - mf.valor_taxa END), 0)
         - COALESCE(SUM(CASE WHEN mf.natureza = 'DEBITO' THEN mf.valor_bruto + mf.valor_taxa END), 0) AS saldo_atual
FROM conta_financeira cf
LEFT JOIN movimento_financeiro mf ON mf.id_conta_financeira = cf.id_conta_financeira
GROUP BY cf.id_conta_financeira, cf.nome, cf.tipo, cf.saldo_inicial, cf.data_saldo_inicial;

-- ---------------------------------------------------------------------
-- CONCILIAÇÃO. Derivados: MOVIMENTO_FINANCEIRO.valor_liquido,
-- valor_previsto_vinculado, diferenca_conciliacao, situacao_conciliacao (RN-36).
-- previsto = Σ valor − taxa contratada sobre o total das transações liquidadas
-- ---------------------------------------------------------------------
CREATE VIEW vw_conciliacao AS
SELECT mf.id_movimento_fin, mf.id_conta_financeira, mf.data_movimento, mf.origem, mf.documento_referencia,
       mf.valor_bruto, mf.valor_taxa, mf.valor_bruto - mf.valor_taxa AS valor_liquido,
       COALESCE(t.qtd, 0) AS qtd_transacoes,
       COALESCE(t.bruto_previsto, 0) AS bruto_previsto,
       COALESCE(t.taxa_prevista, 0) AS taxa_prevista,
       COALESCE(t.bruto_previsto, 0) - COALESCE(t.taxa_prevista, 0) AS valor_previsto_vinculado,
       (mf.valor_bruto - mf.valor_taxa) - (COALESCE(t.bruto_previsto, 0) - COALESCE(t.taxa_prevista, 0)) AS diferenca_conciliacao,
       CASE WHEN t.qtd IS NULL THEN 'SEM_VINCULO'
            WHEN (mf.valor_bruto - mf.valor_taxa) = (t.bruto_previsto - t.taxa_prevista) THEN 'CONCILIADO'
            ELSE 'DIVERGENTE' END AS situacao_conciliacao
FROM movimento_financeiro mf
LEFT JOIN (SELECT x.id_movimento_fin, COUNT(*) AS qtd, SUM(x.valor) AS bruto_previsto,
                  ROUND(SUM(x.valor * x.taxa / 100), 2) AS taxa_prevista
           FROM (SELECT pv.id_movimento_fin, pv.valor, f.taxa_percentual AS taxa
                 FROM pagamento_venda pv JOIN forma_pagamento f ON f.codigo_forma = pv.codigo_forma
                 WHERE pv.id_movimento_fin IS NOT NULL
                 UNION ALL
                 SELECT a.id_movimento_fin, a.valor, f.taxa_percentual
                 FROM abatimento_fiado a JOIN forma_pagamento f ON f.codigo_forma = a.codigo_forma
                 WHERE a.id_movimento_fin IS NOT NULL) x
           GROUP BY x.id_movimento_fin) t ON t.id_movimento_fin = mf.id_movimento_fin
WHERE mf.natureza = 'CREDITO' AND mf.origem IN ('REPASSE_CARTAO','PIX_RECEBIDO');

-- ---------------------------------------------------------------------
-- Pendências de compra por item. Derivados: ITEM_PEDIDO.quantidade_recebida,
-- quantidade_pendente (RN-11).
-- ---------------------------------------------------------------------
CREATE VIEW vw_item_pedido_pendencia AS
SELECT ip.id_pedido, ip.id_produto, p.nome_produto, ip.quantidade_pedida, ip.preco_negociado,
       COALESCE(SUM(ir.quantidade_aceita), 0) AS quantidade_recebida,
       GREATEST(ip.quantidade_pedida - COALESCE(SUM(ir.quantidade_aceita), 0), 0) AS quantidade_pendente
FROM item_pedido ip
JOIN produto p ON p.id_produto = ip.id_produto
LEFT JOIN item_recebimento ir ON ir.id_pedido = ip.id_pedido AND ir.id_produto = ip.id_produto
GROUP BY ip.id_pedido, ip.id_produto, p.nome_produto, ip.quantidade_pedida, ip.preco_negociado;

-- ---------------------------------------------------------------------
-- Situação do pedido. Derivados: PEDIDO_COMPRA.situacao (ABERTO,
-- PARCIALMENTE_RECEBIDO, RECEBIDO, CANCELADO) e valor_previsto (RN-11).
-- ---------------------------------------------------------------------
CREATE VIEW vw_pedido_situacao AS
SELECT pc.id_pedido, pc.id_fornecedor, f.razao_social, pc.data_hora_pedido, pc.canal, pc.cancelado,
       COUNT(*) AS qtd_itens,
       SUM(CASE WHEN x.quantidade_pendente > 0 THEN 1 ELSE 0 END) AS itens_pendentes,
       ROUND(SUM(x.quantidade_pedida * COALESCE(x.preco_negociado, 0)), 2) AS valor_previsto,
       CASE WHEN pc.cancelado THEN 'CANCELADO'
            WHEN SUM(x.quantidade_pendente) = 0 THEN 'RECEBIDO'
            WHEN SUM(x.quantidade_recebida) > 0 THEN 'PARCIALMENTE_RECEBIDO'
            ELSE 'ABERTO' END AS situacao
FROM pedido_compra pc
JOIN fornecedor f ON f.id_fornecedor = pc.id_fornecedor
JOIN vw_item_pedido_pendencia x ON x.id_pedido = pc.id_pedido
GROUP BY pc.id_pedido, pc.id_fornecedor, f.razao_social, pc.data_hora_pedido, pc.canal, pc.cancelado;

-- ---------------------------------------------------------------------
-- Último custo por par fornecedor–produto.
-- Derivados: FORNECE.preco_ultima_compra e data_ultima_compra (antes gravados;
-- removidos da tabela na normalização porque são consequência dos recebimentos).
-- ---------------------------------------------------------------------
CREATE VIEW vw_ultimo_custo_fornecedor AS
SELECT id_fornecedor, id_produto, data_ultima_compra, custo_unitario_base AS preco_ultima_compra
FROM (SELECT r.id_fornecedor, ir.id_produto, DATE(r.data_hora) AS data_ultima_compra,
             ROUND(ir.valor_unitario_nota / ir.fator_conversao_compra, 4) AS custo_unitario_base,
             ROW_NUMBER() OVER (PARTITION BY r.id_fornecedor, ir.id_produto
                                ORDER BY r.data_hora DESC, ir.numero_item_nota DESC) AS rn
      FROM item_recebimento ir
      JOIN recebimento r ON r.id_recebimento = ir.id_recebimento
      WHERE ir.quantidade_aceita > 0 AND ir.valor_unitario_nota > 0) u
WHERE rn = 1;
