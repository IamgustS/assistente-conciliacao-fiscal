"""
Script Gerador de Comprovantes e Recibos Sintéticos para Demonstração e Testes
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

EXEMPLOS_DIR = Path(__file__).resolve().parent / "exemplos"
EXEMPLOS_DIR.mkdir(exist_ok=True)


def gerar_recibo_posto_imagem():
    """Gera uma imagem realista estilo cupom fiscal de papel térmico (Posto de Gasolina)."""
    largura = 500
    altura = 750
    imagem = Image.new("RGB", (largura, altura), color=(248, 248, 245))
    draw = ImageDraw.Draw(imagem)

    # Tenta usar fonte padrão
    font_path = None
    # No Windows, arial.ttf ou cour.ttf (Courier/monospaced)
    font_mono = None
    font_bold = None
    try:
        font_mono = ImageFont.truetype("cour.ttf", 15)
        font_bold = ImageFont.truetype("courbd.ttf", 16)
        font_header = ImageFont.truetype("courbd.ttf", 18)
    except Exception:
        font_mono = ImageFont.load_default()
        font_bold = font_mono
        font_header = font_mono

    # Linhas do cupom térmico
    y = 25
    linhas_cabecalho = [
        ("POSTO E CONVENIENCIA ESTRELA LTDA", font_header, True),
        ("AUTO POSTO ESTRELA SHELL", font_bold, True),
        ("CNPJ: 11.222.333/0001-81 - IE: 110.042.490.114", font_mono, True),
        ("AV. PAULISTA, 1000 - BELA VISTA - SAO PAULO/SP", font_mono, True),
        ("--------------------------------------------------", font_mono, True),
        ("NFC-e - NOTA FISCAL DE CONSUMIDOR ELETRÔNICA", font_bold, True),
        ("Nº 000.142.980  SERIE: 001  EMISSAO: 18/05/2026 14:32:10", font_mono, False),
        ("--------------------------------------------------", font_mono, True),
        ("ITEM  DESCRIÇÃO             QTD   UN   V.UNIT   TOTAL", font_bold, False),
        ("001   GASOLINA ADITIVADA   30,00  L     5,89   176,70", font_mono, False),
        ("002   CAFE EXPRESSO DUPLO   1,00  UN    8,50     8,50", font_mono, False),
        ("003   AGUA MINERAL S/ GAS   2,00  UN    4,00     8,00", font_mono, False),
        ("004   PÃO DE QUEIJO TRAD    2,00  UN    6,00    12,00", font_mono, False),
        ("--------------------------------------------------", font_mono, True),
        ("SUBTOTAL DOS ITENS:                    R$  205,20", font_mono, False),
        ("DESCONTO PROMOCIONAL:                 -R$    5,20", font_mono, False),
        ("ACRÉSCIMOS / TAXAS:                    R$    0,00", font_mono, False),
        ("VALOR TOTAL A PAGAR:                   R$  200,00", font_bold, False),
        ("--------------------------------------------------", font_mono, True),
        ("FORMA DE PAGAMENTO:               CARTÃO DE CRÉDITO", font_mono, False),
        ("Tributos Totais Incidentes (Lei 12.741/12): R$ 42,30", font_mono, False),
        ("--------------------------------------------------", font_mono, True),
        ("Chave de Acesso:", font_mono, True),
        ("3526 0511 2223 3300 0181 6500 1000 1429 8012 3456 7890", font_mono, True),
        ("CONSULTE PELA CHAVE DE ACESSO EM:", font_mono, True),
        ("https://www.nfce.fazenda.sp.gov.br", font_mono, True),
        ("OBRIGADO PELA PREFERENCIA E VOLTE SEMPRE!", font_mono, True),
    ]

    for texto, f, centralizar in linhas_cabecalho:
        if centralizar:
            bbox = draw.textbbox((0, 0), texto, font=f)
            w = bbox[2] - bbox[0]
            x = (largura - w) / 2
        else:
            x = 25
        draw.text((x, y), texto, fill=(30, 30, 30), font=f)
        y += 24

    caminho = EXEMPLOS_DIR / "recibo_posto_conciliado.png"
    imagem.save(caminho)
    return caminho


def gerar_recibo_restaurante_divergente():
    """Gera um recibo onde a soma dos itens apresenta divergência proposital com o total pago."""
    largura = 500
    altura = 720
    imagem = Image.new("RGB", (largura, altura), color=(253, 251, 245))
    draw = ImageDraw.Draw(imagem)

    try:
        font_mono = ImageFont.truetype("cour.ttf", 15)
        font_bold = ImageFont.truetype("courbd.ttf", 16)
        font_header = ImageFont.truetype("courbd.ttf", 18)
    except Exception:
        font_mono = ImageFont.load_default()
        font_bold = font_mono
        font_header = font_mono

    y = 25
    linhas = [
        ("CANTINA & BISTRÔ DO CHEF LTDA", font_header, True),
        ("RESTAURANTE E PIZZARIA SABORES", font_bold, True),
        ("CNPJ: 04.123.456/0001-99", font_mono, True),
        ("RUA DOS PINHEIROS, 450 - SAO PAULO/SP", font_mono, True),
        ("--------------------------------------------------", font_mono, True),
        ("CUPOM NÃO FISCAL / CONFERÊNCIA DE MESA", font_bold, True),
        ("MESA: 14  COMANDA: 894  DATA: 20/05/2026 21:15", font_mono, False),
        ("--------------------------------------------------", font_mono, True),
        ("ITEM  DESCRIÇÃO             QTD   UN   V.UNIT   TOTAL", font_bold, False),
        ("001   RISOTO DE CAMARAO     1,00  UN   89,00    89,00", font_mono, False),
        ("002   FILE MIGNON GRELHADO  1,00  UN   95,00    95,00", font_mono, False),
        ("003   SUCO NATURAL LARANJA  2,00  UN   12,00    24,00", font_mono, False),
        ("004   SOBREMESA PETIT GATE  1,00  UN   28,00    28,00", font_mono, False),
        ("--------------------------------------------------", font_mono, True),
        ("SOMA DOS ITENS:                        R$  236,00", font_mono, False),
        ("TAXA DE SERVICO 10%:                   R$   23,60", font_mono, False),
        ("DESCONTO CORTESIA:                    -R$   10,00", font_mono, False),
        # Nota: 236 + 23.60 - 10 = 249.60, mas o total cobrado foi R$ 265,00 (divergência de R$ 15,40!)
        ("VALOR TOTAL FINAL COBRADO:             R$  265,00", font_bold, False),
        ("--------------------------------------------------", font_mono, True),
        ("FORMA DE PAGAMENTO:                         PIX", font_mono, False),
        ("DIVERGÊNCIA PROPOSITAL DE R$ 15,40 PARA TESTES!", font_bold, True),
    ]

    for texto, f, centralizar in linhas:
        if centralizar:
            bbox = draw.textbbox((0, 0), texto, font=f)
            w = bbox[2] - bbox[0]
            x = (largura - w) / 2
        else:
            x = 25
        draw.text((x, y), texto, fill=(20, 20, 20), font=f)
        y += 24

    caminho = EXEMPLOS_DIR / "recibo_restaurante_divergente.png"
    imagem.save(caminho)
    return caminho


def gerar_danfe_pdf():
    """Gera uma DANFE em PDF de materiais de escritório e tecnologia."""
    caminho = EXEMPLOS_DIR / "danfe_papelaria_tech.pdf"
    c = canvas.Canvas(str(caminho), pagesize=letter)
    
    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 740, "PAPELARIA E TECNOLOGIA GLOBAL S.A.")
    c.setFont("Helvetica", 10)
    c.drawString(50, 725, "CNPJ: 07.526.557/0001-00  -  Inscrição Estadual: 114.887.320.110")
    c.drawString(50, 712, "Rua da Quitanda, 120 - Centro - Rio de Janeiro / RJ - CEP 20011-030")
    
    c.setLineWidth(1)
    c.line(50, 700, 560, 700)

    # Identificação da Nota
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 680, "DANFE - DOCUMENTO AUXILIAR DA NOTA FISCAL ELETRÔNICA")
    c.setFont("Helvetica", 10)
    c.drawString(50, 665, "Número: 000.089.412   Série: 001   Data de Emissão: 22/05/2026")
    c.drawString(50, 650, "Chave de Acesso: 3326 0507 5265 5700 0100 5500 1000 0894 1210 9876 5432")

    c.line(50, 640, 560, 640)

    # Tabela de Itens
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 620, "Cód.")
    c.drawString(90, 620, "Descrição do Produto")
    c.drawString(330, 620, "Qtd")
    c.drawString(390, 620, "V. Unit (R$)")
    c.drawString(480, 620, "V. Total (R$)")
    c.line(50, 615, 560, 615)

    itens = [
        ("01", "Resma de Papel Sulfite A4 75g (500 folhas)", "10", "28,50", "285,00"),
        ("02", "Kit Canetas Esferográficas Ponta Fina (50 un)", "2", "45,00", "90,00"),
        ("03", "Cartucho de Toner Laser Preto HP CF283A", "3", "120,00", "360,00"),
        ("04", "Teclado e Mouse Sem Fio USB Logitech", "4", "150,00", "600,00"),
        ("05", "Cabo de Rede Patch Cord RJ45 Cat6 5m", "6", "15,00", "90,00"),
    ]

    c.setFont("Helvetica", 9)
    y = 598
    for cod, desc, qtd, unit, total in itens:
        c.drawString(50, y, cod)
        c.drawString(90, y, desc)
        c.drawString(330, y, qtd)
        c.drawString(390, y, unit)
        c.drawString(480, y, total)
        y -= 20

    c.line(50, y + 8, 560, y + 8)

    # Totais
    # 285 + 90 + 360 + 600 + 90 = 1425.00
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(350, y, "Total dos Produtos:")
    c.drawRightString(550, y, "R$ 1.425,00")
    
    y -= 18
    c.drawString(350, y, "Frete / Entrega Expressa:")
    c.drawRightString(550, y, "R$ 45,00")

    y -= 18
    c.drawString(350, y, "Desconto Comercial:")
    c.drawRightString(550, y, "-R$ 70,00")

    y -= 22
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y, "VALOR TOTAL DA NOTA:")
    # 1425 + 45 - 70 = 1400.00
    c.drawRightString(550, y, "R$ 1.400,00")

    y -= 30
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Forma de Pagamento: Boleto Bancário 30 Dias")
    c.drawString(50, y - 15, "ICMS Total Estimado: R$ 252,00 (18%) | ISS: R$ 0,00")

    c.save()
    return caminho


if __name__ == "__main__":
    print("Gerando arquivos de exemplo...")
    p1 = gerar_recibo_posto_imagem()
    p2 = gerar_recibo_restaurante_divergente()
    p3 = gerar_danfe_pdf()
    print(f"Gerado: {p1}")
    print(f"Gerado: {p2}")
    print(f"Gerado: {p3}")
