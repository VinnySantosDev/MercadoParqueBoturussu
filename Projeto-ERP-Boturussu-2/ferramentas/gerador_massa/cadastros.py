# -*- coding: utf-8 -*-
"""Cadastros (dados mestres) da massa de teste. Todos os nomes e documentos
são FICTÍCIOS (gerados com dígitos verificadores válidos)."""
import random

R = random.Random(2026)

# ------------------------------------------------------------ documentos
def _dv_mod11(nums, pesos):
    s = sum(n * p for n, p in zip(nums, pesos))
    r = s % 11
    return 0 if r < 2 else 11 - r

def cpf(seed_digits):
    n = [int(c) for c in seed_digits]
    d1 = _dv_mod11(n, range(10, 1, -1))
    d2 = _dv_mod11(n + [d1], range(11, 1, -1))
    return seed_digits + f"{d1}{d2}"

def cnpj(base12):
    """Aceita base numérica ou alfanumérica (12 posições). Valor de cada
    caractere = código ASCII − 48 (regra do CNPJ alfanumérico)."""
    v = [ord(c) - 48 for c in base12]
    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = _dv_mod11(v, p1)
    d2 = _dv_mod11(v + [d1], [6] + p1)
    return base12 + f"{d1}{d2}"

def ean13(base12):
    s = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(base12))
    return base12 + str((10 - s % 10) % 10)

def chave_nfe(aamm, doc14, serie, numero, cnf):
    base = "35" + aamm + doc14 + "55" + f"{serie:03d}" + f"{numero:09d}" + "1" + f"{cnf:08d}"
    v = [ord(c) - 48 for c in base]
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    s = sum(x * pesos[i % 8] for i, x in enumerate(reversed(v)))
    r = s % 11
    dv = 0 if r < 2 else 11 - r
    return base + str(dv)

# ------------------------------------------------------------ pessoas
FUNCIONARIOS = [
    # id, nome, cpf-base, login, função, admissão, telefone
    (1, "Carlos Eduardo Lima", "418273650", "carlos.lima", "GERENCIA", "2012-03-01", "11987654301"),
    (2, "Mariana Souza Prado", "529384761", "mariana.prado", "CAIXA", "2018-07-16", "11987654302"),
    (3, "Rafael Nogueira Dias", "630495872", "rafael.dias", "CAIXA", "2020-02-03", "11987654303"),
    (4, "Juliana Alves Rocha", "741506983", "juliana.rocha", "CAIXA", "2023-05-08", "11987654304"),
    (5, "Pedro Henrique Santos", "852617094", "pedro.santos", "BALANCA", "2021-09-20", "11987654305"),
    (6, "Lucas Ferreira Costa", "963728105", "lucas.costa", "REPOSICAO", "2025-11-03", "11987654306"),
]
PERMISSOES = [
    ("OPERAR_CAIXA", "Abrir, operar e fechar sessão de caixa (PO-11)"),
    ("CADASTRAR_PRODUTO", "Incluir e alterar produtos e embalagens (RN-08, PO-02)"),
    ("ALTERAR_PRECO", "Alterar preço de venda (RN-07, PO-02)"),
    ("RECEBER_MERCADORIA", "Registrar e conferir recebimentos (PO-05)"),
    ("REGISTRAR_PERDA", "Registrar perdas por vencimento e avaria (RN-18)"),
    ("AJUSTAR_ESTOQUE", "Registrar ajustes de inventário (RF-20)"),
    ("AUTORIZAR_DESCONTO", "Autorizar desconto em item de venda (RN-23, PO-03)"),
    ("AUTORIZAR_DEVOLUCAO", "Autorizar devolução e troca de cliente (PO-13)"),
    ("CONCEDER_FIADO", "Autorizar cliente e definir limite de fiado (PO-04)"),
    ("REALIZAR_SANGRIA", "Registrar sangria, suprimento e recolhimento (RN-29)"),
    ("GERENCIAR_FINANCEIRO", "Contas a pagar, pagamentos, conciliação e previsão (PO-14)"),
    ("GERENCIAR_USUARIOS", "Cadastrar funcionários e conceder permissões (RNF-01)"),
]
TODAS = [p[0] for p in PERMISSOES]
PERM_FUNC = {
    1: TODAS,
    2: ["OPERAR_CAIXA", "CADASTRAR_PRODUTO", "ALTERAR_PRECO", "RECEBER_MERCADORIA", "AUTORIZAR_DESCONTO",
        "AUTORIZAR_DEVOLUCAO", "REALIZAR_SANGRIA", "REGISTRAR_PERDA"],
    3: ["OPERAR_CAIXA", "CADASTRAR_PRODUTO", "ALTERAR_PRECO", "RECEBER_MERCADORIA", "AUTORIZAR_DESCONTO",
        "AUTORIZAR_DEVOLUCAO", "REALIZAR_SANGRIA", "REGISTRAR_PERDA"],
    4: ["OPERAR_CAIXA", "REALIZAR_SANGRIA"],
    5: ["OPERAR_CAIXA", "REGISTRAR_PERDA", "RECEBER_MERCADORIA"],
    6: ["REGISTRAR_PERDA", "RECEBER_MERCADORIA"],
}

