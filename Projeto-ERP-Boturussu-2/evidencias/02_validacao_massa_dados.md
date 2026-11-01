# Evidência — validação da massa de dados

Período simulado: 01/09/2026 a 30/09/2026 (30 dias). Data de referência das consultas: 01/10/2026.
Gerador: `ferramentas/gerador_massa/simula.py`, semente fixa 2026 (o mesmo arquivo gera sempre os mesmos dados).

## 1. Registros por tabela

| Tabela | Registros |
|---|---:|
| funcionario | 6 |
| permissao | 12 |
| funcionario_permissao | 35 |
| categoria | 6 |
| produto | 38 |
| embalagem | 42 |
| historico_preco | 6 |
| fornecedor | 8 |
| contato_fornecedor | 11 |
| produto_fornecedor | 52 |
| pedido_compra | 48 |
| item_pedido | 198 |
| recebimento | 56 |
| item_recebimento | 231 |
| lote | 290 |
| caixa | 2 |
| sessao_caixa | 82 |
| cliente | 10 |
| venda | 2210 |
| item_venda | 5431 |
| conta_financeira | 2 |
| movimento_financeiro | 679 |
| forma_pagamento | 6 |
| pagamento_venda | 2268 |
| movimentacao_caixa | 86 |
| devolucao | 4 |
| movimentacao_estoque | 5858 |
| abatimento_fiado | 11 |
| conta_pagar | 159 |
| pagamento_conta | 86 |
| **Total** | **17933** |

## 2. Integridade garantida pelo próprio banco

A carga roda dentro de uma transação, em um banco com todas as PK, FK, UNIQUE e CHECK ativas.
Se um único registro violasse qualquer restrição, a carga inteira seria recusada. Ela termina sem erro,
portanto **todas as PK, FK, UNIQUE e CHECK são respeitadas pelos 100% dos registros** (log em `01_execucao_script_completo.log`).

## 3. Regras entre tabelas (consultas de auditoria)

As regras que envolvem várias linhas ou tabelas foram verificadas pelas 22 consultas de auditoria (`06_consultas_auditoria.sql`).
Os achados estão em `04_resultados_auditoria_antes.txt` (e, depois das correções do script 07, em `06_resultados_auditoria_depois.txt`) e são situações operacionais plantadas de propósito para testar as auditorias
(ex.: diferença de caixa sem justificativa, repasse com taxa acima da contratada) — nenhuma é violação de PK, FK ou CHECK.

## 4. Cobertura dos cenários reais (testes T01–T15 da revisão e regras)

| Cenário | O que a massa contém | Ocorrências |
|---|---|---|
| T01/T02 | Pedido entregue em mais de uma nota (faltante chega depois) | 3 |
| — | Pedido ainda parcialmente recebido na data de referência | 1 |
| T03 | Mesma linha de nota gerando mais de um lote (validades diferentes) | 1 |
| T04 | Itens vendidos que consumiram mais de um lote (custo de dois lotes) | 98 |
| T04 | …dos quais com custos diferentes entre os lotes | 2 |
| T06 | Vendas pagas com duas transações na mesma forma (dois cartões) | 3 |
| T06 | Vendas com mais de uma forma de pagamento | 57 |
| T07 | Vendas parte fiado, parte dinheiro | 6 |
| T08 | Contas pagas em mais de um pagamento (parcial + quitação) | 1 |
| T08 | Contas parcialmente pagas na data de referência | 1 |
| T09 | Créditos de repasse/Pix conciliados | 487 |
| T09 | Créditos com divergência de taxa | 1 |
| T10 | Alterações de preço registradas no histórico | 6 |
| T10 | Embalagens vendidas a dois preços diferentes no mês | 5 |
| T11 | Devoluções (dinheiro, troca, abatimento de fiado, estorno) | DINHEIRO, TROCA_MESMO_PRODUTO, ABATER_FIADO, ESTORNO_ELETRONICO |
| T12 | Lotes de reposição de troca com fornecedor (autorrelacionamento) | 1 |
| T13 | Lotes de inventário inicial (implantação) | 59 |
| T14 | Clientes com fiado e abatimentos parciais | 6 |
| T15 | Vendas operadas por quem não abriu a sessão (cobertura de almoço) | 80 |
| RN-40 | Lotes de ajuste automático por saldo insuficiente | 2 |
| RF-11 | Recebimentos sem pedido (produtor que passa e entrega) | 8 |
| RF-14 | Recebimento recusado / linha não pedida devolvida | 1 recusado(s); 1 linha(s) não pedida(s) |
| — | Bonificação (linha com valor zero → lote de custo zero) | 1 |
| — | Fornecedor pessoa física (CPF) e com CNPJ alfanumérico | 1 CPF; 1 CNPJ alfanumérico |
| — | Itens pesados (quantidade fracionada, código de balança) | 1086 |
| — | Vendas de fardo (fator de conversão 12) | 198 |
| — | Vendas canceladas (sem pagamento e sem baixa) | 2 |
| — | Sangrias, suprimentos e recolhimentos levados ao cofre | 2 sangrias; 1 suprimento; 82 recolhimentos |
| — | Perdas por vencimento e por avaria registradas | 4 vencimento; 28 avaria |
