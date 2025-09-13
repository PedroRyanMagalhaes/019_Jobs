import sqlite3
from datetime import date

DB_FILE = "vagas.db"

def inicializar_banco():
    conexao = None
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()

        print(f"Conectado ao banco de dados '{DB_FILE}'.")

        # Comando SQL ATUALIZADO para incluir o novo campo
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            titulo TEXT NOT NULL,
            localizacao TEXT,
            modelo_trabalho TEXT,
            url_vaga TEXT NOT NULL UNIQUE,
            classificacao_ia TEXT,
            data_coleta TEXT NOT NULL
        );
        """)
        conexao.commit()

    except sqlite3.Error as e:
        print(f"❌ Erro ao inicializar o banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()
            print("Conexão com o banco de dados fechada.")

def salvar_vaga(dados_vaga):
    conexao = None
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()

        dados_vaga['data_coleta'] = date.today().isoformat()
        
        # Query de inserção ATUALIZADA
        cursor.execute("""
        INSERT INTO vagas (empresa, titulo, localizacao, modelo_trabalho, url_vaga, data_coleta)
        VALUES (:empresa, :titulo, :localizacao, :modelo_trabalho, :url_vaga, :data_coleta)
        """, dados_vaga)
        
        conexao.commit()
        print(f"✅ Vaga nova salva: '{dados_vaga['titulo']}' ({dados_vaga.get('modelo_trabalho', 'N/A')})")
        return True

    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"❌ Erro ao salvar vaga no banco: {e}")
        return False
    finally:
        if conexao:
            conexao.close()