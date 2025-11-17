import sqlite3
from datetime import date, datetime
import os
from config.settings import DATABASE_CONFIG

DB_FILE = DATABASE_CONFIG["db_file"]
REMOVED_DB_FILE = "src/database/removidas.db"

# Criar diretório data se não existir
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
os.makedirs(os.path.dirname(REMOVED_DB_FILE), exist_ok=True)

def inicializar_banco():
    # Inicializar banco principal
    _inicializar_banco_vagas()
    # Verificar e migrar se necessário
    _migrar_banco_se_necessario()
    # Inicializar banco de removidas
    _inicializar_banco_removidas()

def _migrar_banco_se_necessario():
    """Adiciona a coluna ultima_atualizacao se ela não existir"""
    conexao = None
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(vagas)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'ultima_atualizacao' not in colunas:
            print("🔄 Migração necessária: adicionando coluna ultima_atualizacao...")
            
            # Adicionar a nova coluna com a data atual para registros existentes
            cursor.execute("""
            ALTER TABLE vagas 
            ADD COLUMN ultima_atualizacao TEXT DEFAULT ''
            """)
            
            # Atualizar registros existentes com a data atual
            data_atual = datetime.now().isoformat()
            cursor.execute("""
            UPDATE vagas 
            SET ultima_atualizacao = ? 
            WHERE ultima_atualizacao = '' OR ultima_atualizacao IS NULL
            """, (data_atual,))
            
            conexao.commit()
            print("✅ Migração concluída!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro na migração do banco: {e}")
    finally:
        if conexao:
            conexao.close()

def _inicializar_banco_vagas():
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
            data_coleta TEXT NOT NULL,
            ultima_atualizacao TEXT NOT NULL
        );
        """)
        conexao.commit()

    except sqlite3.Error as e:
        print(f"❌ Erro ao inicializar o banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()
            print("Conexão com o banco de dados fechada.")

def _inicializar_banco_removidas():
    conexao = None
    try:
        conexao = sqlite3.connect(REMOVED_DB_FILE)
        cursor = conexao.cursor()

        print(f"Conectado ao banco de dados removidas '{REMOVED_DB_FILE}'.")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas_removidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            titulo TEXT NOT NULL,
            localizacao TEXT,
            modelo_trabalho TEXT,
            url_vaga TEXT NOT NULL,
            classificacao_ia TEXT,
            data_coleta TEXT NOT NULL,
            data_remocao TEXT NOT NULL,
            motivo_remocao TEXT DEFAULT 'Não encontrada no último scraping'
        );
        """)
        conexao.commit()

    except sqlite3.Error as e:
        print(f"❌ Erro ao inicializar o banco de removidas: {e}")
    finally:
        if conexao:
            conexao.close()
            print("Conexão com o banco de removidas fechada.")

def salvar_vaga(dados_vaga):
    conexao = None
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()

        dados_vaga['data_coleta'] = date.today().isoformat()
        dados_vaga['ultima_atualizacao'] = datetime.now().isoformat()
        
        # Query de inserção ATUALIZADA
        cursor.execute("""
        INSERT INTO vagas (empresa, titulo, localizacao, modelo_trabalho, url_vaga, data_coleta, ultima_atualizacao)
        VALUES (:empresa, :titulo, :localizacao, :modelo_trabalho, :url_vaga, :data_coleta, :ultima_atualizacao)
        """, dados_vaga)
        
        conexao.commit()
        print(f"✅ Vaga nova salva: '{dados_vaga['titulo']}' ({dados_vaga.get('modelo_trabalho', 'N/A')})")
        return True

    except sqlite3.IntegrityError:
        # Vaga já existe, atualizar ultima_atualizacao
        try:
            cursor.execute("""
            UPDATE vagas 
            SET ultima_atualizacao = ? 
            WHERE url_vaga = ?
            """, (datetime.now().isoformat(), dados_vaga['url_vaga']))
            conexao.commit()
            return False  # Não é uma vaga nova
        except sqlite3.Error as e:
            print(f"❌ Erro ao atualizar vaga existente: {e}")
            return False
    except sqlite3.Error as e:
        print(f"❌ Erro ao salvar vaga no banco: {e}")
        return False
    finally:
        if conexao:
            conexao.close()

