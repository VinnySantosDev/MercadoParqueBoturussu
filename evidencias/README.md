# Evidências

Todas produzidas executando o banco de verdade (MySQL 8.0.46), na ordem do teste pedido pelo manual: banco vazio → script → tabelas → restrições → dados → consultas → verificação.

| Arquivo | O que prova |
|---|---|
| `01_execucao_script_completo.log` | O `script_completo.sql` roda do zero, sem erro (código de saída 0), e cria 30 tabelas e 14 views; contém a saída de tudo o que foi executado |
| `02_validacao_massa_dados.md` | Volume por tabela e presença de cada cenário real exigido pela devolutiva |
| `03_resultados_consultas_gerenciais.txt` | Resultado de cada uma das 16 consultas gerenciais |
| `04_resultados_auditoria_antes.txt` | As 22 auditorias logo após a carga (achados plantados encontrados) |
| `05_resultados_update_delete.txt` | “Antes” e “depois” de cada uma das 9 operações UPDATE/DELETE |
| `06_resultados_auditoria_depois.txt` | As 22 auditorias depois das operações: o que foi resolvido e o que, corretamente, continua |
| `07_testes_restricoes.md` | 32 tentativas de violar regras, todas recusadas com o erro e a restrição esperados |
| `08_conferencia_dicionario_x_banco.md` | Dicionário de dados idêntico ao banco implementado (0 divergências) |
