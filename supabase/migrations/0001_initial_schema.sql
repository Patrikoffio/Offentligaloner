-- Offentligalöner.se – schema v2 (anpassat efter befintlig produktionsdata)
-- Postgres / Supabase. supabase/migrations/0001_initial_schema.sql
--
-- Bakgrund: befintlig Django-databas (salary_salary: ~501k rader 2024,
-- salary_generalizedtitle: 9 383 titlar med AI-beskrivningar, SEO-nyckelord och slugs).
-- Detta schema är målmodellen; migrationsskript flyttar in befintlig data.
--
-- Hårda regler:
--  * Slugs från salary_generalizedtitle BEVARAS EXAKT (SEO-kontinuitet).
--  * Sentineler (-1, 'Okänt', tomsträng) blir NULL vid migrering.
--  * Aggregat med n < 5 exponeras aldrig.
--  * Individdata exponeras aldrig via publika API:er utan separat beslut.

-- ============================================================
-- Arbetsgivare: kommuner, regioner, statliga myndigheter, kommunala bolag
-- ============================================================
create table employers (
  id                bigint generated always as identity primary key,
  name              text not null unique,             -- "Österåkers kommun"
  slug              text not null unique,
  employer_type     text not null check (employer_type in ('kommun','region','myndighet','bolag')),
  parent_id         bigint references employers(id),  -- bolag → ägarkommun
  municipality_code text,                             -- SCB kommunkod
  county            text,                             -- "Stockholms län" (som i befintlig data)
  county_code       text,
  org_number        text,
  include           boolean not null default true,    -- Myndigheter.xlsx "Ta med?"
  created_at        timestamptz not null default now()
);

-- ============================================================
-- Insamling: begäranden per arbetsgivare och år
-- Speglar kolumnerna i Kommunlista 2024/2025 – hela processloggen bor här.
-- ============================================================
create table collection_requests (
  id              bigint generated always as identity primary key,
  employer_id     bigint not null references employers(id),
  collection_year smallint not null,
  requested_at    date,
  received_at     date,
  case_number     text,                               -- ärendenummer hos arbetsgivaren
  status          text not null default 'planned' check (status in
                    ('planned','requested','reminded','processing',   -- "Skickat till handläggare"
                     'received','imported','refused','abandoned')),
  refusal_reason  text,                               -- "Skäl" vid avslag
  fee_required    boolean,                            -- "Taxa"
  fee_per_page    numeric(8,2),                       -- "Pris/sida"
  fee_estimated   numeric(10,2),                      -- "Bedömd kostnad"
  fee_paid        numeric(10,2),
  requires_eid    boolean,                            -- "E-Leg"
  physical_only   boolean,                            -- "Fysiskt" – vägrar digitalt
  notes           text,
  unique (employer_id, collection_year)
);

create table source_documents (
  id              bigint generated always as identity primary key,
  request_id      bigint not null references collection_requests(id),
  salary_date     date,                               -- lönestatistikens mätdatum
  file_reference  text not null,                      -- "Österåker 2024-03-16.xlsx"
  file_format     text,
  received_at     date,
  created_at      timestamptz not null default now()
);

-- ============================================================
-- Klassificering: AID (SKR) primärt, SSYK som valfri brygga
-- ============================================================
create table aid_labels (                             -- Etikettlista AID 2018: 252 koder
  aid_code        text primary key,                   -- "101010"
  label           text not null,                      -- "Ledning, övergripande"
  description     text,
  example_titles  text,
  ansvarskoder    text
);

-- Generaliserade titlar = befintliga salary_generalizedtitle, berikade.
-- Detta är sajtens publika yrkesbegrepp och URL-struktur.
create table generalized_titles (
  id              bigint generated always as identity primary key,
  title           text not null unique,               -- "Förskollärare"
  slug            text not null unique,               -- BEVARAS från befintlig databas
  ai_description  text,
  seo_keywords    text[],
  similar_jobs    text[],
  category        text,                               -- Grupper.txt: "Vård och Omsorg" ...
  aid_code        text references aid_labels(aid_code),
  ssyk_code       text                                -- valfri brygga mot SCB
);

-- Råtitlar: arbetsgivarens exakta sträng → generaliserad titel
create table raw_titles (
  id                    bigint generated always as identity primary key,
  employer_id           bigint references employers(id),  -- null = generell mappning
  raw_title             text not null,
  generalized_title_id  bigint references generalized_titles(id),
  mapping_method        text check (mapping_method in ('manual','rule','ai')),
  mapping_confidence    numeric(3,2),
  reviewed              boolean not null default false,
  unique (employer_id, raw_title)
);

-- Anställningstyp: samma mönster – rå sträng per arbetsgivare, normaliserad kategori
-- (verklig data: "1 Tillsvidare", "1 (Tills vidare)", "2 Vikariat", "SÄVATIM ..." osv)
create table employment_type_mappings (
  id              bigint generated always as identity primary key,
  raw_value       text not null unique,
  normalized      text check (normalized in
                    ('tillsvidare','visstid','vikariat','timanstallning','provanstallning','ovrigt')),
  reviewed        boolean not null default false
);

