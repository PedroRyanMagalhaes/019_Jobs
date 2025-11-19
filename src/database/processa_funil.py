import sqlite3
import json
import requests
from config.settings import GEMINI_API_KEY, DB_FILE
from src.filtro_funil import filtrar_por_palavras_chave, agrupar_duvidas

# Função para ler todas as vagas do banco

def ler_vagas_completas(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vagas')
    vagas = cursor.fetchall()
    # Obter nomes das colunas
    colunas = [desc[0] for desc in cursor.description]
    conn.close()
    return vagas, colunas

# Função para criar banco vagas_filtradas com mesma estrutura + classificação

def criar_banco_filtrado(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Primeiro, apagar tabela se existir para recriar corretamente
    cursor.execute('DROP TABLE IF EXISTS vagas_filtradas')
    
    cursor.execute('''CREATE TABLE vagas_filtradas (
        id INTEGER PRIMARY KEY,
        empresa TEXT NOT NULL,
        titulo TEXT NOT NULL,
        localizacao TEXT,
        modelo_trabalho TEXT,
        url_vaga TEXT NOT NULL,
        classificacao_ia TEXT,
        data_coleta TEXT NOT NULL,
        ultima_atualizacao TEXT NOT NULL,
        classificacao_funil TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

# Função para salvar vagas filtradas

def salvar_vaga_filtrada(db_path, vaga_data, classificacao):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Inserir vaga com classificação do funil
    cursor.execute('''INSERT OR REPLACE INTO vagas_filtradas 
        (id, empresa, titulo, localizacao, modelo_trabalho, url_vaga, classificacao_ia, data_coleta, ultima_atualizacao, classificacao_funil) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (*vaga_data, classificacao))
    conn.commit()
    conn.close()

# Função para chamar Gemini API em lote

def classificar_com_gemini(titulos_com_ids):
    if not titulos_com_ids:
        return {}
    
    # Extrair apenas os títulos para o prompt
    titulos = [item[1] for item in titulos_com_ids]
    
    # URL corrigida para usar gemini-2.5-flash
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}'
    
    prompt = f"""Classifique cada título de vaga abaixo como "tech" (true) ou "non-tech" (false).
Vagas tech incluem: desenvolvimento, programação, dados, TI, engenharia de software, DevOps, etc.
Vagas non-tech incluem: vendas, limpeza, motorista, atendimento, etc.

Responda APENAS com um JSON válido no formato:
{{
    "Título da vaga 1": true,
    "Título da vaga 2": false
}}

Títulos para classificar:
{json.dumps(titulos, ensure_ascii=False, indent=2)}"""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        print(f"🤖 Enviando {len(titulos)} títulos para a Gemini API...")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            resposta_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            print(f"📋 Resposta da IA:\n{resposta_text}")
            
            # Tentar extrair JSON da resposta
            try:
                # Remover markdown se houver
                if "```json" in resposta_text:
                    resposta_text = resposta_text.split("```json")[1].split("```")[0]
                elif "```" in resposta_text:
                    resposta_text = resposta_text.split("```")[1].split("```")[0]
                
                result = json.loads(resposta_text.strip())
                return result
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao decodificar JSON da IA: {e}")
                print(f"Resposta recebida: {resposta_text}")
                return {}
        else:
            print(f"❌ Erro na API Gemini: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print(f"❌ Erro ao chamar Gemini API: {e}")
        return {}

# Funil completo

def processar_funil():
    print("🔄 Iniciando processamento do Funil Inteligente...")
    
    # Ler todas as vagas do banco principal
    vagas, colunas = ler_vagas_completas(DB_FILE)
    print(f"📊 {len(vagas)} vagas encontradas no banco principal")
    
    # Criar banco filtrado
    db_filtrado = DB_FILE.replace('vagas.db', 'vagas_filtradas.db')
    criar_banco_filtrado(db_filtrado)
    
    # Separar por tipo
    aprovadas_direto = []
    reprovadas_direto = []
    duvidas = []
    
    for vaga in vagas:
        titulo = vaga[2]  # Assumindo que título está na posição 2
        tipo = filtrar_por_palavras_chave(titulo)
        
        if tipo == 'tech':
            aprovadas_direto.append(vaga)
        elif tipo == 'non-tech':
            reprovadas_direto.append(vaga)
        else:  # duvida
            duvidas.append(vaga)
    
    print(f"✅ Aprovadas direto (palavras-chave): {len(aprovadas_direto)}")
    print(f"❌ Reprovadas direto (palavras-chave): {len(reprovadas_direto)}")
    print(f"❓ Enviando para IA: {len(duvidas)}")
    
    # Salvar aprovadas direto com marcação "tech funil"
    for vaga in aprovadas_direto:
        salvar_vaga_filtrada(db_filtrado, vaga, 'tech funil')
    
    # Processar dúvidas em lotes
    if duvidas:
        # Agrupar em lotes de 20
        batch_size = 20
        for i in range(0, len(duvidas), batch_size):
            batch_vagas = duvidas[i:i+batch_size]
            
            # Preparar títulos com IDs para a IA
            titulos_com_ids = [(vaga[0], vaga[2]) for vaga in batch_vagas]
            
            print(f"\n🤖 Processando lote {i//batch_size + 1} ({len(batch_vagas)} vagas)...")
            resultado_ia = classificar_com_gemini(titulos_com_ids)
            
            # Salvar resultados
            for vaga in batch_vagas:
                titulo = vaga[2]
                if resultado_ia.get(titulo, False):
                    classificacao = 'tech IA'
                    salvar_vaga_filtrada(db_filtrado, vaga, classificacao)
                    print(f"✅ Tech (IA): {titulo}")
                else:
                    classificacao = 'non-tech'
                    print(f"❌ Non-Tech (IA): {titulo}")
    
    print(f"\n🎉 Funil Inteligente concluído! Resultados salvos em: {db_filtrado}")

if __name__ == "__main__":
    processar_funil()
