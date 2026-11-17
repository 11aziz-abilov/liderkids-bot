-- LiderKids + LiderKids Nazorat bot: Supabase schema (secure version)
-- All writes go through the server (service_role key). The public anon key
-- can only read leaderboard columns of students: no phone numbers, no codes.

create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  grade integer not null default 1 check (grade between 1 and 4),
  region text not null default 'Toshkent shahri',
  school text default '',
  parent_name text not null default '',
  parent_phone text not null,
  plan text not null default 'free',
  coins integer not null default 0 check (coins >= 0),
  xp integer not null default 0 check (xp >= 0),
  streak integer not null default 0 check (streak >= 0),
  last_active_at timestamptz default now(),
  created_at timestamptz default now()
);
create index if not exists idx_students_parent_phone on public.students(parent_phone);
create index if not exists idx_students_grade on public.students(grade);

create table if not exists public.results (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  subject text not null,
  type text not null check (type in ('quiz', 'lesson', 'puzzle')),
  correct integer not null default 0,
  total integer not null default 0,
  coins_earned integer not null default 0,
  created_at timestamptz default now()
);
create index if not exists idx_results_student_id on public.results(student_id);
create index if not exists idx_results_created_at on public.results(created_at);

create table if not exists public.link_codes (
  id uuid primary key default gen_random_uuid(),
  code varchar(6) not null,
  student_id uuid not null references public.students(id) on delete cascade,
  expires_at timestamptz not null,
  used boolean not null default false,
  created_at timestamptz default now()
);
create index if not exists idx_link_codes_code on public.link_codes(code);
create index if not exists idx_link_codes_student_id on public.link_codes(student_id);

create table if not exists public.parent_links (
  id uuid primary key default gen_random_uuid(),
  telegram_chat_id bigint not null,
  student_id uuid not null references public.students(id) on delete cascade,
  created_at timestamptz default now(),
  unique (telegram_chat_id, student_id)
);
create index if not exists idx_parent_links_chat_id on public.parent_links(telegram_chat_id);
create index if not exists idx_parent_links_student_id on public.parent_links(student_id);

alter table public.students enable row level security;
alter table public.results enable row level security;
alter table public.link_codes enable row level security;
alter table public.parent_links enable row level security;

revoke all on public.students, public.results, public.link_codes, public.parent_links from anon, authenticated;
grant all on public.students, public.results, public.link_codes, public.parent_links to service_role;

grant select (id, name, grade, region, school, coins, xp, streak) on public.students to anon, authenticated;
drop policy if exists "Public leaderboard read" on public.students;
create policy "Public leaderboard read" on public.students for select to anon, authenticated using (true);
