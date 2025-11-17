from src.IA.classificador_ollama import ClassificadorVagasOllama
from src.database import database_tech

def main():
    print("== CLASSIFICANDO VAGAS EXISTENTES COM IA ==")
    print("===========================================")
    
    # Inicializar banco tech (caso não exista)
    database_tech.inicializar_banco_tech()
    
    # Classificar vagas
    classificador = ClassificadorVagasOllama()
    vagas_tech_encontradas = classificador.processar_vagas_novas()
    
    # Estatísticas
    total_tech = database_tech.contar_vagas_tech()
    vagas_por_empresa = database_tech.listar_vagas_tech_por_empresa()
    
    print(f"\n📊 RESUMO:")
    print(f"   • Vagas tech encontradas agora: {vagas_tech_encontradas}")
    print(f"   • Total vagas tech no banco: {total_tech}")
    
    if vagas_por_empresa:
        print(f"\n📈 TOP EMPRESAS TECH:")
        for empresa, count in list(vagas_por_empresa.items())[:5]:
            print(f"   • {empresa}: {count} vagas")
    
    print("\n===========================================")
    print("== CLASSIFICAÇÃO FINALIZADA ==")

if __name__ == "__main__":
    main()