import sqlite3
from datetime import date

# Define o nome do arquivo do banco de dados como uma constante.
# Isso facilita a alteração do nome em um único lugar, se necessário.
DB_FILE = "vagas.db"

def inicializar_banco():
    """
    Cria o banco de dados e a tabela 'vagas' se eles ainda não existirem.
    """
    conexao = None # Inicializa a variável de conexão
    try:
        # sqlite3.connect() cria o arquivo .db se ele não existir.
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()

        print(f"Conectado ao banco de dados '{DB_FILE}'.")

        # O comando SQL para criar a tabela.
        # 'IF NOT EXISTS' previne erros se a tabela já foi criada.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            titulo TEXT NOT NULL,
            localizacao TEXT,
            url_vaga TEXT NOT NULL UNIQUE, -- A CHAVE DO NOSSO SISTEMA!
            classificacao_ia TEXT,
            data_coleta TEXT NOT NULL
        );
        """)
        # A restrição 'UNIQUE' na coluna 'url_vaga' é crucial.
        # Ela impede que a mesma URL seja inserida mais de uma vez,
        # evitando vagas duplicadas no nosso banco de dados.

        print("Tabela 'vagas' verificada/criada com sucesso.")
        conexao.commit() # Salva as alterações no banco de dados.

    except sqlite3.Error as e:
        print(f"❌ Erro ao inicializar o banco de dados: {e}")
    finally:
        # O bloco 'finally' garante que a conexão seja fechada,
        # mesmo que ocorra um erro no bloco 'try'.
        if conexao:
            conexao.close()
            print("Conexão com o banco de dados fechada.")

def salvar_vaga(dados_vaga):
    """
    Salva uma única vaga no banco de dados.
    Retorna True se a vaga foi inserida com sucesso, False caso contrário.
    
    Args:
        dados_vaga (dict): Um dicionário contendo os dados da vaga.
                           Ex: {'empresa': 'CI&T', 'titulo': '...', 'url_vaga': '...'}
    """
    conexao = None
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()

        # Adiciona a data da coleta aos dados antes de salvar.
        dados_vaga['data_coleta'] = date.today().isoformat()
        
        # Este é um 'INSERT' parametrizado.
        # Usar '?' ou ':nome' em vez de formatar a string diretamente
        # previne um tipo de ataque chamado SQL Injection. É uma boa prática de segurança.
        cursor.execute("""
        INSERT INTO vagas (empresa, titulo, localizacao, url_vaga, data_coleta)
        VALUES (:empresa, :titulo, :localizacao, :url_vaga, :data_coleta)
        """, dados_vaga)
        
        conexao.commit()
        print(f"✅ Vaga nova salva: '{dados_vaga['titulo']}'")
        return True

    except sqlite3.IntegrityError:
        # Este erro acontece especificamente quando a restrição UNIQUE falha,
        # ou seja, quando tentamos inserir uma 'url_vaga' que já existe.
        # Para nós, isso não é um erro, e sim um comportamento esperado.
        # Apenas informamos que a vaga já existe e seguimos em frente.
        print(f"☑️ Vaga já existe no banco: '{dados_vaga['titulo']}'")
        return False
    except sqlite3.Error as e:
        print(f"❌ Erro ao salvar vaga no banco: {e}")
        return False
    finally:
        if conexao:
            conexao.close()
