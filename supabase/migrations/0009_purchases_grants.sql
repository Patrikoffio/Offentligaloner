-- 0009: Rättighetsfix för purchases (rapportbryggans skrivväg).
--
-- purchases är v2:s första server-side SKRIVväg. 0001 gav bara
-- `grant select ... to service_role`, så webhooken (service_role) fick
-- "permission denied" vid INSERT. Här ges service_role select/insert/update.
--
-- Samtidigt härdas purchases som de känsliga tabellerna i 0003: purchases
-- innehåller kund-e-post (PII) och får ALDRIG nås av anon/authenticated. RLS är
-- redan på utan policies (default-deny), men vi återkallar även grants:en
-- (djupförsvar). All åtkomst sker server-side via service_role.
--
-- Hård regel 2: individ-/persondata exponeras aldrig publikt.

revoke all privileges on table purchases from anon, authenticated;

grant select, insert, update on table purchases to service_role;
