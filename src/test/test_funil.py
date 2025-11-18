import sys
import os
# Adicionar o diretório raiz do projeto ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.processa_funil import processar_funil

if __name__ == "__main__":
    processar_funil()
