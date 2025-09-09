import sqlite3
import pandas as pd
import os

# --- CONFIGURAÇÃO ---
DB_FILE = "vagas.db"
CSV_FILE = "vagas_exportadas.csv"
# --------------------

def exportar_para_csv():
    """
    Lê os dados da tabela 'vagas' do banco de dados SQLite e exporta para um arquivo CSV.
    """
    # Verifica se o arquivo de banco de dados existe antes de tentar conectar.
    if not os.path.exists(DB_FILE):
        print(f"❌ Erro: O arquivo de banco de dados '{DB_FILE}' não foi encontrado.")
        print("Certifique-se de executar o app.py primeiro para coletar os dados e criar o banco.")
        return

    try:
        print(f"🔌 Conectando ao banco de dados '{DB_FILE}'...")
        # Cria a conexão com o banco de dados
        conexao = sqlite3.connect(DB_FILE)
        
        # Usa o Pandas para ler a tabela 'vagas' inteira e carregar em um DataFrame.
        # O DataFrame é como uma planilha em memória, muito poderoso para manipular dados.
        print("📖 Lendo dados da tabela 'vagas'...")
        df = pd.read_sql_query("SELECT * FROM vagas", conexao)
        
        # Fecha a conexão com o banco de dados assim que os dados são lidos.
        conexao.close()
        print("✅ Dados lidos com sucesso. Conexão fechada.")
        
        # Verifica se o DataFrame não está vazio antes de exportar.
        if df.empty:
            print("⚠️ A tabela de vagas está vazia. Nenhum arquivo CSV será gerado.")
            return
            
        # Exporta o DataFrame para um arquivo CSV.
        # index=False: para não salvar o índice do DataFrame como uma coluna no arquivo.
        # encoding='utf-8-sig': garante compatibilidade com caracteres especiais (como ç, ã) no Excel e Google Sheets.
        print(f"✍️ Exportando {len(df)} vagas para o arquivo '{CSV_FILE}'...")
        df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
        
        print("\n========================================================")
        print(f"✅ SUCESSO! Os dados foram exportados para '{CSV_FILE}'.")
        print("========================================================")
        print("\nPróximos passos:")
        print("1. Encontre o arquivo 'vagas_exportadas.csv' na mesma pasta do projeto.")
        print("2. Abra o Google Sheets (sheets.google.com).")
        print("3. Vá em 'Arquivo' -> 'Importar' -> 'Upload' e selecione o arquivo CSV.")

    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado durante a exportação: {e}")

# Ponto de entrada do script.
if __name__ == "__main__":
    exportar_para_csv()

    
