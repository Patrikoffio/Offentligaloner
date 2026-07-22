-- 0006: Matview title_employer_all – per (titel, arbetsgivare): antal anställda
-- (heltidsräknat, samma bas som lönestatistiken) + utlämningsdatum, UTAN lönevärden.
--
-- Driver två saker på yrkessidan:
--   (a) Källhänvisning: vilka arbetsgivare som lämnat ut uppgifter + datumspann.
--   (b) Arbetsgivare med n<5: visa antal anställda men INGA lönesiffror
--       ("underlag för litet för lönestatistik"). n≥5-grinden för lönevärden
--       ligger kvar oförändrad i title_employer_stats.
--
-- Innehåller inga percentiler/medellöner → ingen lönestatistik under n=5 läcker.

create materialized view title_employer_all as
select
  rt.generalized_title_id,
  sr.employer_id,
  e.name                                as employer_name,
  sr.collection_year,
  count(*)                              as n,             -- heltidsräknade poster
  max(sd.received_at)                   as received_at,
  max(sd.salary_date)                   as salary_date
from salary_records sr
join raw_titles rt        on rt.id = sr.raw_title_id
join employers e         on e.id  = sr.employer_id
join source_documents sd on sd.id = sr.source_document_id
where sr.flagged = false
  and rt.generalized_title_id is not null
  and sr.monthly_salary_fulltime is not null
group by rt.generalized_title_id, sr.employer_id, e.name, sr.collection_year;

create unique index on title_employer_all (generalized_title_id, employer_id, collection_year);
create index on title_employer_all (generalized_title_id);