def iniciar_ciclo_scraping():
    """
    Marca o início de um novo ciclo de scraping.
    Deve ser chamada antes de começar a fazer scraping de todas as empresas.
    """
    print("🔄 Iniciando novo ciclo de scraping...")

def finalizar_ciclo_scraping():
    """
    Finaliza o ciclo de scraping e move vagas não encontradas para o banco de removidas.
    Deve ser chamada após terminar o scraping de todas as empresas.
    """
    print("🧹 Finalizando ciclo de scraping e limpando vagas antigas...")
    
    # Pegar data atual para comparação
    data_hoje = datetime.now().date().isoformat()
    
    # Buscar vagas que não foram atualizadas hoje
    vagas_para_remover = _buscar_vagas_nao_atualizadas(data_hoje)
    
    if vagas_para_remover:
        print(f"📦 Encontradas {len(vagas_para_remover)} vagas para mover para removidas...")
        
        # Mover para banco de removidas
        for vaga in vagas_para_remover:
            _mover_vaga_para_removidas(vaga)
            
        # Remover do banco principal
        _remover_vagas_antigas(data_hoje)
        
        print(f"✅ {len(vagas_para_remover)} vagas movidas para banco de removidas")
    else:
        print("✅ Nenhuma vaga antiga encontrada")

def _buscar_vagas_nao_atualizadas(data_hoje):
    """Busca vagas que não foram atualizadas hoje"""
    conexao = None
    vagas = []
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()
        
        cursor.execute("""
        SELECT id, empresa, titulo, localizacao, modelo_trabalho, url_vaga, 
               classificacao_ia, data_coleta, ultima_atualizacao
        FROM vagas 
        WHERE DATE(ultima_atualizacao) < ?
        """, (data_hoje,))
        
        vagas = cursor.fetchall()
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao buscar vagas não atualizadas: {e}")
    finally:
        if conexao:
            conexao.close()
    
    return vagas

def _mover_vaga_para_removidas(vaga):
    """Move uma vaga para o banco de removidas"""
    conexao = None
    try:
        conexao = sqlite3.connect(REMOVED_DB_FILE)
        cursor = conexao.cursor()
        
        # Dados da vaga: (id, empresa, titulo, localizacao, modelo_trabalho, url_vaga, classificacao_ia, data_coleta, ultima_atualizacao)
        cursor.execute("""
        INSERT INTO vagas_removidas 
        (empresa, titulo, localizacao, modelo_trabalho, url_vaga, classificacao_ia, 
         data_coleta, data_remocao, motivo_remocao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vaga[1],  # empresa
            vaga[2],  # titulo
            vaga[3],  # localizacao
            vaga[4],  # modelo_trabalho
            vaga[5],  # url_vaga
            vaga[6],  # classificacao_ia
            vaga[7],  # data_coleta
            datetime.now().isoformat(),  # data_remocao
            'Não encontrada no último scraping'  # motivo_remocao
        ))
        
        conexao.commit()
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao mover vaga para removidas: {e}")
    finally:
        if conexao:
            conexao.close()

def _remover_vagas_antigas(data_hoje):
    """Remove vagas antigas do banco principal"""
    conexao = None
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()
        
        cursor.execute("""
        DELETE FROM vagas 
        WHERE DATE(ultima_atualizacao) < ?
        """, (data_hoje,))
        
        conexao.commit()
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao remover vagas antigas: {e}")
    finally:
        if conexao:
            conexao.close()

def contar_vagas():
    """Conta o número total de vagas ativas"""
    conexao = None
    try:
        conexao = sqlite3.connect(DB_FILE)
        cursor = conexao.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM vagas")
        count = cursor.fetchone()[0]
        return count
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao contar vagas: {e}")
        return 0
    finally:
        if conexao:
            conexao.close()

def contar_vagas_removidas():
    """Conta o número total de vagas removidas"""
    conexao = None
    try:
        conexao = sqlite3.connect(REMOVED_DB_FILE)
        cursor = conexao.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM vagas_removidas")
        count = cursor.fetchone()[0]
        return count
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao contar vagas removidas: {e}")
        return 0
    finally:
        if conexao:
            conexao.close()