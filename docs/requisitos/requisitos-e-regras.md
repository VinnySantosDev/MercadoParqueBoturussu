# Requisitos, regras de negócio e políticas — versão final

Base: primeira entrega revisada após a devolutiva. As linhas marcadas **[… na entrega final]** foram alteradas ou criadas nesta fase; o motivo de cada alteração está em `docs/revisao/alteracoes-do-modelo.md`. Os fluxogramas dos processos estão em `docs/diagramas/fluxogramas/`. Referências a seções e a problemas (PB-xx) apontam para o documento da primeira entrega revisada, em `docs/entrega-1-revisada/`.

## 1. Requisitos funcionais

Requisito funcional responde “o que o sistema deve fazer”. Cada requisito abaixo nasce de um problema identificado na seção 4; nenhum foi copiado de modelo genérico. A coluna “origem” garante a rastreabilidade exigida pelo manual. Requisitos alterados ou criados nesta revisão estão marcados.

### 1.1 Produtos, preços e fornecedores

| ID | Requisito | Origem | Entidades envolvidas |
|------|----------------------------------------|----------|--------------|
| RF-01 | O sistema deverá cadastrar produtos, com identificação da categoria/setor, unidade base, indicação de venda por peso e indicação de controle de validade. | PB-18, PB-19 | PRODUTO, CATEGORIA |
| RF-02 | O sistema deverá cadastrar as formas de venda de um mesmo produto (unidade, pacote, fardo, quilo), cada uma com seu código de leitura, preço e fator de conversão para a unidade base. | PB-19 | EMBALAGEM |
| RF-03 **[alterado]** | O sistema deverá gerar código interno de circulação restrita para itens sem código de fábrica, aceitar o código de balança (PLU) contido na etiqueta dos itens pesados e permitir a busca por nome no caixa. | PB-18 | EMBALAGEM |
| RF-04 | O sistema deverá registrar toda alteração de preço de venda, guardando preço anterior, preço novo, data, hora, motivo e funcionário responsável. | PB-06, PB-11 | HISTORICO_PRECO |
| RF-05 | O sistema deverá sugerir o preço de venda a partir do custo da última compra e da margem de referência do produto. | PB-05 | PRODUTO, LOTE, FORNECE |
| RF-06 | O sistema deverá cadastrar fornecedores (pessoa jurídica ou produtor pessoa física) com seus contatos/vendedores, canal de pedido e condição de pagamento usual. | Entrevista 3.11 | FORNECEDOR |
| RF-07 **[alterado na entrega final]** | O sistema deverá informar, para cada par produto–fornecedor, o custo e a data da última compra, calculados a partir das notas recebidas, permitindo comparar fornecedores do mesmo item. | PB-05 | FORNECE (N:N), ITEM_RECEBIMENTO |

### 1.2 Compras e recebimento

| ID | Requisito | Origem | Entidades envolvidas |
|------|----------------------------------------|----------|--------------|
| RF-08 **[alterado]** | O sistema deverá registrar pedidos de compra, indicando fornecedor, canal (WhatsApp, aplicativo, vendedor) e, para cada produto solicitado, a quantidade e o preço negociado. | PB-15 | PEDIDO_COMPRA, ITEM_PEDIDO |
| RF-09 **[alterado]** | O sistema deverá registrar o recebimento da mercadoria com a identificação da nota (chave de acesso da NF-e, ou modelo, série e número), valor total, volumes declarados e volumes conferidos, e cada linha da nota com produto, quantidade, valor unitário e quantidade aceita. | PB-01, PB-15 | RECEBIMENTO, ITEM_RECEBIMENTO |
| RF-10 **[alterado]** | O sistema deverá vincular cada linha recebida ao item do pedido correspondente e calcular, por item, a quantidade já recebida e a pendente, permitindo que um pedido seja atendido por várias entregas e que uma entrega atenda itens de mais de um pedido. | PB-15 | ITEM_PEDIDO, ITEM_RECEBIMENTO |
| RF-11 | O sistema deverá permitir registrar recebimento sem pedido prévio (compra direta com vendedor que passa no mercado). | Entrevista 3.3 | RECEBIMENTO |
| RF-12 **[alterado]** | O sistema deverá gerar, para cada linha aceita da nota, um lote por data de validade informada, com quantidade e custo unitário; uma linha com duas validades gera dois lotes. | PB-01, PB-03 | ITEM_RECEBIMENTO, LOTE |
| RF-13 **[alterado na entrega final]** | O sistema deverá gerar as contas a pagar do recebimento conforme RN-31: compra à vista gera uma conta quitada no ato; compra a prazo gera uma conta por parcela (7, 14 e 21 dias). | PB-14 | CONTA_PAGAR, PAGAMENTO_CONTA |
| RF-14 **[alterado]** | O sistema deverá registrar a recusa de um recebimento inteiro ou de linhas específicas, com o motivo, sem gerar estoque nem contas a pagar para o que foi recusado. | Entrevista 3.7, 3.16 | RECEBIMENTO, ITEM_RECEBIMENTO |

