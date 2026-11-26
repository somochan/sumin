-- Run this once in Supabase Dashboard → SQL Editor when the project is reachable.
-- Each authenticated user can only read, create, or delete their own saved papers.

create table if not exists public.saved_papers (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    openalex_id text not null,
    title text not null,
    authors text,
    publication_year smallint,
    citations integer not null default 0 check (citations >= 0),
    source text,
    paper_url text,
    domain text not null,
    saved_at timestamptz not null default now(),
    unique (user_id, openalex_id)
);

create index if not exists saved_papers_user_saved_at_idx
    on public.saved_papers (user_id, saved_at desc);

alter table public.saved_papers enable row level security;

grant select, insert, delete on public.saved_papers to authenticated;

create policy "Users can read their saved papers"
    on public.saved_papers for select to authenticated
    using ((select auth.uid()) = user_id);

create policy "Users can save their own papers"
    on public.saved_papers for insert to authenticated
    with check ((select auth.uid()) = user_id);

create policy "Users can delete their saved papers"
    on public.saved_papers for delete to authenticated
    using ((select auth.uid()) = user_id);