CLIENTES = [
    # id, nome, apelido, cpf-base|None, tel, logradouro, nº, compl, bairro, autorizado, limite, cadastro
    (1, "Maria das Graças Oliveira", "Dona Graça", "123456789", "11991230001", "Rua Jacinto Menezes", "112", None, "Parque Boturussu", True, 350.00, "2026-09-01"),
    (2, "José Aparecido Lima", "Zé da Oficina", "234567891", "11991230002", "Rua Pedro Calmon", "45", "fundos", "Parque Boturussu", True, 300.00, "2026-09-01"),
    (3, "Antônia Ferreira da Silva", None, "345678912", "11991230003", "Av. Boturussu", "1880", "apto 12", "Parque Boturussu", True, 250.00, "2026-09-01"),
    (4, "Severino Batista Souza", "Seu Biu", "456789123", "11991230004", "Rua Japuíba", "300", None, "Ermelino Matarazzo", True, 400.00, "2026-09-01"),
    (5, "Cláudia Regina Matos", None, "567891234", "11991230005", "Rua das Amoreiras", "77", None, "Parque Boturussu", True, 200.00, "2026-09-02"),
    (6, "Francisco de Assis Pereira", "Chico", "678912345", "11991230006", "Rua Jacinto Menezes", "230", None, "Parque Boturussu", True, 150.00, "2026-09-03"),
    (7, "Patrícia Gomes Ramos", None, "789123456", "11991230007", None, None, None, None, False, None, "2026-09-05"),
    (8, "Roberto Carlos Nunes", "Betão", None, "11991230008", None, None, None, None, False, None, "2026-09-08"),
    (9, "Luzia Aparecida Campos", None, "891234567", None, "Rua Pedro Calmon", "12", None, "Parque Boturussu", False, None, "2026-09-10"),
    (10, "Edson Rodrigues Moreira", None, "912345678", "11991230010", "Rua Japuíba", "18", "casa 2", "Ermelino Matarazzo", True, 200.00, "2026-09-12"),
]

