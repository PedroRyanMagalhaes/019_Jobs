import sqlite3
from datetime import date

DB_FILE = "vagas.db"

def inicializar_banco():
    """
    Cria o banco de dados e a tabela 'vagas' se não existirem.
    A coluna 'url_vaga' é definida como UNIQUE para evitar duplicatas.
    """
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()

        print("Conectado ao banco de dados SQLite.")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            titulo TEXT NOT NULL,
            localizacao TEXT,
            url_vaga TEXT NOT NULL UNIQUE,
            classificacao_ia TEXT,
            data_coleta TEXT NOT NULL
        );
        """)

        print(f"Tabela 'vagas' verificada/criada com sucesso no arquivo '{DB_FILE}'.")
        conexao.commit()

    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()
            print("Conexão com o banco de dados fechada.")

def salvar_vaga(dados_vaga):
    """
    Salva uma única vaga no banco de dados.
    Não insere se a URL da vaga já existir, graças à restrição UNIQUE.
    
    Args:
        dados_vaga (dict): Um dicionário contendo os dados da vaga.
                           Ex: {'empresa': 'CI&T', 'titulo': '...', 'url_vaga': '...'}
    """
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()

        # Adiciona a data da coleta aos dados da vaga
        dados_vaga['data_coleta'] = date.today().isoformat()

        cursor.execute("""
        INSERT INTO vagas (empresa, titulo, localizacao, url_vaga, data_coleta)
        VALUES (:empresa, :titulo, :localizacao, :url_vaga, :data_coleta)
        """, dados_vaga)
        
        conexao.commit()
        print(f"✅ Vaga salva: '{dados_vaga['titulo']}'")
        return True

    except sqlite3.IntegrityError:
        # Este erro ocorre quando a restrição UNIQUE (na url_vaga) falha.
        # Isso significa que a vaga já está no banco, o que é o comportamento esperado.
        print(f"☑️ Vaga já existe no banco: '{dados_vaga['titulo']}'")
        return False
    except sqlite3.Error as e:
        print(f"❌ Erro ao salvar vaga: {e}")
        return False
    finally:
        if conexao:
            conexao.close()

