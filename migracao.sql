-- =============================================================================
-- MIGRAÇÃO VALORPRO IA — rodar no SQL Editor do Supabase ANTES do deploy
-- Cria as tabelas de proventos e de evolução patrimonial (antes eram CSVs
-- locais que o Streamlit Cloud apagava a cada deploy).
-- =============================================================================

-- 1. PROVENTOS (dividendos, JCP, rendimentos de FII)
create table if not exists public.proventos (
    id               bigint generated always as identity primary key,
    usuario_id       uuid not null,
    data_recebimento date not null,
    ticker           text not null,
    valor            numeric(14,2) not null check (valor > 0),
    tipo             text not null default 'Rendimento FII',
    criado_em        timestamptz not null default now()
);

create index if not exists idx_proventos_usuario
    on public.proventos (usuario_id, data_recebimento desc);

-- 2. EVOLUÇÃO PATRIMONIAL (uma foto por usuário por dia)
create table if not exists public.snapshots_patrimonio (
    id         bigint generated always as identity primary key,
    usuario_id uuid not null,
    data       date not null,
    aportado   numeric(16,2) not null default 0,
    mercado    numeric(16,2) not null default 0,
    unique (usuario_id, data)
);

create index if not exists idx_snapshots_usuario
    on public.snapshots_patrimonio (usuario_id, data);

-- =============================================================================
-- ⚠️ ALERTA DE ARQUITETURA (leia com atenção)
-- =============================================================================
-- O app usa a chave ANON do Supabase SEM Supabase Auth (o login é feito por
-- uma tabela "usuarios" própria). Isso significa que o RLS NÃO consegue saber
-- quem é o usuário logado — qualquer política por usuário fica impossível e,
-- na prática, as tabelas precisam estar abertas para "anon" para o app
-- funcionar. Consequência: quem tiver a URL + chave anon (que fica embutida
-- no app) consegue ler e escrever nas tabelas, incluindo "usuarios".
--
-- Mitigações já aplicadas no código:
--   * Senhas agora são salvas com HASH (scrypt/pbkdf2) — nunca mais texto puro.
--   * Updates/deletes de operações filtram por usuario_id.
--
-- Correção definitiva (recomendada como próximo passo):
--   * Migrar o login para o Supabase Auth (auth.users) e ativar RLS real:
--       alter table public.operacoes enable row level security;
--       create policy "dono" on public.operacoes
--         for all using (auth.uid() = usuario_id);
--     (e o equivalente para proventos, snapshots_patrimonio e usuarios)
-- =============================================================================
