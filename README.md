# 🎯 Jobs Tech Campinas - Sistema Automatizado

Sistema inteligente e automatizado para **coleta, filtragem e distribuição** de vagas de tecnologia em Campinas e região, utilizando **IA Gemini** para classificação e **envio automático de newsletters**.

---

## 🚀 **Funcionalidades**

✅ Web scraping automatizado de múltiplas empresas  
✅ **Filtragem inteligente com IA Gemini** (classifica vagas tech vs non-tech)  
✅ Sistema de bancos de dados sincronizados (vagas, filtradas, removidas)  
✅ **Newsletter automática via Resend** com vagas tech  
✅ Gestão de assinantes com tokens únicos  
✅ Prevenção de duplicatas e limpeza automática  
✅ Sistema modular e escalável  

---

## 📁 **Estrutura do Projeto**

```
019_Jobs/
├── src/
│   ├── database/                # 💾 Gerenciamento de dados
│   │   ├── database.py          # CRUD e ciclo de vida das vagas
│   │   ├── processa_funil.py    # Classificação inteligente com IA
│   │   └── database_usuarios.py # Gestão de assinantes
│   ├── scrapers/                # �️ Web Scrapers
│   │   ├── Bosch.py
│   │   ├── Ciandt.py
│   │   ├── Dell.py
│   │   └── ... (14 empresas)
│   ├── newsletter/              # � Sistema de emails
│   │   ├── enviar_newsletter.py
│   │   ├── buscar_vagas.py
│   │   └── gerenciar_assinantes.py
│   ├── templates/               # 🎨 Templates HTML
│   │   ├── newsletter_base.html
│   │   └── vaga_card.html
│   └── filtro_funil.py          # 🔍 Filtro de palavras-chave
├── config/
│   └── settings.py              # ⚙️ Configurações centralizadas
├── data/
│   └── (arquivos de empresas)
├── src/database/
│   ├── vagas.db                 # 📊 Banco principal
│   ├── vagas_filtradas.db       # ✅ Apenas vagas tech
│   ├── removidas.db             # 🗑️ Histórico de removidas
│   └── usuarios.db              # � Assinantes da newsletter
├── app.py                       # 🎬 Orquestrador principal
└── requirements.txt
```

---

## 🔄 **Fluxo Completo do Sistema**

### **1. Coleta (Scrapers)**
```
🔍 14 scrapers executam simultaneamente
    ↓
💾 Salvam no vagas.db
    - Novas vagas: data_coleta = hoje
    - Existentes: ultima_atualizacao = agora
```

### **2. Limpeza Automática**
```
🧹 finalizar_ciclo_scraping()
    ↓
📋 Identifica vagas não encontradas hoje
    ↓
🗑️ Remove de vagas.db E vagas_filtradas.db
    ↓
📦 Move para removidas.db (histórico)
```

### **3. Classificação Inteligente (Funil)**
```
🔄 Processa apenas vagas de HOJE (data_coleta = hoje)
    ↓
🔍 Filtro de palavras-chave:
    ├─ ✅ Tech direto (Python, Dev, etc) → vagas_filtradas.db
    ├─ ❌ Non-tech direto (Limpeza, RH, etc) → descarta
    └─ ❓ Dúvidas → Envia para Gemini API
        ↓
    🤖 Gemini analisa em lote (batch de 20):
        ├─ ✅ Tech → vagas_filtradas.db
        └─ ❌ Non-tech → descarta
```

### **4. Envio de Newsletter**
```
📧 Busca vagas do dia em vagas_filtradas.db
    ↓
📋 Busca vagas ativas antigas
    ↓
🎨 Renderiza HTML com Jinja2
    ↓
✉️ Envia via Resend API para todos assinantes
    - Vagas Novas: apenas de hoje
    - Vagas Ativas: dias anteriores
```

---

## � **Arquitetura dos Bancos de Dados**

