"""
Script simples para adicionar emails de assinantes
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from newsletter.gerenciar_assinantes import adicionar_assinante, listar_assinantes

def main():
    print("\n" + "="*60)
    print("📧 ADICIONAR ASSINANTE DA NEWSLETTER")
    print("="*60 + "\n")
    
    email = input("Email: ").strip()
    
    if not email:
        print("❌ Email não pode estar vazio")
        return
    
    nome = input("Nome (opcional): ").strip()
    
    ativo_input = input("Ativo? (s/n) [padrão: s]: ").strip().lower()
    ativo = True if ativo_input in ['', 's', 'sim'] else False
    
    if adicionar_assinante(email, nome, ativo):
        print()
        
        # Perguntar se quer adicionar mais
        continuar = input("Adicionar outro email? (s/n): ").strip().lower()
        if continuar == 's':
            main()
        else:
            print("\n📋 Lista de assinantes ativos:\n")
            listar_assinantes()
    else:
        print(f"\n⚠️ {email} já está cadastrado ou ocorreu um erro\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
