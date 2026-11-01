# Normalização — 1FN, 2FN e 3FN

*Extraído das seções 4 e 5 do documento da entrega final.*

## 4.1 Método

A normalização foi feita tabela por tabela com a pergunta de cada forma normal: **1FN** — cada campo guarda um único valor? **2FN** — em chave composta, cada atributo depende da chave *toda*? **3FN** — o atributo depende diretamente da chave ou de outro atributo? As definições de dependência funcional e das formas normais seguem Elmasri e Navathe (2018) e Heuser (2009). Para cada caso relevante apresentamos o formato pedido pelo manual da disciplina (FERRARO, 2026): estrutura analisada → dependência funcional → problema → correção.

Dois cuidados para não “inventar erros”:

- Os casos abaixo são decisões **reais** deste projeto. Alguns foram resolvidos já no modelo conceitual (a primeira entrega já evitava listas e repetições); outros foram descobertos **nesta fase** e mudaram o modelo (marcados como *descoberto nesta fase*).
- Também registramos o que **parece** violar uma forma normal e não viola (seção 4.5), e a única redundância mantida de propósito, com a proteção que a torna segura (seção 4.6). Saber dizer “isto não é dependência funcional” é parte de entender a 3FN.

Notação: `A → B` significa “conhecido A, B fica determinado” (dependência funcional).

## 4.2 Primeira forma normal (1FN): um campo, um valor

**Caso 1 — Contatos do fornecedor (atributo multivalorado e composto).**

- ANTES: `FORNECEDOR(id_fornecedor, razao_social, …, contatos)`, com `contatos = "Fábio 11 9…; Renata 11 9…"`.
- DEPENDÊNCIA: `id_fornecedor →→ {(nome, telefone, whatsapp)}` — um fornecedor tem **vários** contatos (entrevista 3.11: “cada distribuidora manda um vendedor”).
- PROBLEMA: lista dentro de um campo. Não dá para procurar o fornecedor pelo telefone, garantir o formato do telefone, nem trocar só um vendedor.
- DEPOIS: `FORNECEDOR(id_fornecedor, razao_social, …)` e `CONTATO_FORNECEDOR(id_fornecedor, numero_contato, nome, telefone, usa_whatsapp)`, PK (id_fornecedor, numero_contato). O telefone ganhou CHECK de formato; a troca de vendedor é um DELETE + INSERT (operação OP07).

**Caso 2 — Endereço do cliente (atributo composto).**

- ANTES: `CLIENTE(…, endereco)` com “Rua X, 120, fundos, Parque Boturussu”.
- PROBLEMA: um campo com quatro informações. Para cobrar fiado por bairro ou achar o “Seu Biu da Rua X” seria preciso recortar texto.
- DEPOIS: `logradouro`, `numero_endereco`, `complemento`, `bairro` — uma coluna por componente.

**Caso 3 — Identificação da nota fiscal (atributo composto).**

- ANTES: `RECEBIMENTO(…, modelo_serie_numero)`.
- DEPENDÊNCIA: a nota é identificada por `(id_fornecedor, modelo, série, número)` — o número sozinho se repete em séries diferentes (RN-12).
- PROBLEMA: com os três valores em um campo, o banco não consegue impor a unicidade correta nem validar cada parte.
- DEPOIS: `modelo_nota`, `serie_nota`, `numero_nota` em colunas separadas, com `uq_recebimento_nota (id_fornecedor, modelo_nota, serie_nota, numero_nota)` e CHECKs de faixa em cada uma. A chave de acesso da NF-e (44 posições), quando existe, é outra UNIQUE.

**Caso 4 — Relacionamentos N:N.** Produto–fornecedor e funcionário–permissão poderiam ser guardados como “lista de fornecedores do produto” ou “lista de permissões do funcionário”. Viraram as tabelas associativas `produto_fornecedor` e `funcionario_permissao` (seção 3.2). Da mesma forma, não existe `telefone1, telefone2` nem `produto1, produto2` em nenhuma tabela.

**Verificação geral:** todas as 30 tabelas têm PK e todas as 232 colunas têm tipo atômico (número, data, texto curto ou booleano). Nenhuma coluna guarda lista, JSON ou valores separados por vírgula.

## 4.3 Segunda forma normal (2FN): depende da chave toda?

A 2FN só pode ser violada onde há chave composta. As oito tabelas com PK composta foram verificadas; os casos instrutivos:

**Caso 5 — Item de venda: operador × autorizador.**

