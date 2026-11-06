"""
Testes Unitários para Validação das Regras de Negócio e Conciliação
"""

from models import NotaFiscalSchema, ItemNota, StatusConciliacao
from conciliator import validar_cnpj, validar_cpf, conciliar_nota
from database import salvar_nota, obter_nota_completa, init_db, excluir_nota


def test_validador_cnpj():
    # CNPJ válido de exemplo oficial
    assert validar_cnpj("11.222.333/0001-81") is True
    assert validar_cnpj("11222333000181") is True
    
    # CNPJs inválidos
    assert validar_cnpj("11.222.333/0001-82") is False  # dígito incorreto
    assert validar_cnpj("00000000000000") is False      # repetido
    assert validar_cnpj("1234") is False                # tamanho incorreto


def test_validador_cpf():
    # CPF fictício com algoritmo válido
    assert validar_cpf("123.456.789-09") is True
    assert validar_cpf("111.111.111-11") is False


def test_conciliacao_sucesso():
    nota = NotaFiscalSchema(
        razao_social="MERCADO CENTRAL",
        cnpj_cpf="11.222.333/0001-81",
        data_emissao="2026-05-10",
        tipo_documento="NFC-e",
        itens=[
            ItemNota(descricao="Cafe Torrado 500g", quantidade=2, valor_unitario=15.0, valor_total=30.0),
            ItemNota(descricao="Leite Integral 1L", quantidade=4, valor_unitario=5.0, valor_total=20.0),
        ],
        subtotal_itens=50.0,
        desconto=5.0,
        acrescimo_taxas=0.0,
        valor_total=45.0  # 30 + 20 - 5 = 45
    )

    resultado = conciliar_nota(nota)
    assert resultado.status == StatusConciliacao.CONCILIADO
    assert resultado.diferenca == 0.0
    assert resultado.cnpj_valido is True


def test_conciliacao_divergente():
    nota = NotaFiscalSchema(
        razao_social="RESTAURANTE SABORES",
        cnpj_cpf="04.123.456/0001-99",
        data_emissao="2026-05-11",
        tipo_documento="Recibo",
        itens=[
            ItemNota(descricao="Almoço Executivo", quantidade=1, valor_unitario=40.0, valor_total=40.0),
            ItemNota(descricao="Refrigerante Lata", quantidade=1, valor_unitario=8.0, valor_total=8.0),
        ],
        subtotal_itens=48.0,
        desconto=0.0,
        acrescimo_taxas=0.0,
        valor_total=55.0  # Itens somam 48.0, total diz 55.0 -> divergência de R$ -7.00
    )

    resultado = conciliar_nota(nota)
    assert resultado.status == StatusConciliacao.DIVERGENTE
    assert resultado.diferenca == -7.00
    assert any("Divergência matemática" in d for d in resultado.detalhes_divergencia)


def test_database_salvar_e_recuperar():
    init_db()
    nota = NotaFiscalSchema(
        razao_social="TESTE PAPELARIA",
        cnpj_cpf="11222333000181",
        data_emissao="2026-05-12",
        tipo_documento="NF-e",
        itens=[
            ItemNota(descricao="Caderno 10 Matérias", quantidade=1, valor_unitario=25.0, valor_total=25.0)
        ],
        valor_total=25.0
    )
    resultado = conciliar_nota(nota)
    nota_id = salvar_nota(nota, resultado, arquivo_origem="teste.png")
    assert nota_id > 0

    detalhes = obter_nota_completa(nota_id)
    assert detalhes is not None
    assert detalhes["razao_social"] == "TESTE PAPELARIA"
    assert len(detalhes["itens"]) == 1
    assert detalhes["itens"][0]["descricao"] == "Caderno 10 Matérias"

    # Limpeza
    excluir_nota(nota_id)
    assert obter_nota_completa(nota_id) is None


if __name__ == "__main__":
    print("Executando bateria de testes...")
    test_validador_cnpj()
    test_validador_cpf()
    test_conciliacao_sucesso()
    test_conciliacao_divergente()
    test_database_salvar_e_recuperar()
    print(" Todos os 5 testes passaram com sucesso!")
