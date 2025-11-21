"""
Funções para gerenciar assinantes da newsletter
"""
import sqlite3
import uuid
import os

DB_PATH = os.path.join('src', 'database', 'usuarios_newsletter.db')

def adicionar_assinante(email, nome='', ativo=True):
    """Adiciona um novo assinante"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    token = str(uuid.uuid4())
    
    try:
        cursor.execute('''
        INSERT INTO assinantes (email, nome, token_cancelamento, ativo) 
        VALUES (?, ?, ?, ?)
        ''', (email, nome, token, 1 if ativo else 0))
        conn.commit()
        status = "✅ ATIVO" if ativo else "❌ INATIVO"
        print(f"✅ {email} adicionado como {status}!")
        return True
    except sqlite3.IntegrityError:
        print(f"⚠️ {email} já está cadastrado")
        return False
    finally:
        conn.close()

def remover_assinante(email=None, token=None):
    """Remove assinante por email ou token"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if token:
        cursor.execute('UPDATE assinantes SET ativo = 0 WHERE token_cancelamento = ?', (token,))
    elif email:
        cursor.execute('UPDATE assinantes SET ativo = 0 WHERE email = ?', (email,))
    else:
        print("❌ Forneça email ou token")
        return False
    
    conn.commit()
    conn.close()
    print(f"✅ Assinante removido com sucesso!")
    return True

def listar_assinantes(apenas_ativos=True):
    """Lista todos os assinantes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if apenas_ativos:
        cursor.execute('SELECT id, email, nome, data_inscricao FROM assinantes WHERE ativo = 1')
    else:
        cursor.execute('SELECT id, email, nome, data_inscricao, ativo FROM assinantes')
    
    assinantes = cursor.fetchall()
    conn.close()
    
    print(f"\n📧 Total de assinantes: {len(assinantes)}\n")
    for a in assinantes:
        if apenas_ativos:
            print(f"ID: {a[0]} | Email: {a[1]} | Nome: {a[2]} | Data: {a[3]}")
        else:
            status = "✅ Ativo" if a[4] else "❌ Inativo"
            print(f"ID: {a[0]} | Email: {a[1]} | Nome: {a[2]} | Data: {a[3]} | {status}")
    
    return assinantes

def buscar_assinantes_ativos():
    """Retorna lista de assinantes ativos para envio"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT email, nome, token_cancelamento 
    FROM assinantes 
    WHERE ativo = 1
    ''')
    
    assinantes = cursor.fetchall()
    conn.close()
    
    return [{
        'email': a[0],
        'nome': a[1],
        'token': a[2]
    } for a in assinantes]

if __name__ == '__main__':
    # Exemplo de uso
    print("=== Gerenciamento de Assinantes ===\n")
    
    # Adicionar você mesmo como primeiro assinante
    adicionar_assinante('seu_email@exemplo.com', 'Seu Nome')
    
    # Listar todos
    listar_assinantes()
