-- 0011: Lönebegrepp – monthly_salary ÄR redan heltidslön i samtliga utlämnanden.
--
-- Bevisat (per arbetsgivare, titelkontrollerat): rå månadslön sjunker inte med
-- sysselsättningsgrad hos någon arbetsgivare (lägsta kvot deltid/heltid 0,78 mot
-- ~0,56 som utbetalt belopp skulle ge; 0 av 141 uppvisar utbetalt-signaturen).
-- Alltså är det överenskommen heltidslön, inte utbetalt belopp. Den tidigare
-- uppräkningen monthly_salary/employment_rate DUBBELRÄKNADE varje deltidare.
--
-- Fix: monthly_salary_fulltime = monthly_salary för överenskommen heltidslön.
-- Ett explicit lönebegrepp (salary_concept) bär märkningen per post så att en
-- framtida utbetalt-baserad källa (paid_out) räknas upp korrekt medan default
-- (agreed_fulltime) inte rörs. För ALL befintlig data (allt agreed_fulltime)
-- är resultatet bit-för-bit identiskt med den enkla formen monthly_salary.
--
-- Percentilberäkning, n>=5-tröskeln och redirecten är orörda. Kolumnen kan inte
-- ALTER:as – släpp beroende matvyer, byt kolumnuttryck, återskapa matvyerna.
--
-- Hela migrationen körs i EN transaktion. Alla steg är transaktionella i Postgres
-- (drop/create av materialiserad vy, drop/add av STORED generated column, vanlig
-- CREATE INDEX, GRANT). Inget CREATE INDEX CONCURRENTLY eller REFRESH ... CONCURRENTLY
-- används – de vore ej transaktionssäkra. Faller molnkörningen mitt i rullas allt
-- tillbaka; de 2 378 sidorna blir aldrig stående utan statistik.

BEGIN;

DROP MATERIALIZED VIEW title_national_stats;
DROP MATERIALIZED VIEW title_employer_stats;
DROP MATERIALIZED VIEW title_employer_all;

ALTER TABLE salary_records DROP COLUMN monthly_salary_fulltime;

-- Lönebegrepp per post. Default = överenskommen heltidslön (gäller allt hittills).
ALTER TABLE salary_records
  ADD COLUMN salary_concept text NOT NULL DEFAULT 'agreed_fulltime'
    CHECK (salary_concept IN ('agreed_fulltime','paid_out'));

-- Heltidslön: agreed_fulltime = beloppet rakt av; paid_out = räkna upp med grad.
-- Timavlönade (monthly_salary NULL) förblir NULL – oförändrat.
ALTER TABLE salary_records
  ADD COLUMN monthly_salary_fulltime numeric(10,2)
    GENERATED ALWAYS AS (
      CASE
        WHEN monthly_salary IS NULL THEN NULL
        WHEN salary_concept = 'paid_out' AND employment_rate > 0
          THEN round(monthly_salary / employment_rate, 2)
        ELSE monthly_salary
      END
    ) STORED;

-- title_employer_stats (oförändrad def, från 0002)
CREATE MATERIALIZED VIEW title_employer_stats AS
SELECT
  rt.generalized_title_id,
  sr.employer_id,
  sr.collection_year,
  count(*) FILTER (WHERE sr.monthly_salary_fulltime IS NOT NULL)          AS n,
  round(avg(sr.monthly_salary_fulltime))                                  AS mean_salary,
  percentile_cont(0.10) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS p10,
  percentile_cont(0.25) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS p25,
  percentile_cont(0.50) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS median,
  percentile_cont(0.75) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS p75,
  percentile_cont(0.90) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS p90,
  max(sd.received_at)                                                     AS latest_source_date
FROM salary_records sr
JOIN raw_titles rt ON rt.id = sr.raw_title_id
JOIN source_documents sd ON sd.id = sr.source_document_id
WHERE sr.flagged = false
  AND rt.generalized_title_id IS NOT NULL
  AND sr.monthly_salary_fulltime IS NOT NULL
GROUP BY rt.generalized_title_id, sr.employer_id, sr.collection_year
HAVING count(*) FILTER (WHERE sr.monthly_salary_fulltime IS NOT NULL) >= 5;

CREATE UNIQUE INDEX ON title_employer_stats (generalized_title_id, employer_id, collection_year);

-- title_national_stats: n_hourly (antal timavlönade i titeln) ersätter n_raw.
-- n_raw är DÖD men behålls additivt: den nuvarande produktionsdeployen läser
-- ännu n_raw, och den statiska yrkessidan byggs om under deployfönstret – utan
-- kolumnen skulle det bygget/den koden fela. Ingen NY kod läser n_raw.
-- Den tas bort i migration 0012 när koden som läser n_hourly är fullt utrullad.
CREATE MATERIALIZED VIEW title_national_stats AS
SELECT
  rt.generalized_title_id,
  sr.collection_year,
  count(*) FILTER (WHERE sr.monthly_salary_fulltime IS NOT NULL)          AS n,
  count(*) FILTER (WHERE sr.hourly_salary IS NOT NULL)                    AS n_hourly,
  count(*) FILTER (WHERE sr.monthly_salary IS NOT NULL)                   AS n_raw, -- DÖD, tas bort i 0012
  round(avg(sr.monthly_salary_fulltime))                                  AS mean_salary,
  percentile_cont(0.10) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS p10,
  percentile_cont(0.25) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS p25,
  percentile_cont(0.50) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS median,
  percentile_cont(0.75) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS p75,
  percentile_cont(0.90) WITHIN GROUP (ORDER BY sr.monthly_salary_fulltime) AS p90
FROM salary_records sr
JOIN raw_titles rt ON rt.id = sr.raw_title_id
WHERE sr.flagged = false
  AND rt.generalized_title_id IS NOT NULL
GROUP BY rt.generalized_title_id, sr.collection_year
HAVING count(*) FILTER (WHERE sr.monthly_salary_fulltime IS NOT NULL) >= 5;

CREATE UNIQUE INDEX ON title_national_stats (generalized_title_id, collection_year);

-- title_employer_all (oförändrad def, från 0006)
CREATE MATERIALIZED VIEW title_employer_all AS
SELECT
  rt.generalized_title_id,
  sr.employer_id,
  e.name                                AS employer_name,
  sr.collection_year,
  count(*)                              AS n,
  max(sd.received_at)                   AS received_at,
  max(sd.salary_date)                   AS salary_date
FROM salary_records sr
JOIN raw_titles rt        ON rt.id = sr.raw_title_id
JOIN employers e          ON e.id  = sr.employer_id
JOIN source_documents sd  ON sd.id = sr.source_document_id
WHERE sr.flagged = false
  AND rt.generalized_title_id IS NOT NULL
  AND sr.monthly_salary_fulltime IS NOT NULL
GROUP BY rt.generalized_title_id, sr.employer_id, e.name, sr.collection_year;

CREATE UNIQUE INDEX ON title_employer_all (generalized_title_id, employer_id, collection_year);
CREATE INDEX ON title_employer_all (generalized_title_id);

-- Behörigheter (speglar 0002/0006/0010): aggregat/antal, säkra att exponera.
GRANT SELECT ON title_national_stats TO anon, authenticated, service_role;
GRANT SELECT ON title_employer_stats TO anon, authenticated, service_role;
GRANT SELECT ON title_employer_all   TO anon, authenticated, service_role;

COMMIT;
