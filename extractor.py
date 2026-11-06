"""
Módulo de Extração Visual de Documentos Fiscais usando Vision AI (Gemini)
"""

import os
import io
import json
import mimetypes
from pathlib import Path
from typing import Tuple, Union, Optional
from PIL import Image
from pydantic import ValidationError

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL, CATEGORIAS_DESPESA
from models import NotaFiscalSchema, ItemNota


PROMPT_SISTEMA_EXTRACAO = f"""
Você é um auditor financeiro e especialista em documentos fiscais brasileiros (NFC-e, NF-e, SAT, Cupom Fiscal, Recibos de Pagamento e Notas de Débito).
Sua missão é analisar minuciosamente a imagem ou documento PDF fornecido e extrair todos os dados estruturados com precisão máxima.

INSTRUÇÕES ESPECÍFICAS:
1. Razão Social & Nome Fantasia: Identifique o nome comercial ou empresarial no cabeçalho do documento.
2. CNPJ / CPF: Extraia apenas os dígitos ou formato com pontuação padrão do emissor. Se não houver, deixe nulo.
3. Data e Hora: Extraia a data no formato ISO AAAA-MM-DD. Se a data estiver em formato brasileiro (ex: 15/05/2026), converta corretamente.
4. Itens Adquiridos:
   - Para cada item na lista/tabela: identifique o nome/descrição clara, a quantidade (float), o valor unitário e o valor total daquele item.
   - Certifique-se de que quantidade * unitario corresponda ao valor_total de cada item.
5. Totais e Descontos:
   - Subtotal dos itens: soma de todos os itens antes de descontos.
   - Descontos: se houver descontos promocionais ou cupons, anote o valor positivo.
   - Acréscimos/Taxas: gorjetas, taxa de serviço (ex: 10%), frete ou taxa de entrega.
   - Impostos: tributos totais estimados (ex: De Olho no Imposto / Lei 12.741).
   - Valor Total Final: o valor líquido total pago.
6. Categoria Financeira Sugerida:
   - Escolha a categoria mais apropriada dentre as opções:
     {", ".join(CATEGORIAS_DESPESA)}
7. Tipo de Documento: classifique como 'NFC-e', 'NF-e', 'Cupom Fiscal', 'Recibo de Pagamento', 'Comprovante' ou 'Nota de Serviço'.
"""


def _detectar_mimetype(caminho_ou_bytes: Union[str, Path, bytes], nome_arquivo: str = "") -> str:
    """Identifica o MIME type adequado para o arquivo."""
    if isinstance(caminho_ou_bytes, (str, Path)):
        caminho = Path(caminho_ou_bytes)
        mime, _ = mimetypes.guess_type(str(caminho))
        if mime:
            return mime
        ext = caminho.suffix.lower()
    else:
        ext = Path(nome_arquivo).suffix.lower() if nome_arquivo else ""

    mapa = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    return mapa.get(ext, "image/jpeg")


def _gerar_mock_demonstrativo(nome_arquivo: str = "") -> NotaFiscalSchema:
    """
    Retorna uma extração simulada realista para fins de demonstração,
    caso a chave GEMINI_API_KEY não tenha sido configurada no ambiente.
    """
    return NotaFiscalSchema(
        razao_social="POSTO E CONVENIENCIA ESTRELA LTDA",
        nome_fantasia="Auto Posto Estrela Shell",
        cnpj_cpf="11.222.333/0001-81",
        data_emissao="2026-05-18",
        hora_emissao="14:32:10",
        numero_documento="000142980",
        serie="001",
        chave_acesso="35260511222333000181650010001429801234567890",
        tipo_documento="NFC-e",
        itens=[
            ItemNota(descricao="GASOLINA ADITIVADA (LITROS)", quantidade=30.0, valor_unitario=5.89, valor_total=176.70),
            ItemNota(descricao="CAFE EXPRESSO DUPLO", quantidade=1.0, valor_unitario=8.50, valor_total=8.50),
            ItemNota(descricao="AGUA MINERAL SEM GAS 500ML", quantidade=2.0, valor_unitario=4.00, valor_total=8.00),
            ItemNota(descricao="PÃO DE QUEIJO TRADICIONAL", quantidade=2.0, valor_unitario=6.00, valor_total=12.00),
        ],
        subtotal_itens=205.20,
        desconto=5.20,
        acrescimo_taxas=0.00,
        impostos_estimados=42.30,
        valor_total=200.00,
        forma_pagamento="Cartão de Crédito",
        categoria_sugerida="Transporte & Combustível"
    )


def extrair_dados_documento(
    conteudo: Union[bytes, io.BytesIO, Path, str],
    nome_arquivo: str = "documento.jpg",
    api_key: Optional[str] = None
) -> Tuple[NotaFiscalSchema, bool, str]:
    """
    Processa uma imagem ou PDF de recibo / nota fiscal através da Vision AI do Gemini.

    Retorna:
        Tuple[NotaFiscalSchema, is_mock: bool, mensagem_status: str]
    """
    chave = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

    # Leitura dos bytes do arquivo
    if isinstance(conteudo, (str, Path)):
        with open(conteudo, "rb") as f:
            dados_bytes = f.read()
    elif isinstance(conteudo, io.BytesIO):
        dados_bytes = conteudo.getvalue()
    elif isinstance(conteudo, bytes):
        dados_bytes = conteudo
    else:
        raise ValueError("Formato de conteúdo não suportado.")

    mime_type = _detectar_mimetype(conteudo if isinstance(conteudo, (str, Path)) else dados_bytes, nome_arquivo)

    # Se a chave não estiver configurada, usa o modo de demonstração
    if not chave:
        mock = _gerar_mock_demonstrativo(nome_arquivo)
        msg = (
            "[AVISO] GEMINI_API_KEY não detectada. Dados simulados gerados para demonstração do fluxo! "
            "Para leitura real de recibos e cupons via Vision LLM, configure sua GEMINI_API_KEY no arquivo .env."
        )
        return mock, True, msg

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=chave)

        # Configura structured output com o schema Pydantic
        config = types.GenerateContentConfig(
            system_instruction=PROMPT_SISTEMA_EXTRACAO,
            response_mime_type="application/json",
            response_schema=NotaFiscalSchema,
            temperature=0.1,
        )

        part = types.Part.from_bytes(data=dados_bytes, mime_type=mime_type)

        response = client.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=[part, "Analise esta nota fiscal / recibo e extraia os dados conforme o schema estruturado."],
            config=config,
        )

        texto_json = response.text
        if not texto_json:
            raise ValueError("O modelo não retornou conteúdo.")

        nota_dict = json.loads(texto_json)
        nota_extraida = NotaFiscalSchema(**nota_dict)
        return nota_extraida, False, "Extração visual realizada com sucesso via Gemini Vision AI."

    except Exception as e:
        # Se ocorrer falha na chamada à API (ex: quota ou chave inválida), informa o erro e fornece o mock como fallback seguro
        mock = _gerar_mock_demonstrativo(nome_arquivo)
        msg_erro = f"Erro na chamada Gemini Vision AI ({str(e)}). Apresentando dados demonstrativos para continuidade dos testes."
        return mock, True, msg_erro
