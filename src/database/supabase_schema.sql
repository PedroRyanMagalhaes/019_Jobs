-- ================================================
-- Schema 019Jobs - Supabase
-- Cole todo este conteúdo no SQL Editor do Supabase
-- ================================================

-- Tabela principal de vagas
CREATE TABLE IF NOT EXISTS vagas (
    id          BIGSERIAL PRIMARY KEY,
    empresa     TEXT NOT NULL,
    titulo      TEXT NOT NULL,
    localizacao TEXT,
    modelo_trabalho TEXT,
    url_vaga    TEXT NOT NULL UNIQUE,
    classificacao_ia TEXT,
    data_coleta TEXT NOT NULL,
    ultima_atualizacao TEXT NOT NULL
);

-- Tabela de vagas removidas (histórico)
CREATE TABLE IF NOT EXISTS vagas_removidas (
    id              BIGSERIAL PRIMARY KEY,
    empresa         TEXT NOT NULL,
    titulo          TEXT NOT NULL,
    localizacao     TEXT,
    modelo_trabalho TEXT,
    url_vaga        TEXT NOT NULL,
    classificacao_ia TEXT,
    data_coleta     TEXT NOT NULL,
    data_remocao    TEXT NOT NULL,
    motivo_remocao  TEXT DEFAULT 'Não encontrada no último scraping'
);

-- Tabela de vagas filtradas pelo funil de IA
CREATE TABLE IF NOT EXISTS vagas_filtradas (
    id                 BIGSERIAL PRIMARY KEY,
    empresa            TEXT NOT NULL,
    titulo             TEXT NOT NULL,
    localizacao        TEXT,
    modelo_trabalho    TEXT,
    url_vaga           TEXT NOT NULL UNIQUE,
    classificacao_ia   TEXT,
    data_coleta        TEXT NOT NULL,
    ultima_atualizacao TEXT NOT NULL,
    classificacao_funil TEXT NOT NULL
);

-- Tabela de assinantes da newsletter
CREATE TABLE IF NOT EXISTS assinantes (
    id                  BIGSERIAL PRIMARY KEY,
    email               TEXT UNIQUE NOT NULL,
    nome                TEXT,
    data_inscricao      TIMESTAMPTZ DEFAULT NOW(),
    ativo               BOOLEAN DEFAULT TRUE,
    token_cancelamento  TEXT UNIQUE
);
