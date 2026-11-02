# Ferramentas — geração reprodutível

Tudo o que é gerado no projeto sai destes programas (Python 3 + MySQL 8). Não é preciso usá-los para **executar** o banco — para isso basta `sql/script_completo.sql`. Eles existem para que qualquer pessoa possa **conferir e reproduzir** como o DDL, o dicionário e a massa de dados foram feitos.

| Arquivo | Papel |
|---|---|
| `gerador_massa/fis.py` | **Fonte única do modelo lógico/físico**: tabelas, colunas, PK, FK, UNIQUE, CHECK e DEFAULT, cada um com o motivo. Gera `sql/ddl/02_tabelas.sql`. |
| `gerador_massa/spec.py`, `der.py` | Fonte do modelo conceitual (entidades, atributos, relacionamentos e cardinalidades) e geração dos diagramas do DER. |
| `gerador_massa/logico.py` | Diagramas do modelo lógico, dicionário de dados (.md/.csv) e conferência automática dicionário × banco (`information_schema`). |
| `gerador_massa/cadastros.py` | Cadastros fictícios e geradores de documentos válidos (CPF, CNPJ numérico e alfanumérico, EAN-13, chave de NF-e). |
| `gerador_massa/simula.py` | Simulador de 30 dias de operação (semente fixa 2026). Aplica as regras de negócio; não grava valores derivados. |
| `gerador_massa/escreve_sql.py` | Escreve `sql/dados/04_massa_dados.sql` a partir da simulação. |
| `gerador_massa/testes_restricoes.py` | Gera e executa os testes negativos (`sql/testes/`) e a evidência `07`. |
| `gerador_massa/validacao_massa.py` | Evidência de volume e cobertura de cenários (`02`). |
| `gerador_massa/roda_consultas.py` | Executa as consultas bloco a bloco e grava as evidências `03`, `04` e `06`. |
| `gerador_massa/graficos_bi.py` | Gráficos dos painéis de BI, lidos do banco. |

Dados gerados são **fictícios**: nomes, CPFs e CNPJs têm formato válido, mas não pertencem a pessoas ou empresas reais.

## Como reproduzir (testado)

A partir de `ferramentas/gerador_massa/`:

```
python3 escreve_sql.py /tmp/04_massa_dados.sql                                  # massa de dados
python3 -c "import fis; open('/tmp/02_tabelas.sql','w').write(fis.ddl_all())"   # CREATE TABLE
```

Os dois arquivos saem **byte a byte idênticos** aos de `sql/` (conferido por `md5sum`/`cmp`). Os demais programas (diagramas, dicionário e evidências) foram executados na pasta de trabalho do grupo, que tem ao lado as pastas `sql_src/`, `fig/` e `tmp/`; estão aqui como registro de como cada evidência foi produzida e precisam dessa estrutura e de um MySQL local para rodar de novo.
