-- GH-emails-mxf initial schema
-- Run this in Supabase SQL Editor on the "greenhouse" project.

-- ──────────────────────────────────────────────
-- emails
-- ──────────────────────────────────────────────
create table if not exists emails (
  id                 uuid        primary key default gen_random_uuid(),
  outlook_entry_id   text        not null,
  outlook_store_id   text        not null,
  subject            text,
  sender_name        text,
  sender_email       text,
  received_at        timestamptz,
  body_preview       text,
  unread             boolean,
  tier               text        check (tier in ('P0','P1','P2','P3')),
  reason             text,
  suggested_action   text,
  draft_reply        text,
  status             text        not null default 'active',
  synced_at          timestamptz not null default now(),
  unique (outlook_entry_id, outlook_store_id)
);

create index if not exists emails_received_at_idx on emails (received_at desc);
create index if not exists emails_tier_idx        on emails (tier);
create index if not exists emails_status_idx      on emails (status);

-- ──────────────────────────────────────────────
-- action_queue
-- ──────────────────────────────────────────────
create table if not exists action_queue (
  id            uuid        primary key default gen_random_uuid(),
  email_id      uuid        references emails (id) on delete cascade,
  action        text        not null check (action in ('archive','open_on_work_computer','mark_read','move_to_folder')),
  payload       jsonb       not null default '{}',
  status        text        not null default 'pending' check (status in ('pending','processing','completed','failed')),
  error         text,
  requested_at  timestamptz not null default now(),
  processed_at  timestamptz
);

create index if not exists action_queue_status_idx     on action_queue (status);
create index if not exists action_queue_email_id_idx   on action_queue (email_id);
create index if not exists action_queue_requested_idx  on action_queue (requested_at desc);

-- ──────────────────────────────────────────────
-- agent_heartbeat  (single row, id=1)
-- ──────────────────────────────────────────────
create table if not exists agent_heartbeat (
  id               int         primary key default 1,
  last_seen_at     timestamptz not null default now(),
  status           text,
  current_version  text,
  last_error       text
);

-- Seed the single heartbeat row so the agent can upsert it.
insert into agent_heartbeat (id, status) values (1, 'initializing')
  on conflict (id) do nothing;

-- ──────────────────────────────────────────────
-- triage_runs
-- ──────────────────────────────────────────────
create table if not exists triage_runs (
  id              uuid        primary key default gen_random_uuid(),
  started_at      timestamptz not null default now(),
  finished_at     timestamptz,
  emails_scanned  int         not null default 0,
  emails_synced   int         not null default 0,
  p0_count        int         not null default 0,
  p1_count        int         not null default 0,
  p2_count        int         not null default 0,
  p3_count        int         not null default 0,
  error           text
);

create index if not exists triage_runs_started_idx on triage_runs (started_at desc);

-- ──────────────────────────────────────────────
-- Row-Level Security (single-user MVP)
-- Enable RLS but allow all operations via the anon key.
-- For production, replace with user-scoped policies.
-- ──────────────────────────────────────────────
alter table emails          enable row level security;
alter table action_queue    enable row level security;
alter table agent_heartbeat enable row level security;
alter table triage_runs     enable row level security;

-- emails: allow read for anon (web), full access for service_role (agent)
create policy "anon_read_emails" on emails
  for select using (true);

create policy "service_write_emails" on emails
  for all using (auth.role() = 'service_role');

-- action_queue: anon can insert (web creates actions) and read; agent uses service_role
create policy "anon_read_action_queue" on action_queue
  for select using (true);

create policy "anon_insert_action_queue" on action_queue
  for insert with check (true);

create policy "service_all_action_queue" on action_queue
  for all using (auth.role() = 'service_role');

-- agent_heartbeat: anon read only
create policy "anon_read_heartbeat" on agent_heartbeat
  for select using (true);

create policy "service_all_heartbeat" on agent_heartbeat
  for all using (auth.role() = 'service_role');

-- triage_runs: anon read only
create policy "anon_read_triage_runs" on triage_runs
  for select using (true);

create policy "service_all_triage_runs" on triage_runs
  for all using (auth.role() = 'service_role');
