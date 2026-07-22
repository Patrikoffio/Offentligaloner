-- 0005: Spårbarhet för kategorigranskning.
--
-- generalized_titles.category_reviewed = false markerar titlar vars kategori
-- satts med osäkert omdöme (gränsfall) och bör omprövas senare. Default true
-- (befintliga + trygga klassningar räknas som granskade).

alter table generalized_titles
  add column if not exists category_reviewed boolean not null default true;
