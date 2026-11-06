"""
Módulo de Exportação para Planilhas Excel e CSV
"""

import io
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd
from config import EXPORTS_DIR
from database import obter_dataframes


def gerar_relatorio_excel(caminho_saida: Optional[Path] = None) -> Tuple[bytes, str]:
    """
    Gera um arquivo Excel (.xlsx) completo com abas estruturadas:
    1. Resumo das Notas Fiscais
    2. Detalhamento dos Itens
    3. Análise por Categoria de Despesa
    """
    df_notas, df_itens = obter_dataframes()

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Aba 1: Resumo das Notas
        colunas_notas = [
            "id", "data_emissao", "razao_social", "cnpj_cpf", "tipo_documento",
            "valor_total", "subtotal_itens", "desconto", "acrescimo_taxas",
            "forma_pagamento", "categoria", "status_conciliacao", "diferenca_conciliacao"
        ]
        cols_presentes = [c for c in colunas_notas if c in df_notas.columns]
        df_notas_export = df_notas[cols_presentes] if not df_notas.empty else pd.DataFrame(columns=colunas_notas)
        
        # Renomeia colunas para cabeçalhos legíveis em português
        nomes_colunas_notas = {
            "id": "ID",
            "data_emissao": "Data Emissão",
            "razao_social": "Razão Social / Emissor",
            "cnpj_cpf": "CNPJ / CPF",
            "tipo_documento": "Tipo Documento",
            "valor_total": "Valor Total (R$)",
            "subtotal_itens": "Subtotal Itens (R$)",
            "desconto": "Desconto (R$)",
            "acrescimo_taxas": "Taxas/Acréscimos (R$)",
            "forma_pagamento": "Forma Pagamento",
            "categoria": "Categoria Despesa",
            "status_conciliacao": "Status Conciliação",
            "diferenca_conciliacao": "Diferença Conciliação (R$)",
        }
        df_notas_export.rename(columns=nomes_colunas_notas).to_excel(
            writer, sheet_name="Notas e Recibos", index=False
        )

        # Aba 2: Detalhamento dos Itens
        if not df_itens.empty:
            df_itens_export = df_itens.rename(columns={
                "id": "Item ID",
                "nota_id": "Nota ID",
                "descricao": "Descrição do Item",
                "quantidade": "Qtd",
                "valor_unitario": "Valor Unitário (R$)",
                "valor_total": "Total do Item (R$)",
                "razao_social": "Estabelecimento",
                "data_emissao": "Data Emissão",
                "categoria": "Categoria"
            })
            df_itens_export.to_excel(writer, sheet_name="Itens Detalhados", index=False)
        else:
            pd.DataFrame(columns=["Nota ID", "Descrição", "Qtd", "Valor Unitário", "Total Item"]).to_excel(
                writer, sheet_name="Itens Detalhados", index=False
            )

        # Aba 3: Gastos por Categoria
        if not df_notas.empty and "categoria" in df_notas.columns and "valor_total" in df_notas.columns:
            df_cat = df_notas.groupby("categoria", as_index=False).agg(
                Total_Gasto=("valor_total", "sum"),
                Qtd_Notas=("id", "count")
            ).sort_values(by="Total_Gasto", ascending=False)
            df_cat.rename(columns={
                "categoria": "Categoria",
                "Total_Gasto": "Total Gasto (R$)",
                "Qtd_Notas": "Quantidade de Documentos"
            }).to_excel(writer, sheet_name="Gastos por Categoria", index=False)

    buffer.seek(0)
    excel_bytes = buffer.getvalue()

    if caminho_saida:
        caminho_saida = Path(caminho_saida)
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_saida, "wb") as f:
            f.write(excel_bytes)
        return excel_bytes, str(caminho_saida)

    return excel_bytes, "relatorio_conciliacao.xlsx"


def gerar_relatorio_csv(separador: str = ";") -> str:
    """
    Gera conteúdo CSV em formato compatível com Excel e softwares contábeis (UTF-8 com BOM).
    """
    df_notas, _ = obter_dataframes()
    if df_notas.empty:
        return "ID;Data;Razao_Social;CNPJ;Valor_Total;Status_Conciliacao\n"
    
    return df_notas.to_csv(sep=separador, index=False, encoding="utf-8-sig")
