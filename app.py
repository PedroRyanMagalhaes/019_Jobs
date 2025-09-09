import database
from modulos import ciandt_scraper
# No futuro, você importará outros scrapers aqui. Ex:
# from modulos import cpfl_scraper

def main():
    """
    Função principal que orquestra todo o processo de scraping e armazenamento de vagas.
    """
    print("==============================================")
    print("== INICIANDO PROCESSO DE COLETA DE VAGAS ==")
    print("==============================================")

    # 1. Inicializar o banco de dados
    # Garante que o arquivo do banco e a tabela 'vagas' existam antes de qualquer outra operação.
    print("\n--- PASSO 1: Preparando o Banco de Dados ---")
    database.inicializar_banco()

    # 2. Executar o scraper da CI&T
    # Cada scraper será chamado sequencialmente aqui.
    print("\n--- PASSO 2: Executando Scraper da CI&T ---")
    try:
        # A função raspar_ciandt() vai até o site da CI&T e retorna uma lista de dicionários,
        # onde cada dicionário representa uma vaga.
        vagas_ciandt = ciandt_scraper.raspar_ciandt()
    except Exception as e:
        print(f"❌ Falha crítica ao executar o scraper da CI&T: {e}")
        vagas_ciandt = [] # Garante que a lista esteja vazia se o scraper falhar.

    # 3. Salvar os dados coletados no banco de dados
    print("\n--- PASSO 3: Salvando Vagas no Banco de Dados ---")
    if vagas_ciandt:
        print(f"Processando {len(vagas_ciandt)} vagas encontradas na CI&T...")
        novas_vagas_salvas = 0
        # Itera sobre cada vaga retornada pelo scraper.
        for vaga in vagas_ciandt:
            # A função salvar_vaga retorna True se a vaga era nova e foi salva,
            # ou False se a vaga já existia no banco.
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo CI&T: {novas_vagas_salvas} novas vagas foram salvas.")
    else:
        print("Nenhuma vaga da CI&T para salvar.")

    # --- Área para futuros scrapers ---
    # Quando você criar o scraper da CPFL, por exemplo, o código viria aqui:
    # print("\n--- PASSO 4: Executando Scraper da CPFL ---")
    # vagas_cpfl = cpfl_scraper.raspar_cpfl()
    # if vagas_cpfl:
    #     ... (lógica para salvar as vagas da CPFL) ...

    print("\n==============================================")
    print("== PROCESSO FINALIZADO ==")
    print("==============================================")


# Este é um ponto de entrada padrão em Python.
# O código dentro deste 'if' só será executado quando você rodar o script diretamente
# com o comando 'python app.py'.
if __name__ == "__main__":
    main()
