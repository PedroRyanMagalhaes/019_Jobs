"""
Cria o banco de dados para gerenciar assinantes da newsletter
"""
import sqlite3
import os

def criar_banco_usuarios():
    """Cria banco de dados para gerenciar assinantes"""
    db_path = os.path.join('src', 'database', 'usuarios_newsletter.db')
    
    # Criar pasta database se não existir
    os.makedirs(os.path.join('src', 'database'), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assinantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nome TEXT,
        data_inscricao DATETIME DEFAULT CURRENT_TIMESTAMP,
        ativo BOOLEAN DEFAULT 1,
        token_cancelamento TEXT UNIQUE
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Banco de usuários criado em: {db_path}")

if __name__ == '__main__':
    criar_banco_usuarios()
