import sqlite3
import os
from typing import Dict, Optional
from config.settings import DB_TECH_FILE

def inicializar_banco_tech():
    """Cria tabela para vagas tech classificadas pela IA"""
    try:
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(DB_TECH_FILE), exist_ok=True)
        
        conn = sqlite3.connect(DB_TECH_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vagas_tech (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vaga_origem_id INTEGER NOT NULL,
                empresa TEXT NOT NULL,
                titulo TEXT NOT NULL,
                localizacao TEXT,
                modelo_trabalho TEXT,
                url_vaga TEXT,
                confianca_ia REAL NOT NULL,
                motivo_ia TEXT,
                data_classificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vaga_origem_id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_empresa ON vagas_tech(empresa)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_confianca ON vagas_tech(confianca_ia)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data ON vagas_tech(data_classificacao)
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Banco de vagas tech inicializado: {DB_TECH_FILE}")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco tech: {e}")

def salvar_vaga_tech(vaga_tech: Dict) -> bool:
    """
    Salva vaga classificada como tech pela IA
    Returns: True se salvou, False se já existia ou erro
    """
    try:
        conn = sqlite3.connect(DB_TECH_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO vagas_tech 
            (vaga_origem_id, empresa, titulo, localizacao, modelo_trabalho, 
             url_vaga, confianca_ia, motivo_ia)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            vaga_tech["vaga_origem_id"],
            vaga_tech["empresa"],
            vaga_tech["titulo"],
            vaga_tech.get("localizacao"),
            vaga_tech.get("modelo_trabalho"),
            vaga_tech.get("url_vaga"),
            vaga_tech["confianca_ia"],
            vaga_tech.get("motivo_ia", "")
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
        
    except Exception as e:
        print(f"❌ Erro ao salvar vaga tech: {e}")
        return False

def contar_vagas_tech() -> int:
    """Retorna total de vagas tech no banco"""
    try:
        if not os.path.exists(DB_TECH_FILE):
            return 0
            
        conn = sqlite3.connect(DB_TECH_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vagas_tech")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"Erro ao contar vagas tech: {e}")
        return 0

def listar_vagas_tech_por_empresa() -> Dict[str, int]:
    """Retorna contagem de vagas tech por empresa"""
    try:
        if not os.path.exists(DB_TECH_FILE):
            return {}
            
        conn = sqlite3.connect(DB_TECH_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT empresa, COUNT(*) FROM vagas_tech GROUP BY empresa ORDER BY COUNT(*) DESC")
        resultado = {empresa: count for empresa, count in cursor.fetchall()}
        conn.close()
        return resultado
    except Exception as e:
        print(f"Erro ao listar vagas por empresa: {e}")
        return {}

def obter_vagas_tech_recentes(limit: int = 10) -> list:
    """Retorna as vagas tech mais recentemente classificadas"""
    try:
        if not os.path.exists(DB_TECH_FILE):
            return []
            
        conn = sqlite3.connect(DB_TECH_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT empresa, titulo, confianca_ia, data_classificacao 
            FROM vagas_tech 
            ORDER BY data_classificacao DESC 
            LIMIT ?
        """, (limit,))
        resultado = cursor.fetchall()
        conn.close()
        return resultado
    except Exception as e:
        print(f"Erro ao obter vagas recentes: {e}")
        return []