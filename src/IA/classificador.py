import time
import sqlite3
import google.generativeai as genai
import json
from typing import Dict, List, Optional
from config.settings import GEMINI_API_KEY, DB_TECH_FILE, DB_FILE

class ClassificadorVagasTech:
    def __init__(self):
        self.db_origem = DB_FILE
        self.db_tech = DB_TECH_FILE
        self.requests_count = 0
        self.last_reset_time = time.time()
        self.MAX_REQUESTS_PER_MINUTE = 8  # Deixa margem de segurança
        
        # Configure a API do Gemini
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Modelo mais novo
                self.use_ai = True
                print(f"✅ Gemini configurado com rate limiting ({self.MAX_REQUESTS_PER_MINUTE}/min)")
            except Exception as e:
                print(f"❌ Erro ao configurar Gemini: {e}")
                self.use_ai = False
        else:
            self.use_ai = False
    
    def _check_rate_limit(self):
        """Controla o rate limit da API"""
        current_time = time.time()
        
        # Reset contador a cada minuto
        if current_time - self.last_reset_time >= 60:
            self.requests_count = 0
            self.last_reset_time = current_time
        
        # Se atingiu limite, espera
        if self.requests_count >= self.MAX_REQUESTS_PER_MINUTE:
            wait_time = 60 - (current_time - self.last_reset_time)
            if wait_time > 0:
                print(f"⏱️ Rate limit atingido. Aguardando {wait_time:.1f}s...")
                time.sleep(wait_time + 1)  # +1 segundo de segurança
                self.requests_count = 0
                self.last_reset_time = time.time()
        
        self.requests_count += 1

    def classificar_vaga(self, titulo: str, localizacao: str = "") -> Dict:
        """
        Usa IA Gemini com rate limiting
        """
        if not self.use_ai:
            return self._classificacao_fallback(titulo)
        
        # Controle de rate limit
        self._check_rate_limit()
        
        prompt = f"""
        Classifique esta vaga como TECH ou NÃO-TECH:
        
        Título: {titulo}
        
        TECH: Desenvolvimento, DevOps, Data Science, QA, Segurança, Infraestrutura TI, UX/UI, SAP técnico
        NÃO-TECH: RH, Financeiro, Marketing, Vendas, Operações, Administrativo
        
        Responda apenas JSON:
        {{"is_tech": true/false, "confianca": 0.95, "motivo": "explicação curta"}}
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # Remove markdown se existir
            if '```' in content:
                content = content.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"Erro IA: {e}")
            return self._classificacao_fallback(titulo)

    
    def _classificacao_fallback(self, titulo: str) -> Dict:
        """Classificação simples por palavras-chave se a IA falhar"""
        palavras_tech = [
            # Desenvolvimento
            'desenvol', 'developer', 'program', 'software', 'frontend', 'backend', 
            'fullstack', 'mobile', 'web', 'react', 'angular', 'vue', 'python', 
            'java', 'javascript', 'php', 'node', '.net', 'c#', 'c++',
            
            # Dados e Analytics
            'data', 'analis', 'scientist', 'analytics', 'bi', 'business intelligence',
            'sql', 'database', 'dba', 'mongodb', 'mysql', 'oracle',
            
            # DevOps e Cloud
            'devops', 'cloud', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'jenkins', 'terraform', 'ansible', 'sre', 'reliability',
            
            # QA e Testes
            'qa', 'quality', 'teste', 'testing', 'automation', 'selenium',
            
            # Segurança
            'security', 'cyber', 'infosec', 'segurança',
            
            # Design e UX
            'ux', 'ui', 'design', 'product design', 'user experience',
            
            # Infraestrutura
            'infra', 'network', 'sistema', 'ti', 'tech', 'technical',
            
            # IA e ML
            'machine learning', 'artificial intelligence', 'ai', 'ml',
            'deep learning', 'neural'
        ]
        
        titulo_lower = titulo.lower()
        matches = [palavra for palavra in palavras_tech if palavra in titulo_lower]
        
        is_tech = len(matches) > 0
        confianca = min(0.8, 0.4 + (len(matches) * 0.1))  # Máximo 0.8 para fallback
        
        return {
            "is_tech": is_tech,
            "confianca": confianca,
            "motivo": f"Classificação por palavras-chave (fallback). Matches: {matches}" if matches else "Nenhuma palavra-chave tech encontrada"
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
            # Usa LEFT JOIN para pegar apenas vagas que não estão na tabela tech
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
                # Primeira execução - processa todas as vagas
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
        print(f"Usando {'Gemini IA' if self.use_ai else 'classificação por palavras-chave'}")
        
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