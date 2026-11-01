# Consultas gerenciais e de auditoria — pergunta, SQL, resultado e decisão

*Extraído das seções 8 e 9 do documento da entrega final.*

## 8.1 Como as consultas foram pensadas

O manual pede para não começar por “precisamos usar JOIN”, e sim por “que informação o gestor precisa conhecer?”. Cada consulta abaixo nasceu de uma pergunta do gerente na entrevista ou de um problema da primeira entrega (código PB), e termina na decisão que ela apoia: **dado → informação → decisão**.

Todas usam a data de referência 01/10/2026 (o dia seguinte ao último dia da massa) e o período 01 a 30/09/2026. Os resultados são **os da execução real** (`evidencias/03_resultados_consultas_gerenciais.txt`), copiados automaticamente.

| Cód. | Pergunta do gerente | Técnicas SQL | Decisão apoiada |
|---|---|---|---|
| G01 | Quais produtos mais faturam e quanto lucram? | JOIN de 3 views/tabelas, GROUP BY, ORDER BY, LIMIT | O que não pode faltar; onde a margem compensa |
| G02 | Quais produtos concentram 80% do faturamento? (curva ABC) | CTE, função de janela (SUM OVER) | Prioridade de compra e de conferência |
| G03 | Quanto vendemos e lucramos por dia? | GROUP BY data, agregação | Dias fortes e fracos; escala |
| G04 | Quanto entrou em cada forma de pagamento e caixa? | JOIN de 4 tabelas, janela por caixa | Negociar taxas; troco |
| G05 | Quais lotes vencem nos próximos dias? | JOIN, COALESCE (prazo do produto ou da categoria) | Promover, trocar, retirar |
| G06 | O que comprar hoje, quanto e de quem? | 2 CTEs, ROW_NUMBER, LEFT JOIN | Pedido do dia |
| G07 | Quem deve no fiado e há quanto tempo não paga? | View de saldo, CASE | Cobrar, limitar |
| G08 | Quais contas estão em aberto? | View de situação, FIELD para prioridade | O que pagar primeiro |
| G09 | Vai faltar dinheiro nos próximos 21 dias? | CTE recursiva (calendário), soma acumulada | Alerta pedido pelo gerente |
| G10 | Quanto perdemos com vencimento e avaria? | CASE dentro de SUM, HAVING | Comprar menos do que vence |
| G11 | De qual fornecedor comprar? | Janela (MIN OVER), subconsulta | Escolha do fornecedor |
| G12 | O que foi pedido e não chegou? | JOIN de views | Cobrar o fornecedor |
| G13 | Como foi cada operador? | Subconsultas correlacionadas | Treinamento e investigação |
| G14 | Qual a margem de cada setor? | GROUP BY categoria | Revisão de preços (PO-09) |
| G15 | O que gira menos? | CTE, divisão protegida (NULLIF) | Pedir menos; liberar capital |
| G16 | Quanto pagamos de juros por atraso? | JOIN, filtro | Usar a previsão para não atrasar |

## 8.2 As consultas, seus resultados e as decisões

### 8.2.1 G01 — Quais produtos mais faturaram no mês e quanto deixaram de lucro?

*Origem: PB-16, PB-17; entrevista 8.8 e 8.13 (“se vendem bem, giro e proporção de lucro”). Decisão: o que nunca pode faltar na gôndola e onde a margem compensa.*

```sql
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
```

Resultado (10 linhas):

| produto | quantidade_vendida | unidade | faturamento | lucro_bruto | margem_pct |
|----------------|----------------|----------------|----------------|----------------|----------------|
| Cerveja Skol Lata 350 ml | 2435.000 | UN | 8863.28 | 2169.78 | 24.5 |
| Refrigerante Coca-Cola 2 L | 502.000 | UN | 5685.99 | 1978.59 | 34.8 |
| Arroz Tio João Tipo 1 5 kg | 168.000 | UN | 5527.20 | 1339.00 | 24.2 |
| Leite Integral Italac 1 L | 842.000 | UN | 5161.48 | 1378.74 | 26.7 |
| Carne Moída Patinho (kg) | 96.826 | KG | 4252.53 | 1147.34 | 27.0 |
| Refrigerante Guaraná Antarctica 2 L | 468.000 | UN | 4207.32 | 1305.72 | 31.0 |
| Cerveja Brahma Lata 473 ml | 708.000 | UN | 3449.48 | 900.68 | 26.1 |
| Frango Coxa e Sobrecoxa (kg) | 162.437 | KG | 2741.56 | 873.53 | 31.9 |

*Mostradas 8 de 10 linhas; resultado completo em `evidencias/03_resultados_consultas_gerenciais.txt`.*

**Leitura.** A cerveja Skol lata é o produto que mais fatura, mas tem uma das menores margens (24,5%); a Coca-Cola 2 L fatura menos e deixa margem de 34,8%. **Decisão:** os dez itens não podem faltar (são a razão de o cliente entrar); nos de margem baixa e alto giro, negociar custo com o fornecedor rende mais do que subir preço.

### 8.2.2 G02 — Curva ABC: quais produtos concentram 80% do faturamento?

*Decisão: produtos A recebem prioridade de compra, conferência e preço; produtos C são candidatos a sair do mix ou a ter estoque mínimo menor.*

```sql
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
```

Resultado (3 linhas):

| classe | qtd_produtos | faturamento |
|---------------------------------|---------------------------------|---------------------------------|
| A | 18 | 59973.65 |
| B | 10 | 11338.70 |
| C | 10 | 4293.44 |

**Leitura.** 18 dos 38 produtos (classe A) concentram cerca de 79% do faturamento; os 10 da classe C somam menos de 6%. Classe A: Cerveja Skol Lata 350 ml; Refrigerante Coca-Cola 2 L; Arroz Tio João Tipo 1 5 kg; Leite Integral Italac 1 L; Carne Moída Patinho (kg); Refrigerante Guaraná Antarctica 2 L; Cerveja Brahma Lata 473 ml; Frango Coxa e Sobrecoxa (kg); Feijão Carioca Kicaldo 1 kg; Café Pilão Tradicional 500 g; Água Mineral Crystal 500 ml; Queijo Mussarela Fatiado (kg); Contrafilé (kg); Batata (kg); Banana Prata (kg); Tomate (kg); Ovos Brancos Grandes 12 un; Linguiça Toscana Seara (kg). **Decisão:** classe A tem prioridade na conferência de recebimento, no estoque mínimo e na negociação; classe C é candidata a estoque mínimo menor ou a sair do mix.

