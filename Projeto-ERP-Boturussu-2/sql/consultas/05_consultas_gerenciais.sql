-- =====================================================================
-- 05_consultas_gerenciais.sql — CONSULTAS GERENCIAIS
-- Cada consulta parte de uma PERGUNTA do gerente, usa SQL (SELECT/JOIN)
-- e termina na DECISÃO que a informação apoia.
-- Data de referência: 01/10/2026 (dia seguinte ao último dia da massa).
-- Para usar no dia a dia, troque por: SET @data_ref = CURRENT_DATE;
-- =====================================================================
USE mercado_boturussu;
SET NAMES utf8mb4;
SET @data_ref = DATE('2026-10-01');
SET @ini = DATE('2026-09-01');
SET @fim = DATE('2026-09-30');

-- ---------------------------------------------------------------------
-- G01 — Quais produtos mais faturaram no mês e quanto deixaram de lucro?
-- Origem: PB-16, PB-17; entrevista 8.8 e 8.13 (“se vendem bem, giro e proporção de lucro”).
-- Decisão: o que nunca pode faltar na gôndola e onde a margem compensa.
-- ---------------------------------------------------------------------
SELECT p.nome_produto AS produto,
       c.nome AS categoria,
       ROUND(SUM(r.quantidade_base), 3) AS quantidade_vendida,
       p.unidade_base AS unidade,
       ROUND(SUM(r.valor_item - r.valor_reembolsado), 2) AS faturamento,
       ROUND(SUM(r.custo_total), 2) AS custo_mercadoria,
       ROUND(SUM(r.valor_item - r.valor_reembolsado - r.custo_total), 2) AS lucro_bruto,
       ROUND(100 * SUM(r.valor_item - r.valor_reembolsado - r.custo_total) / SUM(r.valor_item - r.valor_reembolsado), 1) AS margem_pct
FROM vw_item_venda_resultado r
JOIN produto p   ON p.id_produto = r.id_produto
JOIN categoria c ON c.codigo_categoria = p.codigo_categoria
WHERE r.situacao_venda = 'CONCLUIDA' AND DATE(r.data_hora) BETWEEN @ini AND @fim
GROUP BY p.id_produto, p.nome_produto, c.nome, p.unidade_base
ORDER BY faturamento DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- G02 — Curva ABC: quais produtos concentram 80% do faturamento?
-- Decisão: produtos A recebem prioridade de compra, conferência e preço;
-- produtos C são candidatos a sair do mix ou a ter estoque mínimo menor.
-- ---------------------------------------------------------------------
WITH fat AS (
  SELECT r.id_produto, SUM(r.valor_item - r.valor_reembolsado) AS faturamento
  FROM vw_item_venda_resultado r
  WHERE r.situacao_venda = 'CONCLUIDA' AND DATE(r.data_hora) BETWEEN @ini AND @fim
  GROUP BY r.id_produto
), acum AS (
  SELECT id_produto, faturamento,
         SUM(faturamento) OVER (ORDER BY faturamento DESC, id_produto) / SUM(faturamento) OVER () AS pct_acumulado
  FROM fat
)
SELECT CASE WHEN pct_acumulado <= 0.80 THEN 'A' WHEN pct_acumulado <= 0.95 THEN 'B' ELSE 'C' END AS classe,
       COUNT(*) AS qtd_produtos,
       ROUND(SUM(faturamento), 2) AS faturamento,
       GROUP_CONCAT(p.nome_produto ORDER BY faturamento DESC SEPARATOR '; ') AS produtos
FROM acum JOIN produto p ON p.id_produto = acum.id_produto
GROUP BY classe
ORDER BY classe;

