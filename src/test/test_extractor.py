#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar a função extrair_titulo_e_localizacao
com casos problemáticos identificados.
"""

import sys
import os

# Adiciona o diretório pai ao path para permitir imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.ciandt import extrair_titulo_e_localizacao

def testar_casos_problematicos():
    """Testa a função com casos problemáticos identificados."""
    
    casos_teste = [
        # Casos com informações de minorias - Campinas/Brazil
        "Senior Java Developer Brazil (Afirmativa para Mulheres)",
        "Mid-Level Data Developer (Afirmativa para Mulheres, Pessoas com Deficiência, Pessoas Pretas, LGBTQIAPN+) Brazil",
        "QA EntryLevel | affirmative position for women Brazil",
        "Senior Backend Developer Campinas (Vaga Afirmativa)",
        
        # Casos com vírgulas no título - Campinas/Brazil
        "Senior Java/Nodejs Developer | Vaga Afirmativa para Mulheres Brazil",
        "Mid level .NET Developer- Afirmativa Mulheres Brazil",
        "Data Engineer, Python Specialist Campinas",
        
        # Casos normais para comparação - Campinas/Brazil
        "Senior Backend Developer Brazil",
        "Mid-Level Python Developer Campinas",
        
        # Casos que devem ser rejeitados (outras localizações)
        "Fullstack, Specialist Developer (Python + React) Colombia", 
        "Data Engineer São Paulo",
        "Tech Lead Rio de Janeiro",
        
        # Casos edge - Campinas/Brazil
        "Tech Lead / Software Architect Java (Vaga afirmativa para Mulheres) Brazil",
        "Exclusiva PCD - Mid Level/Senior Developer Java/AWS Campinas",
    ]
    
    print("=== TESTE DA FUNÇÃO extrair_titulo_e_localizacao ===")
    print("(Filtro: apenas Campinas e Brazil)\n")
    
    vagas_validas = 0
    
    for i, caso in enumerate(casos_teste, 1):
        titulo, localizacao = extrair_titulo_e_localizacao(caso)
        
        # Simula o filtro do scraper
        aceita_vaga = localizacao in ["Campinas", "Brazil"]
        status = "✅ ACEITA" if aceita_vaga else "❌ REJEITADA"
        
        if aceita_vaga:
            vagas_validas += 1
        
        print(f"Caso {i}: {status}")
        print(f"  Input:       '{caso}'")
        print(f"  Título:      '{titulo}'")
        print(f"  Localização: '{localizacao}'")
        print()
    
    print(f"=== RESUMO ===")
    print(f"Total de casos testados: {len(casos_teste)}")
    print(f"Vagas válidas (Campinas/Brazil): {vagas_validas}")
    print(f"Vagas rejeitadas: {len(casos_teste) - vagas_validas}")

if __name__ == "__main__":
    testar_casos_problematicos()
