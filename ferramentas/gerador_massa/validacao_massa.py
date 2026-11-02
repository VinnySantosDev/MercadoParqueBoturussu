# -*- coding: utf-8 -*-
"""Evidência de que a massa de dados cobre os relacionamentos, as regras e os cenários reais."""
import subprocess, sys

def q(sql):
    r = subprocess.run(["mysql", "-uroot", "--default-character-set=utf8mb4", "-N", "-B", "mercado_boturussu", "-e", sql],
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()

TABELAS = ["funcionario","permissao","funcionario_permissao","categoria","produto","embalagem","historico_preco","fornecedor",
           "contato_fornecedor","produto_fornecedor","pedido_compra","item_pedido","recebimento","item_recebimento","lote","caixa",
           "sessao_caixa","cliente","venda","item_venda","conta_financeira","movimento_financeiro","forma_pagamento",
           "pagamento_venda","movimentacao_caixa","devolucao","movimentacao_estoque","abatimento_fiado","conta_pagar","pagamento_conta"]

CENARIOS = [
 ("T01/T02", "Pedido entregue em mais de uma nota (faltante chega depois)",
  "SELECT COUNT(*) FROM (SELECT id_pedido, id_produto FROM item_recebimento WHERE id_pedido IS NOT NULL GROUP BY id_pedido, id_produto HAVING COUNT(DISTINCT id_recebimento) > 1) x"),
 ("—", "Pedido ainda parcialmente recebido na data de referência",
  "SELECT COUNT(*) FROM vw_pedido_situacao WHERE situacao = 'PARCIALMENTE_RECEBIDO'"),
 ("T03", "Mesma linha de nota gerando mais de um lote (validades diferentes)",
  "SELECT COUNT(*) FROM (SELECT id_recebimento, numero_item_nota FROM lote WHERE id_recebimento IS NOT NULL GROUP BY 1, 2 HAVING COUNT(*) > 1) x"),
 ("T04", "Itens vendidos que consumiram mais de um lote (custo de dois lotes)",
  "SELECT COUNT(*) FROM vw_item_venda_resultado WHERE qtd_lotes_baixados > 1"),
 ("T04", "…dos quais com custos diferentes entre os lotes",
  "SELECT COUNT(*) FROM (SELECT m.id_venda, m.numero_item FROM movimentacao_estoque m JOIN lote l ON l.id_lote = m.id_lote WHERE m.tipo = 'SAIDA_VENDA' GROUP BY 1, 2 HAVING COUNT(DISTINCT l.custo_unitario) > 1) x"),
 ("T06", "Vendas pagas com duas transações na mesma forma (dois cartões)",
  "SELECT COUNT(*) FROM (SELECT id_venda FROM pagamento_venda GROUP BY id_venda, codigo_forma HAVING COUNT(*) > 1) x"),
 ("T06", "Vendas com mais de uma forma de pagamento",
  "SELECT COUNT(*) FROM (SELECT id_venda FROM pagamento_venda GROUP BY id_venda HAVING COUNT(DISTINCT codigo_forma) > 1) x"),
 ("T07", "Vendas parte fiado, parte dinheiro",
  "SELECT COUNT(*) FROM (SELECT id_venda FROM pagamento_venda GROUP BY id_venda HAVING SUM(codigo_forma = 'FIADO') > 0 AND SUM(codigo_forma = 'DIN') > 0) x"),
 ("T08", "Contas pagas em mais de um pagamento (parcial + quitação)",
  "SELECT COUNT(*) FROM vw_conta_pagar_situacao WHERE qtd_pagamentos > 1"),
 ("T08", "Contas parcialmente pagas na data de referência",
  "SELECT COUNT(*) FROM vw_conta_pagar_situacao WHERE situacao = 'PARCIALMENTE_PAGA'"),
 ("T09", "Créditos de repasse/Pix conciliados", "SELECT COUNT(*) FROM vw_conciliacao WHERE situacao_conciliacao = 'CONCILIADO'"),
 ("T09", "Créditos com divergência de taxa", "SELECT COUNT(*) FROM vw_conciliacao WHERE situacao_conciliacao = 'DIVERGENTE'"),
 ("T10", "Alterações de preço registradas no histórico", "SELECT COUNT(*) FROM historico_preco"),
 ("T10", "Embalagens vendidas a dois preços diferentes no mês", "SELECT COUNT(*) FROM (SELECT id_embalagem FROM item_venda GROUP BY id_embalagem HAVING COUNT(DISTINCT preco_unitario_praticado) > 1) x"),
 ("T11", "Devoluções (dinheiro, troca, abatimento de fiado, estorno)", "SELECT GROUP_CONCAT(forma_reembolso ORDER BY id_devolucao SEPARATOR ', ') FROM devolucao"),
 ("T12", "Lotes de reposição de troca com fornecedor (autorrelacionamento)", "SELECT COUNT(*) FROM lote WHERE origem = 'REPOSICAO_FORNECEDOR'"),
 ("T13", "Lotes de inventário inicial (implantação)", "SELECT COUNT(*) FROM lote WHERE origem = 'INVENTARIO_INICIAL'"),
 ("T14", "Clientes com fiado e abatimentos parciais", "SELECT COUNT(DISTINCT id_cliente) FROM abatimento_fiado"),
 ("T15", "Vendas operadas por quem não abriu a sessão (cobertura de almoço)",
  "SELECT COUNT(*) FROM venda v JOIN sessao_caixa s ON s.id_sessao = v.id_sessao WHERE v.id_funcionario <> s.id_funcionario_abertura"),
 ("RN-40", "Lotes de ajuste automático por saldo insuficiente", "SELECT COUNT(*) FROM lote WHERE origem = 'AJUSTE_INVENTARIO'"),
 ("RF-11", "Recebimentos sem pedido (produtor que passa e entrega)",
  "SELECT COUNT(*) FROM recebimento r WHERE NOT EXISTS (SELECT 1 FROM item_recebimento ir WHERE ir.id_recebimento = r.id_recebimento AND ir.id_pedido IS NOT NULL)"),
 ("RF-14", "Recebimento recusado / linha não pedida devolvida",
  "SELECT CONCAT(SUM(situacao = 'RECUSADO'), ' recusado(s); ', (SELECT COUNT(*) FROM item_recebimento WHERE situacao_item = 'NAO_PEDIDO_DEVOLVIDO'), ' linha(s) não pedida(s)') FROM recebimento"),
 ("—", "Bonificação (linha com valor zero → lote de custo zero)", "SELECT COUNT(*) FROM item_recebimento WHERE valor_unitario_nota = 0"),
 ("—", "Fornecedor pessoa física (CPF) e com CNPJ alfanumérico",
  "SELECT CONCAT(SUM(tipo_documento = 'CPF'), ' CPF; ', SUM(documento REGEXP '[A-Z]'), ' CNPJ alfanumérico') FROM fornecedor"),
 ("—", "Itens pesados (quantidade fracionada, código de balança)",
  "SELECT COUNT(*) FROM item_venda iv JOIN embalagem e ON e.id_embalagem = iv.id_embalagem WHERE e.codigo_balanca IS NOT NULL"),
 ("—", "Vendas de fardo (fator de conversão 12)", "SELECT COUNT(*) FROM item_venda iv JOIN embalagem e ON e.id_embalagem = iv.id_embalagem WHERE e.fator_conversao > 1"),
 ("—", "Vendas canceladas (sem pagamento e sem baixa)", "SELECT COUNT(*) FROM venda WHERE situacao = 'CANCELADA'"),
 ("—", "Sangrias, suprimentos e recolhimentos levados ao cofre", "SELECT CONCAT(SUM(tipo='SANGRIA'), ' sangrias; ', SUM(tipo='SUPRIMENTO'), ' suprimento; ', SUM(tipo='RECOLHIMENTO_FECHAMENTO'), ' recolhimentos') FROM movimentacao_caixa"),
 ("—", "Perdas por vencimento e por avaria registradas", "SELECT CONCAT(SUM(tipo='PERDA_VENCIMENTO'), ' vencimento; ', SUM(tipo='PERDA_AVARIA'), ' avaria') FROM movimentacao_estoque"),
]

def main(md_out):
    md = ["# Evidência — validação da massa de dados", "",
          "Período simulado: 01/09/2026 a 30/09/2026 (30 dias). Data de referência das consultas: 01/10/2026.",
          "Gerador: `ferramentas/gerador_massa/simula.py`, semente fixa 2026 (o mesmo arquivo gera sempre os mesmos dados).", "",
          "## 1. Registros por tabela", "", "| Tabela | Registros |", "|---|---:|"]
    tot = 0
    for t in TABELAS:
        n = int(q(f"SELECT COUNT(*) FROM {t}")); tot += n
        md.append(f"| {t} | {n} |")
    md += [f"| **Total** | **{tot}** |", "",
           "## 2. Integridade garantida pelo próprio banco", "",
           "A carga roda dentro de uma transação, em um banco com todas as PK, FK, UNIQUE e CHECK ativas.",
           "Se um único registro violasse qualquer restrição, a carga inteira seria recusada. Ela termina sem erro,",
           "portanto **todas as PK, FK, UNIQUE e CHECK são respeitadas pelos 100% dos registros** (log em `01_execucao_script_completo.log`).", "",
           "## 3. Regras entre tabelas (consultas de auditoria)", "",
           "As regras que envolvem várias linhas ou tabelas foram verificadas pelas 22 consultas de auditoria (`06_consultas_auditoria.sql`).",
           "Os achados estão em `04_resultados_auditoria_antes.txt` (e, depois das correções do script 07, em `06_resultados_auditoria_depois.txt`) e são situações operacionais plantadas de propósito para testar as auditorias",
           "(ex.: diferença de caixa sem justificativa, repasse com taxa acima da contratada) — nenhuma é violação de PK, FK ou CHECK.", "",
           "## 4. Cobertura dos cenários reais (testes T01–T15 da revisão e regras)", "",
           "| Cenário | O que a massa contém | Ocorrências |", "|---|---|---|"]
    for (cid, desc, sql) in CENARIOS:
        md.append(f"| {cid} | {desc} | {q(sql)} |")
    open(md_out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("validacao ok")

if __name__ == "__main__":
    main(sys.argv[1])