### 8.2.3 G03 — Quanto vendemos e quanto lucramos por dia? (“lucro do dia”, entrevista 6.20)

*Decisão: separar movimento de resultado; identificar dias fortes e fracos.*

```sql
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
```

Resultado (30 linhas):

| dia | dia_semana | vendas | faturamento | ticket_medio | lucro_bruto | margem_pct |
|--------------|--------------|--------------|--------------|--------------|--------------|--------------|
| 2026-09-01 | ter | 76 | 2738.68 | 36.04 | 830.69 | 30.3 |
| 2026-09-02 | qua | 76 | 2878.18 | 37.87 | 839.19 | 29.2 |
| 2026-09-03 | qui | 74 | 2281.57 | 30.83 | 695.44 | 30.5 |
| 2026-09-04 | sex | 98 | 3431.38 | 35.01 | 1015.63 | 29.6 |
| 2026-09-05 | sáb | 91 | 3340.03 | 36.70 | 1027.44 | 30.8 |
| 2026-09-06 | dom | 27 | 569.26 | 21.08 | 176.77 | 31.1 |
| 2026-09-07 | seg | 67 | 1828.83 | 27.30 | 543.28 | 29.7 |
| 2026-09-08 | ter | 76 | 2834.02 | 37.43 | 825.75 | 29.1 |
| 2026-09-09 | qua | 76 | 2853.44 | 37.55 | 849.94 | 29.8 |
| 2026-09-10 | qui | 75 | 3085.09 | 41.13 | 932.43 | 30.2 |

*Mostradas 10 de 30 linhas; resultado completo em `evidencias/03_resultados_consultas_gerenciais.txt`.*

**Leitura.** Sextas e sábados passam de R$ 3.000; os domingos (meio período) ficam abaixo de R$ 900. A margem diária é estável, entre 29,1% e 31,7%. **Decisão:** o “lucro do dia” que o gerente pediu (entrevista 6.20) agora existe; reforçar a escala de sexta e sábado e concentrar promoções nos dias fracos.

### 8.2.4 G04 — Quanto entrou em cada forma de pagamento e em cada caixa? (RF-37; PB-10)

*Decisão: negociar taxas com a operadora; dimensionar troco; ver o peso do fiado.*

```sql
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
```

Resultado (12 linhas):

| caixa | forma | transacoes | valor_bruto | taxa_contratada_pct | custo_estimado_taxa | pct_no_caixa |
|--------------|--------------|--------------|--------------|--------------|--------------|--------------|
| 1 | Dinheiro | 566 | 17756.56 | 0.00 | 0.00 | 31.1 |
| 1 | Cartão de débito | 478 | 15851.03 | 1.49 | 236.18 | 27.8 |
| 1 | Pix | 339 | 12697.03 | 0.00 | 0.00 | 22.2 |
| 1 | Cartão de crédito | 214 | 7154.32 | 3.19 | 228.22 | 12.5 |
| 1 | Vale-alimentação | 70 | 2317.18 | 6.00 | 139.03 | 4.1 |
| 1 | Fiado (caderno) | 43 | 1314.90 | 0.00 | 0.00 | 2.3 |
| 2 | Dinheiro | 184 | 6434.60 | 0.00 | 0.00 | 34.7 |
| 2 | Cartão de débito | 144 | 4946.02 | 1.49 | 73.70 | 26.7 |
| 2 | Pix | 116 | 3633.00 | 0.00 | 0.00 | 19.6 |
| 2 | Cartão de crédito | 74 | 2174.88 | 3.19 | 69.38 | 11.7 |
| 2 | Fiado (caderno) | 14 | 715.06 | 0.00 | 0.00 | 3.9 |
| 2 | Vale-alimentação | 26 | 634.98 | 6.00 | 38.10 | 3.4 |

**Leitura.** Dinheiro é a forma mais usada nos dois caixas (31% e 35%); o vale-alimentação tem a maior taxa (6%). As taxas custaram cerca de R$ 785 no mês. **Decisão:** negociar a taxa do vale e do crédito; incentivar o Pix (taxa zero); dimensionar o troco pelo volume de dinheiro.

### 8.2.5 G05 — LISTA DE VALIDADES: quais lotes vencem nos próximos dias? (prioridade nº 1; RF-17)

*Usa o prazo de alerta do produto ou, na falta dele, o da categoria (RNF-09). Decisão: promover, conferir na gôndola ou negociar troca antes de vencer.*

```sql
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
```

Resultado (3 linhas):

| produto | data_validade | dias_para_vencer | prazo_alerta | saldo | unidade | valor_em_risco_custo | acao_sugerida |
|------------|------------|------------|------------|------------|------------|------------|------------|
| Carne Moída Patinho (kg) | 2026-10-03 | 2 | 2 | 10.174 | KG | 339.81 | Promover hoje |
| Ovos Brancos Grandes 12 un | 2026-10-11 | 10 | 30 | 11.000 | UN | 101.20 | Acompanhar |
| Ovos Brancos Grandes 12 un | 2026-10-17 | 16 | 30 | 13.000 | UN | 119.60 | Acompanhar |

**Leitura.** Um lote de carne moída vence em 2 dias, com R$ 339,81 a preço de custo em risco. Os ovos aparecem porque o prazo de alerta da categoria é longo (30 dias). **Decisão:** promover a carne hoje; os demais, acompanhar. É a lista de validades que era a prioridade nº 1 do gerente.

### 8.2.6 G06 — O que está abaixo do estoque mínimo, quanto comprar e de quem? (RF-19; PB-02, PB-05)

*Sugestão = 7 dias da média vendida nos últimos 7 dias + mínimo − estoque atual. Fornecedor sugerido = menor último custo registrado. Decisão: montar o pedido do dia sem conferir gôndola por gôndola.*

```sql
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
```

Resultado (6 linhas):

