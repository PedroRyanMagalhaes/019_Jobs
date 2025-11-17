import sqlite3
import requests
import json
import time
from typing import Dict, List, Optional
from config.settings import USE_OLLAMA, OLLAMA_BASE_URL, OLLAMA_MODEL, GEMINI_API_KEY, DB_TECH_FILE, DB_FILE

class ClassificadorVagasOllama:
    def __init__(self):
        self.db_origem = DB_FILE
        self.db_tech = DB_TECH_FILE
        
        if USE_OLLAMA:
            # Configuração Ollama
            self.use_ai = self._test_ollama_connection()
            self.ai_type = "Ollama Local"
        else:
            # Configuração Gemini (backup)
            self.use_ai = self._setup_gemini()
            self.ai_type = "Gemini API"
        
        if not self.use_ai:
            print("⚠️ Nenhuma IA disponível. Usando classificação por palavras-chave.")
    
    def _test_ollama_connection(self) -> bool:
        """Testa conexão com Ollama local"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if OLLAMA_MODEL in model_names or f"{OLLAMA_MODEL}:latest" in model_names:
                    print(f"✅ Ollama conectado! Modelo: {OLLAMA_MODEL}")
                    return True
                else:
                    print(f"❌ Modelo {OLLAMA_MODEL} não encontrado no Ollama.")
                    print(f"   Modelos disponíveis: {model_names}")
                    print(f"   Execute: ollama pull {OLLAMA_MODEL}")
                    return False
            else:
                print("❌ Ollama não está respondendo.")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao conectar com Ollama: {e}")
            print("   Certifique-se que o Ollama está rodando: ollama serve")
            return False
    
    def _setup_gemini(self) -> bool:
        """Setup Gemini como backup"""
        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-pro')
                print("✅ Gemini configurado como backup")
                return True
            except Exception as e:
                print(f"❌ Erro ao configurar Gemini: {e}")
                return False
        return False
    
    def _query_ollama(self, prompt: str) -> str:
        """Consulta o Ollama local"""
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                print(f"Erro Ollama: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"Erro ao consultar Ollama: {e}")
            return ""
    
    def _query_gemini(self, prompt: str) -> str:
        """Consulta Gemini como backup"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Erro Gemini: {e}")
            return ""
    
    def classificar_vaga(self, titulo: str, localizacao: str = "") -> Dict:
        """
        Classifica vaga usando Ollama ou Gemini
        """
        if not self.use_ai:
            return self._classificacao_fallback(titulo)
        
        prompt = f"""Classifique esta vaga como TECH ou NÃO-TECH.

Título: {titulo}
Localização: {localizacao}

TECH: Desenvolvimento, DevOps, Data Science, QA, Segurança, Infraestrutura TI, UX/UI, SAP técnico, Machine Learning
NÃO-TECH: RH, Financeiro, Marketing, Vendas, Operações, Administrativo, Limpeza, Segurança física

Responda APENAS este JSON:
{{"is_tech": true/false, "confianca": 0.95, "motivo": "explicação curta"}}"""
        
        try:
            if USE_OLLAMA:
                response = self._query_ollama(prompt)
            else:
                response = self._query_gemini(prompt)
            
            if not response:
                return self._classificacao_fallback(titulo)
            
            # Parse do JSON
            content = response.strip()
            
            # Remove marcadores se existirem
            if '```' in content:
                content = content.replace('```json', '').replace('```', '').strip()
            
            # Tenta extrair JSON da resposta
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = content[json_start:json_end]
                result = json.loads(json_content)
                
                # Validação
                if "is_tech" in result and "confianca" in result:
                    return result
            
            # Se chegou aqui, houve problema no parse
            print(f"Resposta da IA não é JSON válido: {content[:100]}...")
            return self._classificacao_fallback(titulo)
            
        except Exception as e:
            print(f"Erro na classificação IA ({self.ai_type}): {e}")
            return self._classificacao_fallback(titulo)
    
    def _classificacao_fallback(self, titulo: str) -> Dict:
        """Classificação robusta por palavras-chave se IA falhar"""
        palavras_tech = [
            # Desenvolvimento
            'desenvol', 'developer', 'program', 'software', 'engineer', 'engenheiro',
            'frontend', 'backend', 'fullstack', 'full stack', 'mobile', 'web',
            'react', 'angular', 'vue', 'python', 'java', 'javascript', 'php', 
            'node', '.net', 'c#', 'c++', 'ruby', 'golang', 'kotlin', 'swift',
            
            # Dados e Analytics
            'data', 'scientist', 'analytics', 'bi', 'business intelligence',
            'sql', 'database', 'dba', 'mongodb', 'mysql', 'postgresql', 'oracle',
            'machine learning', 'ml', 'ai', 'artificial intelligence',
            
            # DevOps e Cloud
            'devops', 'cloud', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'jenkins', 'terraform', 'ansible', 'sre', 'reliability',
            
            # QA e Testes
            'qa', 'quality assurance', 'teste', 'testing', 'automation', 'selenium',
            
            # Segurança
            'security', 'cyber', 'infosec', 'segurança',
            
            # Design e UX
            'ux', 'ui', 'design', 'product design', 'user experience',
            
            # Infraestrutura e SAP
            'infra', 'network', 'sistema', 'ti', 'tech', 'technical',
            'sap', 'basis', 'abap', 'salesforce',
            
            # Áreas específicas
            'embedded', 'firmware', 'hardware', 'iot', 'blockchain'
        ]
        
        titulo_lower = titulo.lower()
        matches = [palavra for palavra in palavras_tech if palavra in titulo_lower]
        
        is_tech = len(matches) > 0
        confianca = min(0.8, 0.4 + (len(matches) * 0.1))  # Máximo 0.8 para fallback
        
        return {
            "is_tech": is_tech,
            "confianca": confianca,
            "motivo": f"Palavras-chave encontradas: {matches}" if matches else "Nenhuma palavra-chave tech encontrada"
        }
    
    def processar_vagas_novas(self) -> int:
        """
        Processa vagas que ainda não foram classificadas
        Returns: número de vagas tech encontradas
        """
        from src.database.database_tech import salvar_vaga_tech
        
        try:
            conn_origem = sqlite3.connect(self.db_origem)
            cursor_origem = conn_origem.cursor()
            
            # Busca vagas que ainda não foram processadas
            query = """
            SELECT v.id, v.empresa, v.titulo, v.localizacao, v.modelo_trabalho, v.url_vaga
            FROM vagas v
            WHERE v.id NOT IN (
                SELECT DISTINCT vaga_origem_id 
                FROM vagas_tech 
                WHERE vaga_origem_id IS NOT NULL
            )
            ORDER BY v.id DESC
            """
            
            cursor_origem.execute(query)
            vagas_nao_processadas = cursor_origem.fetchall()
            conn_origem.close()
            
        except sqlite3.OperationalError as e:
            if "no such table: vagas_tech" in str(e):
                # Primeira execução
                conn_origem = sqlite3.connect(self.db_origem)
                cursor_origem = conn_origem.cursor()
                cursor_origem.execute("SELECT id, empresa, titulo, localizacao, modelo_trabalho, url_vaga FROM vagas ORDER BY id DESC")
                vagas_nao_processadas = cursor_origem.fetchall()
                conn_origem.close()
            else:
                print(f"Erro ao acessar banco: {e}")
                return 0
        
        vagas_tech_encontradas = 0
        total_processadas = len(vagas_nao_processadas)
        
        if total_processadas == 0:
            print("✅ Todas as vagas já foram classificadas!")
            return 0
        
        print(f"Processando {total_processadas} vagas não classificadas...")
        print(f"Usando {self.ai_type}")
        
        for i, (vaga_id, empresa, titulo, localizacao, modelo, url) in enumerate(vagas_nao_processadas):
            print(f"[{i+1}/{total_processadas}] Analisando: {titulo[:50]}...")
            
            classificacao = self.classificar_vaga(titulo, localizacao or "")
            
            if classificacao["is_tech"]:
                vaga_tech = {
                    "vaga_origem_id": vaga_id,
                    "empresa": empresa,
                    "titulo": titulo,
                    "localizacao": localizacao,
                    "modelo_trabalho": modelo,
                    "url_vaga": url,
                    "confianca_ia": classificacao["confianca"],
                    "motivo_ia": classificacao["motivo"]
                }
                
                if salvar_vaga_tech(vaga_tech):
                    vagas_tech_encontradas += 1
                    print(f"  ✅ TECH: {titulo} (confiança: {classificacao['confianca']:.2f})")
                else:
                    print(f"  ⚠️ Erro ao salvar vaga tech")
            else:
                print(f"  ❌ NÃO-TECH: {titulo}")
        
        print(f"\n✅ Classificação concluída: {vagas_tech_encontradas} vagas tech de {total_processadas} analisadas")
        return vagas_tech_encontradas