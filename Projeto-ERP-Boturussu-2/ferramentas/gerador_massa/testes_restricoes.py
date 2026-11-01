# -*- coding: utf-8 -*-
"""Testes de restrição: cada comando DEVE ser recusado pelo banco.
Gera sql/testes/08_testes_restricoes.sql e evidencias/07_testes_restricoes.md
com o erro que o MySQL realmente devolveu."""
import subprocess, sys, os, datetime

TESTES = [
 # (id, o que tenta, regra protegida, restrição esperada, código esperado, SQL)
 ("T01", "Cadastrar segundo funcionário com o mesmo CPF", "CPF identifica uma única pessoa", "uq_funcionario_cpf (UNIQUE)", 1062,
  "INSERT INTO funcionario (cpf, login, nome, funcao_principal) SELECT cpf, 'outro.login', 'Pessoa Duplicada', 'CAIXA' FROM funcionario WHERE id_funcionario = 2;"),
 ("T02", "Produto em categoria que não existe", "RN-01: todo produto pertence a um setor existente", "fk_produto_categoria (FOREIGN KEY)", 1452,
  "INSERT INTO produto (codigo_categoria, nome_produto, unidade_base) VALUES ('XXXX', 'Produto Fantasma', 'UN');"),
 ("T03", "Produto vendido por peso contado em unidade", "RN-02: produto pesado é contado em quilo", "ck_produto_peso_kg (CHECK)", 3819,
  "INSERT INTO produto (codigo_categoria, nome_produto, unidade_base, vendido_por_peso) VALUES ('HORTI', 'Mamão (kg)', 'UN', TRUE);"),
 ("T04", "Embalagem sem nenhum código de leitura", "RN-04: toda forma de venda é identificável no caixa", "ck_embalagem_codigo (CHECK)", 3819,
  "INSERT INTO embalagem (id_produto, descricao, fator_conversao, preco_venda) VALUES (1, 'Pacote sem código', 1, 30.00);"),
 ("T05", "Dois produtos com o mesmo código de barras", "O código lido no caixa aponta para uma só embalagem", "uq_embalagem_barras (UNIQUE)", 1062,
  "INSERT INTO embalagem (id_produto, codigo_barras, descricao, fator_conversao, preco_venda) SELECT 2, codigo_barras, 'Duplicada', 1, 9.99 FROM embalagem WHERE id_embalagem = 1;"),
 ("T06", "Fator de conversão zero", "D-01: vender fardo baixa a quantidade certa", "ck_embalagem_fator (CHECK)", 3819,
  "UPDATE embalagem SET fator_conversao = 0 WHERE id_embalagem = 1;"),
 ("T07", "Histórico de preço sem mudança de preço", "RN-06: só se registra alteração real", "ck_hp_precos (CHECK)", 3819,
  "INSERT INTO historico_preco (id_embalagem, id_funcionario, preco_anterior, preco_novo, motivo) VALUES (1, 2, 32.90, 32.90, 'CORRECAO');"),
 ("T08", "Desconto em item de venda sem autorizador", "RN-23: desconto só com autorização registrada", "ck_iv_autorizacao (CHECK)", 3819,
  "INSERT INTO item_venda (id_venda, numero_item, id_embalagem, quantidade, preco_unitario_praticado, desconto_unitario) VALUES (1, 99, 1, 1, 32.90, 5.00);"),
 ("T09", "Quantidade vendida negativa", "Quantidade não pode ser negativa", "ck_iv_qtd (CHECK)", 3819,
  "INSERT INTO item_venda (id_venda, numero_item, id_embalagem, quantidade, preco_unitario_praticado) VALUES (1, 98, 1, -2, 32.90);"),
 ("T10", "Autorizar fiado para cliente sem CPF", "RN-24 / PO-04: fiado exige cliente identificado", "ck_cliente_fiado_cpf (CHECK)", 3819,
  "INSERT INTO cliente (nome, autorizado_fiado, limite_fiado) VALUES ('Cliente Sem CPF', TRUE, 100.00);"),
 ("T11", "Pagar fiado com a forma FIADO", "RN-27: fiado não paga fiado", "ck_ab_forma (CHECK)", 3819,
  "INSERT INTO abatimento_fiado (id_cliente, codigo_forma, id_funcionario, data_hora, valor) VALUES (1, 'FIADO', 2, '2026-10-01 10:00:00', 10.00);"),
 ("T12", "Pagamento por Pix sem NSU/ID da transação", "RN-36: transação eletrônica precisa ser conciliável", "ck_pv_nsu (CHECK)", 3819,
  "INSERT INTO pagamento_venda (id_venda, numero_pagamento, codigo_forma, valor) VALUES (1, 9, 'PIX', 5.00);"),
 ("T13", "Registrar duas vezes a mesma transação de cartão", "Impede duplicidade de recebíveis", "uq_pv_nsu (UNIQUE)", 1062,
  "INSERT INTO pagamento_venda (id_venda, numero_pagamento, codigo_forma, valor, nsu_autorizacao) SELECT 1, 9, codigo_forma, 1.00, nsu_autorizacao FROM pagamento_venda WHERE nsu_autorizacao IS NOT NULL LIMIT 1;"),
 ("T14", "Lançar a mesma nota fiscal duas vezes", "RN-12: nota identificada por emitente, modelo, série e número", "uq_recebimento_nota (UNIQUE)", 1062,
  "INSERT INTO recebimento (id_fornecedor, id_funcionario, modelo_nota, serie_nota, numero_nota, data_hora, valor_total_nota, volumes_nota, volumes_conferidos, situacao) SELECT id_fornecedor, id_funcionario, modelo_nota, serie_nota, numero_nota, data_hora, valor_total_nota, volumes_nota, volumes_conferidos, situacao FROM recebimento WHERE id_recebimento = 1;"),
 ("T15", "Aceitar mais do que a nota faturou", "RN-14: não se aceita mais do que foi faturado", "ck_ir_aceita (CHECK)", 3819,
  "UPDATE item_recebimento SET quantidade_aceita = quantidade_nota * fator_conversao_compra + 1 WHERE id_recebimento = 1 AND numero_item_nota = 1;"),
 ("T16", "Lote apontando para linha de nota de OUTRO produto", "R19: produto do lote = produto da linha da nota", "fk_lote_item_receb (FOREIGN KEY composta)", 1452,
  "INSERT INTO lote (id_produto, id_recebimento, numero_item_nota, origem, data_entrada, custo_unitario) SELECT CASE WHEN ir.id_produto = 1 THEN 2 ELSE 1 END, ir.id_recebimento, ir.numero_item_nota, 'RECEBIMENTO', NOW(), 1.00 FROM item_recebimento ir WHERE ir.quantidade_aceita > 0 LIMIT 1;"),
 ("T17", "Lote de recebimento sem a linha da nota", "RN-14: lote de nota nasce de uma linha", "ck_lote_origem_nota (CHECK)", 3819,
  "INSERT INTO lote (id_produto, origem, data_entrada, custo_unitario) VALUES (1, 'RECEBIMENTO', NOW(), 24.90);"),
 ("T18", "Linha da nota atendendo pedido de outro produto", "R18: linha só atende item pedido do mesmo produto", "fk_ir_item_pedido (FOREIGN KEY composta)", 1452,
  "UPDATE item_recebimento SET id_pedido = (SELECT MIN(pc.id_pedido) FROM pedido_compra pc WHERE pc.id_pedido NOT IN (SELECT id_pedido FROM item_pedido WHERE id_produto = 38)) WHERE (id_recebimento, numero_item_nota) IN (SELECT * FROM (SELECT id_recebimento, numero_item_nota FROM item_recebimento WHERE id_produto = 38 LIMIT 1) x);"),
 ("T19", "Perda registrada sem responsável", "RN-18: perda exige funcionário responsável", "ck_me_responsavel (CHECK)", 3819,
  "INSERT INTO movimentacao_estoque (id_lote, data_hora, tipo, quantidade, motivo) VALUES (1, NOW(), 'PERDA_AVARIA', 1, 'Quebrou');"),
 ("T20", "Baixa de venda sem apontar o item vendido", "RN-17: toda baixa de venda aponta para o item", "ck_me_venda (CHECK)", 3819,
  "INSERT INTO movimentacao_estoque (id_lote, data_hora, tipo, quantidade) VALUES (1, NOW(), 'SAIDA_VENDA', 1);"),
 ("T21", "Fechar sessão sem contar o dinheiro", "RN-30: fechamento exige contagem e responsável", "ck_sessao_fechamento (CHECK)", 3819,
  "INSERT INTO sessao_caixa (numero_caixa, id_funcionario_abertura, data_hora_abertura, valor_inicial, data_hora_fechamento) VALUES (1, 2, '2026-10-01 07:00:00', 150.00, '2026-10-01 14:00:00');"),
 ("T22", "Sangria que não chega ao cofre", "RN-37: dinheiro que sai da gaveta fica registrado no cofre", "ck_mc_cofre (CHECK)", 3819,
  "INSERT INTO movimentacao_caixa (id_sessao, id_funcionario, data_hora, tipo, valor, motivo) VALUES (1, 2, '2026-09-01 10:00:00', 'SANGRIA', 300.00, 'Teste');"),
 ("T23", "Usar a mesma saída de dinheiro para dois pagamentos de conta", "R46: cada pagamento corresponde a uma saída de dinheiro", "uq_pc_movimento (UNIQUE)", 1062,
  "INSERT INTO pagamento_conta (id_conta, numero_pagamento, id_funcionario, id_movimento_fin, data_pagamento, valor_principal) SELECT id_conta, 9, 1, id_movimento_fin, data_pagamento, 1.00 FROM pagamento_conta LIMIT 1;"),
 ("T24", "Repasse de cartão lançado como débito", "Coerência entre origem e sentido do movimento", "ck_mf_origem (CHECK)", 3819,
  "INSERT INTO movimento_financeiro (id_conta_financeira, data_movimento, natureza, origem, valor_bruto) VALUES (1, '2026-10-01', 'DEBITO', 'REPASSE_CARTAO', 100.00);"),
 ("T25", "Devolução em dinheiro sem registrar a saída da gaveta", "RN-28 / RN-37: reembolso em dinheiro aparece no caixa", "ck_dev_dinheiro (CHECK)", 3819,
  "INSERT INTO devolucao (id_venda, numero_item, id_funcionario, data_hora, quantidade_devolvida, motivo, destino, forma_reembolso, valor_reembolsado) VALUES (1, 1, 2, NOW(), 1, 'DEFEITO', 'DESCARTE', 'DINHEIRO', 5.00);"),
 ("T26", "Excluir produto que já tem embalagens, lotes e vendas", "RNF-06 / PO-12: histórico não é apagado (FK sem CASCADE)", "fk_embalagem_produto (RESTRICT)", 1451,
  "DELETE FROM produto WHERE id_produto = 1;"),
 ("T27", "Excluir venda já registrada", "RNF-06: venda é histórico; cancela-se por situação", "fk_iv_venda (RESTRICT)", 1451,
  "DELETE FROM venda WHERE id_venda = 1;"),
 ("T28", "Excluir item de pedido que já foi recebido", "RN-11: o que chegou não some do pedido", "fk_ir_item_pedido (RESTRICT)", 1451,
  "DELETE ip FROM item_pedido ip JOIN item_recebimento ir ON ir.id_pedido = ip.id_pedido AND ir.id_produto = ip.id_produto;"),
 ("T29", "Fornecedor com CNPJ em formato inválido", "Formato do documento (CNPJ alfanumérico desde 07/2026)", "ck_fornecedor_doc (CHECK)", 3819,
  "INSERT INTO fornecedor (tipo_documento, documento, razao_social, canal_pedido) VALUES ('CNPJ', '1234567/000199', 'Teste', 'WHATSAPP');"),
 ("T30", "Conta de despesa fixa apontando para nota de fornecedor", "RN-32: só conta de fornecedor nasce de recebimento", "ck_cp_origem (CHECK)", 3819,
  "INSERT INTO conta_pagar (id_recebimento, credor, descricao, categoria_despesa, valor_original, data_vencimento) VALUES (1, 'Enel SP', 'Luz', 'LUZ', 100.00, '2026-10-20');"),
 ("T31", "Revogar uma permissão com data anterior à concessão", "Histórico de permissões coerente (auditoria A13 depende dele)", "ck_fp_periodo (CHECK)", 3819,
  "UPDATE funcionario_permissao SET data_revogacao = DATE_SUB(data_concessao, INTERVAL 1 DAY) WHERE id_funcionario = 1 LIMIT 1;"),
 ("T32", "Linha de nota recusada com quantidade aceita", "RN-14: situação da linha coerente com o aceito", "ck_ir_situacao (CHECK)", 3819,
  "UPDATE item_recebimento SET situacao_item = 'RECUSADO' WHERE quantidade_aceita > 0 LIMIT 1;"),
]