| produto | estoque_atual | estoque_minimo | unidade | media_vendida_dia | sugestao_compra | fornecedor_mais_barato | ultimo_custo |
|------------|------------|------------|------------|------------|------------|------------|------------|
| Refrigerante Guaraná Antarctica 2 L | 0.000 | 18.000 | UN | 18.00 | 144 | Bebidas Leste | 6.2000 |
| Queijo Mussarela Fatiado (kg) | 0.413 | 2.000 | KG | 1.43 | 12 | Vale Verde | 32.0000 |
| Detergente Ypê Neutro 500 ml | 17.000 | 24.000 | UN | 5.43 | 45 | Limpeza Total | 1.9000 |
| Papel Higiênico Neve Pacote 4 rolos | 9.000 | 12.000 | UN | 5.43 | 41 | Limpeza Total | 6.4000 |
| Cerveja Brahma Lata 473 ml | 21.000 | 24.000 | UN | 29.57 | 210 | Bebidas Leste | 3.6000 |
| Contrafilé (kg) | 1.792 | 2.000 | KG | 1.38 | 10 | Frigo ZL | 46.8000 |

**Leitura.** O Guaraná 2 L está zerado e vende 18 unidades por dia; a sugestão é comprar 144, do fornecedor com menor último custo. **Decisão:** o pedido do dia sai da consulta, sem percorrer gôndola por gôndola. A média simples dos últimos 7 dias é o ponto de partida; a seção 10.4 (IA-1) mostra como melhorá-la.

### 8.2.7 G07 — Quem deve no fiado, quanto e há quanto tempo não paga? (PB-07, PB-08; RF-27)

*Decisão: cobrar, suspender novas compras ou rever o limite (PO-04).*

```sql
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
```

Resultado (7 linhas):

| cliente | apelido | saldo_devedor | limite_fiado | pct_limite | dias_sem_pagar | situacao |
|--------------|--------------|--------------|--------------|--------------|--------------|--------------|
| Severino Batista Souza | Seu Biu | 199.89 | 400.00 | 50 | 7 | Em dia |
| José Aparecido Lima | Zé da Oficina | 178.28 | 300.00 | 59 | 6 | Em dia |
| Maria das Graças Oliveira | Dona Graça | 164.54 | 350.00 | 47 | 3 | Em dia |
| Francisco de Assis Pereira | Chico | 149.01 | 150.00 | 99 | 23 | Nunca pagou — cobrar |
| Antônia Ferreira da Silva |  | 148.29 | 250.00 | 59 | 2 | Em dia |
| Cláudia Regina Matos |  | 92.46 | 200.00 | 46 | 10 | Em dia |
| Edson Rodrigues Moreira |  | 19.76 | 200.00 | 10 | 5 | Em dia |

**Leitura.** Sete clientes devem R$ 952,23 no total. Um deles (“Chico”) nunca pagou nada e já usa 99% do limite. **Decisão:** cobrar e reduzir o limite — executado na operação OP06 (seção 9.3).

### 8.2.8 G08 — Quais contas estão em aberto, por vencimento e prioridade? (RF-41; PB-14)

*Mostra o SALDO em aberto (pagamentos parciais já descontados — RN-38). Decisão: o que pagar primeiro quando o dinheiro não cobre tudo (PO-06).*

```sql
SELECT c.data_vencimento, c.prioridade, c.credor, c.descricao, c.categoria_despesa,
       c.valor_original, c.valor_principal_pago, c.saldo_em_aberto, c.situacao,
       CASE WHEN c.data_vencimento < @data_ref THEN CONCAT('VENCIDA há ', DATEDIFF(@data_ref, c.data_vencimento), ' dia(s)')
            WHEN c.data_vencimento <= DATE_ADD(@data_ref, INTERVAL 7 DAY) THEN 'Vence nesta semana'
            ELSE 'A vencer' END AS alerta
FROM vw_conta_pagar_situacao c
WHERE c.situacao IN ('ABERTA','PARCIALMENTE_PAGA')
ORDER BY c.data_vencimento, FIELD(c.prioridade, 'ALTA','MEDIA','BAIXA'), c.saldo_em_aberto DESC;
```

Resultado (75 linhas):

| data_vencimento | prioridade | credor | descricao | saldo_em_aberto | situacao | alerta |
|--------------|--------------|--------------|--------------|--------------|--------------|--------------|
| 2026-09-28 | ALTA | Frigorífico Zona Leste Ltda | NF 1075 — parcela 3/3 | 255.00 | ABERTA | VENCIDA há 3 dia(s) |
| 2026-09-29 | ALTA | Laticínios Vale Verde Ltda | NF 1151 — parcela 2/3 | 135.78 | PARCIALMENTE_PAGA | VENCIDA há 2 dia(s) |
| 2026-10-01 | ALTA | Laticínios Vale Verde Ltda | NF 1237 — parcela 1/3 | 287.42 | ABERTA | Vence nesta semana |
| 2026-10-01 | ALTA | Laticínios Vale Verde Ltda | NF 1182 — parcela 2/3 | 16.80 | ABERTA | Vence nesta semana |
| 2026-10-01 | ALTA | Laticínios Vale Verde Ltda | NF 1086 — parcela 3/3 | 16.80 | ABERTA | Vence nesta semana |
| 2026-10-01 | MEDIA | Limpeza Total Distribuidora Ltda | NF 1013 — parcela 3/3 | 373.84 | ABERTA | Vence nesta semana |
| 2026-10-01 | MEDIA | Limpeza Total Distribuidora Ltda | NF 1068 — parcela 1/3 | 234.40 | ABERTA | Vence nesta semana |
| 2026-10-01 | MEDIA | Limpeza Total Distribuidora Ltda | NF 1050 — parcela 2/3 | 97.33 | ABERTA | Vence nesta semana |
| 2026-10-02 | ALTA | Frigorífico Zona Leste Ltda | NF 1111 — parcela 3/3 | 160.00 | ABERTA | Vence nesta semana |
| 2026-10-02 | ALTA | Frigorífico Zona Leste Ltda | NF 1246 — parcela 1/3 | 38.33 | ABERTA | Vence nesta semana |

*Mostradas 10 de 75 linhas; resultado completo em `evidencias/03_resultados_consultas_gerenciais.txt`.*

**Leitura.** 75 contas em aberto; duas já vencidas (uma integral e uma parcialmente paga). **Decisão:** pagar primeiro as vencidas e as de prioridade ALTA (PO-06). A vencida do frigorífico é quitada na OP04.

### 8.2.9 G09 — PREVISÃO DE DISPONIBILIDADE: vai faltar dinheiro nos próximos 21 dias? (RF-35, RF-36, RN-39)

