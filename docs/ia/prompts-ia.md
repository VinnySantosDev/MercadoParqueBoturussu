# Uso de IA no projeto e prompts utilizados

O manual da entrega final (etapa 17) permite usar IA na elaboração de scripts e da massa de dados, desde que (1) os prompts usados na geração em escala sejam documentados e (2) o grupo verifique se o resultado respeita PKs, FKs e constraints, faz sentido para o negócio e não cria inconsistências. Este arquivo cumpre o item (1); o item (2) está em `evidencias/` e na seção 7 do documento final.

## 1. Ferramenta

- **Claude** (assistente de IA da Anthropic), usado em conversa.
- Entradas fornecidas à IA: manual da primeira entrega, devolutiva do professor, primeira entrega do grupo, roteiro de 100 perguntas da entrevista com o gerente e manual da entrega final.

## 2. Como a IA foi usada — e como NÃO foi usada

A IA **não** gerou registros diretamente (“gere 500 vendas”). Pedido assim, um modelo de linguagem produz dados que *parecem* plausíveis mas não fecham entre si: estoque que fica negativo, pagamentos que não somam o total da venda, lote vendido antes de entrar, cliente fiado sem CPF.

Em vez disso, a IA escreveu um **programa** — `ferramentas/gerador_massa/simula.py` — que simula a operação do mercado aplicando as regras do modelo. Os registros saem do programa, que é:

- **determinístico** (semente 2026): a mesma execução gera sempre os mesmos dados;
- **auditável**: as regras estão no código, em funções com nome (ex.: `baixa_fefo`, `rn40`, `paga_conta`, `gera_contas`);
- **corrigível**: quando um teste falhou, corrigiu-se o programa ou o modelo e gerou-se tudo de novo.

## 3. Prompts utilizados (na íntegra)

### Prompt 1 — revisão da primeira entrega

> Aqui temos 4 arquivos, um se refere ao manual de entrega, outro sobre a devolutiva da entrega, outro sobre a entrega e outro são 100 perguntas para compreendermos o estabelecimento. veja que foi pedido que revisados na entrega 1. Quero que corrija todos os apontamentos e deixe de forma impecável. no final gere um relatório do antes de depois para que eu veja a diferença e me explique o por que esta certo ou errado. caso identifique que não há necessidade alteração me informe o por que também.

Instrução permanente dada à IA durante todo o trabalho:

> Seja meu parceiro de debate, seja crítico comigo, ache meus pontos fracos e ache meus pontos cegos, para de concordar comigo e busque sempre a verdade (…). Seja direto e duro, se precisar me contrariar, contrarie. Se não tiver certeza de algo, diga que não tem certeza e verifique na internet antes.

### Prompt 2 — entrega final (inclui a geração da massa de dados em escala)

> quero que de acordo com todas as analises feitas anteriormente, atenda e faça perfeitamente o que esta sendo pedido nesse documento que mandei da entrega final. não é permitido erros, quero todos os documentos e me explique de forma impecável tudo que esta sendo feito.

## 4. Especificação que guiou o gerador da massa de dados

Os prompts acima são curtos; o que de fato determinou os dados foi a especificação abaixo, montada a partir do manual, da devolutiva e da entrevista. Ela está registrada aqui para que qualquer pessoa entenda **por que** os dados são como são e possa pedir a outra ferramenta o mesmo resultado.

> Escreva um programa em Python que gere os INSERTs do banco `mercado_boturussu` (MySQL 8) simulando 30 dias de operação do Supermercado Parque Boturussu, de 01/09/2026 a 30/09/2026, com data de referência 01/10/2026 e semente aleatória fixa 2026.
>
> **Cadastros:** 6 funcionários com permissões individuais (gerente com todas; quem confere nota altera preço; um funcionário sem experiência de caixa); 12 permissões; 6 categorias (hortifruti, bebidas, limpeza, alimentos básicos, frios/laticínios/congelados, carnes); 38 produtos e 42 embalagens (lata e fardo de 12, itens pesados com código de balança, item sem código de fábrica com código interno de prefixo 2); 8 fornecedores (um produtor pessoa física com CPF e um com CNPJ alfanumérico), com contatos; 10 clientes, 7 autorizados no fiado com limite; 2 caixas; 6 formas de pagamento (dinheiro, débito D+1 1,49%, crédito D+30 3,19%, Pix, vale D+30 6%, fiado); conta bancária e cofre.
>
> **Regras obrigatórias:** nenhum valor derivado é gravado (totais, saldos e situações vêm das views); todo saldo nasce de movimentação; baixa FEFO lote a lote, com uma movimentação por lote; se o saldo não bastar, criar lote de AJUSTE_INVENTARIO pendente de conferência (RN-40); inventário inicial em lotes próprios (RN-41); cada linha aceita da nota gera um lote por validade e a soma dos lotes é igual à quantidade aceita; o preço praticado é o vigente no momento da venda e toda alteração de preço gera histórico com autor; a soma dos pagamentos de venda concluída é igual ao total; fiado só para cliente autorizado; sangria, suprimento e recolhimento passam pelo cofre; repasses de cartão e Pix creditam na data prevista e liquidam as transações (conciliação); compra à vista gera conta quitada no ato e compra a prazo gera parcelas de 7/14/21 dias; despesas fixas (folha, Simples Nacional, água, luz, internet) sem recebimento.
>
> **Cenários que precisam aparecer** (pedidos na devolutiva): pedido entregue em mais de uma nota; pedido ainda parcialmente recebido; uma linha de nota com duas validades; itens que consomem dois lotes de custos diferentes; venda com dois cartões; venda parte fiado, parte dinheiro; conta paga em parcelas e conta parcialmente paga na data de referência; alterações de preço; devoluções nas quatro formas de reembolso; troca com fornecedor e lote de reposição; cobertura de almoço no caixa; recebimento sem pedido; recebimento recusado; bonificação; vendas canceladas.
>
> **Situações erradas plantadas** (para as auditorias encontrarem; não podem violar PK, FK ou CHECK): um lote sem validade; uma sobra de caixa e uma diferença de maquininha sem justificativa; uma transação de débito nunca creditada; um repasse com taxa acima da contratada; uma conta vencida sem pagamento; um desconto autorizado por quem não tem a permissão; um preço digitado errado (11,99 → 1,99) e corrigido horas depois.

## 5. Verificação do resultado (gerar → testar → validar → corrigir)

| Etapa | O que foi feito | Evidência |
|---|---|---|
| Gerar | O simulador produz `sql/dados/04_massa_dados.sql` | `ferramentas/gerador_massa/` |
| Testar | Carga em banco vazio, com todas as PK, FK, UNIQUE e CHECK ativas, dentro de uma transação | `evidencias/01_execucao_script_completo.log` |
| Testar | 32 tentativas de violar regras (todas recusadas pelo banco) | `evidencias/07_testes_restricoes.md` |
| Validar | 22 auditorias de regras entre tabelas | `evidencias/04_…antes.txt`, `evidencias/06_…depois.txt` |
| Validar | Contagem de cobertura de cada cenário exigido | `evidencias/02_validacao_massa_dados.md` |
| Corrigir | Lista das correções que este ciclo provocou no modelo e no gerador | Documento final, seção 7.4 |

## 6. Responsabilidade

A IA auxiliou; a responsabilidade técnica é do grupo. Por isso cada integrante deve ser capaz de explicar as decisões — `apresentacao/roteiro-defesa.md` reúne as perguntas que o manual diz que a banca fará e as respostas fundamentadas.
