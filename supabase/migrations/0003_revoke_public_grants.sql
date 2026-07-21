-- 0003: Härda API-åtkomst – återkalla anon/authenticated-privilegier på
-- individ- och processdata (djupförsvar utöver RLS).
--
-- Bakgrund: RLS är på för dessa tabeller och det finns inga policies, så
-- default-deny skyddar redan individdata via PostgREST. Men de breda grants:en
-- (SELECT/INSERT/UPDATE/DELETE/TRUNCATE) betyder att skyddet enbart vilar på att
-- RLS förblir på och policy-fritt. Om RLS någon gång stängs av, eller en policy
-- läggs till av misstag, skulle individ-/processdata annars kunna nås via API:et.
-- Vi återkallar därför allt för anon/authenticated på de känsliga tabellerna.
-- service_role (används av statisk generering) och postgres/ägare berörs INTE.
--
-- Hård regel 2: individdata exponeras aldrig publikt.

revoke all privileges on table salary_records      from anon, authenticated;
revoke all privileges on table raw_titles          from anon, authenticated;
revoke all privileges on table collection_requests from anon, authenticated;
revoke all privileges on table source_documents    from anon, authenticated;
