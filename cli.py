"""
Módulo CLI - Interface de Linha de Comando para Processamento em Lote
"""

import sys
import io

# Garante suporte a UTF-8 no Windows Console sem erros de codificação
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from extractor import extrair_dados_documento
from conciliator import conciliar_nota, formatar_documento
from database import salvar_nota, listar_notas
from exporter import gerar_relatorio_excel, gerar_relatorio_csv

console = Console(safe_box=True)


def processar_arquivo(caminho_arquivo: Path, salvar_banco: bool = True):
    """Processa um comprovante individual e imprime o diagnóstico na tela."""
    console.print(f"\n[cyan]Processando arquivo:[/cyan] [bold]{caminho_arquivo.name}[/bold]")
    
    nota, is_mock, msg_extracao = extrair_dados_documento(caminho_arquivo, caminho_arquivo.name)
    if is_mock:
        console.print(f"[yellow]{msg_extracao}[/yellow]")

    conciliacao = conciliar_nota(nota)

    # Tabela com resumo da nota
    tab_resumo = Table(title=f"Nota Fiscal: {nota.razao_social}", show_header=True)
    tab_resumo.add_column("Campo", style="dim")
    tab_resumo.add_column("Valor Extraído", style="bold")

    tab_resumo.add_row("Razão Social", nota.razao_social)
    tab_resumo.add_row("CNPJ / CPF", formatar_documento(nota.cnpj_cpf))
    tab_resumo.add_row("Data / Hora", f"{nota.data_emissao or ''} {nota.hora_emissao or ''}")
    tab_resumo.add_row("Tipo Documento", nota.tipo_documento)
    tab_resumo.add_row("Categoria", nota.categoria_sugerida)
    tab_resumo.add_row("Forma Pagamento", nota.forma_pagamento or "Não identificada")
    tab_resumo.add_row("Subtotal Itens", f"R$ {nota.subtotal_itens:.2f}")
    tab_resumo.add_row("Descontos", f"R$ {nota.desconto:.2f}")
    tab_resumo.add_row("Taxas/Acréscimos", f"R$ {nota.acrescimo_taxas:.2f}")
    tab_resumo.add_row("Valor Total Pago", f"R$ {nota.valor_total:.2f}")
    console.print(tab_resumo)

    # Tabela com os Itens
    if nota.itens:
        tab_itens = Table(title="Itens Detalhados", show_header=True)
        tab_itens.add_column("Item", justify="center")
        tab_itens.add_column("Descrição")
        tab_itens.add_column("Qtd", justify="right")
        tab_itens.add_column("V. Unit", justify="right")
        tab_itens.add_column("Total Item", justify="right", style="green")

        for idx, it in enumerate(nota.itens, 1):
            tab_itens.add_row(
                str(idx),
                it.descricao,
                f"{it.quantidade:.2f}",
                f"R$ {it.valor_unitario:.2f}",
                f"R$ {it.valor_total:.2f}"
            )
        console.print(tab_itens)

    # Painel de Conciliação
    cor_status = "green" if conciliacao.status.value == "CONCILIADO" else "red"
    painel_texto = (
        f"[bold {cor_status}]STATUS DA CONCILIAÇÃO: {conciliacao.status.value}[/bold {cor_status}]\n"
        f"• {conciliacao.resumo_status}\n"
        f"• Validação CNPJ: {conciliacao.mensagem_cnpj}\n"
    )
    if conciliacao.detalhes_divergencia:
        painel_texto += "\n[bold]Observações / Auditoria:[/bold]\n"
        for det in conciliacao.detalhes_divergencia:
            painel_texto += f"  - {det}\n"

    console.print(Panel(painel_texto, title="Auditoria de Conciliação", border_style=cor_status))

    if salvar_banco:
        id_salvo = salvar_nota(nota, conciliacao, arquivo_origem=caminho_arquivo.name)
        console.print(f"[green] Salvo com sucesso no banco de dados SQLite (ID #{id_salvo}).[/green]")

    return nota, conciliacao