### 1.3 Estoque e validade

| ID | Requisito | Origem | Entidades envolvidas |
|------|----------------------------------------|----------|--------------|
| RF-15 | O sistema deverá controlar o saldo de estoque por produto e por lote, atualizando-o a cada entrada ou saída. | PB-01, PB-02 | LOTE, MOVIMENTACAO_ESTOQUE |
| RF-16 | O sistema deverá registrar toda movimentação de estoque indicando o tipo (entrada por recebimento, entrada de inventário, saída por venda, devolução de cliente, perda por vencimento, perda por avaria, troca com fornecedor, ajuste de inventário). | PB-04 | MOVIMENTACAO_ESTOQUE |
| RF-17 | O sistema deverá listar os lotes com vencimento dentro do prazo de alerta definido para o produto ou para a categoria. | PB-03 | LOTE, PRODUTO, CATEGORIA |
| RF-18 **[alterado]** | O sistema deverá registrar a perda por vencimento, a situação do lote separado para troca e, quando o fornecedor trocar, o lote de reposição vinculado ao lote trocado. | PB-04 | LOTE, MOVIMENTACAO_ESTOQUE |
| RF-19 | O sistema deverá emitir alerta quando o saldo do produto ficar abaixo do estoque mínimo definido. | PB-02 | PRODUTO |
| RF-20 | O sistema deverá permitir ajuste manual de estoque (inventário), com motivo e responsável obrigatórios. | Entrevista 2.16 | MOVIMENTACAO_ESTOQUE |
| RF-21 **[alterado]** | O sistema deverá baixar o estoque pelo lote de vencimento mais próximo (FEFO) no momento da venda; quando um lote não bastar, o restante será baixado do lote seguinte, com uma movimentação para cada lote. | PB-03, PB-04, PB-17 | ITEM_VENDA, LOTE, MOVIMENTACAO_ESTOQUE |
| RF-43 **[novo]** | O sistema deverá permitir a carga inicial do estoque por inventário, criando lotes com quantidade, validade e custo (último custo de compra conhecido). | PB-22 | LOTE, MOVIMENTACAO_ESTOQUE |

### 1.4 Vendas, caixa e fiado

| ID | Requisito | Origem | Entidades envolvidas |
|------|----------------------------------------|----------|--------------|
| RF-22 | O sistema deverá registrar vendas com seus itens, quantidade, preço praticado e desconto aplicado. | PB-09 | VENDA, ITEM_VENDA |
| RF-23 | O sistema deverá registrar quantidades fracionadas para produtos vendidos por peso (carnes, frutas, verduras). | Entrevista 2.11 | ITEM_VENDA |
| RF-24 **[alterado]** | O sistema deverá permitir que uma venda seja paga em mais de uma forma de pagamento — inclusive duas transações na mesma forma, como dois cartões —, registrando o valor e o NSU/autorização de cada transação. | PB-10, PB-21 | PAGAMENTO_VENDA, FORMA_PAGAMENTO |
| RF-25 | O sistema deverá registrar a venda fiada vinculada a um cliente identificado e atualizar seu saldo devedor. | PB-07 | CLIENTE, VENDA |
| RF-26 | O sistema deverá registrar pagamentos totais ou parciais da dívida do cliente, mantendo o histórico de cada abatimento. | PB-08 | ABATIMENTO_FIADO |
| RF-27 | O sistema deverá consultar, a qualquer momento, o saldo devedor de cada cliente e o total geral a receber de fiado. | PB-07 | CLIENTE, ABATIMENTO_FIADO |
| RF-28 **[alterado]** | O sistema deverá controlar sessões de caixa, com abertura (fundo de troco informado), fechamento, valor contado, total informado pelas maquininhas e as diferenças apuradas em dinheiro e em meios eletrônicos. | PB-12, PB-21 | CAIXA, SESSAO_CAIXA |
| RF-29 **[alterado]** | O sistema deverá registrar sangrias, suprimentos e o recolhimento do fechamento, com valor, motivo e responsável, e levar esse dinheiro ao cofre (ou retirá-lo dele). | PB-12 | MOVIMENTACAO_CAIXA, MOVIMENTO_FINANCEIRO |
| RF-30 | O sistema deverá identificar o funcionário que operou cada venda, alteração de preço, recebimento, perda, sangria, devolução, abatimento e pagamento de conta. | PB-11 | FUNCIONARIO |
| RF-31 **[alterado]** | O sistema deverá registrar devoluções e trocas de produto pelo cliente, vinculadas ao item vendido, com motivo, destino do produto, forma e valor do reembolso, devolvendo a quantidade ao lote de origem. | Entrevista 4.9 | DEVOLUCAO, ITEM_VENDA, MOVIMENTACAO_ESTOQUE |
| RF-32 **[alterado na entrega final]** | O sistema deverá calcular o valor esperado em dinheiro na gaveta: fundo inicial + pagamentos em dinheiro (líquidos de troco) + abatimentos em dinheiro + suprimentos − sangrias − reembolsos em dinheiro. O recolhimento do fechamento acontece depois da contagem e não entra. | PB-12 | SESSAO_CAIXA |