*Saldo inicial = saldo realizado (banco + cofre) + dinheiro nas gavetas abertas. Entradas previstas = recebíveis de cartão/Pix/vale ainda não conciliados, pela data   prevista de crédito (valor líquido da taxa). Vencidos e não creditados entram no 1º dia. Saídas previstas = saldo em aberto das contas, pelo vencimento (vencidas no 1º dia). Vendas futuras NÃO entram: a previsão é conservadora de propósito. Decisão: o ALERTA pedido pelo gerente (“sim, muito”): antecipar recebíveis, negociar prazo ou escolher, pela prioridade, o que pagar.*

```sql
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
```

Resultado (21 linhas):

| dia | entradas_previstas | saidas_previstas | saldo_previsto | alerta |
|--------------------|--------------------|--------------------|--------------------|--------------------|
| 2026-10-01 | 1598.86 | 1417.37 | 25759.95 |  |
| 2026-10-02 | 215.61 | 1862.13 | 24113.43 |  |
| 2026-10-03 | 140.87 | 2185.19 | 22069.11 |  |
| 2026-10-04 | 857.81 | 0.00 | 22926.92 |  |
| 2026-10-05 | 830.51 | 14608.33 | 9149.10 |  |
| 2026-10-06 | 103.09 | 3472.09 | 5780.10 |  |
| 2026-10-07 | 276.58 | 2021.50 | 4035.18 |  |
| 2026-10-08 | 412.62 | 635.96 | 3811.84 |  |
| 2026-10-09 | 349.48 | 1016.53 | 3144.79 |  |
| 2026-10-10 | 782.78 | 1603.94 | 2323.63 |  |
| 2026-10-11 | 328.79 | 0.00 | 2652.42 |  |
| 2026-10-12 | 465.59 | 480.83 | 2637.18 |  |
| 2026-10-13 | 84.56 | 2054.73 | 667.01 |  |
| 2026-10-14 | 241.51 | 1444.48 | -535.96 | ALERTA: saldo insuficiente |
| 2026-10-15 | 520.98 | 1764.92 | -1779.90 | ALERTA: saldo insuficiente |
| 2026-10-16 | 406.99 | 643.94 | -2016.85 | ALERTA: saldo insuficiente |
| 2026-10-17 | 492.86 | 510.20 | -2034.19 | ALERTA: saldo insuficiente |
| 2026-10-18 | 485.49 | 0.00 | -1548.70 | ALERTA: saldo insuficiente |
| 2026-10-19 | 533.23 | 330.84 | -1346.31 | ALERTA: saldo insuficiente |
| 2026-10-20 | 152.54 | 6193.40 | -7387.17 | ALERTA: saldo insuficiente |
| 2026-10-21 | 179.36 | 732.68 | -7940.49 | ALERTA: saldo insuficiente |

**Leitura.** O saldo previsto começa em R$ 25,7 mil, cai com a folha em 05/10 e fica negativo a partir de 14/10. **Decisão:** o alerta pedido pelo gerente (“sim, muito”, entrevista) dispara com 13 dias de antecedência — tempo para negociar prazo com fornecedores ou antecipar recebíveis. A leitura completa está na seção 10.3.

### 8.2.10 G10 — Quanto perdemos com vencimento e avaria, e em quais produtos? (RF-40; PB-04)

*Perda líquida = perdas − reposições recebidas do fornecedor (troca). Decisão: reduzir compra dos produtos que mais vencem; negociar troca; promover antes.*

```sql
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
```

Resultado (10 linhas):

| produto | categoria | perda_vencimento | perda_avaria | recuperado_na_troca | perda_liquida |
|----------------|----------------|----------------|----------------|----------------|----------------|
| Contrafilé (kg) | Carnes | 103.50 | 0.00 | 0.00 | 103.50 |
| Batata (kg) | Hortifruti | 0.00 | 25.70 | 0.00 | 25.70 |
| Refrigerante Coca-Cola 2 L | Bebidas | 0.00 | 14.80 | 0.00 | 14.80 |
| Cebola (kg) | Hortifruti | 0.00 | 14.10 | 0.00 | 14.10 |
| Feijão Carioca Kicaldo 1 kg | Alimentos básicos | 0.00 | 6.80 | 0.00 | 6.80 |
| Tomate (kg) | Hortifruti | 0.00 | 6.27 | 0.00 | 6.27 |
| Banana Prata (kg) | Hortifruti | 0.00 | 5.93 | 0.00 | 5.93 |
| Cerveja Skol Lata 350 ml | Bebidas | 0.00 | 2.75 | 0.00 | 2.75 |

*Mostradas 8 de 10 linhas; resultado completo em `evidencias/03_resultados_consultas_gerenciais.txt`.*

**Leitura.** O contrafilé vencido é a maior perda líquida (R$ 103,50). O presunto também venceu (R$ 162,99), mas o fornecedor repôs: perda líquida zero — a política de troca (PO-07) funcionando aparece no número. **Decisão:** comprar menos contrafilé ou promovê-lo antes; manter a troca com o fornecedor de frios.

### 8.2.11 G11 — De quem comprar? Último custo de cada produto por fornecedor (RF-07; PB-05)

*Só aparecem produtos comprados de mais de um fornecedor. Decisão: escolher o fornecedor do próximo pedido (ex.: o leite).*

```sql
SELECT p.nome_produto AS produto, f.nome_fantasia AS fornecedor,
       u.data_ultima_compra, u.preco_ultima_compra AS custo_unitario,
       ROUND(u.preco_ultima_compra - MIN(u.preco_ultima_compra) OVER (PARTITION BY u.id_produto), 4) AS diferenca_para_o_menor
FROM vw_ultimo_custo_fornecedor u
JOIN produto p    ON p.id_produto = u.id_produto
JOIN fornecedor f ON f.id_fornecedor = u.id_fornecedor
WHERE u.id_produto IN (SELECT id_produto FROM vw_ultimo_custo_fornecedor GROUP BY id_produto HAVING COUNT(*) > 1)
ORDER BY produto, custo_unitario;
```

Resultado (4 linhas):

| produto | fornecedor | data_ultima_compra | custo_unitario | diferenca_para_o_menor |
|--------------------|--------------------|--------------------|--------------------|--------------------|
| Arroz Tio João Tipo 1 5 kg | Atacadão Penha | 2026-09-30 | 24.9000 | 0.0000 |
| Arroz Tio João Tipo 1 5 kg | Nova Rota | 2026-09-15 | 25.4000 | 0.5000 |
| Leite Integral Italac 1 L | Vale Verde | 2026-09-29 | 4.6900 | 0.0000 |
| Leite Integral Italac 1 L | Nova Rota | 2026-09-15 | 5.2500 | 0.5600 |