-- ============================================================
-- Löneposter (individnivå – ALDRIG publik utan separat beslut)
-- Fälten följer "Tänka på till 2025": + ålder, förvaltning, tjänsteställe, AID.
-- ============================================================
create table salary_records (
  id                      bigint generated always as identity primary key,
  legacy_id               bigint unique,              -- id från gamla salary_salary
  employer_id             bigint not null references employers(id),
  source_document_id      bigint not null references source_documents(id),
  source_row_nr           integer,
  collection_year         smallint not null,
  salary_date             date,
  raw_title_id            bigint not null references raw_titles(id),
  aid_code                text references aid_labels(aid_code),  -- om utlämnad direkt
  monthly_salary          numeric(10,2),              -- null om timavlönad
  hourly_salary           numeric(10,2),              -- null om månadsavlönad
  salary_supplements      numeric(10,2),              -- lönetillägg om utlämnat
  employment_rate         numeric(4,3),               -- null = okänd (ALDRIG -1)
  employment_rate_assumed boolean not null default false,
  monthly_salary_fulltime numeric(10,2) generated always as
                            (round(monthly_salary / nullif(employment_rate,0), 2)) stored,
  employment_type_raw     text,
  gender                  text check (gender in ('K','M') or gender is null),  -- 'Okänt' → null
  age                     smallint,                   -- nytt 2025
  department              text,                       -- förvaltning, nytt 2025
  workplace               text,                       -- placering/tjänsteställe, nytt 2025
  tenure_years            numeric(4,1),               -- anställningstid om utlämnad
  flagged                 boolean not null default false,
  flag_reason             text,
  imported_at             timestamptz not null default now()
);
create index on salary_records (employer_id, collection_year);
create index on salary_records (raw_title_id);
create index on salary_records (aid_code);

-- ============================================================
-- Publika aggregat. HÅRD REGEL: n >= 5. Endast omräknad heltidslön.
-- ============================================================
create materialized view title_employer_stats as
select
  rt.generalized_title_id,
  sr.employer_id,
  sr.collection_year,
  count(*) filter (where sr.monthly_salary_fulltime is not null)          as n,
  round(avg(sr.monthly_salary_fulltime))                                  as mean_salary,
  percentile_cont(0.10) within group (order by sr.monthly_salary_fulltime) as p10,
  percentile_cont(0.25) within group (order by sr.monthly_salary_fulltime) as p25,
  percentile_cont(0.50) within group (order by sr.monthly_salary_fulltime) as median,
  percentile_cont(0.75) within group (order by sr.monthly_salary_fulltime) as p75,
  percentile_cont(0.90) within group (order by sr.monthly_salary_fulltime) as p90,
  max(sd.received_at)                                                     as latest_source_date
from salary_records sr
join raw_titles rt on rt.id = sr.raw_title_id
join source_documents sd on sd.id = sr.source_document_id
where sr.flagged = false
  and rt.generalized_title_id is not null
  and sr.monthly_salary_fulltime is not null
group by rt.generalized_title_id, sr.employer_id, sr.collection_year
having count(*) filter (where sr.monthly_salary_fulltime is not null) >= 5;

create unique index on title_employer_stats (generalized_title_id, employer_id, collection_year);

create materialized view title_national_stats as
select
  rt.generalized_title_id,
  sr.collection_year,
  count(*) filter (where sr.monthly_salary_fulltime is not null)          as n,
  round(avg(sr.monthly_salary_fulltime))                                  as mean_salary,
  percentile_cont(0.10) within group (order by sr.monthly_salary_fulltime) as p10,
  percentile_cont(0.25) within group (order by sr.monthly_salary_fulltime) as p25,
  percentile_cont(0.50) within group (order by sr.monthly_salary_fulltime) as median,
  percentile_cont(0.75) within group (order by sr.monthly_salary_fulltime) as p75,
  percentile_cont(0.90) within group (order by sr.monthly_salary_fulltime) as p90
from salary_records sr
join raw_titles rt on rt.id = sr.raw_title_id
where sr.flagged = false
  and rt.generalized_title_id is not null
  and sr.monthly_salary_fulltime is not null
group by rt.generalized_title_id, sr.collection_year
having count(*) filter (where sr.monthly_salary_fulltime is not null) >= 5;

create unique index on title_national_stats (generalized_title_id, collection_year);

-- ============================================================
-- Radnivåsäkerhet
-- ============================================================
alter table salary_records          enable row level security;
alter table raw_titles              enable row level security;
alter table source_documents        enable row level security;
alter table collection_requests     enable row level security;
alter table employment_type_mappings enable row level security;
alter table employers               enable row level security;
alter table generalized_titles      enable row level security;
alter table aid_labels              enable row level security;

create policy "public read employers"          on employers          for select using (true);
create policy "public read generalized_titles" on generalized_titles for select using (true);
create policy "public read aid_labels"         on aid_labels         for select using (true);
-- salary_records m.fl.: ingen publik policy → endast service role.

-- ============================================================
-- Fas 3: köp
-- ============================================================
create table purchases (
  id                   bigint generated always as identity primary key,
  email                text not null,
  product              text not null check (product in ('lonerapport','forhandlingsunderlag','datalicens')),
  generalized_title_id bigint references generalized_titles(id),
  employer_id          bigint references employers(id),
  amount_sek           numeric(10,2) not null,
  stripe_session       text,
  created_at           timestamptz not null default now()
);
alter table purchases enable row level security;
