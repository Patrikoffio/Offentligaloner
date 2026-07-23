-- 0008: Rapporten avgränsas till valda arbetsgivare (max 5 kommuner/regioner)
-- utöver valda yrken (max 5). selected_slugs finns sedan 0007; här läggs de valda
-- arbetsgivarnas id till. Webhooken (sanningskälla) skriver båda ur Stripe-metadata.
-- Ingen individdata – bara referenser till employers(id).

alter table purchases
  add column if not exists selected_employers bigint[];  -- valda arbetsgivare (max 5)
