-- 0010: Täckningsredovisning – lägg till n_raw i title_national_stats.
--
-- n (n_ft) = antal poster med KÄND heltidslön (monthly_salary_fulltime not null),
--            oförändrad – grindar fortsatt publicering (HAVING >= 5).
-- n_raw    = antal poster med månadslön satt (monthly_salary not null), dvs.
--            underlaget FÖRE heltidsfiltret. n_ft <= n_raw. Driver
--            täckningsraden på yrkessidan + i lönerapporten.
--
-- OFÖRÄNDRAT (verifierat mot 0002): percentiler, mean_salary, n och tröskeln
-- n_ft >= 5. WHERE-villkoret "monthly_salary_fulltime IS NOT NULL" tas bort så
-- att månadsavlönade poster utan känd grad kommer med i gruppen och kan räknas
-- av n_raw – men percentile_cont/avg/n räknar bara icke-NULL heltidsvärden, så
-- de publicerade talen är bit-för-bit identiska. Endast n_raw är nytt.

DROP MATERIALIZED VIEW title_national_stats;

CREATE MATERIALIZED VIEW title_national_stats AS
SELECT
  rt.generalized_title_id,
  sr.collection_year,
  count(*) FILTER (WHERE sr.monthly_salary_fulltime IS NOT NULL)          AS n,
  count(*) FILTER (WHERE sr.monthly_salary IS NOT NULL)                   AS n_raw,
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

-- Behörigheter (speglar 0002)
GRANT SELECT ON title_national_stats TO anon, authenticated, service_role;
