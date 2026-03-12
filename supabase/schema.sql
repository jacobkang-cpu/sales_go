-- Run this in Supabase SQL Editor

create table if not exists public.card_profiles (
  slug text primary key,
  name text not null,
  headline text not null,
  tags jsonb not null default '[]'::jsonb,
  phone text not null,
  email text not null,
  profile_subtitle text not null,
  news_label text not null,
  news_url text not null,
  instagram_label text not null,
  instagram_url text not null,
  image_data text not null default '',
  updated_at timestamptz not null default now()
);

create table if not exists public.card_events (
  id bigint generated always as identity primary key,
  slug text not null,
  event_type text not null,
  event_target text not null default '',
  page text not null default '',
  session_id text not null default '',
  ip text not null default '',
  user_agent text not null default '',
  referer text not null default '',
  created_at timestamptz not null default now()
);

create index if not exists idx_card_events_slug_created_at
  on public.card_events (slug, created_at desc);

create index if not exists idx_card_events_slug_type
  on public.card_events (slug, event_type);

insert into public.card_profiles (
  slug, name, headline, tags, phone, email, profile_subtitle,
  news_label, news_url, instagram_label, instagram_url, image_data
)
values (
  'woojin',
  '남우진',
  '애터미와 함께 노후 안정.',
  '["#성장파트너","#성장동력"]'::jsonb,
  '010-5429-9916',
  '%%',
  '파트너와 함께 성장합니다.',
  '애터미 소식',
  'https://www.atomy.kr/',
  '인스타그램',
  'https://www.instagram.com/',
  ''
)
on conflict (slug) do nothing;