### 1.5 Financeiro e relatórios

| ID | Requisito | Origem | Entidades envolvidas |
|------|----------------------------------------|----------|--------------|
| RF-33 | O sistema deverá registrar contas a pagar de qualquer natureza (fornecedor, Simples Nacional, folha, internet, água, luz, aluguel), com vencimento, prioridade e situação. | PB-14 | CONTA_PAGAR |
| RF-34 **[alterado]** | O sistema deverá registrar um ou mais pagamentos para a mesma conta, cada um com data, valor principal, juros/multa, desconto, conta de origem do dinheiro e funcionário responsável, calculando o saldo em aberto e a situação da conta. | PB-13, PB-14 | CONTA_PAGAR, PAGAMENTO_CONTA, MOVIMENTO_FINANCEIRO |
| RF-35 **[alterado]** | O sistema deverá projetar, dia a dia, a disponibilidade financeira a partir do saldo realizado nas contas financeiras, somando os recebíveis ainda não conciliados pela data prevista de crédito e subtraindo os saldos das contas a pagar pelo vencimento. | PB-13 | CONTA_FINANCEIRA, PAGAMENTO_VENDA, CONTA_PAGAR |
| RF-36 | O sistema deverá alertar o gerente quando as contas a vencer no período superarem o saldo previsto. | PB-13 (pedido explícito) | CONTA_PAGAR, PAGAMENTO_VENDA |
| RF-37 | O sistema deverá apresentar o faturamento do dia separado por forma de pagamento e por caixa. | PB-09, PB-10 | VENDA, PAGAMENTO_VENDA, SESSAO_CAIXA |
| RF-38 **[alterado]** | O sistema deverá apurar o lucro bruto do período a partir do preço praticado e do custo dos lotes efetivamente consumidos por cada item vendido, descontadas as devoluções. | PB-17 | ITEM_VENDA, MOVIMENTACAO_ESTOQUE, LOTE |
| RF-39 | O sistema deverá informar a quantidade vendida por produto em um período, identificando os itens de maior e menor giro. | PB-16 | ITEM_VENDA, VENDA |
| RF-40 | O sistema deverá apresentar relatório de perdas por vencimento por produto e por período. | PB-04 | MOVIMENTACAO_ESTOQUE |
| RF-41 | O sistema deverá apresentar a relação de boletos e contas em aberto ordenada por vencimento e prioridade, com o saldo em aberto de cada uma. | PB-14 | CONTA_PAGAR |
| RF-42 **[alterado na entrega final]** | O sistema deverá controlar o acesso dos funcionários por permissão individual (operar caixa, cadastrar produto, alterar preço, autorizar desconto, autorizar devolução, conceder fiado, realizar sangria, gerenciar financeiro), guardando a data de concessão e a de revogação de cada permissão (RN-42). | PB-20 | FUNCIONARIO, PERMISSAO |
| RF-44 **[novo]** | O sistema deverá registrar as contas financeiras do mercado (banco, conta da maquininha, cofre) e os movimentos de entrada e saída nelas, mantendo o saldo realizado. | PB-13, PB-21 | CONTA_FINANCEIRA, MOVIMENTO_FINANCEIRO |
| RF-45 **[novo]** | O sistema deverá conciliar cada crédito recebido em conta com as transações de venda e de abatimento que ele liquida, apontando divergências de valor, de taxa e de data. | PB-21 | MOVIMENTO_FINANCEIRO, PAGAMENTO_VENDA, ABATIMENTO_FIADO |

