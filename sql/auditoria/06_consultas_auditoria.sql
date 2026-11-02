-- =====================================================================
-- 06_consultas_auditoria.sql — CONSULTAS DE AUDITORIA
-- Objetivo: verificar a QUALIDADE e a CONSISTÊNCIA dos dados.
-- Cada consulta lista as linhas que merecem verificação. Resultado vazio
-- significa que a regra foi respeitada em todo o banco.
-- Regras entre várias linhas/tabelas não cabem em CHECK; por isso são
-- verificadas aqui (decisão D-20 do documento).
-- =====================================================================
USE mercado_boturussu;
SET NAMES utf8mb4;
SET @data_ref = DATE('2026-10-01');

-- ---------------------------------------------------------------------
-- A01 — Vendas concluídas cujo total não bate com a soma dos pagamentos (RN-21)
-- Verifica: venda paga a menos ou a mais (erro de caixa ou de registro).
-- ---------------------------------------------------------------------
SELECT v.id_venda, v.numero_caixa, v.numero_cupom, v.data_hora, v.valor_total, v.total_pago,
       v.total_pago - v.valor_total AS diferenca
FROM vw_venda_resumo v
WHERE v.situacao = 'CONCLUIDA' AND v.total_pago <> v.valor_total;

-- ---------------------------------------------------------------------
-- A02 — Itens de venda concluída sem baixa completa de estoque (RN-17, RN-22)
-- Verifica: item cuja quantidade vendida (na unidade base) não foi toda baixada
-- dos lotes — o estoque e o custo da venda estariam errados.
-- ---------------------------------------------------------------------
SELECT r.id_venda, r.numero_item, p.nome_produto, r.quantidade_base,
       COALESCE(SUM(m.quantidade), 0) AS quantidade_baixada
FROM vw_item_venda_resultado r
JOIN produto p ON p.id_produto = r.id_produto
LEFT JOIN movimentacao_estoque m ON m.id_venda = r.id_venda AND m.numero_item = r.numero_item AND m.tipo = 'SAIDA_VENDA'
WHERE r.situacao_venda = 'CONCLUIDA'
GROUP BY r.id_venda, r.numero_item, p.nome_produto, r.quantidade_base
HAVING quantidade_baixada <> r.quantidade_base;

-- ---------------------------------------------------------------------
-- A03 — Lotes sem movimentação de entrada ou com saldo negativo (RN-16; cardinalidade LOTE 1,N)
-- Verifica: “estoque fantasma” (lote sem origem) e baixa maior que o existente.
-- ---------------------------------------------------------------------
SELECT s.id_lote, s.nome_produto, s.origem, s.quantidade_inicial, s.quantidade_atual,
       CASE WHEN s.quantidade_inicial = 0 THEN 'Lote sem movimentação de entrada'
            ELSE 'Saldo negativo' END AS problema
FROM vw_lote_saldo s
WHERE s.quantidade_inicial = 0 OR s.quantidade_atual < 0;

-- ---------------------------------------------------------------------
-- A04 — Venda fiada sem cliente identificado ou de cliente não autorizado (RN-24, PO-04)
-- Verifica: fiado concedido fora da política. Limitação conhecida: o banco guarda a autorização
-- VIGENTE do cliente, não o histórico dela; se o gerente suspender um cliente, as vendas antigas
-- dele também aparecerão aqui. Por isso a suspensão do crédito é feita pelo limite (OP06).
-- ---------------------------------------------------------------------
SELECT v.id_venda, v.data_hora, c.nome AS cliente, c.autorizado_fiado, pv.valor AS valor_fiado,
       CASE WHEN v.id_cliente IS NULL THEN 'Fiado sem cliente'
            WHEN NOT c.autorizado_fiado THEN 'Cliente não autorizado'
            ELSE 'Verificar' END AS problema
FROM pagamento_venda pv
JOIN venda v ON v.id_venda = pv.id_venda
LEFT JOIN cliente c ON c.id_cliente = v.id_cliente
WHERE pv.codigo_forma = 'FIADO' AND v.situacao = 'CONCLUIDA'
  AND (v.id_cliente IS NULL OR c.autorizado_fiado = FALSE);

-- ---------------------------------------------------------------------
-- A05 — Lotes sem data de validade em produto que controla validade (RN-15)
-- Verifica: lote que nunca aparecerá na lista de validades (prioridade nº 1).
-- ---------------------------------------------------------------------
SELECT s.id_lote, s.nome_produto, s.origem, s.data_entrada, s.quantidade_atual
FROM vw_lote_saldo s
JOIN produto p ON p.id_produto = s.id_produto
WHERE p.controla_validade = TRUE AND s.data_validade IS NULL;

