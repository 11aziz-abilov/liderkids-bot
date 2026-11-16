-- ========================================================
-- LiderKids & LiderKids Nazorat Bot — Supabase Schema
-- ========================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. STUDENTS TABLE
create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  grade integer not null default 1 check (grade between 1 and 4),
  region text not null default 'Toshkent shahri',
  school text default '',
  parent_name text not null default '',
  parent_phone text not null,
  coins integer not null default 0 check (coins >= 0),
  xp integer not null default 0 check (xp >= 0),
  streak integer not null default 0 check (streak >= 0),
  last_active_at timestamp with time zone default timezone('utc'::text, now()),
  created_at timestamp with time zone default timezone('utc'::text, now())
);

create index if not exists idx_students_parent_phone on public.students(parent_phone);
create index if not exists idx_students_grade on public.students(grade);

-- 2. RESULTS TABLE
create table if not exists public.results (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  subject text not null,
  type text not null check (type in ('quiz', 'lesson', 'puzzle')),
  correct integer not null default 0,
  total integer not null default 0,
  coins_earned integer not null default 0,
  created_at timestamp with time zone default timezone('utc'::text, now())
);

create index if not exists idx_results_student_id on public.results(student_id);
create index if not exists idx_results_created_at on public.results(created_at);

-- 3. LINK_CODES TABLE
create table if not exists public.link_codes (
  id uuid primary key default gen_random_uuid(),
  code varchar(6) not null,
  student_id uuid not null references public.students(id) on delete cascade,
  expires_at timestamp with time zone not null,
  used boolean not null default false,
  created_at timestamp with time zone default timezone('utc'::text, now())
);

create index if not exists idx_link_codes_code on public.link_codes(code);
create index if not exists idx_link_codes_student_id on public.link_codes(student_id);

-- 4. PARENT_LINKS TABLE
create table if not exists public.parent_links (
  id uuid primary key default gen_random_uuid(),
  telegram_chat_id bigint not null,
  student_id uuid not null references public.students(id) on delete cascade,
  created_at timestamp with time zone default timezone('utc'::text, now()),
  unique(telegram_chat_id, student_id)
);

create index if not exists idx_parent_links_chat_id on public.parent_links(telegram_chat_id);
create index if not exists idx_parent_links_student_id on public.parent_links(student_id);

-- ROW LEVEL SECURITY (RLS)
alter table public.students enable row level security;
alter table public.results enable row level security;
alter table public.link_codes enable row level security;
alter table public.parent_links enable row level security;

-- Policies for public / anon client access
create policy "Allow select students" on public.students
  for select using (true);

create policy "Allow insert students" on public.students
  for insert with check (true);

create policy "Allow update students" on public.students
  for update using (true);

create policy "Allow select results" on public.results
  for select using (true);

create policy "Allow insert results" on public.results
  for insert with check (true);

create policy "Allow select link codes" on public.link_codes
  for select using (true);

create policy "Allow insert link codes" on public.link_codes
  for insert with check (true);

create policy "Allow update link codes" on public.link_codes
  for update using (true);

create policy "Allow select parent links" on public.parent_links
  for select using (true);

create policy "Allow insert parent links" on public.parent_links
  for insert with check (true);