## 2. Requisitos não funcionais

Requisito não funcional responde “como o sistema deve funcionar”: características, restrições e condições de operação. Não descrevem funções, e por isso não geram entidades por si, mas condicionam decisões do modelo (por exemplo, exigir autoria e histórico impede a simples sobrescrita de valores; exigir operação offline impede chaves que dependam do relógio do caixa).

| ID | Categoria | Requisito | Justificativa na realidade do mercado |
|------|----------|-------------------------------|-------------------------|
| RNF-01 | Controle de acesso | O acesso deverá ser individual (login por funcionário) e as operações liberadas conforme as permissões concedidas a cada um. | As funções se sobrepõem: quase todos operam caixa, mas só alguns cadastram produtos e alteram preços |
| RNF-02 | Auditabilidade | O sistema deverá manter registro de data, hora e funcionário responsável nas operações sensíveis (preço, estoque, caixa, fiado, financeiro). | Pedido explícito: “para evitar confusões sobre alterações indevidas ou extremas” |
| RNF-03 | Desempenho | A consulta de preço por leitura de código de barras deverá responder em tempo compatível com a operação de frente de caixa (inferior a 1 segundo). | Fila do caixa em mercado de bairro, com dois PDVs |
| RNF-04 | Usabilidade | As telas operacionais deverão ser simples o bastante para uso por funcionário sem experiência prévia com sistema de caixa. | Um dos seis funcionários não tem experiência com caixa |
| RNF-05 | Integridade | Nenhuma alteração de saldo de estoque poderá ocorrer sem a movimentação correspondente registrada. | Evita o problema atual de estoque sem origem verificável |
| RNF-06 | Preservação do histórico | Registros operacionais não deverão ser excluídos fisicamente; o encerramento deve ocorrer por mudança de situação (ativo/inativo, aberta/paga). | Hoje a baixa do fiado é “riscar o nome”, e a informação se perde |
| RNF-07 | Disponibilidade | A operação de venda deverá continuar funcionando durante instabilidade de internet, com sincronização posterior. | Mercado não pode parar de vender; hoje o caixa é local |
| RNF-08 | Confiabilidade | Deverá haver rotina diária de backup dos dados. | Hoje a informação crítica está em cadernos e papéis, sem cópia |
| RNF-09 | Configurabilidade | Os prazos de alerta de validade e os níveis de estoque mínimo deverão ser parametrizáveis por produto e por categoria. | Alimentos básicos exigem vigilância maior que os demais |
| RNF-10 | Precisão | Valores monetários deverão ser tratados com duas casas decimais e quantidades de itens pesados com três casas. | Venda por quilo de carnes, frutas e verduras |
| RNF-11 | Escalabilidade | O sistema deverá suportar os dois caixas atuais operando simultaneamente e permitir a inclusão de novos caixas e usuários sem alteração estrutural. | Dois PDVs hoje; crescimento previsto |
| RNF-12 | Interoperabilidade | O sistema deverá operar com leitor de código de barras e com balança etiquetadora, e permitir a importação futura de arquivos de nota fiscal eletrônica e de extratos das maquininhas. | Equipamentos já existentes; digitação manual da nota e do extrato é o gargalo |
| RNF-13 | Privacidade (LGPD) | Dados pessoais de clientes e funcionários deverão ser coletados apenas para a finalidade necessária, acessíveis somente a usuários autorizados e não replicados como identificador em tabelas operacionais. | O cadastro de cliente só existe por causa do fiado; o CPF não precisa circular em cada venda |

> **Distinção exigida pelo manual.** “O sistema deverá registrar vendas” é funcional (descreve uma função). “O registro de vendas deverá identificar o usuário responsável conforme seu perfil de acesso” é não funcional (descreve uma condição de funcionamento). Os dois aparecem separadamente acima — RF-22/RF-30 e RNF-01/RNF-02 — e não como um item único.