**Leitura.** O leite custa R$ 4,69 na Vale Verde e R$ 5,25 na Nova Rota: R$ 0,56 de diferença por litro — o problema relatado na entrevista (“quase um real de diferença no leite”). **Decisão:** comprar da Vale Verde enquanto a diferença se mantiver.

### 8.2.12 G12 — O que foi pedido e ainda não chegou? (RF-10; PB-15)

*Decisão: cobrar o fornecedor; não pedir de novo o que já está a caminho.*

```sql
SELECT ps.id_pedido, ps.razao_social AS fornecedor, DATE(ps.data_hora_pedido) AS data_pedido, ps.situacao,
       x.nome_produto AS produto, x.quantidade_pedida, x.quantidade_recebida, x.quantidade_pendente
FROM vw_pedido_situacao ps
JOIN vw_item_pedido_pendencia x ON x.id_pedido = ps.id_pedido
WHERE ps.situacao IN ('ABERTO','PARCIALMENTE_RECEBIDO') AND x.quantidade_pendente > 0
ORDER BY ps.data_hora_pedido, produto;
```

Resultado (10 linhas):

| id_pedido | fornecedor | situacao | produto | quantidade_pedida | quantidade_recebida | quantidade_pendente |
|--------------|--------------|--------------|--------------|--------------|--------------|--------------|
| 33 | Laticínios Vale Verde Ltda | PARCIALMENTE_RECEBIDO | Leite Integral Italac 1 L | 72.000 | 71.000 | 1.000 |
| 47 | Laticínios Vale Verde Ltda | ABERTO | Hambúrguer Seara 672 g | 5.000 | 0.000 | 5.000 |
| 47 | Laticínios Vale Verde Ltda | ABERTO | Leite Integral Italac 1 L | 60.000 | 0.000 | 60.000 |
| 47 | Laticínios Vale Verde Ltda | ABERTO | Pão de Queijo Forno de Minas 400 g | 5.000 | 0.000 | 5.000 |
| 47 | Laticínios Vale Verde Ltda | ABERTO | Queijo Mussarela Fatiado (kg) | 10.000 | 0.000 | 10.000 |
| 48 | Limpeza Total Distribuidora Ltda | ABERTO | Água Sanitária Qboa 2 L | 24.000 | 0.000 | 24.000 |
| 48 | Limpeza Total Distribuidora Ltda | ABERTO | Detergente Ypê Neutro 500 ml | 72.000 | 0.000 | 72.000 |
| 48 | Limpeza Total Distribuidora Ltda | ABERTO | Esponja Scotch-Brite 3 un | 11.000 | 0.000 | 11.000 |

*Mostradas 8 de 10 linhas; resultado completo em `evidencias/03_resultados_consultas_gerenciais.txt`.*

**Leitura.** Falta chegar 1 caixa de leite do pedido 33 (entregue em parte) e os pedidos 47 e 48 de 30/09 ainda estão abertos. **Decisão:** cobrar a pendência; não pedir de novo o que já está a caminho.

### 8.2.13 G13 — Como foi cada operador no caixa? Vendas, ticket e diferenças de fechamento (PB-11, PB-12)

*Decisão: treinamento (RNF-04), escala e investigação de diferenças recorrentes.*

```sql
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
```

Resultado (4 linhas):

| operador | vendas | faturamento | ticket_medio | sessoes_fechadas | soma_diferencas_dinheiro |
|----------------|----------------|----------------|----------------|----------------|----------------|
| Juliana Alves Rocha | 600 | 21286.40 | 35.48 | 22 | -4.00 |
| Rafael Nogueira Dias | 637 | 20897.50 | 32.81 | 21 | -2.50 |
| Mariana Souza Prado | 525 | 18840.52 | 35.89 | 22 | 0.00 |
| Pedro Henrique Santos | 446 | 14605.14 | 32.75 | 17 | 0.00 |

**Leitura.** Os quatro operadores têm ticket médio parecido; as diferenças de dinheiro somadas no mês são pequenas (R$ −4,00 e R$ −2,50). **Decisão:** sem indício de problema recorrente; a consulta passa a ser o acompanhamento mensal (e a base para o treinamento do funcionário sem experiência, RNF-04).

### 8.2.14 G14 — Qual a margem de cada setor? (PO-09: margem de 35–40% nos itens comuns)

*Decisão: rever preços do setor cuja margem real ficou abaixo da política.*

```sql
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
```

Resultado (6 linhas):

| categoria | faturamento | custo_mercadoria | margem_sobre_venda_pct | markup_sobre_custo_pct |
|--------------------|--------------------|--------------------|--------------------|--------------------|
| Alimentos básicos | 17435.52 | 13002.50 | 25.4 | 34.1 |
| Carnes | 10630.78 | 7568.50 | 28.8 | 40.5 |
| Bebidas | 25499.88 | 17752.30 | 30.4 | 43.6 |
| Frios, laticínios e congelados | 10738.97 | 7435.91 | 30.8 | 44.4 |
| Limpeza | 4340.59 | 2912.00 | 32.9 | 49.1 |
| Hortifruti | 6960.05 | 4128.31 | 40.7 | 68.6 |

**Leitura.** Alimentos básicos têm a menor margem (25,4% sobre a venda; 34,1% sobre o custo); hortifruti a maior. **Decisão:** depende de como o gerente define a política de 35–40% (sobre a venda ou sobre o custo) — ponto a confirmar (seção 10.2).

### 8.2.15 G15 — Quais produtos giram menos? Dias de cobertura do estoque atual (entrevista 8.9)

*Cobertura = estoque atual ÷ média diária vendida no mês. Decisão: pedir menos dos itens parados (capital empatado e risco de vencer).*

```sql
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
```

Resultado (10 linhas):

| produto | estoque_atual | unidade | media_dia | dias_de_cobertura | capital_parado |
|----------------|----------------|----------------|----------------|----------------|----------------|
| Sal Refinado Cisne 1 kg | 18.000 | UN | 1.30 | 13.8 | 28.80 |
| Óleo de Soja Liza 900 ml | 58.000 | UN | 5.60 | 10.4 | 365.40 |
| Lentilha Yoki 500 g | 10.000 | UN | 1.03 | 9.7 | 61.00 |
| Macarrão Espaguete Renata 500 g | 48.000 | UN | 6.47 | 7.4 | 153.60 |
| Feijão Carioca Kicaldo 1 kg | 64.000 | UN | 9.30 | 6.9 | 435.20 |
| Água Sanitária Qboa 2 L | 24.000 | UN | 3.47 | 6.9 | 98.40 |
| Hambúrguer Seara 672 g | 4.000 | UN | 0.67 | 6.0 | 55.60 |
| Esponja Scotch-Brite 3 un | 11.000 | UN | 1.87 | 5.9 | 46.20 |

