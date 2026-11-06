"""
Assistente de Extração e Conciliação de Notas Fiscais e Recibos
Interface Web Moderna e Interativa (Streamlit)
"""

import os
import io
from pathlib import Path
import streamlit as st
import pandas as pd
from PIL import Image

from config import (
    GEMINI_API_KEY,
    DEFAULT_GEMINI_MODEL,
    CATEGORIAS_DESPESA,
    UPLOADS_DIR,
)
from models import NotaFiscalSchema, ItemNota, StatusConciliacao
from extractor import extrair_dados_documento
from conciliator import conciliar_nota, formatar_documento
from database import (
    salvar_nota,
    listar_notas,
    obter_nota_completa,
    excluir_nota,
    obter_dataframes,
    init_db,
)
from exporter import gerar_relatorio_excel, gerar_relatorio_csv

# Configuração da página Streamlit
st.set_page_config(
    page_title="Assistente de Conciliação Fiscal",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa o banco de dados
init_db()

# Estilos customizados CSS para acabamento profissional
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .card-conciliado {
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    .card-divergente {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    .badge-success {
        background-color: #10B981;
        color: white;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-error {
        background-color: #EF4444;
        color: white;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/receipt.png", width=64)
    st.title("Configurações")
    
    # Campo para chave do Gemini (se quiser sobrescrever ou informar via UI)
    api_key_input = st.text_input(
        "Chave Gemini API",
        type="password",
        value=GEMINI_API_KEY,
        help="Insira sua GEMINI_API_KEY. Se deixada em branco, o sistema utilizará simulação para testes."
    )
    
    modelo_selecionado = st.selectbox(
        "Modelo Vision AI",
        ["gemini-2.5-flash", "gemini-2.5-pro"],
        index=0
    )

    tolerancia = st.number_input(
        "Tolerância de Arredondamento (R$)",
        min_value=0.00,
        max_value=0.50,
        value=0.02,
        step=0.01,
        help="Diferença máxima em centavos aceita como arredondamento fiscal automático."
    )

    st.markdown("---")
    st.markdown("### Exemplos Rápidos de Teste")
    st.caption("Clique para carregar comprovantes de demonstração:")
    
    exemplos_dir = Path(__file__).resolve().parent / "exemplos"
    exemplo_escolhido = None

    if (exemplos_dir / "recibo_posto_conciliado.png").exists():
        if st.button("⛽ Cupom Posto (100% Conciliado)", use_container_width=True):
            exemplo_escolhido = exemplos_dir / "recibo_posto_conciliado.png"

    if (exemplos_dir / "recibo_restaurante_divergente.png").exists():
        if st.button("🍽️ Recibo Bistrô (Divergência R$ 15,40)", use_container_width=True):
            exemplo_escolhido = exemplos_dir / "recibo_restaurante_divergente.png"

    if (exemplos_dir / "danfe_papelaria_tech.pdf").exists():
        if st.button("📄 DANFE PDF Papelaria & Tech", use_container_width=True):
            exemplo_escolhido = exemplos_dir / "danfe_papelaria_tech.pdf"

    st.markdown("---")
    st.caption("Desenvolvido para pequenos negócios, contabilidades e autônomos.")


# --- CABEÇALHO PRINCIPAL ---
st.markdown('<div class="main-header">🧾 Assistente de Extração & Conciliação Fiscal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Elimine a digitação manual de notas fiscais, recibos e cupons com leitura visual multimodal e validação contábil automática.</div>',
    unsafe_allow_html=True
)

tab_leitura, tab_painel, tab_exportar = st.tabs([
    "📥 Nova Leitura & Auditoria",
    "📊 Painel Financeiro & Histórico",
    "📤 Exportação de Planilhas"
])


# --- ABA 1: NOVA LEITURA & CONCILIAÇÃO ---
with tab_leitura:
    st.subheader("Envio de Comprovante")
    
    uploaded_file = st.file_uploader(
        "Arraste ou selecione uma imagem ou PDF de Nota Fiscal / Recibo / Cupom Fiscal",
        type=["png", "jpg", "jpeg", "pdf", "webp"],
        help="Formatos aceitos: Imagens de recibos amassados ou fotos de celular (PNG, JPG) e documentos digitais em PDF."
    )

    arquivo_bytes = None
    nome_arquivo = ""
    is_pdf = False

    if uploaded_file is not None:
        arquivo_bytes = uploaded_file.getvalue()
        nome_arquivo = uploaded_file.name
        is_pdf = nome_arquivo.lower().endswith(".pdf")
    elif exemplo_escolhido is not None:
        with open(exemplo_escolhido, "rb") as f:
            arquivo_bytes = f.read()
        nome_arquivo = exemplo_escolhido.name
        is_pdf = nome_arquivo.lower().endswith(".pdf")
        st.info(f"Carregado arquivo de demonstração: **{nome_arquivo}**")

    if arquivo_bytes:
        col_doc, col_extracao = st.columns([1, 1.2])

        with col_doc:
            st.markdown("#### 📄 Documento Original")
            if is_pdf:
                st.success(f"Arquivo PDF: **{nome_arquivo}** ({len(arquivo_bytes) / 1024:.1f} KB)")
                st.caption("Documento digital pronto para extração pelo Gemini Vision.")
            else:
                try:
                    img = Image.open(io.BytesIO(arquivo_bytes))
                    st.image(img, caption=nome_arquivo, use_container_width=True)
                except Exception:
                    st.warning("Não foi possível renderizar o preview da imagem.")

        with col_extracao:
            st.markdown("#### 🧠 Extração & Auditoria")
            
            with st.spinner("Realizando leitura visual e conciliação matemática..."):
                nota_extraida, is_mock, msg_info = extrair_dados_documento(
                    arquivo_bytes,
                    nome_arquivo=nome_arquivo,
                    api_key=api_key_input
                )
                conciliacao = conciliar_nota(nota_extraida, tolerancia_maxima=tolerancia)

            if is_mock:
                st.warning(msg_info)
            else:
                st.success(msg_info)

            # Card de Conciliação
            if conciliacao.status == StatusConciliacao.CONCILIADO:
                st.markdown(f"""
                <div class="card-conciliado">
                    <span class="badge-success">CONCILIADO COM SUCESSO</span>
                    <h4 style="color: #065F46; margin-top: 0.5rem; margin-bottom: 0.2rem;">Soma dos itens confere com o valor total</h4>
                    <p style="color: #047857; margin-bottom: 0;">{conciliacao.resumo_status}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card-divergente">
                    <span class="badge-error">DIVERGÊNCIA DETECTADA</span>
                    <h4 style="color: #991B1B; margin-top: 0.5rem; margin-bottom: 0.2rem;">Discrepância nos valores da nota</h4>
                    <p style="color: #B91C1C; margin-bottom: 0;">{conciliacao.resumo_status}</p>
                </div>
                """, unsafe_allow_html=True)

            # Detalhes Cadastrais
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Estabelecimento:** {nota_extraida.razao_social}")
                if nota_extraida.nome_fantasia:
                    st.caption(f"Nome Fantasia: {nota_extraida.nome_fantasia}")
                
                cnpj_fmt = formatar_documento(nota_extraida.cnpj_cpf)
                if conciliacao.cnpj_valido is True:
                    st.write(f"**CNPJ:** `{cnpj_fmt}`  🟢 (Válido)")
                elif conciliacao.cnpj_valido is False:
                    st.write(f"**CNPJ:** `{cnpj_fmt}`  🔴 (Dígitos Inválidos)")
                else:
                    st.write(f"**CNPJ:** `{cnpj_fmt}`")

            with c2:
                st.write(f"**Data:** {nota_extraida.data_emissao or 'N/D'} {nota_extraida.hora_emissao or ''}")
                st.write(f"**Tipo:** {nota_extraida.tipo_documento}")
                st.write(f"**Nº Doc:** {nota_extraida.numero_documento or 'N/D'}")
                st.write(f"**Pagamento:** {nota_extraida.forma_pagamento or 'N/D'}")

            # Categoria da Despesa (editável antes de salvar)
            idx_cat = 0
            if nota_extraida.categoria_sugerida in CATEGORIAS_DESPESA:
                idx_cat = CATEGORIAS_DESPESA.index(nota_extraida.categoria_sugerida)
            categoria_final = st.selectbox("Categoria da Despesa", CATEGORIAS_DESPESA, index=idx_cat)
            nota_extraida.categoria_sugerida = categoria_final

            # Tabela de Itens Comprados
            st.markdown("##### 🛒 Itens Identificados no Comprovante")
            if nota_extraida.itens:
                dados_itens = [
                    {
                        "Item": i + 1,
                        "Descrição": it.descricao,
                        "Qtd": it.quantidade,
                        "Valor Unitário (R$)": f"R$ {it.valor_unitario:.2f}",
                        "Valor Total (R$)": f"R$ {it.valor_total:.2f}",
                    }
                    for i, it in enumerate(nota_extraida.itens)
                ]
                st.dataframe(pd.DataFrame(dados_itens), use_container_width=True, hide_index=True)
            else:
                st.caption("Nenhum item individual discriminado.")

            # Resumo Numérico
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Subtotal Itens", f"R$ {nota_extraida.subtotal_itens:.2f}")
            m2.metric("Descontos", f"- R$ {nota_extraida.desconto:.2f}")
            m3.metric("Taxas / Acréscimos", f"+ R$ {nota_extraida.acrescimo_taxas:.2f}")
            m4.metric("Valor Total Pago", f"R$ {nota_extraida.valor_total:.2f}")

            # Auditoria detalhada
            if conciliacao.detalhes_divergencia:
                with st.expander("🔍 Detalhes da Auditoria & Regras de Validação"):
                    for d in conciliacao.detalhes_divergencia:
                        st.write(f"- {d}")

            # Botão de Gravação
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Confirmar e Gravar no Banco de Dados", type="primary", use_container_width=True):
                # Salva no disco uploads
                caminho_salvo = UPLOADS_DIR / nome_arquivo
                with open(caminho_salvo, "wb") as f:
                    f.write(arquivo_bytes)

                id_gravado = salvar_nota(nota_extraida, conciliacao, arquivo_origem=nome_arquivo)
                st.success(f"Nota Fiscal cadastrada com sucesso! Registro **#{id_gravado}** gravado no banco de dados.")
                st.balloons()
    else:
        st.info("👆 Faça o upload de um arquivo ou clique em um dos botões de exemplo na barra lateral para iniciar a análise.")


# --- ABA 2: PAINEL FINANCEIRO & HISTÓRICO ---
with tab_painel:
    st.subheader("Painel de Controle Financeiro")
    
    df_notas, df_itens = obter_dataframes()

    if df_notas.empty:
        st.info("Nenhuma nota fiscal ou recibo foi cadastrado até o momento. Processe algum comprovante na aba 'Nova Leitura'.")
    else:
        # Métricas Consolidadas
        total_notas = len(df_notas)
        total_gasto = df_notas["valor_total"].sum()
        notas_conciliadas = len(df_notas[df_notas["status_conciliacao"] == "CONCILIADO"])
        taxa_conciliacao = (notas_conciliadas / total_notas) * 100 if total_notas > 0 else 0
        ticket_medio = total_gasto / total_notas if total_notas > 0 else 0

        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        c_m1.metric("Comprovantes Registrados", f"{total_notas}")
        c_m2.metric("Total Acumulado", f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c_m3.metric("Taxa de Conciliação", f"{taxa_conciliacao:.1f}%", f"{notas_conciliadas}/{total_notas} conc.")
        c_m4.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")

        st.markdown("---")

        # Gráfico por Categoria
        col_graf, col_tabela = st.columns([1, 1.2])

        with col_graf:
            st.markdown("##### 📊 Gastos por Categoria")
            if "categoria" in df_notas.columns:
                gastos_por_cat = df_notas.groupby("categoria")["valor_total"].sum().reset_index()
                gastos_por_cat = gastos_por_cat.sort_values(by="valor_total", ascending=False)
                st.bar_chart(gastos_por_cat.set_index("categoria"), use_container_width=True)

        with col_tabela:
            st.markdown("##### 📑 Últimos Documentos Registrados")
            colunas_exibicao = [
                "id", "data_emissao", "razao_social", "valor_total", "categoria", "status_conciliacao"
            ]
            cols_ok = [c for c in colunas_exibicao if c in df_notas.columns]
            df_display = df_notas[cols_ok].copy()
            df_display.rename(columns={
                "id": "ID",
                "data_emissao": "Data",
                "razao_social": "Emissor",
                "valor_total": "Total (R$)",
                "categoria": "Categoria",
                "status_conciliacao": "Status",
            }, inplace=True)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Gestão e Exclusão de Comprovante
        st.markdown("---")
        st.markdown("##### 🔍 Detalhes e Gerenciamento de Registro")
        c_sel, c_del = st.columns([3, 1])
        with c_sel:
            nota_ids = df_notas["id"].tolist()
            id_selecionado = st.selectbox("Selecione um ID para ver itens detalhados:", nota_ids)
        
        with c_del:
            st.write("")
            st.write("")
            if st.button("🗑️ Excluir Registro", type="secondary"):
                if excluir_nota(id_selecionado):
                    st.success(f"Registro #{id_selecionado} excluído.")
                    st.rerun()

        if id_selecionado:
            nota_info = obter_nota_completa(id_selecionado)
            if nota_info and nota_info.get("itens"):
                st.markdown(f"**Itens da Nota #{id_selecionado} ({nota_info['razao_social']}):**")
                st.dataframe(pd.DataFrame(nota_info["itens"])[["descricao", "quantidade", "valor_unitario", "valor_total"]], use_container_width=True)


# --- ABA 3: EXPORTAÇÃO DE PLANILHAS ---
with tab_exportar:
    st.subheader("Exportação de Dados para Contabilidade e Gestão")
    st.write(
        "Gere relatórios formatados prontos para importar no seu software financeiro, ERP contábil ou Microsoft Excel."
    )

    df_notas_exp, _ = obter_dataframes()

    if df_notas_exp.empty:
        st.warning("Não há dados cadastrados para exportação no momento.")
    else:
        col_ex1, col_ex2 = st.columns(2)

        with col_ex1:
            st.markdown("#### 📗 Planilha Microsoft Excel (.xlsx)")
            st.write(
                "Exporta pasta de trabalho completa contendo 3 abas estruturadas:\n"
                "- **Notas e Recibos**: Visão consolidada com status de conciliação e dados do emissor.\n"
                "- **Itens Detalhados**: Linha a linha com todos os produtos adquiridos.\n"
                "- **Gastos por Categoria**: Totais acumulados para controle de centro de custo."
            )
            excel_bytes, _ = gerar_relatorio_excel()
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=excel_bytes,
                file_name="relatorio_conciliacao_fiscal.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )

        with col_ex2:
            st.markdown("#### 📄 Arquivo CSV Separado por Ponto e Vírgula")
            st.write(
                "Exporta arquivo CSV com codificação UTF-8 com BOM, compatível diretamente com o Excel brasileiro e softwares de ERP contábil."
            )
            csv_dados = gerar_relatorio_csv(separador=";")
            st.download_button(
                label="📥 Baixar Arquivo CSV (.csv)",
                data=csv_dados,
                file_name="extracao_notas_fiscais.csv",
                mime="text/csv",
                use_container_width=True
            )