## 3. Regras de negócio e operacionais

As regras abaixo expressam o que pode e o que não pode acontecer no negócio. São elas que sustentam as cardinalidades da seção 13 e as decisões da seção 16: sempre que uma cardinalidade for questionada, a resposta estará em uma destas regras. Regras alteradas ou criadas nesta revisão estão marcadas; a numeração original foi mantida para preservar as referências.

### 3.1 Produto, preço e fornecimento

| ID | Regra | Origem / impacto no modelo |
|------|---------------------------------------|------------------------|
| RN-01 | Todo produto pertence a exatamente uma categoria/setor; uma categoria pode não ter nenhum produto cadastrado ainda. | Setores do mercado → CATEGORIA (0,N) : PRODUTO (1,1) |
| RN-02 | Produto vendido por peso tem quantidade fracionada e unidade base em quilo; os demais têm unidade base em unidade. | Carnes, frutas e verduras → atributos vendido_por_peso e unidade_base |
| RN-03 | Um produto só pode ser vendido se possuir ao menos uma forma de venda (embalagem) ativa; cada forma de venda pertence a um único produto. | Lata, fardo, pacote, quilo → PRODUTO (1,N) : EMBALAGEM (1,1) |
| RN-04 **[alterado]** | Toda forma de venda tem um código de leitura único. Item com código de fábrica usa o GTIN/EAN; item sem código recebe um código interno de circulação restrita (prefixo 2, reservado para uso interno), impresso em etiqueta; item pesado é identificado pelo código de balança (PLU), pois a etiqueta da balança traz o prefixo 2, o código do item e o preço ou peso — o código lido muda a cada etiqueta. | Cervejas sem código e itens pesados → codigo_barras e codigo_balanca como chaves alternativas de EMBALAGEM |
| RN-05 | O preço de venda é calculado sobre o custo da última compra acrescido da margem: 35% a 40% em itens de giro comum e margem maior em itens de custo baixo. | Política de precificação declarada → RF-05 |
| RN-06 | Toda alteração de preço de venda gera um registro histórico com preço anterior, preço novo, data, hora e motivo. | Impede sobrescrever o preço sem rastro → entidade HISTORICO_PRECO |
| RN-07 | Toda alteração de preço é atribuída ao funcionário que a realizou, e só pode ser feita por quem tem a permissão ALTERAR_PRECO. | “Os funcionários que verificam notas alteram preços” → FUNCIONARIO (0,N) : HISTORICO_PRECO (1,1) |
| RN-08 | Somente funcionário com a permissão CADASTRAR_PRODUTO pode incluir ou alterar produtos e embalagens. | “Nem todos possuem o conhecimento para cadastrar/alterar produtos” |
| RN-09 | O mesmo produto pode ser comprado de vários fornecedores, com preços diferentes; o preço de compra pertence ao par produto–fornecedor, e não ao produto isoladamente. | Diferença de quase um real no leite → relacionamento N:N FORNECE com atributos |

### 3.2 Compras, recebimento e estoque

