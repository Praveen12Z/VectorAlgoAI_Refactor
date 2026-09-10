create table if not exists public.research_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  record_hash text not null,
  strategy_name text not null,
  market text not null,
  timeframe text not null,
  contract_version text not null,
  contract_fingerprint text,
  rules_fingerprint text,
  strategy_yaml text not null,
  source_text text not null default '',
  evidence_engine_version text not null,
  execution_assumptions jsonb not null,
  data_start text,
  data_end text,
  data_bars integer not null default 0,
  full_metrics jsonb not null,
  development_metrics jsonb not null,
  holdout_metrics jsonb not null,
  validation_status text not null,
  validation_passed boolean not null default false,
  regime_analysis jsonb not null default '{}'::jsonb,
  trade_records jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (user_id, record_hash)
);

alter table public.research_records enable row level security;

drop policy if exists "Users insert their own research records" on public.research_records;
create policy "Users insert their own research records" on public.research_records
  for insert to authenticated with check (auth.uid() = user_id);

drop policy if exists "Users read their own research records" on public.research_records;
create policy "Users read their own research records" on public.research_records
  for select to authenticated using (auth.uid() = user_id);

revoke all on public.research_records from anon;
revoke update, delete on public.research_records from authenticated;
grant select, insert on public.research_records to authenticated;