-- ---------------------------------------------------------------------
-- G03 — Quanto vendemos e quanto lucramos por dia? (“lucro do dia”, entrevista 6.20)
-- Decisão: separar movimento de resultado; identificar dias fortes e fracos.
-- ---------------------------------------------------------------------
SELECT DATE(v.data_hora) AS dia,
       ELT(DAYOFWEEK(v.data_hora), 'dom','seg','ter','qua','qui','sex','sáb') AS dia_semana,
       COUNT(*) AS vendas,
       ROUND(SUM(v.valor_total - v.valor_reembolsado), 2) AS faturamento,
       ROUND(AVG(v.valor_total), 2) AS ticket_medio,
       ROUND(SUM(v.lucro_bruto), 2) AS lucro_bruto,
       ROUND(100 * SUM(v.lucro_bruto) / SUM(v.valor_total - v.valor_reembolsado), 1) AS margem_pct
FROM vw_venda_resumo v
WHERE v.situacao = 'CONCLUIDA' AND DATE(v.data_hora) BETWEEN @ini AND @fim
GROUP BY DATE(v.data_hora), dia_semana
ORDER BY dia;

-- ---------------------------------------------------------------------
-- G04 — Quanto entrou em cada forma de pagamento e em cada caixa? (RF-37; PB-10)
-- Decisão: negociar taxas com a operadora; dimensionar troco; ver o peso do fiado.
-- ---------------------------------------------------------------------
SELECT s.numero_caixa AS caixa,
       f.descricao AS forma,
       COUNT(*) AS transacoes,
       ROUND(SUM(pv.valor), 2) AS valor_bruto,
       f.taxa_percentual AS taxa_contratada_pct,
       ROUND(SUM(pv.valor) * f.taxa_percentual / 100, 2) AS custo_estimado_taxa,
       ROUND(100 * SUM(pv.valor) / SUM(SUM(pv.valor)) OVER (PARTITION BY s.numero_caixa), 1) AS pct_no_caixa
FROM pagamento_venda pv
JOIN venda v           ON v.id_venda = pv.id_venda
JOIN sessao_caixa s    ON s.id_sessao = v.id_sessao
JOIN forma_pagamento f ON f.codigo_forma = pv.codigo_forma
WHERE v.situacao = 'CONCLUIDA' AND DATE(v.data_hora) BETWEEN @ini AND @fim
GROUP BY s.numero_caixa, f.codigo_forma, f.descricao, f.taxa_percentual
ORDER BY caixa, valor_bruto DESC;

-- ---------------------------------------------------------------------
-- G05 — LISTA DE VALIDADES: quais lotes vencem nos próximos dias? (prioridade nº 1; RF-17)
-- Usa o prazo de alerta do produto ou, na falta dele, o da categoria (RNF-09).
-- Decisão: promover, conferir na gôndola ou negociar troca antes de vencer.
-- ---------------------------------------------------------------------
SELECT s.id_lote, s.nome_produto AS produto, c.nome AS categoria,
       s.data_validade,
       DATEDIFF(s.data_validade, @data_ref) AS dias_para_vencer,
       COALESCE(p.dias_alerta_validade, c.dias_alerta_validade_padrao) AS prazo_alerta,
       s.quantidade_atual AS saldo, p.unidade_base AS unidade,
       ROUND(s.quantidade_atual * s.custo_unitario, 2) AS valor_em_risco_custo,
       CASE WHEN DATEDIFF(s.data_validade, @data_ref) < 0 THEN 'VENCIDO — retirar'
            WHEN DATEDIFF(s.data_validade, @data_ref) <= 2 THEN 'Promover hoje'
            ELSE 'Acompanhar' END AS acao_sugerida
FROM vw_lote_saldo s
JOIN produto p   ON p.id_produto = s.id_produto
JOIN categoria c ON c.codigo_categoria = p.codigo_categoria
WHERE s.situacao = 'DISPONIVEL' AND s.quantidade_atual > 0 AND s.data_validade IS NOT NULL
  AND DATEDIFF(s.data_validade, @data_ref) <= COALESCE(p.dias_alerta_validade, c.dias_alerta_validade_padrao, 7)
ORDER BY s.data_validade, valor_em_risco_custo DESC;

