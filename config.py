"""
Módulo de Configuração da Aplicação
Assistente de Extração e Conciliação de Notas Fiscais e Recibos
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env se existir
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

EXPORTS_DIR = DATA_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "notas_fiscais.db"

# Chave da API do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Modelo padrão do Gemini para Visão Multimodal
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Categorias predefinidas para classificação automática
CATEGORIAS_DESPESA = [
    "Alimentação & Refeição",
    "Transporte & Combustível",
    "Material de Escritório & Suprimentos",
    "Tecnologia, Software & Hospedagem",
    "Serviços Profissionais & Terceirizados",
    "Manutenção & Obras",
    "Viagens & Estadias",
    "Impostos & Taxas",
    "Educação & Treinamento",
    "Outros / Diversos",
]
