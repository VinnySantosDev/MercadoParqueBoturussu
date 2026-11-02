# Contribuição e histórico de commits

O manual avalia **histórico de commits (3%)**, **evidências colaborativas (3%)** e, na dimensão atitudinal, participação, colaboração e entrega dos itens sob responsabilidade de cada um. E alerta: “não concentrem todos os commits em um único integrante ou apenas no final”.

Este arquivo **não** é a evidência — a evidência é o histórico do Git. Ele organiza o trabalho para que o histórico mostre, com verdade, quem fez o quê. Um histórico fabricado (commits feitos por uma pessoa em nome de outras, ou datas forjadas) é falta ética e é facilmente percebido; não façam isso.

## 1. Divisão sugerida por bloco

Os nomes ao lado de cada bloco devem ser preenchidos pela equipe. Cada bloco tem um responsável e um revisor (outra pessoa), para que haja colaboração registrada.

| Bloco | Arquivos | Responsável | Revisor |
|---|---|---|---|
| Revisão da 1ª entrega e requisitos | `docs/revisao/`, `docs/requisitos/` | | |
| DER e modelo lógico | `docs/diagramas/`, `docs/modelo-logico/`, `ferramentas/gerador_massa/fis.py`, `spec.py` | | |
| Normalização e decisões físicas | `docs/normalizacao/` | | |
| DDL, views e restrições | `sql/ddl/`, `sql/testes/` | | |
| Massa de dados e uso de IA | `sql/dados/`, `ferramentas/gerador_massa/simula.py`, `docs/ia/` | | |
| Consultas gerenciais | `sql/consultas/`, `docs/consultas/` | | |
| Consultas de auditoria e operações | `sql/auditoria/`, `sql/dml/` | | |
| Dicionário de dados | `docs/dicionario-dados/` | | |
| BI e IA | `docs/bi-ia/` | | |
| Documento final e README | `docs/entrega-final/`, `README.md` | | |
| Apresentação e defesa | `apresentacao/` | | |

## 2. Sequência de commits que acompanha o manual

O manual exige “negócio → modelo → banco”, nunca SQL primeiro. O histórico deve contar essa ordem:

1. `docs: primeira entrega original e revisada após a devolutiva`
2. `revisao: quadro de alterações e regras atualizadas (RN-31, RN-42…)`
3. `modelo-logico: conversão entidades/relacionamentos e justificativa das PKs`
4. `normalizacao: 1FN/2FN/3FN; situacao da sessão passa a ser derivada`
5. `ddl: tabelas, PK, FK, UNIQUE, CHECK e DEFAULT`
6. `ddl: views dos atributos derivados`
7. `dicionario: dicionário gerado da mesma fonte do DDL`
8. `dados: gerador da massa e INSERTs; prompts de IA documentados`
9. `testes: testes negativos das restrições`
10. `consultas: gerenciais G01–G16`
11. `auditoria: A01–A22 e operações UPDATE/DELETE`
12. `evidencias: execução integral em banco vazio`
13. `bi-ia: indicadores, painéis e casos de IA`
14. `docs: documento final e README`
15. `apresentacao: roteiro de defesa e slides`

Mensagens boas dizem **o que** mudou e **por quê**: `normalizacao: remove preco_ultima_compra de produto_fornecedor (derivado das notas)` é melhor que `atualizações`.

## 3. Como registrar a colaboração

- Cada bloco em um *branch* próprio e incorporado por **pull request** revisado por outro integrante (o comentário de revisão é a evidência de colaboração).
- Divergências de modelagem discutidas em *issues* (ex.: “VENDA — PAGAMENTO deve ser (0,N)?”), com a decisão registrada.
- Commits ao longo do período do projeto, não todos no último dia.