-- ---------------------------------------------------------------------
-- A06 — Sessões fechadas com diferença de caixa (dinheiro ou maquininhas) sem justificativa (RN-30)
-- Verifica: sobra/falta que ninguém explicou.
-- ---------------------------------------------------------------------
SELECT sc.id_sessao, sc.numero_caixa, sc.data_hora_abertura, f.nome AS fechada_por,
       sc.valor_esperado, sc.valor_contado, sc.diferenca_dinheiro,
       sc.total_eletronico_registrado, sc.total_maquininhas_informado, sc.diferenca_eletronica
FROM vw_sessao_conferencia sc
JOIN funcionario f ON f.id_funcionario = sc.id_funcionario_fechamento
WHERE sc.situacao = 'FECHADA'
  AND (sc.diferenca_dinheiro <> 0 OR sc.diferenca_eletronica <> 0)
  AND sc.justificativa_diferenca IS NULL;

-- ---------------------------------------------------------------------
-- A07 — Transações de cartão/Pix/vale não creditadas após a data prevista (RN-36)
-- Verifica: dinheiro que a operadora deveria ter pago e não pagou (conciliação).
-- Tolerância de 1 dia útil após a data prevista.
-- ---------------------------------------------------------------------
SELECT p.id_venda, p.numero_pagamento, p.codigo_forma, DATE(p.data_venda) AS data_venda, p.nsu_autorizacao,
       p.valor, p.data_prevista_credito, DATEDIFF(@data_ref, p.data_prevista_credito) AS dias_de_atraso
FROM vw_pagamento_venda_previsao p
WHERE p.situacao_credito = 'PENDENTE' AND p.situacao_venda = 'CONCLUIDA'
  AND p.data_prevista_credito < DATE_SUB(@data_ref, INTERVAL 1 DAY);

-- ---------------------------------------------------------------------
-- A08 — Créditos conciliados com divergência de valor ou taxa (RN-36)
-- Verifica: repasse menor que o previsto (taxa acima da contratada ou transação faltante).
-- ---------------------------------------------------------------------
SELECT c.id_movimento_fin, c.data_movimento, c.documento_referencia, c.qtd_transacoes,
       c.bruto_previsto, c.valor_bruto, c.taxa_prevista, c.valor_taxa,
       ROUND(100 * c.valor_taxa / c.valor_bruto, 2) AS taxa_cobrada_pct,
       c.diferenca_conciliacao
FROM vw_conciliacao c
WHERE c.situacao_conciliacao <> 'CONCILIADO';

-- ---------------------------------------------------------------------
-- A09 — Contas a pagar: pagamento acima do valor original ou conta vencida sem quitação (RN-38)
-- Verifica: erro de lançamento (pagou a mais) e obrigações em atraso (juros correndo).
-- ---------------------------------------------------------------------
SELECT c.id_conta, c.credor, c.descricao, c.data_vencimento, c.valor_original, c.valor_principal_pago,
       c.saldo_em_aberto, c.situacao,
       CASE WHEN c.valor_principal_pago > c.valor_original THEN 'Pago acima do valor'
            ELSE CONCAT('Vencida há ', DATEDIFF(@data_ref, c.data_vencimento), ' dia(s)') END AS problema
FROM vw_conta_pagar_situacao c
WHERE c.valor_principal_pago > c.valor_original
   OR (c.situacao IN ('ABERTA','PARCIALMENTE_PAGA') AND c.data_vencimento < @data_ref);

-- ---------------------------------------------------------------------
-- A10 — Lotes vencidos ainda disponíveis para venda (RN-19; fluxo F3)
-- Verifica: a rotina diária de validade não foi executada para esse lote.
-- ---------------------------------------------------------------------
SELECT s.id_lote, s.nome_produto, s.data_validade, DATEDIFF(@data_ref, s.data_validade) AS dias_vencido,
       s.quantidade_atual
FROM vw_lote_saldo s
WHERE s.situacao = 'DISPONIVEL' AND s.quantidade_atual > 0 AND s.data_validade < @data_ref;

-- ---------------------------------------------------------------------
-- A11 — Lotes de ajuste automático aguardando conferência física (RN-40)
-- Verifica: venda feita com saldo do sistema insuficiente que ainda não foi conferida.
-- ---------------------------------------------------------------------
SELECT s.id_lote, s.nome_produto, s.data_entrada, s.quantidade_inicial, s.custo_unitario, s.quantidade_atual
FROM vw_lote_saldo s
WHERE s.pendente_conferencia = TRUE;

