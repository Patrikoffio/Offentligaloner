-- 0004: Ta bort UNIQUE(title) på generalized_titles.
--
-- Slug är den unika SEO-nyckeln (bevaras exakt). Titeln är publikt visningsnamn
-- och behöver INTE vara unik: efter titelstädningen på källsajten finns flera
-- distinkta slugs som delar samma visningsnamn (t.ex. typo-varianter
-- 'enhetschef-fatighet'/'enhetschef-fastighet', eller dag/natt-varianter av
-- 'Vårdare (Gruppboende)'). Alla live-slugs ska ha egen sida (SEO-kontinuitet),
-- så unik-kravet på title tas bort. slug förblir unik.

alter table generalized_titles drop constraint if exists generalized_titles_title_key;