- ESTRUTURA ANALISADA: `ITEM_VENDA(id_venda, numero_item, id_embalagem, quantidade, preco_unitario_praticado, desconto_unitario, id_funcionario_operador?, data_hora?, id_funcionario_autorizador)`.
- DEPENDÊNCIAS: `id_venda → id_funcionario_operador, data_hora` (o operador e o momento são da venda inteira) e `(id_venda, numero_item) → id_funcionario_autorizador` (o desconto é autorizado item a item).
- PROBLEMA: operador e data/hora dependeriam de **parte** da chave. Um cupom de 20 itens repetiria 20 vezes o mesmo operador — e bastaria um erro para o mesmo cupom ter dois operadores.
- DEPOIS: operador e data/hora ficam em `VENDA(id_venda, …, id_funcionario, data_hora)`; o autorizador do desconto fica em `ITEM_VENDA`, porque depende da chave toda. É exatamente por isso que a mesma tabela `funcionario` é referenciada pelas duas: são papéis diferentes, em níveis diferentes.

**Caso 6 — Linha da nota fiscal.**

- ESTRUTURA: `ITEM_RECEBIMENTO(id_recebimento, numero_item_nota, id_produto, …, id_fornecedor?, data_hora?, nome_produto?)`.
- DEPENDÊNCIAS: `id_recebimento → id_fornecedor, data_hora`; `id_produto → nome_produto`.
- PROBLEMA: dependência parcial (fornecedor e data dependem só da nota) e dado de outra entidade (nome do produto).
- DEPOIS: fornecedor e data ficam em `RECEBIMENTO`; o nome fica em `PRODUTO`. A linha guarda só o que depende da linha: produto, pedido atendido, quantidades, valor e resultado da conferência.

**Caso 7 — Permissões.**

- ESTRUTURA: `FUNCIONARIO_PERMISSAO(id_funcionario, codigo_permissao, data_concessao, data_revogacao, descricao_permissao?, nome_funcionario?)`.
- DEPENDÊNCIAS: `codigo_permissao → descricao_permissao`; `id_funcionario → nome_funcionario`.
- DEPOIS: a descrição fica em `PERMISSAO`, o nome em `FUNCIONARIO`. Na associativa só ficam as datas, que dependem da chave toda: a mesma pessoa pode ter a mesma permissão concedida, revogada e concedida de novo, e cada período é uma linha (*descoberto nesta fase*, seção 2.2).

**Caso 8 — Pedido e item do pedido.** `ITEM_PEDIDO(id_pedido, id_produto, quantidade_pedida, preco_negociado)`: quantidade e preço negociado dependem do par (o mesmo produto tem preço diferente em cada pedido). `id_pedido → id_fornecedor, data_hora_pedido` ficam em `PEDIDO_COMPRA`. Está na 2FN.

**Demais tabelas de PK composta** (`contato_fornecedor`, `produto_fornecedor`, `pagamento_venda`, `pagamento_conta`): os atributos não chave dependem da chave toda — por exemplo, em `pagamento_venda`, a forma, o valor e o NSU são de **cada transação** (venda + sequência), não da venda.

## 4.4 Terceira forma normal (3FN): depende da chave ou de outro atributo?

**Caso 9 — Situação da sessão de caixa** *(descoberto nesta fase)*.

- ANTES: `SESSAO_CAIXA(id_sessao, …, data_hora_fechamento, situacao)`.
- DEPENDÊNCIAS: `id_sessao → data_hora_fechamento` e `data_hora_fechamento → situacao` (vazia = ABERTA; preenchida = FECHADA).
- PROBLEMA: dependência transitiva. O banco aceitaria uma sessão “ABERTA” com data de fechamento — e o fechamento de caixa dependeria de alguém lembrar de atualizar dois campos.
- DEPOIS: `situacao` saiu da tabela e é calculada na view `vw_sessao_conferencia`. O CHECK `ck_sessao_fechamento` exige que data, responsável e valor contado sejam preenchidos juntos.

**Caso 10 — Código do item no catálogo do fornecedor.**

- ESTRUTURA ANALISADA: `ITEM_PEDIDO(id_pedido, id_produto, …, codigo_no_fornecedor)`.
- DEPENDÊNCIAS: `id_pedido → id_fornecedor` e `(id_fornecedor, id_produto) → codigo_no_fornecedor`.
- PROBLEMA: o código depende do par fornecedor–produto, que só é alcançado **através** do pedido: dependência transitiva. Cada pedido repetiria o código; se o fornecedor mudasse o código, pedidos antigos e novos discordariam.
- DEPOIS: `codigo_no_fornecedor` está em `PRODUTO_FORNECEDOR(id_fornecedor, id_produto)`, onde depende da chave toda.

