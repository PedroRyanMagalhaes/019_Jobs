"""
Busca vagas tech do banco vagas_filtradas.db
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join('src', 'database', 'vagas_filtradas.db')

def buscar_vagas_recentes(dias=1):
    """
    Busca vagas tech dos últimos N dias
    
    Args:
        dias: Número de dias para buscar (padrão: 1 = hoje)
    
    Returns:
        Lista de dicionários com dados das vagas
    """
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco não encontrado: {DB_PATH}")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Buscar vagas tech dos últimos N dias
    query = """
    SELECT titulo, empresa, localizacao, url_vaga, data_coleta, classificacao_funil
    FROM vagas_filtradas 
    WHERE classificacao_funil IN ('tech funil', 'tech IA')
    AND date(data_coleta) >= date('now', '-' || ? || ' days')
    ORDER BY data_coleta DESC
    LIMIT 50
    """
    
    try:
        cursor.execute(query, (dias,))
        vagas = cursor.fetchall()
        conn.close()
        
        return [{
            'titulo': v[0],
            'empresa': v[1],
            'localizacao': v[2] if v[2] else 'Não especificado',
            'link': v[3],
            'data': v[4],
            'origem': v[5]
        } for v in vagas]
    
    except sqlite3.OperationalError as e:
        print(f"❌ Erro ao buscar vagas: {e}")
        conn.close()
        return []

def buscar_vagas_ativas():
    """
    Busca todas as vagas tech ativas (exceto as de hoje)
    
    Returns:
        Lista de dicionários com dados das vagas ativas
    """
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco não encontrado: {DB_PATH}")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Buscar vagas tech que NÃO são de hoje (vagas ativas antigas)
    query = """
    SELECT titulo, empresa, localizacao, url_vaga, data_coleta, classificacao_funil
    FROM vagas_filtradas 
    WHERE classificacao_funil IN ('tech funil', 'tech IA')
    AND date(data_coleta) < date('now')
    ORDER BY data_coleta DESC
    """
    
    try:
        cursor.execute(query)
        vagas = cursor.fetchall()
        conn.close()
        
        return [{
            'titulo': v[0],
            'empresa': v[1],
            'localizacao': v[2] if v[2] else 'Não especificado',
            'link': v[3],
            'data': v[4],
            'origem': v[5]
        } for v in vagas]
    
    except sqlite3.OperationalError as e:
        print(f"❌ Erro ao buscar vagas ativas: {e}")
        conn.close()
        return []

def contar_vagas_por_origem():
    """Conta quantas vagas vieram do filtro vs IA"""
    if not os.path.exists(DB_PATH):
        return {}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT classificacao_funil, COUNT(*) 
    FROM vagas_filtradas 
    WHERE date(data_coleta) = date('now')
    GROUP BY classificacao_funil
    """)
    
    resultados = cursor.fetchall()
    conn.close()
    
    stats = {r[0]: r[1] for r in resultados}
    return stats

if __name__ == '__main__':
    # Testar busca
    print("🔍 Buscando vagas recentes...\n")
    
    vagas = buscar_vagas_recentes(dias=1)
    print(f"📊 {len(vagas)} vagas encontradas\n")
    
    for i, vaga in enumerate(vagas[:5], 1):
        print(f"{i}. {vaga['titulo']}")
        print(f"   {vaga['empresa']} | {vaga['localizacao']}")
        print(f"   Origem: {vaga['origem']}\n")
    
    # Estatísticas
    stats = contar_vagas_por_origem()
    print("\n📈 Estatísticas de hoje:")
    for origem, count in stats.items():
        print(f"   {origem}: {count} vagas")