*Mostradas 8 de 10 linhas; resultado completo em `evidencias/03_resultados_consultas_gerenciais.txt`.*

**Leitura.** O sal tem estoque para quase 14 dias e o óleo para 10, com R$ 365,40 parados. **Decisão:** reduzir o próximo pedido desses itens e liberar capital para os de giro alto.

### 8.2.16 G16 — Quanto pagamos de juros por atraso? (entrevista, bloco 2e: o “prejuízo invisível”)

*Decisão: usar a previsão (G09) para evitar o atraso; renegociar prazos.*

```sql
SELECT cp.credor, cp.descricao, cp.data_vencimento, pc.data_pagamento,
       DATEDIFF(pc.data_pagamento, cp.data_vencimento) AS dias_atraso,
       pc.valor_principal, pc.valor_juros_multa
FROM pagamento_conta pc
JOIN conta_pagar cp ON cp.id_conta = pc.id_conta
WHERE pc.valor_juros_multa > 0
ORDER BY pc.data_pagamento;
```

Resultado (2 linhas):

| credor | descricao | data_vencimento | data_pagamento | dias_atraso | valor_principal | valor_juros_multa |
|--------------|--------------|--------------|--------------|--------------|--------------|--------------|
| Enel SP | Energia elétrica — 08/2026 | 2026-09-15 | 2026-09-17 | 2 | 1186.40 | 24.51 |
| Atacadão Alimentos Penha Ltda | NF 1049 — parcela 2/3 | 2026-09-23 | 2026-09-28 | 5 | 231.15 | 5.00 |

**Leitura.** Dois atrasos custaram R$ 29,51 em juros (a conta de luz paga 2 dias depois rendeu R$ 24,51 de encargos). **Decisão:** usar a previsão (G09) para não atrasar; é o “prejuízo invisível” descrito na entrevista.


# 9 Consultas de auditoria, operações e testes de restrição

## 9.1 Finalidade

A consulta gerencial responde “o que está acontecendo no negócio?”. A de auditoria responde “**os dados merecem confiança?**”. Cada uma procura um tipo de situação que não deveria existir; resultado vazio significa que a regra foi respeitada em todo o banco. Elas cobrem o que as restrições não alcançam: regras entre várias linhas ou tabelas (D-20), mínimos 1 de cardinalidade que a FK não garante (A21), a redundância controlada (A22) e erros de operação que o banco aceita mas o gerente precisa ver (preço abaixo do custo, diferença de caixa sem explicação).

## 9.2 Resultado das 22 auditorias — antes e depois das ações

As auditorias foram executadas duas vezes: logo após a carga (“antes”) e depois do script de operações, em que o gerente age sobre o que elas mostraram (“depois”). O SQL de todas está no Apêndice C.

| Cód. | O que procura (regra) | Por que importa | Antes | Ação tomada (script 07) | Depois |
|-----|------------------------|----------------------------|-------|------------------------|--------|
| A01 | Vendas concluídas cujo total não bate com a soma dos pagamentos (RN-21) | venda paga a menos ou a mais (erro de caixa ou de registro). | 0 | — | 0 |
| A02 | Itens de venda concluída sem baixa completa de estoque (RN-17, RN-22) | item cuja quantidade vendida (na unidade base) não foi toda baixada dos lotes — o estoque e o custo da venda estariam errados. | 0 | — | 0 |
| A03 | Lotes sem movimentação de entrada ou com saldo negativo (RN-16; cardinalidade LOTE 1,N) | “estoque fantasma” (lote sem origem) e baixa maior que o existente. | 0 | — | 0 |
| A04 | Venda fiada sem cliente identificado ou de cliente não autorizado (RN-24, PO-04) | fiado concedido fora da política. Limitação conhecida: o banco guarda a autorização VIGENTE do cliente, não o histórico dela; se o gerente suspender um cliente, as vendas antigas dele também aparecerão aqui. Por isso a suspensão do crédito é feita pelo limite (OP06). | 0 | — | 0 |
| A05 | Lotes sem data de validade em produto que controla validade (RN-15) | lote que nunca aparecerá na lista de validades (prioridade nº 1). | 2 | OP01 e OP02: validades lançadas | 0 |
| A06 | Sessões fechadas com diferença de caixa (dinheiro ou maquininhas) sem justificativa (RN-30) | sobra/falta que ninguém explicou. | 2 | OP03: justificativas registradas | 0 |
| A07 | Transações de cartão/Pix/vale não creditadas após a data prevista (RN-36) | dinheiro que a operadora deveria ter pago e não pagou (conciliação). Tolerância de 1 dia útil após a data prevista. | 1 | Contestar com a operadora (fora do banco) | 1 |
| A08 | Créditos conciliados com divergência de valor ou taxa (RN-36) | repasse menor que o previsto (taxa acima da contratada ou transação faltante). | 1 | Contestar a taxa com a operadora (fora do banco) | 1 |
| A09 | Contas a pagar: pagamento acima do valor original ou conta vencida sem quitação (RN-38) | erro de lançamento (pagou a mais) e obrigações em atraso (juros correndo). | 2 | OP04: parcela do frigorífico quitada com juros | 1 |
| A10 | Lotes vencidos ainda disponíveis para venda (RN-19; fluxo F3) | a rotina diária de validade não foi executada para esse lote. | 0 | — | 0 |
| A11 | Lotes de ajuste automático aguardando conferência física (RN-40) | venda feita com saldo do sistema insuficiente que ainda não foi conferida. | 1 | OP01: contagem registrada | 0 |
| A12 | Devoluções que somam mais do que foi vendido no item (RN-28) | devolução duplicada ou digitada errada. | 0 | — | 0 |
| A13 | Operações sensíveis feitas por quem não tinha a permissão (RN-07, RN-23, PO-11, PO-13, RNF-01) | o controle de acesso foi contornado (ex.: senha emprestada). A permissão é conferida NA DATA DA OPERAÇÃO (concessão e revogação), por isso revogar hoje não “suja” o passado. | 1 | Investigar (fato passado; não se apaga) | 1 |
| A14 | Preço vigente diferente do último preço registrado no histórico (RN-06) | preço alterado direto na embalagem, sem deixar histórico. | 0 | — | 0 |
| A15 | Itens vendidos abaixo do custo (preço praticado menor que o custo dos lotes baixados) | erro de preço, desconto exagerado ou custo de lote digitado errado. | 4 | OP09: permissão de alterar preço revogada | 4 |
| A16 | Baixa de venda feita em lote de outro produto (RN-17) | incoerência que a FK sozinha não impede (o lote é de um produto, o item é de uma embalagem — o produto dos dois precisa ser o mesmo). | 0 | — | 0 |
| A17 | Nota de um fornecedor atendendo pedido de outro fornecedor (RN-11, RN-12) | vínculo indevido entre recebimento e pedido. | 0 | — | 0 |
| A18 | Linha de nota cuja soma dos lotes difere da quantidade aceita (RN-14) | estoque gerado a mais ou a menos que o aceito na conferência. | 0 | — | 0 |
| A19 | Fundo de troco: abertura diferente do que ficou na gaveta no fechamento anterior do mesmo caixa | dinheiro que “sumiu” ou “apareceu” entre duas sessões. | 0 | — | 0 |
| A20 | Venda baixada de lote que já estava vencido na data da venda (RN-17, RN-19, PO-07) | venda de produto vencido (risco sanitário e de reclamação). | 0 | — | 0 |
| A21 | Cardinalidades mínimas 1 que a FK não consegue garantir (R02, R06, R12, R16, R27, R37) | “cabeçalho sem filho obrigatório”. A FK garante que o filho aponta para um pai existente, mas não que todo pai tenha ao menos um filho. Ex.: produto ativo sem embalagem ativa (não pode ser vendido — RN-03), pedido sem item, nota sem linha, venda sem item, devolução sem movimento de estoque. | 0 | — | 0 |
| A22 | Custo do lote diferente da sua origem (RN-19, RN-22; redundância controlada) | o custo copiado para o lote na entrada continua igual à fonte — linha da nota (valor unitário ÷ fator de conversão) ou, na reposição de troca, o custo do lote trocado. É a contrapartida de guardar o custo no lote (necessário para lotes sem nota). | 0 | — | 0 |