def processar_diretorio(diretorio: Path):
    """Processa todos os arquivos de imagem e PDF de um diretório."""
    extensoes = {".png", ".jpg", ".jpeg", ".pdf", ".webp"}
    arquivos = [f for f in diretorio.iterdir() if f.suffix.lower() in extensoes]

    if not arquivos:
        console.print(f"[yellow]Nenhum comprovante (PNG, JPG, PDF) encontrado em '{diretorio}'.[/yellow]")
        return

    console.print(f"[bold cyan]Encontrados {len(arquivos)} arquivos para processar.[/bold cyan]")
    total_conciliados = 0
    total_divergentes = 0

    for arq in arquivos:
        _, conc = processar_arquivo(arq)
        if conc.status.value == "CONCILIADO":
            total_conciliados += 1
        else:
            total_divergentes += 1

    console.print("\n" + "="*50)
    console.print(f"[bold]Resumo do Lote:[/bold] {len(arquivos)} processados | "
                  f"[green]{total_conciliados} Conciliados[/green] | "
                  f"[red]{total_divergentes} Divergentes[/red]")


def listar_historico():
    """Lista as notas gravadas no banco de dados."""
    notas = listar_notas(limit=20)
    if not notas:
        console.print("[yellow]Nenhuma nota fiscal cadastrada no banco de dados ainda.[/yellow]")
        return

    tab = Table(title="Histórico de Notas e Recibos Cadastrados", show_header=True)
    tab.add_column("ID", justify="center")
    tab.add_column("Data")
    tab.add_column("Emissor")
    tab.add_column("Total (R$)", justify="right")
    tab.add_column("Categoria")
    tab.add_column("Status Conciliação", justify="center")

    for n in notas:
        cor = "green" if n["status_conciliacao"] == "CONCILIADO" else "red"
        status_formatado = f"[{cor}]{n['status_conciliacao']}[/{cor}]"
        tab.add_row(
            str(n["id"]),
            n["data_emissao"] or "N/D",
            n["razao_social"],
            f"R$ {n['valor_total']:.2f}",
            n["categoria"] or "Outros",
            status_formatado
        )
    console.print(tab)


def main():
    parser = argparse.ArgumentParser(description="Assistente de Extração e Conciliação de Notas Fiscais e Recibos")
    subparsers = parser.add_subparsers(dest="comando")

    # Comando 'processar'
    p_proc = subparsers.add_parser("processar", help="Processa um único arquivo de recibo ou nota")
    p_proc.add_argument("arquivo", type=str, help="Caminho do arquivo (imagem ou PDF)")

    # Comando 'lote'
    p_lote = subparsers.add_parser("lote", help="Processa todos os recibos de uma pasta")
    p_lote.add_argument("pasta", type=str, help="Caminho da pasta com os recibos")

    # Comando 'listar'
    subparsers.add_parser("listar", help="Lista as notas registradas no banco de dados")

    # Comando 'exportar'
    p_exp = subparsers.add_parser("exportar", help="Exporta as notas para Excel ou CSV")
    p_exp.add_argument("--formato", choices=["excel", "csv"], default="excel", help="Formato de exportação")
    p_exp.add_argument("--saida", type=str, default="", help="Caminho do arquivo de saída")

    args = parser.parse_args()

    if args.comando == "processar":
        processar_arquivo(Path(args.arquivo))
    elif args.comando == "lote":
        processar_diretorio(Path(args.pasta))
    elif args.comando == "listar":
        listar_historico()
    elif args.comando == "exportar":
        if args.formato == "excel":
            saida = args.saida or "relatorio_notas_conciliadas.xlsx"
            _, path = gerar_relatorio_excel(Path(saida))
            console.print(f"[green] Planilha Excel exportada com sucesso em:[/green] [bold]{path}[/bold]")
        else:
            saida = args.saida or "relatorio_notas_conciliadas.csv"
            csv_content = gerar_relatorio_csv()
            with open(saida, "w", encoding="utf-8-sig") as f:
                f.write(csv_content)
            console.print(f"[green] Arquivo CSV exportado com sucesso em:[/green] [bold]{saida}[/bold]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