def roda(sql):
    p = subprocess.run(["mysql", "-uroot", "--default-character-set=utf8mb4", "mercado_boturussu", "-e",
                        "SET NAMES utf8mb4; START TRANSACTION; " + sql + " ROLLBACK;"],
                       capture_output=True, text=True)
    return p.returncode, (p.stderr or "").strip()

def main(sql_out, md_out):
    linhas_sql = ["-- =====================================================================",
                  "-- 08_testes_restricoes.sql — TESTES NEGATIVOS DAS RESTRIÇÕES",
                  "-- Cada comando abaixo DEVE FALHAR. Execute com:",
                  "--   mysql -u root --force mercado_boturussu < sql/testes/08_testes_restricoes.sql",
                  "-- (--force continua após cada erro). O resultado obtido está em evidencias/07_testes_restricoes.md.",
                  "-- Cada teste está entre START TRANSACTION e ROLLBACK: nada é gravado.",
                  "-- =====================================================================",
                  "USE mercado_boturussu;", "SET NAMES utf8mb4;", ""]
    md = ["# Evidência — testes negativos das restrições", "",
          f"Executado em {datetime.date.today().isoformat()} no MySQL 8.0, sobre o banco recém-criado e carregado com a massa de dados.",
          "Cada linha tenta violar uma regra. **Passou** = o banco recusou com o erro esperado.", "",
          "| Teste | O que tenta fazer | Regra protegida | Restrição | Erro esperado | Resultado obtido | Situação |",
          "|---|---|---|---|---|---|---|"]
    ok = 0
    for (tid, oque, regra, restr, esperado, sql) in TESTES:
        linhas_sql += [f"-- {tid} — {oque}", f"-- Regra: {regra} | Esperado: erro {esperado} ({restr})",
                       "START TRANSACTION;", sql, "ROLLBACK;", ""]
        rc, err = roda(sql)
        obtido = err.replace("ERROR ", "").split("\n")[-1] if err else "(sem erro)"
        cod = None
        if err.startswith("ERROR"):
            try: cod = int(err.split()[1])
            except Exception: pass
        passou = rc != 0 and cod == esperado and restr.split()[0] in err   # exige o código E o nome da restrição
        ok += passou
        md.append(f"| {tid} | {oque} | {regra} | `{restr}` | {esperado} | `{obtido.replace('|', '/')}` | {'Passou' if passou else 'FALHOU'} |")
    md += ["", f"**Resultado: {ok} de {len(TESTES)} testes passaram.**"]
    open(sql_out, "w", encoding="utf-8").write("\n".join(linhas_sql) + "\n")
    open(md_out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(ok, "/", len(TESTES))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