| ID | Regra | Origem / impacto no modelo |
|------|---------------------------------------|------------------------|
| RN-10 | Todo pedido de compra é dirigido a um único fornecedor e deve conter ao menos um produto; cada produto aparece uma única vez no pedido. | FORNECEDOR (0,N) : PEDIDO_COMPRA (1,1); PEDIDO_COMPRA (1,N) : ITEM_PEDIDO (1,1) |
| RN-11 **[alterado]** | Um item pedido pode ser atendido por mais de uma entrega, pois produtos faltantes chegam depois; cada linha de nota atende no máximo um item pedido. A situação do pedido (aberto, parcialmente recebido, recebido) é calculada pela comparação, item a item, entre o pedido e o recebido. | ITEM_PEDIDO (0,N) : ITEM_RECEBIMENTO (0,1) |
| RN-12 **[alterado]** | Todo recebimento pertence a um fornecedor e é acompanhado de nota fiscal, mesmo quando não houve pedido formal registrado. A nota é identificada pela chave de acesso da NF-e quando existir; na falta dela, por fornecedor + modelo + série + número (o número sozinho pode se repetir em séries diferentes). | Vendedor que passa e entrega na hora → recebimento sem pedido; chaves alternativas de RECEBIMENTO |
| RN-13 **[alterado]** | A conferência do recebimento ocorre em duas etapas: volumes declarados na nota e conferência item a item. Cada linha da nota é registrada com a quantidade aceita; qualquer divergência deve ser registrada. | Procedimento descrito na entrevista → ITEM_RECEBIMENTO |
| RN-14 **[alterado]** | Cada linha aceita da nota gera um lote para cada data de validade distinta encontrada na conferência, e a soma das quantidades dos lotes é igual à quantidade aceita da linha. Linha ou recebimento recusado não gera lote nem conta a pagar. | Dois lotes do mesmo produto na mesma nota → ITEM_RECEBIMENTO (0,N) : LOTE (0,1); LOTE com identificador próprio |
| RN-15 | Todo lote de produto com controle de validade deve ter data de validade informada na entrada. | Condição para a lista de validades (prioridade nº 1 do gerente) |
| RN-16 | Toda movimentação de estoque afeta um único lote, e o saldo nunca é alterado sem movimentação correspondente. | Garante auditabilidade (RNF-05) → LOTE (1,N) : MOVIMENTACAO_ESTOQUE (1,1) |
| RN-17 **[alterado]** | A baixa de estoque na venda segue o critério FEFO: sai primeiro o lote que vence primeiro. Quando o lote não tem saldo suficiente, o restante sai do lote seguinte, gerando uma movimentação para cada lote consumido. | ITEM_VENDA (0,N) : MOVIMENTACAO_ESTOQUE (0,1) |
| RN-18 | Perdas, trocas com fornecedor e ajustes de inventário exigem motivo e funcionário responsável. | Hoje nada é registrado (PB-04) → RF-16, RF-20 |
| RN-19 **[alterada na entrega final]** | Produto vencido é retirado da gôndola e registrado como perda; o lote fica SEPARADO_TROCA. Se o fornecedor trocar, o lote passa a TROCADO e a reposição entra como novo lote (origem REPOSICAO_FORNECEDOR), vinculado ao lote trocado e com o custo dele; se não trocar, o lote é DESCARTADO. “Esgotado” não é situação: é saldo zero (derivado). | LOTE (0,N) — é reposto por — LOTE (0,1) |
| RN-20 | Nenhuma venda pode ser registrada fora de uma sessão de caixa aberta. | SESSAO_CAIXA (0,N) : VENDA (1,1) |
| RN-40 **[alterada na entrega final]** | A venda não é bloqueada quando o saldo dos lotes for insuficiente (o produto está fisicamente no caixa). Nesse caso o sistema cria automaticamente um lote de AJUSTE_INVENTARIO com o custo da última compra, baixa a venda dele e o marca como pendente de conferência até a contagem física. | LOTE.pendente_conferencia; auditoria A11 |
| RN-41 **[novo]** | Na implantação, o estoque existente é carregado por inventário inicial: cada produto contado gera um lote de origem INVENTARIO_INICIAL, com validade (quando houver) e custo da última nota conhecida. | PB-22 → lotes sem recebimento |

### 3.3 Venda, pagamento e fiado

| ID | Regra | Origem / impacto no modelo |
|------|---------------------------------------|------------------------|
| RN-21 **[esclarecida na entrega final]** | Toda venda possui pelo menos um item. A venda concluída possui ao menos um pagamento, e a soma dos pagamentos (já líquidos de troco) é igual ao total; pode haver mais de um pagamento na mesma forma. A venda cancelada antes do pagamento não tem pagamento nem baixa de estoque. | VENDA (1,N) : ITEM_VENDA (1,1) e VENDA (0,N) : PAGAMENTO_VENDA (1,1); auditoria A01 |
| RN-22 **[alterado]** | O preço praticado é congelado no item no momento da venda. O custo unitário do lote é definido na entrada e não muda depois. O custo do item vendido é a soma, para cada lote baixado, da quantidade baixada × custo unitário do lote; uma devolução estorna pelo custo do mesmo lote. | Condição para apurar lucro histórico (RF-38) com lotes de custos diferentes |
| RN-23 | Desconto em item de venda só pode ser aplicado por funcionário com permissão de autorização, e o autorizador fica registrado. | “Os funcionários que realizam alterações dos preços” autorizam desconto |
| RN-24 | Venda com pagamento na forma FIADO exige cliente cadastrado, autorizado e com CPF informado; venda sem fiado pode ser anônima. | CLIENTE (0,N) : VENDA (0,1) — FK id_cliente opcional em VENDA |
| RN-25 | Um cliente pode ter várias compras fiadas em aberto simultaneamente, desde que esteja autorizado e, havendo limite definido, dentro do limite. | “Sim, mas desde que a pessoa esteja pagando” |
| RN-26 **[alterado]** | O saldo devedor do cliente é a soma dos pagamentos em fiado menos a soma dos abatimentos registrados e das devoluções reembolsadas como abatimento de fiado. | Atributo derivado saldo_devedor em CLIENTE |
| RN-27 | O abatimento de fiado pode ser total ou parcial, é sempre vinculado ao cliente e nunca pode ser pago na própria forma FIADO. | Substitui o caderno; permite histórico de pagamentos parciais |
| RN-28 **[alterado]** | Devolução ou troca ao cliente só é aceita por defeito do produto ou validade vencida, refere-se a um item de uma venda registrada e não pode exceder a quantidade vendida menos o já devolvido. A quantidade volta ao lote de onde saiu; o destino (revenda, separado para troca, descarte) é registrado; o reembolso pode ser troca pelo mesmo produto, dinheiro (sai da gaveta), estorno eletrônico (sai da conta) ou abatimento de fiado. | Política declarada de trocas → entidade DEVOLUCAO |

