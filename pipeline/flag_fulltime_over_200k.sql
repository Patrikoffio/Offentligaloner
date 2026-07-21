-- Datakvalitet: flagga oflaggade rader vars heltidsekvivalenta månadslön
-- överstiger 200 000 kr. Dessa uppstår när en normal lön delas med en låg
-- sysselsättningsgrad (heltidslön = lön / grad) och är inte rimliga heltidslöner.
-- Flaggning (inte cappning) exkluderar dem ur de publika vyerna (WHERE flagged=false).
-- Jfr importregeln "månadslön > 200 000 → flagga".

update salary_records
set flagged = true,
    flag_reason = 'Heltidslön (heltidsekvivalent) > 200000 – låg sysselsättningsgrad'
where flagged = false
  and monthly_salary_fulltime is not null
  and monthly_salary_fulltime > 200000;
