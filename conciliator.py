"""
Módulo de Conciliação Financeira e Validação Cadastral
"""

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Optional
from models import NotaFiscalSchema, ResultadoConciliacao, StatusConciliacao


def limpar_documento(doc: Optional[str]) -> str:
    """Remove caracteres não numéricos de um CPF ou CNPJ."""
    if not doc:
        return ""
    return re.sub(r"\D", "", doc)


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ brasileiro calculando os dígitos verificadores.
    """
    cnpj = limpar_documento(cnpj)
    if len(cnpj) != 14:
        return False

    # Elimina números com todos os dígitos iguais (ex: 00000000000000, 11111111111111)
    if cnpj == cnpj[0] * 14:
        return False

    # Primeiro dígito verificador
    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_1 = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
    resto_1 = soma_1 % 11
    digito_1 = 0 if resto_1 < 2 else 11 - resto_1

    if int(cnpj[12]) != digito_1:
        return False

    # Segundo dígito verificador
    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_2 = sum(int(cnpj[i]) * pesos_2[i] for i in range(13))
    resto_2 = soma_2 % 11
    digito_2 = 0 if resto_2 < 2 else 11 - resto_2

    return int(cnpj[13]) == digito_2


def validar_cpf(cpf: str) -> bool:
    """
    Valida um CPF brasileiro calculando os dígitos verificadores.
    """
    cpf = limpar_documento(cpf)
    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    soma_1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito_1 = (soma_1 * 10 % 11) % 10
    if int(cpf[9]) != digito_1:
        return False

    soma_2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito_2 = (soma_2 * 10 % 11) % 10
    return int(cpf[10]) == digito_2


def formatar_documento(doc: Optional[str]) -> str:
    """Formata CPF ou CNPJ para exibição visual limpa."""
    limpo = limpar_documento(doc)
    if len(limpo) == 14:
        return f"{limpo[:2]}.{limpo[2:5]}.{limpo[5:8]}/{limpo[8:12]}-{limpo[12:]}"
    elif len(limpo) == 11:
        return f"{limpo[:3]}.{limpo[3:6]}.{limpo[6:9]}-{limpo[9:]}"
    return doc or "Não informado"


def conciliar_nota(nota: NotaFiscalSchema, tolerancia_maxima: float = 0.02) -> ResultadoConciliacao:
    """
    Executa a conferência e conciliação matemática da nota fiscal ou recibo:
    1. Soma dos itens da lista
    2. Consideração de descontos e acréscimos/taxas
    3. Comparação com o valor total informado no cabeçalho
    4. Validação cadastral do CNPJ/CPF do emissor
    """
    detalhes = []

    # Cálculo preciso em Decimal
    soma_itens = sum(Decimal(str(item.valor_total)) for item in nota.itens)
    desconto = Decimal(str(nota.desconto or 0.0))
    acrescimo = Decimal(str(nota.acrescimo_taxas or 0.0))
    total_declarado = Decimal(str(nota.valor_total))

    total_esperado = (soma_itens - desconto + acrescimo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    diferenca = (total_esperado - total_declarado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    abs_diferenca = abs(diferenca)

    tolerancia = Decimal(str(tolerancia_maxima))
    tolerancia_aplicada = False

    # Validação dos Itens
    if not nota.itens:
        status = StatusConciliacao.INCOMPLETO
        detalhes.append("Nenhum item individual foi identificado na nota/recibo.")
        resumo_status = "Incompleto: Itens individuais não identificados."
    elif abs_diferenca == Decimal("0.00"):
        status = StatusConciliacao.CONCILIADO
        resumo_status = "Conciliado perfeitamente (Diferença R$ 0,00)."
    elif abs_diferenca <= tolerancia:
        status = StatusConciliacao.CONCILIADO
        tolerancia_aplicada = True
        detalhes.append(f"Pequena variação de centavos (R$ {diferenca:+.2f}) aceita dentro da tolerância de arredondamento fiscal.")
        resumo_status = f"Conciliado com tolerância de arredondamento (Diferença R$ {diferenca:+.2f})."
    else:
        status = StatusConciliacao.DIVERGENTE
        detalhes.append(
            f"Divergência matemática detectada: A soma calculada dos itens "
            f"(R$ {soma_itens:.2f}) - Descontos (R$ {desconto:.2f}) + Taxas (R$ {acrescimo:.2f}) = "
            f"R$ {total_esperado:.2f}, mas o valor total indicado no documento é R$ {total_declarado:.2f} "
            f"(Diferença de R$ {diferenca:+.2f})."
        )
        resumo_status = f"Divergência detectada: diferença de R$ {diferenca:+.2f}."

    # Validação do CNPJ / CPF
    cnpj_limpo = limpar_documento(nota.cnpj_cpf)
    cnpj_valido: Optional[bool] = None
    msg_cnpj = ""

    if cnpj_limpo:
        if len(cnpj_limpo) == 14:
            cnpj_valido = validar_cnpj(cnpj_limpo)
            if cnpj_valido:
                msg_cnpj = f"CNPJ {formatar_documento(cnpj_limpo)} válido na base da Receita Federal."
            else:
                msg_cnpj = f"CNPJ {formatar_documento(cnpj_limpo)} possui dígitos verificadores inválidos."
                detalhes.append(msg_cnpj)
        elif len(cnpj_limpo) == 11:
            cnpj_valido = validar_cpf(cnpj_limpo)
            if cnpj_valido:
                msg_cnpj = f"CPF {formatar_documento(cnpj_limpo)} válido."
            else:
                msg_cnpj = f"CPF {formatar_documento(cnpj_limpo)} possui dígitos verificadores inválidos."
                detalhes.append(msg_cnpj)
        else:
            cnpj_valido = False
            msg_cnpj = f"Documento cadastral '{nota.cnpj_cpf}' com quantidade de dígitos incorreta."
            detalhes.append(msg_cnpj)
    else:
        msg_cnpj = "CNPJ ou CPF do emissor não informado no comprovante."

    return ResultadoConciliacao(
        status=status,
        soma_itens=float(soma_itens),
        valor_total_declarado=float(total_declarado),
        diferenca=float(diferenca),
        tolerancia_aplicada=tolerancia_aplicada,
        cnpj_valido=cnpj_valido,
        mensagem_cnpj=msg_cnpj,
        detalhes_divergencia=detalhes,
        resumo_status=resumo_status
    )