### **vagas.db** (Banco Principal)
```sql
CREATE TABLE vagas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa TEXT NOT NULL,
    titulo TEXT NOT NULL,
    localizacao TEXT,
    modelo_trabalho TEXT,
    url_vaga TEXT NOT NULL UNIQUE,
    classificacao_ia TEXT,
    data_coleta TEXT NOT NULL,           -- Data que foi encontrada
    ultima_atualizacao TEXT NOT NULL     -- Última vez vista no scraping
);
```

### **vagas_filtradas.db** (Apenas Tech)
```sql
CREATE TABLE vagas_filtradas (
    id INTEGER PRIMARY KEY,
    empresa TEXT NOT NULL,
    titulo TEXT NOT NULL,
    localizacao TEXT,
    modelo_trabalho TEXT,
    url_vaga TEXT NOT NULL UNIQUE,
    classificacao_ia TEXT,
    data_coleta TEXT NOT NULL,
    ultima_atualizacao TEXT NOT NULL,
    classificacao_funil TEXT NOT NULL    -- 'tech funil' ou 'tech IA'
);
```

### **removidas.db** (Histórico)
```sql
CREATE TABLE vagas_removidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa TEXT NOT NULL,
    titulo TEXT NOT NULL,
    url_vaga TEXT NOT NULL,
    data_coleta TEXT NOT NULL,
    data_remocao TEXT NOT NULL,
    motivo_remocao TEXT DEFAULT 'Não encontrada no último scraping'
);
```

### **usuarios.db** (Assinantes)
```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    token TEXT NOT NULL UNIQUE,
    data_cadastro TEXT NOT NULL,
    ativo INTEGER DEFAULT 1
);
```

---

## ⚙️ **Tecnologias Utilizadas**

- **Python 3.x**
- **Playwright** - Web scraping robusto
- **SQLite3** - Banco de dados local
- **Google Gemini 2.5 Flash** - Classificação com IA
- **Resend API** - Envio de emails transacionais
- **Jinja2** - Templates HTML
- **dotenv** - Gerenciamento de variáveis de ambiente

---

## 🎯 **Otimizações Implementadas**

### **Economia de Tokens da IA**
- ✅ Processa apenas vagas novas do dia (não reprocessa)
- ✅ Filtro de palavras-chave reduz chamadas à API em ~60%
- ✅ Processamento em lote (batch de 20 vagas)
- ✅ Cache automático via banco de dados

### **Performance**
- ✅ Scrapers modulares e independentes
- ✅ Sincronização automática entre bancos
- ✅ Índices em campos de busca (url_vaga, data_coleta)

### **Confiabilidade**
- ✅ Tratamento de erros por scraper (um falha não afeta outros)
- ✅ Logs detalhados de cada etapa
- ✅ Histórico completo de vagas removidas
- ✅ Sistema de tokens para gerenciar inscrições/desinscrições

---

## 📊 **Empresas Monitoradas**

Bosch | CI&T | CPFL | Dell | Enforce | iFood | John Deere | Kryptus | Kumulus | Lenovo | Sensedia | Venturus | Ypê | Ambevtech

---

## 🤖 **Classificação Inteligente**

### **Filtro de Palavras-Chave (1ª camada)**
Identifica instantaneamente vagas **tech** e **non-tech** por palavras no título:

**Tech**: desenvolvedor, programador, software, backend, frontend, dados, devops, cloud, python, java, javascript, react, etc.

**Non-tech**: limpeza, motorista, segurança, vendas, atendente, recepção, porteiro, etc.

### **IA Gemini (2ª camada)**
Vagas ambíguas são enviadas para a Gemini 2.5 Flash que analisa contexto e decide com precisão.

---

## 👤 **Autor**

**Pedro Ryan Magalhães**  
GitHub: [@PedroRyanMagalhaes](https://github.com/PedroRyanMagalhaes)

---

**⚡ Desenvolvido com Python + IA Gemini + Resend**