-- ---------------------------------------------------------------------
-- A12 — Devoluções que somam mais do que foi vendido no item (RN-28)
-- Verifica: devolução duplicada ou digitada errada.
-- ---------------------------------------------------------------------
SELECT iv.id_venda, iv.numero_item, iv.quantidade AS vendida, SUM(d.quantidade_devolvida) AS devolvida
FROM devolucao d
JOIN item_venda iv ON iv.id_venda = d.id_venda AND iv.numero_item = d.numero_item
GROUP BY iv.id_venda, iv.numero_item, iv.quantidade
HAVING SUM(d.quantidade_devolvida) > iv.quantidade;

-- ---------------------------------------------------------------------
-- A13 — Operações sensíveis feitas por quem não tinha a permissão (RN-07, RN-23, PO-11, PO-13, RNF-01)
-- Verifica: o controle de acesso foi contornado (ex.: senha emprestada). A permissão é conferida
-- NA DATA DA OPERAÇÃO (concessão e revogação), por isso revogar hoje não “suja” o passado.
-- ---------------------------------------------------------------------
SELECT 'Desconto autorizado' AS operacao, iv.id_venda AS referencia, f.nome AS funcionario, v.data_hora AS quando,
       'AUTORIZAR_DESCONTO' AS permissao_exigida
FROM item_venda iv JOIN venda v ON v.id_venda = iv.id_venda
JOIN funcionario f ON f.id_funcionario = iv.id_funcionario_autorizador
WHERE iv.id_funcionario_autorizador IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM funcionario_permissao fp WHERE fp.id_funcionario = iv.id_funcionario_autorizador
                  AND fp.codigo_permissao = 'AUTORIZAR_DESCONTO' AND fp.data_concessao <= DATE(v.data_hora)
                  AND (fp.data_revogacao IS NULL OR fp.data_revogacao > DATE(v.data_hora)))
UNION ALL
SELECT 'Alteração de preço', hp.id_historico, f.nome, hp.data_hora, 'ALTERAR_PRECO'
FROM historico_preco hp JOIN funcionario f ON f.id_funcionario = hp.id_funcionario
WHERE NOT EXISTS (SELECT 1 FROM funcionario_permissao fp WHERE fp.id_funcionario = hp.id_funcionario
                  AND fp.codigo_permissao = 'ALTERAR_PRECO' AND fp.data_concessao <= DATE(hp.data_hora)
                  AND (fp.data_revogacao IS NULL OR fp.data_revogacao > DATE(hp.data_hora)))
UNION ALL
SELECT 'Abertura de caixa', s.id_sessao, f.nome, s.data_hora_abertura, 'OPERAR_CAIXA'
FROM sessao_caixa s JOIN funcionario f ON f.id_funcionario = s.id_funcionario_abertura
WHERE NOT EXISTS (SELECT 1 FROM funcionario_permissao fp WHERE fp.id_funcionario = s.id_funcionario_abertura
                  AND fp.codigo_permissao = 'OPERAR_CAIXA' AND fp.data_concessao <= DATE(s.data_hora_abertura)
                  AND (fp.data_revogacao IS NULL OR fp.data_revogacao > DATE(s.data_hora_abertura)))
UNION ALL
SELECT 'Devolução autorizada', d.id_devolucao, f.nome, d.data_hora, 'AUTORIZAR_DEVOLUCAO'
FROM devolucao d JOIN funcionario f ON f.id_funcionario = d.id_funcionario
WHERE NOT EXISTS (SELECT 1 FROM funcionario_permissao fp WHERE fp.id_funcionario = d.id_funcionario
                  AND fp.codigo_permissao = 'AUTORIZAR_DEVOLUCAO' AND fp.data_concessao <= DATE(d.data_hora)
                  AND (fp.data_revogacao IS NULL OR fp.data_revogacao > DATE(d.data_hora)))
UNION ALL
SELECT 'Registro de perda', m.id_movimentacao, f.nome, m.data_hora, 'REGISTRAR_PERDA'
FROM movimentacao_estoque m JOIN funcionario f ON f.id_funcionario = m.id_funcionario
WHERE m.tipo IN ('PERDA_VENCIMENTO','PERDA_AVARIA')
  AND NOT EXISTS (SELECT 1 FROM funcionario_permissao fp WHERE fp.id_funcionario = m.id_funcionario
                  AND fp.codigo_permissao = 'REGISTRAR_PERDA' AND fp.data_concessao <= DATE(m.data_hora)
                  AND (fp.data_revogacao IS NULL OR fp.data_revogacao > DATE(m.data_hora)));

