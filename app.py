
import database
from modulos import ciandt_scraper

def main():
    """
    Função principal que orquestra o processo de scraping e armazenamento.
    """
    print("==============================================")
    print("== INICIANDO PROCESSO DE COLETA DE VAGAS ==")
    print("==============================================")

    # 1. Inicializar o banco de dados
    print("\n--- PASSO 1: Preparando o Banco de Dados ---")
    database.inicializar_banco()

    # 2. Executar o scraper da CI&T
    print("\n--- PASSO 2: Executando Scraper da CI&T ---")
    try:
        vagas_ciandt = ciandt_scraper.raspar_ciandt()
    except Exception as e:
        print(f"❌ Falha crítica ao executar o scraper da CI&T: {e}")
        vagas_ciandt = [] # Garante que a lista esteja vazia em caso de erro

    # 3. Salvar os dados coletados no banco de dados
    print("\n--- PASSO 3: Salvando Vagas no Banco de Dados ---")
    if vagas_ciandt:
        print(f"Processando {len(vagas_ciandt)} vagas encontradas na CI&T...")
        novas_vagas_salvas = 0
        for vaga in vagas_ciandt:
            if database.salvar_vaga(vaga):
                novas_vagas_salvas += 1
        print(f"\nResumo CI&T: {novas_vagas_salvas} novas vagas foram salvas.")
    else:
        print("Nenhuma vaga da CI&T para salvar.")

    # Futuramente, você pode adicionar chamadas para outros scrapers aqui
    # print("\n--- Executando Scraper da CPFL ---")
    # vagas_cpfl = cpfl_scraper.raspar_cpfl()
    # ... e assim por diante

    print("\n==============================================")
    print("== PROCESSO FINALIZADO ==")
    print("==============================================")


if __name__ == "__main__":
    main()
