"""
Módulo de Modelos de Dados (Schemas Pydantic)
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class StatusConciliacao(str, Enum):
    CONCILIADO = "CONCILIADO"
    DIVERGENTE = "DIVERGENTE"
    INCOMPLETO = "INCOMPLETO"


class ItemNota(BaseModel):
    descricao: str = Field(..., description="Nome ou descrição do produto ou serviço adquirido")
    quantidade: float = Field(default=1.0, description="Quantidade de unidades adquiridas")
    valor_unitario: float = Field(default=0.0, description="Valor por unidade em Reais (BRL)")
    valor_total: float = Field(..., description="Valor total do item (quantidade * unitario) em Reais (BRL)")


class NotaFiscalSchema(BaseModel):
    razao_social: str = Field(..., description="Razão Social ou Nome do Estabelecimento Emissor")
    nome_fantasia: Optional[str] = Field(None, description="Nome Fantasia do Estabelecimento, se visível")
    cnpj_cpf: Optional[str] = Field(None, description="CNPJ ou CPF do emissor sem pontuação ou com pontuação")
    data_emissao: Optional[str] = Field(None, description="Data da emissão no formato AAAA-MM-DD (ex: 2026-05-15) ou texto original")
    hora_emissao: Optional[str] = Field(None, description="Horário da emissão no formato HH:MM:SS, se disponível")
    numero_documento: Optional[str] = Field(None, description="Número da Nota Fiscal, Cupom Fiscal ou Recibo")
    serie: Optional[str] = Field(None, description="Série do documento fiscal, se houver")
    chave_acesso: Optional[str] = Field(None, description="Chave de acesso de 44 dígitos da NF-e / NFC-e, se presente")
    tipo_documento: str = Field(
        default="Recibo", 
        description="Tipo de comprovante: NFC-e, NF-e, Cupom Fiscal, Recibo Comercial, Comprovante de Pagamento, etc."
    )
    itens: List[ItemNota] = Field(default_factory=list, description="Lista dos itens detalhados comprados")
    subtotal_itens: float = Field(default=0.0, description="Soma dos valores totais de cada item")
    desconto: float = Field(default=0.0, description="Valor total de descontos aplicados")
    acrescimo_taxas: float = Field(default=0.0, description="Acréscimos, gorjetas, taxas de entrega ou frete")
    impostos_estimados: float = Field(default=0.0, description="Tributos aproximados (ex: Lei da Transparência / De Olho no Imposto / ICMS / ISS)")
    valor_total: float = Field(..., description="Valor total líquido final pago pelo cliente")
    forma_pagamento: Optional[str] = Field(None, description="Forma de pagamento (Cartão de Crédito, Débito, Pix, Dinheiro, Boleto, etc.)")
    categoria_sugerida: str = Field(
        default="Outros / Diversos",
        description="Categoria financeira da despesa (ex: Alimentação & Refeição, Transporte & Combustível, Tecnologia, Material de Escritório)"
    )


class ResultadoConciliacao(BaseModel):
    status: StatusConciliacao
    soma_itens: float
    valor_total_declarado: float
    diferenca: float
    tolerancia_aplicada: bool = False
    cnpj_valido: Optional[bool] = None
    mensagem_cnpj: str = ""
    detalhes_divergencia: List[str] = Field(default_factory=list)
    resumo_status: str = ""
