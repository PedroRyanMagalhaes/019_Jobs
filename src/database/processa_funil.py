import json
import requests
from datetime import date
from config.settings import GEMINI_API_KEY
from src.filtro_funil import filtrar_por_palavras_chave, agrupar_duvidas
from src.database.supabase_client import get_supabase


def ler_vagas_do_dia():
    """
    Retorna todas as vagas coletadas hoje do Supabase.
    """
    sb = get_supabase()
    data_hoje = date.today().isoformat()
    res = sb.table("vagas").select("*").eq("data_coleta", data_hoje).execute()
    return res.data


def criar_banco_filtrado(_db_path=None):
    """Compatibilidade: verifica tabela vagas_filtradas no Supabase."""
    sb = get_supabase()
    sb.table("vagas_filtradas").select("id").limit(1).execute()


def salvar_vaga_filtrada(_db_path, vaga_data, classificacao):
    """Insere ou atualiza vaga no Supabase com classificacao do funil."""
    sb = get_supabase()
    # vaga_data pode ser dict (Supabase) ou tuple (legado)
    if isinstance(vaga_data, dict):
        registro = {
            "empresa": vaga_data["empresa"],
            "titulo": vaga_data["titulo"],
            "localizacao": vaga_data.get("localizacao"),
            "modelo_trabalho": vaga_data.get("modelo_trabalho"),
            "url_vaga": vaga_data["url_vaga"],
            "classificacao_ia": vaga_data.get("classificacao_ia"),
            "data_coleta": vaga_data["data_coleta"],
            "ultima_atualizacao": vaga_data["ultima_atualizacao"],
            "classificacao_funil": classificacao,
        }
    else:
        # tuple: (id, empresa, titulo, localizacao, modelo_trabalho, url_vaga, classificacao_ia, data_coleta, ultima_atualizacao)
        registro = {
            "empresa": vaga_data[1],
            "titulo": vaga_data[2],
            "localizacao": vaga_data[3],
            "modelo_trabalho": vaga_data[4],
            "url_vaga": vaga_data[5],
            "classificacao_ia": vaga_data[6],
            "data_coleta": vaga_data[7],
            "ultima_atualizacao": vaga_data[8],
            "classificacao_funil": classificacao,
        }
    sb.table("vagas_filtradas").upsert(registro, on_conflict="url_vaga").execute()

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

# Função auxiliar para remover vagas do banco filtrado que não estão mais no banco principal
# (REMOVIDA - agora essa lógica está no database.py na função finalizar_ciclo_scraping)

# Funil completo

def processar_funil():
    print("🔄 Iniciando processamento do Funil Inteligente...")
    
    # Verificar tabela filtrada
    criar_banco_filtrado()
    
    # Ler todas as vagas coletadas HOJE
    vagas = ler_vagas_do_dia()
    
    if not vagas:
        print("✅ Nenhuma vaga coletada hoje para processar!")
        return
    
    print(f"📊 {len(vagas)} vagas coletadas HOJE para processar")
    
    # Separar por tipo
    aprovadas_direto = []
    reprovadas_direto = []
    duvidas = []
    
    for vaga in vagas:
        titulo = vaga["titulo"]
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
        salvar_vaga_filtrada(None, vaga, 'tech funil')
    
    # Processar dúvidas em lotes
    if duvidas:
        # Agrupar em lotes de 20
        batch_size = 20
        for i in range(0, len(duvidas), batch_size):
            batch_vagas = duvidas[i:i+batch_size]
            
            # Preparar títulos com IDs para a IA
            titulos_com_ids = [(vaga["id"], vaga["titulo"]) for vaga in batch_vagas]
            
            print(f"\n🤖 Processando lote {i//batch_size + 1} ({len(batch_vagas)} vagas)...")
            resultado_ia = classificar_com_gemini(titulos_com_ids)
            
            # Salvar resultados
            for vaga in batch_vagas:
                titulo = vaga["titulo"]
                if resultado_ia.get(titulo, False):
                    classificacao = 'tech IA'
                    salvar_vaga_filtrada(None, vaga, classificacao)
                    print(f"✅ Tech (IA): {titulo}")
                else:
                    classificacao = 'non-tech'
                    print(f"❌ Non-Tech (IA): {titulo}")
    
    print(f"\n🎉 Funil Inteligente concluído!")

if __name__ == "__main__":
    processar_funil()
