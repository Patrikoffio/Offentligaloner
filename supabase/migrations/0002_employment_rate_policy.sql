-- Offentligalöner.se – migration 0002
-- Policy: employment_rate < 0.25 → monthly_salary_fulltime = NULL
--
-- Bakgrund: 1 152 rader har sysselsättningsgrad under 25 % (10–20 %).
-- Extrapolation till heltidslön för dessa ger missvisande värden (t.ex.
-- Skolläkare p90 372 000 → 185 000, Danspedagog 167 000 → 69 000).
-- Dessa individer arbetar ett fåtal timmar/månad; heltidsekvivalenten
-- är inte meningsfull och förvrider statistiken.
-- Regel: monthly_salary_fulltime sätts NULL om employment_rate < 0.25.
-- NULL-rate (okänd sysselsättningsgrad) ger fortsatt NULL – oförändrat.

-- Ny formel: employment_rate >= 0.25 → beräkna, annars NULL
-- (employment_rate = NULL: 0.25 >= NULL evalueras NULL → ELSE → NULL ✓)

-- Materialiserade vyer beror på kolumnen – måste tappas och återskapas
DROP MATERIALIZED VIEW title_national_stats;
DROP MATERIALIZED VIEW title_employer_stats;

ALTER TABLE salary_records DROP COLUMN monthly_salary_fulltime;

ALTER TABLE salary_records
  ADD COLUMN monthly_salary_fulltime numeric(10,2)
    GENERATED ALWAYS AS (
      CASE
        WHEN employment_rate >= 0.25
        THEN round(monthly_salary / employment_rate, 2)
        ELSE NULL
      END
    ) STORED;

-- Återskapa identiska vyer (kopierade från 0001_initial_schema.sql)
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

CREATE MATERIALIZED VIEW title_national_stats AS
SELECT
  rt.generalized_title_id,
  sr.collection_year,
  count(*) FILTER (WHERE sr.monthly_salary_fulltime IS NOT NULL)          AS n,
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
  AND sr.monthly_salary_fulltime IS NOT NULL
GROUP BY rt.generalized_title_id, sr.collection_year
HAVING count(*) FILTER (WHERE sr.monthly_salary_fulltime IS NOT NULL) >= 5;

CREATE UNIQUE INDEX ON title_national_stats (generalized_title_id, collection_year);

-- Behörigheter (speglar 0001)
GRANT SELECT ON title_employer_stats TO anon, authenticated, service_role;
GRANT SELECT ON title_national_stats  TO anon, authenticated, service_role;