### 3.4 Caixa e financeiro

| ID | Regra | Origem / impacto no modelo |
|------|---------------------------------------|------------------------|
| RN-29 | Sangrias e suprimentos exigem valor, motivo e funcionário responsável, e afetam o valor esperado da sessão de caixa. | Hoje inexistente (PB-12) → MOVIMENTACAO_CAIXA |
| RN-30 **[alterado]** | O fechamento de caixa é feito por sessão: o dinheiro contado é comparado com o valor esperado, e o total informado pelas maquininhas é comparado com o total eletrônico registrado no sistema. Qualquer diferença exige justificativa. O fechamento não confirma que o dinheiro eletrônico caiu na conta — isso é a conciliação (RN-36). | “Não é fixo”; conferência atual é informal |
| RN-31 **[alterada na entrega final]** | Todo recebimento aceito gera contas a pagar conforme a condição acordada: compra à vista gera uma conta quitada no ato, com o pagamento e a saída de dinheiro registrados; compra a prazo gera uma conta por parcela. Recebimento recusado não gera conta. | RECEBIMENTO (0,N) : CONTA_PAGAR (0,1) |
| RN-32 | Existem contas a pagar sem vínculo com recebimento: Simples Nacional, folha de funcionários, internet, água, luz e aluguel. | Justifica o lado opcional do relacionamento |
| RN-33 **[alterado]** | O valor recebido em cartão e Pix só fica disponível após o prazo da respectiva forma de pagamento. Até ser conciliado, entra na previsão pela data prevista e pelo valor líquido previsto; depois de conciliado, passa a contar pelo valor e data reais. | “As maquininhas mostram quanto dinheiro tem para cair” → atributo prazo_credito_dias |
| RN-34 | Quando o total das contas a vencer no período superar o saldo previsto, o gerente deve ser alertado. | Pedido explícito e prioritário do gerente → RF-36 |
| RN-35 | Toda operação sensível (venda, preço, estoque, caixa, fiado, devolução, pagamento) é atribuída ao funcionário que a executou. | Base do controle por permissão (RF-30, RF-42) |
| RN-36 **[novo]** | Conciliação: todo pagamento de venda ou abatimento feito em forma que exige conciliação (débito, crédito, Pix, vale) só é considerado realizado quando vinculado a um crédito efetivo em conta financeira. Um crédito pode liquidar várias transações; a diferença entre o previsto e o recebido (valor, taxa ou data) é registrada como divergência. | MOVIMENTO_FINANCEIRO (0,N) — liquida — PAGAMENTO_VENDA (0,1) |
| RN-37 **[novo]** | O dinheiro só sai da gaveta por movimentação de caixa. Sangria e recolhimento do fechamento geram entrada no cofre; suprimento gera saída do cofre; reembolso de devolução em dinheiro sai da gaveta direto ao cliente. | MOVIMENTACAO_CAIXA (0,1) — gera — MOVIMENTO_FINANCEIRO (0,1) |
| RN-38 **[novo]** | Uma conta a pagar pode receber um ou vários pagamentos. Cada pagamento registra data, valor principal, juros/multa, desconto, conta financeira de onde saiu o dinheiro e responsável. A soma do principal pago nunca ultrapassa o valor original; a situação (aberta, parcialmente paga, paga) é calculada, não digitada. | CONTA_PAGAR (0,N) : PAGAMENTO_CONTA (1,1) |
| RN-39 **[novo]** | A previsão de disponibilidade não é um registro: é um cálculo, feito dia a dia, igual a saldo realizado das contas financeiras + dinheiro das sessões abertas + recebíveis ainda não conciliados (pela data prevista) − saldos em aberto das contas a pagar (pelo vencimento). | Base do alerta RF-36; distingue previsão de fechamento e de conciliação |
| RN-42 **[nova na entrega final]** | Toda permissão tem período de vigência: data de concessão e, se retirada, data de revogação. Revogar não apaga o registro. Uma operação sensível é válida se o funcionário tinha a permissão na data da operação. | FUNCIONARIO_PERMISSAO.data_revogacao; auditoria A13 |

