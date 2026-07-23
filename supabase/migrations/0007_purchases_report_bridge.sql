-- 0007: Utöka purchases för rapportbryggan (variant C, leveransrobust).
--
-- Rapporten levereras via en tokenserad URL (report_token); webhooken
-- (checkout.session.completed / async_payment_succeeded) är sanningskälla och
-- skriver raden idempotent på stripe_session. Rapportinnehållet byggs ur
-- matviews (n≥5) – ingen individdata lagras här.
--
-- Befintliga kolumner: id, email, product, generalized_title_id, employer_id,
-- amount_sek, stripe_session, created_at.

alter table purchases
  add column if not exists report_token   text,        -- slumpad access-token (rapport-URL)
  add column if not exists selected_slugs text[],       -- valda titlar (max 5), rapportens innehåll
  add column if not exists status         text,         -- pending | paid | failed | cancelled
  add column if not exists expires_at     timestamptz;  -- giltig t.o.m. (köp + 3 mån)

-- report_token unik när den är satt (Postgres tillåter flera NULL i unikt index).
create unique index if not exists purchases_report_token_key
  on purchases (report_token);

-- Idempotens i webhooken: en purchases-rad per Stripe-session.
create unique index if not exists purchases_stripe_session_key
  on purchases (stripe_session);

-- Snabb uppslagning för /rapport/skicka-igen (giltiga länkar per e-post).
create index if not exists purchases_email_idx on purchases (email);

-- Tillåtna statusvärden (nullbar tills webhooken sätter status).
do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'purchases_status_check'
  ) then
    alter table purchases
      add constraint purchases_status_check
      check (status is null or status in ('pending','paid','failed','cancelled'));
  end if;
end $$;