-- ---------------------------------------------------------------------
-- G06 — O que está abaixo do estoque mínimo, quanto comprar e de quem? (RF-19; PB-02, PB-05)
-- Sugestão = 7 dias da média vendida nos últimos 7 dias + mínimo − estoque atual.
-- Fornecedor sugerido = menor último custo registrado.
-- Decisão: montar o pedido do dia sem conferir gôndola por gôndola.
-- ---------------------------------------------------------------------
WITH media AS (
  SELECT r.id_produto, SUM(r.quantidade_base) / 7 AS media_dia
  FROM vw_item_venda_resultado r
  WHERE r.situacao_venda = 'CONCLUIDA' AND DATE(r.data_hora) BETWEEN DATE_SUB(@data_ref, INTERVAL 7 DAY) AND DATE_SUB(@data_ref, INTERVAL 1 DAY)
  GROUP BY r.id_produto
), melhor AS (
  SELECT u.id_produto, u.id_fornecedor, u.preco_ultima_compra,
         ROW_NUMBER() OVER (PARTITION BY u.id_produto ORDER BY u.preco_ultima_compra) AS rn
  FROM vw_ultimo_custo_fornecedor u
)
SELECT e.nome_produto AS produto, e.estoque_atual, e.estoque_minimo, e.unidade_base AS unidade,
       ROUND(COALESCE(m.media_dia, 0), 2) AS media_vendida_dia,
       ROUND(GREATEST(COALESCE(m.media_dia, 0) * 7 + e.estoque_minimo - e.estoque_atual, 0), 0) AS sugestao_compra,
       f.nome_fantasia AS fornecedor_mais_barato, b.preco_ultima_compra AS ultimo_custo
FROM vw_estoque_produto e
LEFT JOIN media m  ON m.id_produto = e.id_produto
LEFT JOIN melhor b ON b.id_produto = e.id_produto AND b.rn = 1
LEFT JOIN fornecedor f ON f.id_fornecedor = b.id_fornecedor
WHERE e.ativo AND e.abaixo_minimo = 1
ORDER BY (e.estoque_atual / NULLIF(e.estoque_minimo, 0)), produto;

-- ---------------------------------------------------------------------
-- G07 — Quem deve no fiado, quanto e há quanto tempo não paga? (PB-07, PB-08; RF-27)
-- Decisão: cobrar, suspender novas compras ou rever o limite (PO-04).
-- ---------------------------------------------------------------------
SELECT cs.nome AS cliente, COALESCE(cs.apelido, '') AS apelido,
       cs.saldo_devedor, cs.limite_fiado,
       ROUND(100 * cs.saldo_devedor / NULLIF(cs.limite_fiado, 0), 0) AS pct_limite,
       DATE(cs.ultima_compra_fiado) AS ultima_compra,
       DATE(cs.ultimo_abatimento) AS ultimo_pagamento,
       DATEDIFF(@data_ref, COALESCE(cs.ultimo_abatimento, cs.primeira_compra_fiado)) AS dias_sem_pagar,
       CASE WHEN cs.saldo_devedor > cs.limite_fiado THEN 'Acima do limite — suspender'
            WHEN cs.ultimo_abatimento IS NULL AND DATEDIFF(@data_ref, cs.primeira_compra_fiado) > 15 THEN 'Nunca pagou — cobrar'
            WHEN DATEDIFF(@data_ref, COALESCE(cs.ultimo_abatimento, cs.primeira_compra_fiado)) > 15 THEN 'Sem pagar há mais de 15 dias — cobrar'
            WHEN cs.saldo_devedor >= 0.8 * cs.limite_fiado THEN 'Perto do limite'
            ELSE 'Em dia' END AS situacao
FROM vw_cliente_saldo cs
WHERE cs.saldo_devedor > 0
ORDER BY cs.saldo_devedor DESC;