# ------------------------------------------------------------ fornecedores
FORNECEDORES = [
    # id, tipo, base doc, razão, fantasia, canal, condição, contatos[(nome, tel, wpp)]
    (1, "CNPJ", "123456780001", "Distribuidora de Bebidas Leste Ltda", "Bebidas Leste", "APLICATIVO", "7/14/21 dias",
     [("Fábio Martins", "11940010001", True), ("Central de pedidos", "1125550001", False)]),
    (2, "CNPJ", "234567890001", "Atacadão Alimentos Penha Ltda", "Atacadão Penha", "VENDEDOR_VISITA", "7/14/21 dias",
     [("Sandra Lopes", "11940020002", True)]),
    (3, "CNPJ", "345678900001", "Laticínios Vale Verde Ltda", "Vale Verde", "WHATSAPP", "7/14/21 dias",
     [("Márcio Teixeira", "11940030003", True), ("Ana Clara Mendes", "11940030004", True)]),
    (4, "CNPJ", "456789010001", "Frigorífico Zona Leste Ltda", "Frigo ZL", "WHATSAPP", "7/14/21 dias",
     [("Gilberto Rosa", "11940040005", True)]),
    (5, "CPF", "321654987", "Antônio Pereira dos Santos", "Sítio Santo Antônio", "VENDEDOR_VISITA", "À vista",
     [("Antônio Pereira", "11940050006", True)]),
    (6, "CNPJ", "567890120001", "Ceasa Express Hortifruti Ltda", "Ceasa Express", "WHATSAPP", "À vista",
     [("Kátia Ribeiro", "11940060007", True)]),
    (7, "CNPJ", "678901230001", "Limpeza Total Distribuidora Ltda", "Limpeza Total", "VENDEDOR_VISITA", "7/14/21 dias",
     [("Wagner Silva", "11940070008", True), ("Escritório", "1125550009", False)]),
    (8, "CNPJ", "12ABC34501DE", "Nova Rota Distribuidora Ltda", "Nova Rota", "APLICATIVO", "7/14/21 dias",
     [("Thiago Barros", "11940080010", True)]),
]

def doc_fornecedor(f):
    return cpf(f[2]) if f[1] == "CPF" else cnpj(f[2])

# ------------------------------------------------------------ categorias
CATEGORIAS = [
    ("BASIC", "Alimentos básicos", True, 30),
    ("BEBID", "Bebidas", False, 20),
    ("LIMPZ", "Limpeza", False, None),
    ("FRIOS", "Frios, laticínios e congelados", False, 5),
    ("CARNE", "Carnes", True, 2),
    ("HORTI", "Hortifruti", False, None),
]

