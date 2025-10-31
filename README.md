# 🎯 Jobs Tech Campinas - MVP

Sistema inteligente automatizado para **coleta e filtragem** de vagas de tecnologia em Campinas e região, utilizando **IA Gemini** para classificação automática.

---

## 🚀 **Funcionalidades**

✅ Web scraping de múltiplas empresas simultaneamente  
✅ **Filtragem inteligente com IA Gemini** (identifica automaticamente vagas de tech)  
✅ Armazenamento local em SQLite (apenas vagas relevantes)  
✅ Sistema modular e escalável  
✅ Prevenção de duplicatas  
✅ Logs detalhados do processo  

---

## 📁 **Estrutura do Projeto**

```
019_Jobs/
├── src/
│   ├── ai/                      # 🤖 Módulo de IA
│   │   ├── __init__.py
│   │   └── gemini_filter.py     # Filtro inteligente com Gemini API
│   ├── database/                # 💾 Banco de dados
│   │   ├── __init__.py
│   │   └── database.py          # Funções SQLite
│   ├── scrapers/                # 🕷️ Web Scrapers
│   │   
│   └── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py              # ⚙️ Configurações (API keys, empresas ativas)
├── data/
│   ├── Empresas.txt
│   ├── Empresas_Extras.txt
│   ├── PrimeirasEmpresas.txt
│   └── vagas.db                 # 📊 Banco SQLite (gerado automaticamente)
├── app.py                       # 🎬 Arquivo principal
├── requirements.txt
└── README.md
```

---

## 🔄 **Fluxo de Funcionamento**

```
┌─────────────────┐
│   Inicializa    │ Prepara banco de dados
│    Sistema      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Web Scraping  │ Coleta vagas das empresas
│  (Bosch, CI&T,  │ (título, descrição, link, etc)
│   Dell, etc)    │
└────────┬────────┘
         │
         ↓ (50 vagas coletadas)
         │
┌─────────────────┐
│  🤖 IA Gemini   │ Analisa cada vaga:
│   Classifica    │ ✅ "Dev Python" → TECH
│                 │ ❌ "Analista RH" → Descarta
└────────┬────────┘
         │
         ↓ (30 vagas tech filtradas)
         │
┌─────────────────┐
│  Salva no BD    │ Apenas vagas de tecnologia
│   (vagas.db)    │ Evita duplicatas
└─────────────────┘
```



## 📊 **Estrutura do Banco de Dados**

Tabela `vagas`:
```sql
CREATE TABLE vagas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    empresa TEXT NOT NULL,
    localizacao TEXT,
    link TEXT UNIQUE,
    descricao TEXT,
    data_coleta DATE,
    is_tech BOOLEAN DEFAULT 1
)
```

---

## 📈 **Próximas Melhorias (Roadmap)**

- [ ] 📧 Envio de vagas por e-mail
- [ ] 💬 Notificações via Telegram
- [ ] 📊 Dashboard web com estatísticas
- [ ] 🔄 Cache de decisões da IA
- [ ] ⚡ Análise em lote paralela
- [ ] 🎯 Filtros personalizados (seniority, salário, etc)

---


## 👤 **Autor**

**Pedro Ryan Magalhães**  
GitHub: [@PedroRyanMagalhaes](https://github.com/PedroRyanMagalhaes)

---


**⚡ Desenvolvido com Python + IA Gemini**