-- ---------------------------------------------------------------------
-- A14 — Preço vigente diferente do último preço registrado no histórico (RN-06)
-- Verifica: preço alterado direto na embalagem, sem deixar histórico.
-- ---------------------------------------------------------------------
SELECT e.id_embalagem, p.nome_produto, e.descricao, e.preco_venda AS preco_vigente, h.preco_novo AS ultimo_preco_historico
FROM embalagem e
JOIN produto p ON p.id_produto = e.id_produto
JOIN historico_preco h ON h.id_embalagem = e.id_embalagem
WHERE h.data_hora = (SELECT MAX(h2.data_hora) FROM historico_preco h2 WHERE h2.id_embalagem = e.id_embalagem)
  AND h.preco_novo <> e.preco_venda;

-- ---------------------------------------------------------------------
-- A15 — Itens vendidos abaixo do custo (preço praticado menor que o custo dos lotes baixados)
-- Verifica: erro de preço, desconto exagerado ou custo de lote digitado errado.
-- ---------------------------------------------------------------------
SELECT r.id_venda, r.numero_item, p.nome_produto, r.data_hora, r.quantidade_base,
       ROUND(r.valor_item / r.quantidade_base, 2) AS preco_liquido_unitario,
       ROUND(r.custo_baixado / r.quantidade_base, 2) AS custo_unitario,
       ROUND(r.valor_item - r.custo_baixado, 2) AS prejuizo_no_item
FROM vw_item_venda_resultado r
JOIN produto p ON p.id_produto = r.id_produto
WHERE r.situacao_venda = 'CONCLUIDA' AND r.valor_item < r.custo_baixado
ORDER BY prejuizo_no_item;

-- ---------------------------------------------------------------------
-- A16 — Baixa de venda feita em lote de outro produto (RN-17)
-- Verifica: incoerência que a FK sozinha não impede (o lote é de um produto,
-- o item é de uma embalagem — o produto dos dois precisa ser o mesmo).
-- ---------------------------------------------------------------------
SELECT m.id_movimentacao, m.id_venda, m.numero_item, l.id_produto AS produto_do_lote, e.id_produto AS produto_vendido
FROM movimentacao_estoque m
JOIN lote l ON l.id_lote = m.id_lote
JOIN item_venda iv ON iv.id_venda = m.id_venda AND iv.numero_item = m.numero_item
JOIN embalagem e ON e.id_embalagem = iv.id_embalagem
WHERE m.tipo = 'SAIDA_VENDA' AND l.id_produto <> e.id_produto;

-- ---------------------------------------------------------------------
-- A17 — Nota de um fornecedor atendendo pedido de outro fornecedor (RN-11, RN-12)
-- Verifica: vínculo indevido entre recebimento e pedido.
-- ---------------------------------------------------------------------
SELECT ir.id_recebimento, ir.numero_item_nota, r.id_fornecedor AS fornecedor_da_nota, pc.id_fornecedor AS fornecedor_do_pedido
FROM item_recebimento ir
JOIN recebimento r ON r.id_recebimento = ir.id_recebimento
JOIN pedido_compra pc ON pc.id_pedido = ir.id_pedido
WHERE r.id_fornecedor <> pc.id_fornecedor;

-- ---------------------------------------------------------------------
-- A18 — Linha de nota cuja soma dos lotes difere da quantidade aceita (RN-14)
-- Verifica: estoque gerado a mais ou a menos que o aceito na conferência.
-- ---------------------------------------------------------------------
SELECT ir.id_recebimento, ir.numero_item_nota, p.nome_produto, ir.quantidade_aceita,
       COALESCE(SUM(s.quantidade_inicial), 0) AS soma_dos_lotes
FROM item_recebimento ir
JOIN produto p ON p.id_produto = ir.id_produto
LEFT JOIN vw_lote_saldo s ON s.id_recebimento = ir.id_recebimento AND s.numero_item_nota = ir.numero_item_nota
GROUP BY ir.id_recebimento, ir.numero_item_nota, p.nome_produto, ir.quantidade_aceita
HAVING soma_dos_lotes <> ir.quantidade_aceita;