**Leitura dos achados — o que cada um significa e por que alguns continuam depois das ações:**

- **A05 (2 → 0) e A11 (1 → 0)** — o lote de margarina sem validade nunca apareceria na lista de validades, a prioridade nº 1 do gerente; o lote de ajuste automático do Guaraná (RN-40) aguardava contagem. As operações OP01 e OP02 registraram a contagem e as validades.
- **A06 (2 → 0)** — uma sobra de R$ 1,00 e uma diferença de R$ 15,00 nas maquininhas sem explicação. A OP03 registrou as justificativas.
- **A09 (2 → 1)** — duas parcelas vencidas. A OP04 quitou a do frigorífico com juros; a outra (parcialmente paga) **continua**, de propósito: pagar tudo hoje é uma decisão de caixa que depende da previsão G09. A auditoria continuará mostrando-a até ser paga — é o comportamento correto.
- **A07 e A08 (1 → 1)** — uma transação de débito não creditada há 18 dias e um repasse com taxa de 1,99% quando a contratada é 1,49% (R$ 3,99 a menos). A ação é **fora do banco**: contestar com a operadora. Os achados continuam até o crédito ou o estorno entrarem; nenhum UPDATE deve “apagar” essa evidência.
- **A13 (1 → 1)** — um desconto autorizado por uma operadora que não tem a permissão AUTORIZAR_DESCONTO (indício de senha emprestada). É um fato passado: não se corrige, investiga-se. Repare que a revogação feita pela OP09 **não** criou novos achados — antes da correção da seção 2.2, criava.
- **A15 (4 → 4)** — quatro vendas de Coca-Cola 2 L a R$ 1,99 em 17/09: o preço foi digitado como 1,99 em vez de 11,99 e corrigido às 11h40 (as duas alterações estão no histórico de preços). As vendas já aconteceram; o que se decide é **como evitar a repetição** — a OP09 retirou a permissão de alterar preço do funcionário envolvido.

## 9.3 Operações UPDATE e DELETE sobre os achados

O script `07_operacoes_update_delete.sql` simula a manhã de 01/10/2026: o gerente lê as consultas e age. Cada operação mostra o “antes”, a alteração (em transação quando envolve mais de uma tabela) e o “depois”. Nenhum identificador está fixo no código: as linhas são localizadas pelas mesmas condições das consultas, como faria o sistema.

| Op. | Comando | Origem | O que faz | Resultado |
|---|---|---|---|---|
| OP01 | INSERT + UPDATE | A11 | Contagem do lote de ajuste do Guaraná: entrada de 10 garrafas encontradas, validade lida, pendência baixada | Lote deixa de estar pendente; saldo 0 → 10 |
| OP02 | UPDATE | A05 | Validade da margarina lançada | O lote passa a aparecer na lista de validades |
| OP03 | UPDATE com JOIN em view | A06 | Justificativas das duas diferenças de caixa | Sessões sem justificativa: 2 → 0 |
| OP04 | INSERT em 2 tabelas, transação | A09, G08 | Pagamento da parcela vencida do frigorífico com multa de 2% + juros diários: primeiro a saída de dinheiro, depois o pagamento que aponta para ela | Situação ABERTA → PAGA; juros registrados |
| OP05 | INSERT + UPDATE, transação | RN-05/06 | Reajuste do leite: histórico e preço novo na mesma transação | Preço 6,29 → 6,49, com autor e motivo |
| OP06 | UPDATE | G07 | Limite de fiado do cliente que nunca pagou reduzido para R$ 100,00 | Saldo acima do limite: novas compras fiadas bloqueadas; a dívida continua registrada |
| OP07 | DELETE + INSERT | Cadastro | Vendedor saiu da distribuidora: contato removido, novo contato cadastrado | Contato é cadastro, não histórico: pode ser excluído |
| OP08 | DELETE | G12 | Item ainda não entregue retirado de um pedido em aberto | Só é possível porque nada foi recebido; a FK bloquearia o item já recebido (teste T28) |
| OP09 | UPDATE (não DELETE) | A15 | Revogação da permissão ALTERAR_PRECO, com data | O histórico de permissões é preservado (D-24) |

