"""
Módulo de Banco de Dados SQLite para Persistência e Auditoria
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from config import DATABASE_PATH
from models import NotaFiscalSchema, ResultadoConciliacao


def get_connection():
    """Retorna uma conexão ativa com o banco SQLite com suporte a Foreign Keys."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Cria as tabelas necessárias se não existirem."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo_origem TEXT,
            razao_social TEXT NOT NULL,
            nome_fantasia TEXT,
            cnpj_cpf TEXT,
            data_emissao TEXT,
            hora_emissao TEXT,
            numero_documento TEXT,
            tipo_documento TEXT,
            subtotal_itens REAL DEFAULT 0.0,
            desconto REAL DEFAULT 0.0,
            acrescimo_taxas REAL DEFAULT 0.0,
            impostos_estimados REAL DEFAULT 0.0,
            valor_total REAL NOT NULL,
            forma_pagamento TEXT,
            categoria TEXT,
            status_conciliacao TEXT,
            diferenca_conciliacao REAL,
            cnpj_valido INTEGER,
            detalhes_conciliacao TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_nota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nota_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            quantidade REAL NOT NULL,
            valor_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            FOREIGN KEY (nota_id) REFERENCES notas(id) ON DELETE CASCADE
        )
        """)
        conn.commit()


def salvar_nota(
    nota: NotaFiscalSchema,
    conciliacao: ResultadoConciliacao,
    arquivo_origem: str = ""
) -> int:
    """
    Insere uma nota fiscal e seus itens no banco de dados.
    Retorna o ID da nota inserida.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cnpj_valido_int = 1 if conciliacao.cnpj_valido is True else (0 if conciliacao.cnpj_valido is False else None)
        detalhes_json = json.dumps(conciliacao.detalhes_divergencia, ensure_ascii=False)

        cursor.execute("""
            INSERT INTO notas (
                arquivo_origem, razao_social, nome_fantasia, cnpj_cpf,
                data_emissao, hora_emissao, numero_documento, tipo_documento,
                subtotal_itens, desconto, acrescimo_taxas, impostos_estimados,
                valor_total, forma_pagamento, categoria, status_conciliacao,
                diferenca_conciliacao, cnpj_valido, detalhes_conciliacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            arquivo_origem,
            nota.razao_social,
            nota.nome_fantasia,
            nota.cnpj_cpf,
            nota.data_emissao,
            nota.hora_emissao,
            nota.numero_documento,
            nota.tipo_documento,
            nota.subtotal_itens,
            nota.desconto,
            nota.acrescimo_taxas,
            nota.impostos_estimados,
            nota.valor_total,
            nota.forma_pagamento,
            nota.categoria_sugerida,
            conciliacao.status.value,
            conciliacao.diferenca,
            cnpj_valido_int,
            detalhes_json
        ))
        
        nota_id = cursor.lastrowid

        for item in nota.itens:
            cursor.execute("""
                INSERT INTO itens_nota (
                    nota_id, descricao, quantidade, valor_unitario, valor_total
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                nota_id,
                item.descricao,
                item.quantidade,
                item.valor_unitario,
                item.valor_total
            ))

        conn.commit()
        return nota_id


def listar_notas(limit: int = 100) -> List[Dict[str, Any]]:
    """Recupera as últimas notas cadastradas em ordem decrescente."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notas ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        return rows


def obter_nota_completa(nota_id: int) -> Optional[Dict[str, Any]]:
    """Recupera os detalhes de uma nota fiscal com todos os seus itens."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notas WHERE id = ?", (nota_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        nota_dict = dict(row)
        cursor.execute("SELECT * FROM itens_nota WHERE nota_id = ? ORDER BY id ASC", (nota_id,))
        nota_dict["itens"] = [dict(r) for r in cursor.fetchall()]
        return nota_dict


def excluir_nota(nota_id: int) -> bool:
    """Exclui uma nota e seus itens (por chave estrangeira em cascata)."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notas WHERE id = ?", (nota_id,))
        conn.commit()
        return cursor.rowcount > 0


def obter_dataframes() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna DataFrames Pandas para análises e exportação."""
    init_db()
    with get_connection() as conn:
        df_notas = pd.read_sql_query("SELECT * FROM notas ORDER BY id DESC", conn)
        df_itens = pd.read_sql_query("""
            SELECT i.*, n.razao_social, n.data_emissao, n.categoria 
            FROM itens_nota i 
            JOIN notas n ON i.nota_id = n.id 
            ORDER BY i.nota_id DESC, i.id ASC
        """, conn)
        return df_notas, df_itens