-- ---------------------------------------------------------------------
-- G08 — Quais contas estão em aberto, por vencimento e prioridade? (RF-41; PB-14)
-- Mostra o SALDO em aberto (pagamentos parciais já descontados — RN-38).
-- Decisão: o que pagar primeiro quando o dinheiro não cobre tudo (PO-06).
-- ---------------------------------------------------------------------
SELECT c.data_vencimento, c.prioridade, c.credor, c.descricao, c.categoria_despesa,
       c.valor_original, c.valor_principal_pago, c.saldo_em_aberto, c.situacao,
       CASE WHEN c.data_vencimento < @data_ref THEN CONCAT('VENCIDA há ', DATEDIFF(@data_ref, c.data_vencimento), ' dia(s)')
            WHEN c.data_vencimento <= DATE_ADD(@data_ref, INTERVAL 7 DAY) THEN 'Vence nesta semana'
            ELSE 'A vencer' END AS alerta
FROM vw_conta_pagar_situacao c
WHERE c.situacao IN ('ABERTA','PARCIALMENTE_PAGA')
ORDER BY c.data_vencimento, FIELD(c.prioridade, 'ALTA','MEDIA','BAIXA'), c.saldo_em_aberto DESC;

-- ---------------------------------------------------------------------
-- G09 — PREVISÃO DE DISPONIBILIDADE: vai faltar dinheiro nos próximos 21 dias? (RF-35, RF-36, RN-39)
-- Saldo inicial = saldo realizado (banco + cofre) + dinheiro nas gavetas abertas.
-- Entradas previstas = recebíveis de cartão/Pix/vale ainda não conciliados, pela data
--   prevista de crédito (valor líquido da taxa). Vencidos e não creditados entram no 1º dia.
-- Saídas previstas = saldo em aberto das contas, pelo vencimento (vencidas no 1º dia).
-- Vendas futuras NÃO entram: a previsão é conservadora de propósito.
-- Decisão: o ALERTA pedido pelo gerente (“sim, muito”): antecipar recebíveis, negociar prazo
-- ou escolher, pela prioridade, o que pagar.
-- ---------------------------------------------------------------------
WITH RECURSIVE dias AS (
  SELECT @data_ref AS dia
  UNION ALL
  SELECT DATE_ADD(dia, INTERVAL 1 DAY) FROM dias WHERE dia < DATE_ADD(@data_ref, INTERVAL 20 DAY)
), saldo_ini AS (
  SELECT (SELECT SUM(saldo_atual) FROM vw_conta_financeira_saldo)
       + (SELECT COALESCE(SUM(valor_esperado), 0) FROM vw_sessao_conferencia WHERE situacao = 'ABERTA') AS valor
), entradas AS (
  SELECT GREATEST(data_prevista_credito, @data_ref) AS dia, SUM(valor_liquido_previsto) AS valor
  FROM vw_pagamento_venda_previsao
  WHERE situacao_credito = 'PENDENTE' AND situacao_venda = 'CONCLUIDA'
  GROUP BY GREATEST(data_prevista_credito, @data_ref)
), saidas AS (
  SELECT GREATEST(data_vencimento, @data_ref) AS dia, SUM(saldo_em_aberto) AS valor
  FROM vw_conta_pagar_situacao
  WHERE situacao IN ('ABERTA','PARCIALMENTE_PAGA')
  GROUP BY GREATEST(data_vencimento, @data_ref)
), fluxo AS (
  SELECT d.dia, COALESCE(e.valor, 0) AS entradas, COALESCE(s.valor, 0) AS saidas
  FROM dias d LEFT JOIN entradas e ON e.dia = d.dia LEFT JOIN saidas s ON s.dia = d.dia
)
SELECT f.dia,
       ROUND(f.entradas, 2) AS entradas_previstas,
       ROUND(f.saidas, 2) AS saidas_previstas,
       ROUND((SELECT valor FROM saldo_ini) + SUM(f.entradas - f.saidas) OVER (ORDER BY f.dia), 2) AS saldo_previsto,
       CASE WHEN (SELECT valor FROM saldo_ini) + SUM(f.entradas - f.saidas) OVER (ORDER BY f.dia) < 0
            THEN 'ALERTA: saldo insuficiente' ELSE '' END AS alerta
FROM fluxo f
ORDER BY f.dia;

