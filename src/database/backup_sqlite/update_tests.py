"""
Script para atualizar todos os testes para usar SQLite isolado
Execute: python update_tests.py
"""
import os
import sqlite3

TEST_TEMPLATE = '''"""
Teste unitário para o scraper da {empresa}
"""
import sys
from pathlib import Path
import sqlite3
import os

root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.scrapers import {modulo}

TEST_DB_FILE = "src/database/teste.db"

def criar_banco_teste():
    os.makedirs(os.path.dirname(TEST_DB_FILE), exist_ok=True)
    conn = sqlite3.connect(TEST_DB_FILE)
    cursor = conn.cursor()
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
    )
    """)
    conn.commit()
    conn.close()

def test_scraper():
    print(f"--- TESTANDO SCRAPER {empresa_upper} ---")
    print(f"Usando banco de teste isolado: {{TEST_DB_FILE}}\\n")
    
    criar_banco_teste()
    vagas_coletadas = {modulo}.raspar()

    assert vagas_coletadas, "❌ Nenhuma vaga encontrada."
    assert len(vagas_coletadas) > 0, "Lista de vagas está vazia"
    
    print(f"\\n✅ SUCESSO! {{len(vagas_coletadas)}} vagas encontradas.")
    print(f"Primeiras 3 vagas:")
    for i, vaga in enumerate(vagas_coletadas[:3], 1):
        print(f"  {{i}}. {{vaga['titulo']}} ({{vaga.get('localizacao', 'N/A')}})") 
    
    conn = sqlite3.connect(TEST_DB_FILE)
    cursor = conn.cursor()
    novas_vagas_salvas = 0
    for vaga in vagas_coletadas:
        try:
            cursor.execute("""
            INSERT INTO vagas (empresa, titulo, localizacao, modelo_trabalho, url_vaga, data_coleta, ultima_atualizacao)
            VALUES (?, ?, ?, ?, ?, DATE('now'), DATETIME('now'))
            """, (vaga.get('empresa'), vaga.get('titulo'), vaga.get('localizacao'), 
                   vaga.get('modelo_trabalho'), vaga.get('url_vaga')))
            novas_vagas_salvas += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    
    print(f"\\nResumo: {{novas_vagas_salvas}} vagas salvas em '{{TEST_DB_FILE}}'.")
    
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

if __name__ == "__main__":
    test_scraper()
'''

# Mapeamento de arquivos para módulos e empresas
TESTES = {
    'test_abinbev.py': ('Abinbev', 'AB INBEV'),
    'test_ambevtech.py': ('Ambevtech', 'AMBEV TECH'),
    'test_bosch.py': ('Bosch', 'BOSCH'),
    'test_ciandt.py': ('Ciandt', 'CI&T'),
    'test_cnhindustrial.py': ('Cnhindustrial', 'CNH INDUSTRIAL'),
    'test_cpfl.py': ('Cpfl', 'CPFL'),
    'test_dell.py': ('Dell', 'DELL'),
    'test_eldorado.py': ('Eldorado', 'ELDORADO'),
    'test_enforce.py': ('Enforce', 'ENFORCE'),
    'test_generalmotors.py': ('Generalmotors', 'GENERAL MOTORS'),
    'test_goodyear.py': ('Goodyear', 'GOODYEAR'),
    'test_honda.py': ('Honda', 'HONDA'),
    'test_huawei.py': ('Huawei', 'HUAWEI'),
    'test_ibm.py': ('Ibm', 'IBM'),
    'test_ifood.py': ('Ifood', 'IFOOD'),
    'test_johndeere.py': ('Johndeere', 'JOHN DEERE'),
    'test_kryptus.py': ('Kryptus', 'KRYPTUS'),
    'test_kumulus.py': ('Kumulus', 'KUMULUS'),
    'test_lenovo.py': ('Lenovo', 'LENOVO'),
    'test_motorola.py': ('Motorola', 'MOTOROLA'),
    'test_samsung.py': ('Samsung', 'SAMSUNG'),
    'test_sensedia.py': ('Sensedia', 'SENSEDIA'),
    'test_toyota.py': ('Toyota', 'TOYOTA'),
    'test_tresm.py': ('Tresm', '3M'),
    'test_venturus.py': ('Venturus', 'VENTURUS'),
    'test_ype.py': ('Ype', 'YPÊ'),
}

test_dir = 'src/test/unit_test'
atualizados = 0

for arquivo, (modulo, empresa) in TESTES.items():
    caminho = os.path.join(test_dir, arquivo)
    if os.path.exists(caminho):
        conteudo = TEST_TEMPLATE.format(
            empresa=empresa,
            modulo=modulo,
            empresa_upper=empresa
        )
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        atualizados += 1
        print(f"✅ {arquivo}")
    else:
        print(f"⚠️ {arquivo} não encontrado")

print(f"\n✅ {atualizados} arquivos de teste atualizados!")