## 9.4 Testes negativos: o banco recusa o que deve recusar

Um banco que aceita os dados certos ainda não está provado; é preciso mostrar que ele **recusa os errados**. Cada teste abaixo tenta violar uma regra e só “passa” se o MySQL recusar com o código de erro esperado **e** se a mensagem citar a restrição esperada (1062 = UNIQUE, 1451/1452 = FK, 3819 = CHECK). Resultado: **32 de 32 testes passaram**.

| Teste | Tentativa (deve falhar) | Regra protegida | Restrição que barrou | Erro | Resultado |
|-----|----------------------------|---------------------------|----------------------|------|--------|
| T01 | Cadastrar segundo funcionário com o mesmo CPF | CPF identifica uma única pessoa | uq_funcionario_cpf (UNIQUE) | 1062 | Passou |
| T02 | Produto em categoria que não existe | RN-01: todo produto pertence a um setor existente | fk_produto_categoria (FOREIGN KEY) | 1452 | Passou |
| T03 | Produto vendido por peso contado em unidade | RN-02: produto pesado é contado em quilo | ck_produto_peso_kg (CHECK) | 3819 | Passou |
| T04 | Embalagem sem nenhum código de leitura | RN-04: toda forma de venda é identificável no caixa | ck_embalagem_codigo (CHECK) | 3819 | Passou |
| T05 | Dois produtos com o mesmo código de barras | O código lido no caixa aponta para uma só embalagem | uq_embalagem_barras (UNIQUE) | 1062 | Passou |
| T06 | Fator de conversão zero | D-01: vender fardo baixa a quantidade certa | ck_embalagem_fator (CHECK) | 3819 | Passou |
| T07 | Histórico de preço sem mudança de preço | RN-06: só se registra alteração real | ck_hp_precos (CHECK) | 3819 | Passou |
| T08 | Desconto em item de venda sem autorizador | RN-23: desconto só com autorização registrada | ck_iv_autorizacao (CHECK) | 3819 | Passou |
| T09 | Quantidade vendida negativa | Quantidade não pode ser negativa | ck_iv_qtd (CHECK) | 3819 | Passou |
| T10 | Autorizar fiado para cliente sem CPF | RN-24 / PO-04: fiado exige cliente identificado | ck_cliente_fiado_cpf (CHECK) | 3819 | Passou |
| T11 | Pagar fiado com a forma FIADO | RN-27: fiado não paga fiado | ck_ab_forma (CHECK) | 3819 | Passou |
| T12 | Pagamento por Pix sem NSU/ID da transação | RN-36: transação eletrônica precisa ser conciliável | ck_pv_nsu (CHECK) | 3819 | Passou |
| T13 | Registrar duas vezes a mesma transação de cartão | Impede duplicidade de recebíveis | uq_pv_nsu (UNIQUE) | 1062 | Passou |
| T14 | Lançar a mesma nota fiscal duas vezes | RN-12: nota identificada por emitente, modelo, série e número | uq_recebimento_nota (UNIQUE) | 1062 | Passou |
| T15 | Aceitar mais do que a nota faturou | RN-14: não se aceita mais do que foi faturado | ck_ir_aceita (CHECK) | 3819 | Passou |
| T16 | Lote apontando para linha de nota de OUTRO produto | R19: produto do lote = produto da linha da nota | fk_lote_item_receb (FOREIGN KEY composta) | 1452 | Passou |
| T17 | Lote de recebimento sem a linha da nota | RN-14: lote de nota nasce de uma linha | ck_lote_origem_nota (CHECK) | 3819 | Passou |
| T18 | Linha da nota atendendo pedido de outro produto | R18: linha só atende item pedido do mesmo produto | fk_ir_item_pedido (FOREIGN KEY composta) | 1452 | Passou |
| T19 | Perda registrada sem responsável | RN-18: perda exige funcionário responsável | ck_me_responsavel (CHECK) | 3819 | Passou |
| T20 | Baixa de venda sem apontar o item vendido | RN-17: toda baixa de venda aponta para o item | ck_me_venda (CHECK) | 3819 | Passou |
| T21 | Fechar sessão sem contar o dinheiro | RN-30: fechamento exige contagem e responsável | ck_sessao_fechamento (CHECK) | 3819 | Passou |
| T22 | Sangria que não chega ao cofre | RN-37: dinheiro que sai da gaveta fica registrado no cofre | ck_mc_cofre (CHECK) | 3819 | Passou |
| T23 | Usar a mesma saída de dinheiro para dois pagamentos de conta | R46: cada pagamento corresponde a uma saída de dinheiro | uq_pc_movimento (UNIQUE) | 1062 | Passou |
| T24 | Repasse de cartão lançado como débito | Coerência entre origem e sentido do movimento | ck_mf_origem (CHECK) | 3819 | Passou |
| T25 | Devolução em dinheiro sem registrar a saída da gaveta | RN-28 / RN-37: reembolso em dinheiro aparece no caixa | ck_dev_dinheiro (CHECK) | 3819 | Passou |
| T26 | Excluir produto que já tem embalagens, lotes e vendas | RNF-06 / PO-12: histórico não é apagado (FK sem CASCADE) | fk_embalagem_produto (RESTRICT) | 1451 | Passou |
| T27 | Excluir venda já registrada | RNF-06: venda é histórico; cancela-se por situação | fk_iv_venda (RESTRICT) | 1451 | Passou |
| T28 | Excluir item de pedido que já foi recebido | RN-11: o que chegou não some do pedido | fk_ir_item_pedido (RESTRICT) | 1451 | Passou |
| T29 | Fornecedor com CNPJ em formato inválido | Formato do documento (CNPJ alfanumérico desde 07/2026) | ck_fornecedor_doc (CHECK) | 3819 | Passou |
| T30 | Conta de despesa fixa apontando para nota de fornecedor | RN-32: só conta de fornecedor nasce de recebimento | ck_cp_origem (CHECK) | 3819 | Passou |
| T31 | Revogar uma permissão com data anterior à concessão | Histórico de permissões coerente (auditoria A13 depende dele) | ck_fp_periodo (CHECK) | 3819 | Passou |
| T32 | Linha de nota recusada com quantidade aceita | RN-14: situação da linha coerente com o aceito | ck_ir_situacao (CHECK) | 3819 | Passou |