-- ---------------------------------------------------------------------
-- G10 — Quanto perdemos com vencimento e avaria, e em quais produtos? (RF-40; PB-04)
-- Perda líquida = perdas − reposições recebidas do fornecedor (troca).
-- Decisão: reduzir compra dos produtos que mais vencem; negociar troca; promover antes.
-- ---------------------------------------------------------------------
SELECT p.nome_produto AS produto, c.nome AS categoria,
       ROUND(SUM(CASE WHEN m.tipo = 'PERDA_VENCIMENTO' THEN m.valor_custo ELSE 0 END), 2) AS perda_vencimento,
       ROUND(SUM(CASE WHEN m.tipo = 'PERDA_AVARIA' THEN m.valor_custo ELSE 0 END), 2) AS perda_avaria,
       ROUND(SUM(CASE WHEN m.tipo = 'TROCA_FORNECEDOR' THEN m.valor_custo ELSE 0 END), 2) AS recuperado_na_troca,
       ROUND(SUM(CASE WHEN m.tipo IN ('PERDA_VENCIMENTO','PERDA_AVARIA') THEN m.valor_custo
                      WHEN m.tipo = 'TROCA_FORNECEDOR' THEN -m.valor_custo ELSE 0 END), 2) AS perda_liquida
FROM vw_movimentacao_valorizada m
JOIN produto p   ON p.id_produto = m.id_produto
JOIN categoria c ON c.codigo_categoria = p.codigo_categoria
WHERE m.tipo IN ('PERDA_VENCIMENTO','PERDA_AVARIA','TROCA_FORNECEDOR')
  AND DATE(m.data_hora) BETWEEN @ini AND @fim
GROUP BY p.id_produto, p.nome_produto, c.nome
HAVING perda_vencimento + perda_avaria > 0
ORDER BY perda_liquida DESC;

-- ---------------------------------------------------------------------
-- G11 — De quem comprar? Último custo de cada produto por fornecedor (RF-07; PB-05)
-- Só aparecem produtos comprados de mais de um fornecedor.
-- Decisão: escolher o fornecedor do próximo pedido (ex.: o leite).
-- ---------------------------------------------------------------------
SELECT p.nome_produto AS produto, f.nome_fantasia AS fornecedor,
       u.data_ultima_compra, u.preco_ultima_compra AS custo_unitario,
       ROUND(u.preco_ultima_compra - MIN(u.preco_ultima_compra) OVER (PARTITION BY u.id_produto), 4) AS diferenca_para_o_menor
FROM vw_ultimo_custo_fornecedor u
JOIN produto p    ON p.id_produto = u.id_produto
JOIN fornecedor f ON f.id_fornecedor = u.id_fornecedor
WHERE u.id_produto IN (SELECT id_produto FROM vw_ultimo_custo_fornecedor GROUP BY id_produto HAVING COUNT(*) > 1)
ORDER BY produto, custo_unitario;

-- ---------------------------------------------------------------------
-- G12 — O que foi pedido e ainda não chegou? (RF-10; PB-15)
-- Decisão: cobrar o fornecedor; não pedir de novo o que já está a caminho.
-- ---------------------------------------------------------------------
SELECT ps.id_pedido, ps.razao_social AS fornecedor, DATE(ps.data_hora_pedido) AS data_pedido, ps.situacao,
       x.nome_produto AS produto, x.quantidade_pedida, x.quantidade_recebida, x.quantidade_pendente
FROM vw_pedido_situacao ps
JOIN vw_item_pedido_pendencia x ON x.id_pedido = ps.id_pedido
WHERE ps.situacao IN ('ABERTO','PARCIALMENTE_RECEBIDO') AND x.quantidade_pendente > 0
ORDER BY ps.data_hora_pedido, produto;

