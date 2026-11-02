# Roteiro de defesa — perguntas que a banca fará

> **Atenção:** o manual da entrega final diz que a apresentação “seguirá manual específico disponibilizado pelo professor”. Esse manual **não** estava entre os arquivos usados para preparar este material. Antes de montar os slides, confiram tempo, formato e itens obrigatórios nele. Este roteiro cobre o que o manual da entrega final já anuncia: a banca vai perguntar **“de onde veio esta decisão?”** e **“como vocês provam que ela funciona?”** (seção 31).

Regra de ouro para responder: **decisão → regra de negócio que a exige → evidência no banco**. Sempre que possível, mostrem o arquivo de evidência ou rodem a consulta ao vivo.

## 1. As perguntas da seção 31 do manual

**“Por que esta tabela existe?”** — Exemplo: `item_recebimento`. Uma nota fiscal traz várias linhas, e o mesmo produto pode vir em duas linhas com validades diferentes; o pedido é atendido item a item (o leite faltante chega depois). Sem a linha da nota não há como ligar o que foi pedido ao que chegou, nem gerar um lote por validade. Prova: G12 mostra o leite pendente do pedido 33; cenário “mesma linha de nota gerando mais de um lote” em `evidencias/02_validacao_massa_dados.md`.

**“Por que esta FK está aqui?”** — Exemplo: `venda.id_sessao → sessao_caixa`. RN-20: não existe venda fora de uma sessão de caixa aberta; é a sessão que fecha o caixa e confere o dinheiro. NOT NULL porque a cardinalidade é (1,1) do lado da venda. Prova: seção 3.3 (conferência automática DER × lógico).

**“Por que utilizaram uma chave composta?”** — Exemplo: `item_venda (id_venda, numero_item)`. A linha só existe dentro da venda (dona) e é identificada pela posição no cupom. Não usamos (venda, embalagem) porque o mesmo produto pode ser lido duas vezes no mesmo cupom. Contraexemplo: `item_pedido (id_pedido, id_produto)` — ali a RN-10 diz que o produto aparece uma única vez no pedido, então o par **é** a identidade.

**“Como sabem que esta tabela está na 3FN?”** — Exemplo: `sessao_caixa`. Verificamos se algum atributo não chave dependia de outro: `situacao` dependia de `data_hora_fechamento` (vazia = aberta). Era transitiva — removemos e calculamos na view. Hoje todo atributo da sessão depende só de `id_sessao`. E sabemos dizer a exceção: `lote.id_produto` é redundante para lotes de nota, mas é necessário para lotes sem nota e a FK composta impede a divergência (teste T16).

**“Que regra esta constraint protege?”** — Exemplo: `ck_iv_autorizacao (desconto_unitario = 0 OR id_funcionario_autorizador IS NOT NULL)`: RN-23, desconto só com autorizador registrado. Prova: teste T08 — o banco recusa com erro 3819.

**“Que informação esta consulta produz?”** — Exemplo: G09. Dia a dia, o saldo previsto = dinheiro em banco e cofre + recebíveis de cartão/Pix pela data de crédito − contas pelo vencimento. Mostra que, sem contar vendas futuras, o dinheiro deixa de cobrir as contas em 14/10 (a folha de 05/10 é a maior saída).

**“Como esses dados poderiam apoiar uma decisão?”** — G09 dá 13 dias de antecedência para negociar prazo ou antecipar recebíveis — o alerta que o gerente pediu na entrevista. G11 mostra R$ 0,56 de diferença por litro de leite entre dois fornecedores: decisão de compra.

## 2. Perguntas prováveis sobre as decisões mais discutíveis

| Pergunta | Resposta curta | Evidência |
|---|---|---|
| Por que não usaram chave natural em tudo, como na 1ª entrega? | Nome de produto muda, data/hora colide, CPF não deve circular (LGPD). As naturais viraram UNIQUE: continuam impedindo duplicidade | Seção 3.4; T01, T05, T14 |
| Por que não usaram CASCADE? | Apagar produto apagaria vendas. Histórico não se apaga (RNF-06) | T26, T27, T28 |
| Por que não usaram triggers? | CHECK não vê outras linhas; trigger esconderia a regra e pararia a venda quando o estoque do sistema está errado (RN-40 manda não parar). Auditoria mostra sem bloquear | D-20; 22 auditorias |
| Por que o total da venda não é coluna? | É calculável; gravar cria duas verdades. Está em `vw_venda_resumo` | Seção 4.4, caso 13 |
| Por que DECIMAL e não FLOAT? | FLOAT não representa centavos exatamente | D-26 |
| Por que a permissão tem data de revogação? | Apagar a permissão fazia a auditoria acusar como irregulares operações feitas quando ela valia | Seção 2.2; A13 antes/depois |
| Por que VENDA — PAGAMENTO é (0,N) se toda venda é paga? | A venda cancelada não tem pagamento; o mínimo 1 vale para a concluída e é verificado pela A01 | Seção 2.2 |
| A massa foi feita por IA. Como sabem que está certa? | A IA escreveu um simulador com as regras; os dados foram carregados com todas as restrições ativas, passaram por 22 auditorias e 32 testes negativos; o ciclo gerou 9 correções reais | Seção 7.4; `docs/ia/prompts-ia.md` |
| Por que a margem ficou abaixo da política de 35–40%? | Provavelmente a política é markup sobre custo (35% de markup = 25,9% de margem). A G14 calcula as duas; é ponto a confirmar com o gerente | Seção 10.2 |
| O que o modelo ainda não faz? | Não guarda histórico da taxa da operadora nem do limite de fiado; massa de 30 dias não serve para treinar IA | Seção 14 |

## 3. Demonstração sugerida (5 minutos, ao vivo)

1. `mysql … < sql/script_completo.sql` — banco vazio até consultas em ~2 s, código de saída 0.
2. Rodar um teste negativo (ex.: T08, desconto sem autorizador) e mostrar o erro 3819 com o nome da restrição.
3. Rodar a G05 (lista de validades) e a G09 (previsão) — as duas prioridades do gerente.
4. Rodar a A13 antes e depois da OP09 e explicar por que o resultado **não** muda (permissão com vigência).

## 4. Divisão sugerida da fala

Cada integrante deve dominar ao menos um bloco e saber responder às perguntas do bloco vizinho: (1) problema e revisão do modelo; (2) modelo lógico e chaves; (3) normalização; (4) SQL, restrições e testes; (5) massa de dados e IA; (6) consultas gerenciais e de auditoria; (7) BI, IA e evolução.