**Caso 11 — Produto na movimentação de estoque.**

- ESTRUTURA ANALISADA: `MOVIMENTACAO_ESTOQUE(id_movimentacao, id_lote, id_produto?, …)`.
- DEPENDÊNCIAS: `id_movimentacao → id_lote` e `id_lote → id_produto`.
- PROBLEMA: guardar o produto na movimentação seria dependência transitiva e permitiria uma baixa “do lote de leite” registrada “no produto café”.
- DEPOIS: a movimentação não tem `id_produto`; quem precisa do produto o obtém pelo lote (a view `vw_movimentacao_valorizada` já faz o JOIN).

**Caso 12 — Taxa e prazo do pagamento.**

- ESTRUTURA ANALISADA: `PAGAMENTO_VENDA(id_venda, numero_pagamento, codigo_forma, valor, taxa_percentual?, prazo_credito_dias?)`.
- DEPENDÊNCIAS: `(id_venda, numero_pagamento) → codigo_forma` e `codigo_forma → taxa_percentual, prazo_credito_dias`.
- DEPOIS: taxa e prazo ficam em `FORMA_PAGAMENTO`. Data prevista do crédito e valor líquido previsto são calculados (`vw_pagamento_venda_previsao`).

**Caso 13 — Atributos que podiam ser calculados a partir de outras linhas** *(descoberto nesta fase)*. Não são violações clássicas da 3FN (a dependência não é entre colunas da mesma linha), mas produzem o mesmo defeito — a mesma informação em dois lugares:

| Atributo removido | De onde ele já podia ser obtido | Risco se fosse gravado | Agora é calculado em |
|---|---|---|---|
| `lote.quantidade_inicial` | Quantidade da movimentação de entrada do lote | Lote dizendo 24 e movimentação dizendo 12 | `vw_lote_saldo` |
| `lote.situacao = 'ESGOTADO'` | Saldo do lote igual a zero | Lote “esgotado” com saldo 3 | `vw_lote_saldo` (saldo) |
| `produto_fornecedor.preco_ultima_compra`, `data_ultima_compra` | Linhas de nota recebidas do par | Sugestão de fornecedor com preço velho | `vw_ultimo_custo_fornecedor` |

O mesmo critério já valia na primeira entrega para os totais e saldos marcados como derivados no DER (total da venda, saldo do fiado, saldo da conta a pagar, estoque atual…): nenhum deles é coluna; os 14 cálculos estão nas views (lista no dicionário, Apêndice A).

## 4.5 O que parece violar a 3FN e não viola

**Preço praticado no item de venda.** Parece que `item_venda.preco_unitario_praticado` depende de `id_embalagem → preco_venda`. Não depende: o preço da embalagem **muda com o tempo** (seis alterações no mês da massa de dados), e o item precisa guardar o preço daquele momento. Não existe a dependência funcional `id_embalagem → preço praticado`, porque a mesma embalagem foi vendida a preços diferentes (cinco embalagens na massa). É uma fotografia do fato, exigida pela RN-22 para que o faturamento de setembro não mude quando o preço mudar em outubro.

**Valor unitário da nota e custo do lote.** O mesmo raciocínio vale para o custo: é o valor daquela compra, não um atributo do produto.

## 4.6 A redundância mantida de propósito — e por que ela é segura

**`lote.id_produto`.** Para lotes que vieram de nota, existe a cadeia `id_lote → (id_recebimento, numero_item_nota) → id_produto`, e `id_produto` no lote seria transitivo. Ele foi mantido porque:

1. **Há lotes sem nota** (inventário inicial, ajuste automático da RN-40, reposição do fornecedor). Para eles o lote é o único lugar onde o produto pode estar. Tirar a coluna obrigaria a criar uma estrutura diferente para cada origem.
2. **A redundância não pode divergir**: a FK composta `fk_lote_item_receb (id_recebimento, numero_item_nota, id_produto)` obriga o produto do lote a ser o mesmo da linha da nota. O banco recusa a divergência (teste T16).

**`lote.custo_unitario`.** Pelo mesmo motivo (lotes sem nota precisam de custo), o custo é gravado no lote, inclusive nos que vêm de nota, onde ele é `valor_unitario_nota ÷ fator_conversao_compra`. Como uma igualdade com cálculo não cabe em FK, ela é verificada pela auditoria **A22** (custo do lote igual ao da origem, também na reposição de troca), que retorna zero linhas.