# ------------------------------------------------------------ produtos
# id, cat, nome, marca, base, peso, ctrl_val, vida(dias), custo, margem, est_min, popularidade, fornecedores,
# embalagens [(descr, fator, tipo_codigo, preco)]  tipo_codigo: EAN | INT (interno prefixo 2) | PLU
PRODUTOS = [
 (1, "BASIC", "Arroz Tio João Tipo 1 5 kg", "Tio João", "UN", False, True, 365, 24.90, 35, 15, 6, [2, 8], [("Pacote 5 kg", 1, "EAN", 32.90)]),
 (2, "BASIC", "Feijão Carioca Kicaldo 1 kg", "Kicaldo", "UN", False, True, 300, 6.80, 35, 20, 8, [2, 8], [("Pacote 1 kg", 1, "EAN", 8.99)]),
 (3, "BASIC", "Feijão Preto Camil 1 kg", "Camil", "UN", False, True, 300, 7.20, 35, 10, 3, [2], [("Pacote 1 kg", 1, "EAN", 9.49)]),
 (4, "BASIC", "Lentilha Yoki 500 g", "Yoki", "UN", False, True, 365, 6.10, 40, 6, 1, [2], [("Pacote 500 g", 1, "EAN", 8.49)]),
 (5, "BASIC", "Açúcar Refinado União 1 kg", "União", "UN", False, True, 720, 4.10, 35, 15, 6, [2, 8], [("Pacote 1 kg", 1, "EAN", 5.49)]),
 (6, "BASIC", "Óleo de Soja Liza 900 ml", "Liza", "UN", False, True, 365, 6.30, 30, 15, 5, [2, 8], [("Frasco 900 ml", 1, "EAN", 8.29)]),
 (7, "BASIC", "Macarrão Espaguete Renata 500 g", "Renata", "UN", False, True, 540, 3.20, 40, 15, 5, [2, 8], [("Pacote 500 g", 1, "EAN", 4.49)]),
 (8, "BASIC", "Café Pilão Tradicional 500 g", "Pilão", "UN", False, True, 270, 16.90, 35, 10, 4, [2, 8], [("Pacote 500 g", 1, "EAN", 22.90)]),
 (9, "BASIC", "Farinha de Trigo Dona Benta 1 kg", "Dona Benta", "UN", False, True, 240, 4.30, 35, 8, 2, [2], [("Pacote 1 kg", 1, "EAN", 5.79)]),
 (10, "BASIC", "Sal Refinado Cisne 1 kg", "Cisne", "UN", False, True, 720, 1.60, 55, 6, 1.5, [2], [("Pacote 1 kg", 1, "EAN", 2.49)]),
 (11, "BASIC", "Ovos Brancos Grandes 12 un", "Granja Mantiqueira", "UN", False, True, 21, 9.20, 40, 10, 4, [2], [("Bandeja 12 un", 1, "EAN", 12.90)]),
 (12, "BEBID", "Cerveja Skol Lata 350 ml", "Skol", "UN", False, True, 180, 2.75, 38, 48, 40, [1], [("Lata 350 ml", 1, "EAN", 3.79), ("Fardo 12 latas", 12, "EAN", 41.90)]),
 (13, "BEBID", "Cerveja Brahma Lata 473 ml", "Brahma", "UN", False, True, 180, 3.60, 38, 24, 16, [1], [("Lata 473 ml", 1, "INT", 4.99), ("Fardo 12 latas", 12, "EAN", 56.90)]),
 (14, "BEBID", "Refrigerante Coca-Cola 2 L", "Coca-Cola", "UN", False, True, 120, 7.40, 48, 24, 12, [1], [("Garrafa 2 L", 1, "EAN", 10.99)]),
 (15, "BEBID", "Refrigerante Guaraná Antarctica 2 L", "Antarctica", "UN", False, True, 120, 6.20, 45, 18, 8, [1], [("Garrafa 2 L", 1, "EAN", 8.99)]),
 (16, "BEBID", "Água Mineral Crystal 500 ml", "Crystal", "UN", False, True, 365, 0.95, 110, 48, 20, [1], [("Garrafa 500 ml", 1, "EAN", 2.00), ("Fardo 12 garrafas", 12, "EAN", 19.90)]),
 (17, "BEBID", "Suco Del Valle Uva 1 L", "Del Valle", "UN", False, True, 240, 6.90, 38, 6, 2.5, [1], [("Caixa 1 L", 1, "EAN", 9.49)]),
 (18, "LIMPZ", "Detergente Ypê Neutro 500 ml", "Ypê", "UN", False, False, None, 1.90, 47, 24, 6, [7], [("Frasco 500 ml", 1, "EAN", 2.79)]),
 (19, "LIMPZ", "Sabão em Pó Omo 1,6 kg", "Omo", "UN", False, False, None, 17.50, 42, 6, 1.5, [7], [("Caixa 1,6 kg", 1, "EAN", 24.90)]),
 (20, "LIMPZ", "Água Sanitária Qboa 2 L", "Qboa", "UN", False, False, None, 4.10, 58, 10, 3, [7], [("Frasco 2 L", 1, "EAN", 6.49)]),
 (21, "LIMPZ", "Papel Higiênico Neve Pacote 4 rolos", "Neve", "UN", False, False, None, 6.40, 55, 12, 4, [7], [("Pacote 4 rolos", 1, "EAN", 9.90), ("Fardo 4 pacotes", 4, "EAN", 36.90)]),
 (22, "LIMPZ", "Esponja Scotch-Brite 3 un", "Scotch-Brite", "UN", False, False, None, 4.20, 55, 6, 1.5, [7], [("Pacote 3 un", 1, "EAN", 6.49)]),
 (23, "FRIOS", "Leite Integral Italac 1 L", "Italac", "UN", False, True, 120, 4.35, 38, 48, 30, [3, 2, 8], [("Caixa 1 L", 1, "EAN", 5.99)]),
 (24, "FRIOS", "Iogurte Batavo Morango 170 g", "Batavo", "UN", False, True, 30, 2.10, 66, 12, 5, [3], [("Pote 170 g", 1, "EAN", 3.49)]),
 (25, "FRIOS", "Queijo Mussarela Fatiado (kg)", None, "KG", True, True, 25, 32.00, 56, 2, 1.5, [3], [("Quilo", 1, "PLU", 49.90)]),
 (26, "FRIOS", "Presunto Cozido Sadia Fatiado (kg)", "Sadia", "KG", True, True, 20, 26.00, 53, 2, 1.2, [3], [("Quilo", 1, "PLU", 39.90)]),
 (27, "FRIOS", "Margarina Qualy 500 g", "Qualy", "UN", False, True, 120, 6.90, 45, 8, 2, [3, 2], [("Pote 500 g", 1, "EAN", 9.99)]),
 (28, "FRIOS", "Pão de Queijo Forno de Minas 400 g", "Forno de Minas", "UN", False, True, 180, 9.80, 52, 5, 1, [3], [("Pacote 400 g", 1, "EAN", 14.90)]),
 (29, "FRIOS", "Hambúrguer Seara 672 g", "Seara", "UN", False, True, 180, 13.90, 43, 4, 0.8, [3], [("Caixa 672 g", 1, "EAN", 19.90)]),
 (30, "CARNE", "Carne Moída Patinho (kg)", None, "KG", True, True, 7, 32.00, 40, 3, 4, [4], [("Quilo", 1, "PLU", 44.90)]),
 (31, "CARNE", "Frango Coxa e Sobrecoxa (kg)", None, "KG", True, True, 8, 11.50, 47, 5, 6, [4], [("Quilo", 1, "PLU", 16.90)]),
 (32, "CARNE", "Linguiça Toscana Seara (kg)", "Seara", "KG", True, True, 20, 17.00, 46, 3, 2, [4], [("Quilo", 1, "PLU", 24.90)]),
 (33, "CARNE", "Contrafilé (kg)", None, "KG", True, True, 10, 45.00, 40, 2, 1.5, [4], [("Quilo", 1, "PLU", 62.90)]),
 (34, "HORTI", "Banana Prata (kg)", None, "KG", True, False, 6, 3.80, 71, 8, 8, [5, 6], [("Quilo", 1, "PLU", 6.49)]),
 (35, "HORTI", "Tomate (kg)", None, "KG", True, False, 7, 5.50, 63, 6, 6, [5, 6], [("Quilo", 1, "PLU", 8.99)]),
 (36, "HORTI", "Batata (kg)", None, "KG", True, False, 20, 4.20, 66, 8, 7, [5, 6], [("Quilo", 1, "PLU", 6.99)]),
 (37, "HORTI", "Cebola (kg)", None, "KG", True, False, 25, 3.90, 66, 5, 4, [5, 6], [("Quilo", 1, "PLU", 6.49)]),
 (38, "HORTI", "Alface Crespa (unidade)", None, "UN", False, False, 4, 1.80, 94, 5, 5, [5, 6], [("Unidade", 1, "INT", 3.49)]),
]

# fator de compra (quantas unidades base por unidade da nota) e custos por fornecedor
FATOR_COMPRA = {12: 12, 13: 12, 14: 6, 15: 6, 16: 12, 17: 12, 23: 12, 24: 24, 18: 24, 20: 12, 21: 4, 2: 10, 3: 10, 5: 10, 6: 20, 7: 20, 10: 10}
CUSTO_FORN = {  # (fornecedor, produto) -> custo por unidade base (início do mês)
    (8, 1): 25.40, (8, 2): 6.60, (8, 5): 4.25, (8, 6): 6.10, (8, 7): 3.35, (8, 8): 17.40,
    (2, 23): 5.20, (2, 27): 7.10, (8, 23): 5.25,
}