## 4. Restrições e políticas organizacionais

Políticas são decisões da empresa que o sistema precisa respeitar, mesmo quando não decorrem de uma necessidade técnica. Foram separadas das regras de negócio porque podem mudar por decisão da gerência sem que o modelo de dados mude.

| ID | Tipo | Política / restrição | Reflexo no sistema |
|------|----------|-------------------------------|------------------|
| PO-01 | Alçada | Somente funcionários designados fazem pedidos aos fornecedores. | Permissão específica; pedido sempre vinculado ao solicitante |
| PO-02 | Alçada | Somente os funcionários que conferem notas podem cadastrar produtos e alterar preços. | Permissões CADASTRAR_PRODUTO e ALTERAR_PRECO |
| PO-03 | Comercial | Desconto só é concedido por proximidade de vencimento ou avaria, com autorização. | Motivo obrigatório no histórico de preço e no item de venda |
| PO-04 | Crédito | A concessão de fiado é decisão do gerente e restrita a clientes conhecidos e com histórico de pagamento; apenas o gerente altera a autorização e o limite do cliente. | Atributos autorizado_fiado e limite_fiado, alteráveis por permissão |
| PO-05 | Operacional | O recebimento pode ser conferido por qualquer funcionário disponível no momento da entrega, mas o responsável fica registrado. | FUNCIONARIO (0,N) : RECEBIMENTO (1,1) |
| PO-06 | Financeira | Os boletos são organizados por prioridade e vencimento; havendo insuficiência de caixa, paga-se primeiro os de maior prioridade e os demais podem ser pagos em parte ou com juros. | Atributo prioridade; pagamentos parciais em PAGAMENTO_CONTA |
| PO-07 | Estoque | Produto vencido não pode ser descartado antes da tentativa de troca com o fornecedor. | Situação do lote: SEPARADO_TROCA antes de DESCARTADO |
| PO-08 | Estoque | Mantém-se parte do produto no depósito enquanto o restante fica exposto na gôndola. | Estoque mínimo por produto; alerta de reposição |
| PO-09 | Comercial | Margem padrão de 35% a 40% nos itens de giro comum, podendo ser maior nos itens adquiridos com custo baixo. | Atributo margem_referencia e sugestão de preço |
| PO-10 | Financeira | Alguns fornecedores só operam à vista; a maioria trabalha com boleto parcelado em 7, 14 e 21 dias. | Condição de pagamento padrão por fornecedor |
| PO-11 | Operacional | Apenas operadores habilitados abrem e fecham o caixa; cinco dos seis funcionários estão aptos. | Permissão OPERAR_CAIXA |
| PO-12 | Informacional | Nenhum registro operacional é apagado; encerra-se por mudança de situação, preservando o histórico. | Atributos de situação em vez de exclusão física (RNF-06) |
| PO-13 **[nova]** | Alçada | Devoluções só são aceitas com autorização de funcionário com permissão AUTORIZAR_DEVOLUCAO; o reembolso nunca supera o valor pago pelo item. | FUNCIONARIO (0,N) : DEVOLUCAO (1,1); regra de valor em DEVOLUCAO |
| PO-14 **[nova]** | Financeira | A conciliação dos recebimentos de cartão e Pix é feita diariamente pelo gerente (ou por quem tiver GERENCIAR_FINANCEIRO). | Permissão GERENCIAR_FINANCEIRO; situação de conciliação |