-- ---------------------------------------------------------------------
-- G13 — Como foi cada operador no caixa? Vendas, ticket e diferenças de fechamento (PB-11, PB-12)
-- Decisão: treinamento (RNF-04), escala e investigação de diferenças recorrentes.
-- ---------------------------------------------------------------------
SELECT fu.nome AS operador,
       COUNT(DISTINCT v.id_venda) AS vendas,
       ROUND(SUM(v.valor_total), 2) AS faturamento,
       ROUND(AVG(v.valor_total), 2) AS ticket_medio,
       (SELECT COUNT(*) FROM vw_sessao_conferencia sc WHERE sc.id_funcionario_fechamento = fu.id_funcionario) AS sessoes_fechadas,
       (SELECT COALESCE(SUM(sc.diferenca_dinheiro), 0) FROM vw_sessao_conferencia sc WHERE sc.id_funcionario_fechamento = fu.id_funcionario) AS soma_diferencas_dinheiro
FROM vw_venda_resumo v
JOIN funcionario fu ON fu.id_funcionario = v.id_funcionario
WHERE v.situacao = 'CONCLUIDA' AND DATE(v.data_hora) BETWEEN @ini AND @fim
GROUP BY fu.id_funcionario, fu.nome
ORDER BY faturamento DESC;

-- ---------------------------------------------------------------------
-- G14 — Qual a margem de cada setor? (PO-09: margem de 35–40% nos itens comuns)
-- Decisão: rever preços do setor cuja margem real ficou abaixo da política.
-- ---------------------------------------------------------------------
SELECT c.nome AS categoria,
       ROUND(SUM(r.valor_item - r.valor_reembolsado), 2) AS faturamento,
       ROUND(SUM(r.custo_total), 2) AS custo_mercadoria,
       ROUND(100 * SUM(r.valor_item - r.valor_reembolsado - r.custo_total) / SUM(r.valor_item - r.valor_reembolsado), 1) AS margem_sobre_venda_pct,
       ROUND(100 * SUM(r.valor_item - r.valor_reembolsado - r.custo_total) / SUM(r.custo_total), 1) AS markup_sobre_custo_pct
FROM vw_item_venda_resultado r
JOIN produto p   ON p.id_produto = r.id_produto
JOIN categoria c ON c.codigo_categoria = p.codigo_categoria
WHERE r.situacao_venda = 'CONCLUIDA' AND DATE(r.data_hora) BETWEEN @ini AND @fim
GROUP BY c.codigo_categoria, c.nome
ORDER BY margem_sobre_venda_pct;

-- ---------------------------------------------------------------------
-- G15 — Quais produtos giram menos? Dias de cobertura do estoque atual (entrevista 8.9)
-- Cobertura = estoque atual ÷ média diária vendida no mês.
-- Decisão: pedir menos dos itens parados (capital empatado e risco de vencer).
-- ---------------------------------------------------------------------
WITH vendido AS (
  SELECT r.id_produto, SUM(r.quantidade_base) AS qtd_mes
  FROM vw_item_venda_resultado r
  WHERE r.situacao_venda = 'CONCLUIDA' AND DATE(r.data_hora) BETWEEN @ini AND @fim
  GROUP BY r.id_produto
)
SELECT e.nome_produto AS produto, e.estoque_atual, e.unidade_base AS unidade,
       ROUND(COALESCE(v.qtd_mes, 0) / 30, 2) AS media_dia,
       ROUND(e.estoque_atual / NULLIF(COALESCE(v.qtd_mes, 0) / 30, 0), 1) AS dias_de_cobertura,
       ROUND(e.valor_estoque_custo, 2) AS capital_parado
FROM vw_estoque_produto e
LEFT JOIN vendido v ON v.id_produto = e.id_produto
WHERE e.ativo
ORDER BY dias_de_cobertura DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- G16 — Quanto pagamos de juros por atraso? (entrevista, bloco 2e: o “prejuízo invisível”)
-- Decisão: usar a previsão (G09) para evitar o atraso; renegociar prazos.
-- ---------------------------------------------------------------------
SELECT cp.credor, cp.descricao, cp.data_vencimento, pc.data_pagamento,
       DATEDIFF(pc.data_pagamento, cp.data_vencimento) AS dias_atraso,
       pc.valor_principal, pc.valor_juros_multa
FROM pagamento_conta pc
JOIN conta_pagar cp ON cp.id_conta = pc.id_conta
WHERE pc.valor_juros_multa > 0
ORDER BY pc.data_pagamento;