-- ---------------------------------------------------------------------
-- A19 — Fundo de troco: abertura diferente do que ficou na gaveta no fechamento anterior do mesmo caixa
-- Verifica: dinheiro que “sumiu” ou “apareceu” entre duas sessões.
-- ---------------------------------------------------------------------
WITH ordem AS (
  SELECT sc.id_sessao, sc.numero_caixa, sc.data_hora_abertura, sc.valor_inicial,
         sc.valor_contado - sc.recolhido_fechamento AS ficou_na_gaveta,
         LAG(sc.valor_contado - sc.recolhido_fechamento) OVER (PARTITION BY sc.numero_caixa ORDER BY sc.data_hora_abertura) AS deixado_antes
  FROM vw_sessao_conferencia sc
)
SELECT id_sessao, numero_caixa, data_hora_abertura, deixado_antes, valor_inicial, valor_inicial - deixado_antes AS diferenca
FROM ordem
WHERE deixado_antes IS NOT NULL AND valor_inicial <> deixado_antes;

-- ---------------------------------------------------------------------
-- A20 — Venda baixada de lote que já estava vencido na data da venda (RN-17, RN-19, PO-07)
-- Verifica: venda de produto vencido (risco sanitário e de reclamação).
-- ---------------------------------------------------------------------
SELECT m.id_venda, m.numero_item, l.id_lote, p.nome_produto, l.data_validade, DATE(m.data_hora) AS data_venda
FROM movimentacao_estoque m
JOIN lote l ON l.id_lote = m.id_lote
JOIN produto p ON p.id_produto = l.id_produto
WHERE m.tipo = 'SAIDA_VENDA' AND l.data_validade IS NOT NULL AND l.data_validade < DATE(m.data_hora);

-- ---------------------------------------------------------------------
-- A21 — Cardinalidades mínimas 1 que a FK não consegue garantir (R02, R06, R12, R16, R27, R37)
-- Verifica: “cabeçalho sem filho obrigatório”. A FK garante que o filho aponta para um pai existente,
-- mas não que todo pai tenha ao menos um filho. Ex.: produto ativo sem embalagem ativa (não pode ser
-- vendido — RN-03), pedido sem item, nota sem linha, venda sem item, devolução sem movimento de estoque.
-- ---------------------------------------------------------------------
SELECT 'Produto ativo sem embalagem ativa (R02, RN-03)' AS problema, p.id_produto AS referencia
FROM produto p
WHERE p.ativo AND NOT EXISTS (SELECT 1 FROM embalagem e WHERE e.id_produto = p.id_produto AND e.ativa)
UNION ALL
SELECT 'Lote sem nenhuma movimentação (R06, RN-16)', l.id_lote
FROM lote l WHERE NOT EXISTS (SELECT 1 FROM movimentacao_estoque m WHERE m.id_lote = l.id_lote)
UNION ALL
SELECT 'Pedido sem itens (R12, RN-10)', pc.id_pedido
FROM pedido_compra pc WHERE NOT EXISTS (SELECT 1 FROM item_pedido ip WHERE ip.id_pedido = pc.id_pedido)
UNION ALL
SELECT 'Recebimento sem linhas de nota (R16, RN-13)', r.id_recebimento
FROM recebimento r WHERE NOT EXISTS (SELECT 1 FROM item_recebimento ir WHERE ir.id_recebimento = r.id_recebimento)
UNION ALL
SELECT 'Venda sem itens (R27, RN-21)', v.id_venda
FROM venda v WHERE NOT EXISTS (SELECT 1 FROM item_venda iv WHERE iv.id_venda = v.id_venda)
UNION ALL
SELECT 'Devolução sem retorno ao estoque (R37, RN-28)', d.id_devolucao
FROM devolucao d WHERE NOT EXISTS (SELECT 1 FROM movimentacao_estoque m WHERE m.id_devolucao = d.id_devolucao);

-- ---------------------------------------------------------------------
-- A22 — Custo do lote diferente da sua origem (RN-19, RN-22; redundância controlada)
-- Verifica: o custo copiado para o lote na entrada continua igual à fonte — linha da nota
-- (valor unitário ÷ fator de conversão) ou, na reposição de troca, o custo do lote trocado.
-- É a contrapartida de guardar o custo no lote (necessário para lotes sem nota).
-- ---------------------------------------------------------------------
SELECT l.id_lote, l.origem, l.custo_unitario AS custo_no_lote,
       ROUND(ir.valor_unitario_nota / ir.fator_conversao_compra, 4) AS custo_na_origem
FROM lote l
JOIN item_recebimento ir ON ir.id_recebimento = l.id_recebimento AND ir.numero_item_nota = l.numero_item_nota
WHERE l.custo_unitario <> ROUND(ir.valor_unitario_nota / ir.fator_conversao_compra, 4)
UNION ALL
SELECT l.id_lote, l.origem, l.custo_unitario, r.custo_unitario
FROM lote l JOIN lote r ON r.id_lote = l.id_lote_reposto
WHERE l.custo_unitario <> r.custo_unitario;
