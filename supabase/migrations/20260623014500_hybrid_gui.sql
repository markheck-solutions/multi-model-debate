-- Hybrid GUI support for public demos, saved panels, run history, and reports.
-- This schema intentionally stores no raw API keys, subscription tokens, or credentials.

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.panel_presets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  panel jsonb not null,
  is_public boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint panel_presets_name_not_blank check (length(trim(name)) > 0),
  constraint panel_presets_panel_object check (jsonb_typeof(panel) = 'object')
);

create table if not exists public.demo_runs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references auth.users(id) on delete cascade,
  question text not null,
  panel jsonb not null,
  status text not null default 'completed',
  final_report text not null,
  share_slug text unique,
  is_public boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint demo_runs_question_not_blank check (length(trim(question)) > 0),
  constraint demo_runs_panel_object check (jsonb_typeof(panel) = 'object'),
  constraint demo_runs_status_known check (
    status in ('ready', 'running', 'completed', 'failed', 'cancelled')
  )
);

create table if not exists public.run_events (
  id bigserial primary key,
  run_id uuid not null references public.demo_runs(id) on delete cascade,
  phase text not null,
  status text not null,
  title text not null,
  detail text not null,
  progress integer not null,
  created_at timestamptz not null default timezone('utc', now()),
  constraint run_events_progress_range check (progress between 0 and 100),
  constraint run_events_phase_known check (
    phase in ('build', 'critique', 'debate', 'judge', 'final')
  ),
  constraint run_events_status_known check (
    status in ('ready', 'running', 'completed', 'failed', 'cancelled')
  )
);

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create trigger panel_presets_set_updated_at
before update on public.panel_presets
for each row execute function public.set_updated_at();

create trigger demo_runs_set_updated_at
before update on public.demo_runs
for each row execute function public.set_updated_at();

alter table public.profiles enable row level security;
alter table public.panel_presets enable row level security;
alter table public.demo_runs enable row level security;
alter table public.run_events enable row level security;

create policy "profiles_select_own"
on public.profiles for select
using ((select auth.uid()) = id);

create policy "profiles_insert_own"
on public.profiles for insert
with check ((select auth.uid()) = id);

create policy "profiles_update_own"
on public.profiles for update
using ((select auth.uid()) = id)
with check ((select auth.uid()) = id);

create policy "panel_presets_select_visible"
on public.panel_presets for select
using (is_public or (select auth.uid()) = owner_id);

create policy "panel_presets_insert_own"
on public.panel_presets for insert
with check ((select auth.uid()) = owner_id);

create policy "panel_presets_update_own"
on public.panel_presets for update
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

create policy "panel_presets_delete_own"
on public.panel_presets for delete
using ((select auth.uid()) = owner_id);

create policy "demo_runs_select_visible"
on public.demo_runs for select
using (is_public or (select auth.uid()) = owner_id);

create policy "demo_runs_insert_own"
on public.demo_runs for insert
with check ((select auth.uid()) = owner_id);

create policy "demo_runs_update_own"
on public.demo_runs for update
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

create policy "demo_runs_delete_own"
on public.demo_runs for delete
using ((select auth.uid()) = owner_id);

create policy "run_events_select_visible_run"
on public.run_events for select
using (
  exists (
    select 1
    from public.demo_runs
    where demo_runs.id = run_events.run_id
      and (demo_runs.is_public or (select auth.uid()) = demo_runs.owner_id)
  )
);

create policy "run_events_insert_own_run"
on public.run_events for insert
with check (
  exists (
    select 1
    from public.demo_runs
    where demo_runs.id = run_events.run_id
      and (select auth.uid()) = demo_runs.owner_id
  )
);