Essa é a diferença entre redundância descontrolada e **redundância controlada**: ela existe por um motivo de negócio, está documentada e há um mecanismo que impede ou detecta a divergência.

## 4.7 Conclusão da normalização

| Forma normal | Como foi verificada | Resultado |
|---|---|---|
| 1FN | Nenhuma coluna guarda lista ou grupo repetitivo; compostos decompostos; multivalorado em tabela própria | Atende — casos 1 a 4 |
| 2FN | As 8 tabelas com PK composta: cada atributo não chave depende da chave toda | Atende — casos 5 a 8 |
| 3FN | Nenhum atributo não chave depende de outro atributo não chave; derivados em views | Atende — casos 9 a 13 |
| Exceção consciente | `lote.id_produto` e `lote.custo_unitario` (lotes de nota) | Protegidas por FK composta e pela auditoria A22 |


# Decisões do modelo físico


As decisões D-01 a D-19 foram justificadas na primeira entrega revisada. As decisões abaixo são desta fase e respondem à pergunta “por que foi feito assim?” no nível físico.

| ID | Decisão | Alternativa descartada | Por quê |
|---|---|---|---|
| D-20 | Regras entre várias linhas ou tabelas são verificadas por **consultas de auditoria**, não por triggers | Triggers em cada tabela | CHECK no MySQL só enxerga a própria linha. Triggers esconderiam a regra dentro do banco, tornariam a carga lenta e difícil de testar e bloqueariam a venda quando o estoque do sistema está errado (RN-40 manda **não** parar a fila). A auditoria mostra o problema sem impedir a operação |
| D-21 | Atributos derivados ficam em **views** | Colunas atualizadas pela aplicação | Uma só verdade; impossível o total da venda divergir dos itens (seção 4.4) |
| D-22 | Nenhuma FK com CASCADE | ON DELETE CASCADE | Um DELETE em produto apagaria o histórico de vendas (RNF-06, PO-12) |
| D-23 | FKs compostas para coerência de produto (superchave `uq_ir_lote_ref`) | FKs simples + verificação depois | O banco impede o erro em vez de só detectá-lo (seção 3.6) |
| D-24 | Permissão com vigência (`data_revogacao`); revogar não apaga | DELETE da permissão | O passado precisa continuar auditável (seção 2.2) |
| D-25 | `lote.id_produto` e `lote.custo_unitario` mantidos | Remover e criar uma estrutura por origem de lote | Seção 4.6 |
| D-26 | Tipos: `DECIMAL(12,2)` para dinheiro; `DECIMAL(12,4)` para custo unitário; `DECIMAL(12,3)` para quantidade; `INT UNSIGNED` para identificadores | `FLOAT`/`DOUBLE` | FLOAT não representa 0,10 exatamente: somas de dinheiro sairiam com centavos errados. Custo unitário precisa de 4 casas (fardo de R$ 49,90 ÷ 12 = 4,1583). Quantidade com 3 casas cobre o grama na balança (RNF-10) |
| D-27 | CHECKs citam códigos naturais estáveis (`'DIN'`, `'FIADO'`) | Colunas indicadoras extras | Os códigos são chaves naturais fixas (D-13); evita duplicar o que a forma de pagamento já diz |
| D-28 | Documento do fornecedor `VARCHAR(14)` aceitando CNPJ alfanumérico; chave de NF-e `CHAR(44)` | `BIGINT` para CNPJ | Desde julho de 2026 o CNPJ pode ter letras (BRASIL, 2024); um campo numérico recusaria os novos fornecedores. A chave da NF-e tem sempre 44 posições |
| D-29 | MySQL 8.0 (≥ 8.0.16), InnoDB, `utf8mb4` | MySQL 5.7 / MyISAM | Antes da 8.0.16 o MySQL **ignorava** CHECK em silêncio (ORACLE, 2026); MyISAM não tem FK nem transação; `utf8mb4` grava “ç”, “ã” e emojis do WhatsApp sem perda. Testado em 8.0.46 |
| D-30 | Relacionamento 1:1 = FK + UNIQUE no lado opcional | Fundir as tabelas | Pagamento de conta e movimento financeiro têm ciclos de vida diferentes (o movimento pode ser tarifa, repasse…) |
| D-31 | Data de referência das consultas em variável (`@data_ref`) | `CURRENT_DATE` fixo no SQL | Os resultados entregues são reprodutíveis em qualquer dia; em produção basta `SET @data_ref = CURRENT_DATE` |

