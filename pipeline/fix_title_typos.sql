-- Rättning av visningsnamn (title) i generalized_titles inför go-live.
-- ENDAST title-kolumnen. slug lämnas orörd (SEO). n<5-rader påverkas inte.
-- Matchning på exakt nuvarande sträng → 1 rad var. Appliceras moln + lokalt.

-- ── Strukturella (obalanserad parentes / dubbla mellanslag / avslutande blanksteg) ──
update generalized_titles set title = 'Assistent/Fritidspedagog'
  where title = 'Assistent/Fritidspedagog)';
update generalized_titles set title = 'Barnskötare/Fritidsledare/Elevassistent'
  where title = 'Barnskötare/Fritidsledare/Elevassistent)';
update generalized_titles set title = 'Bibliotekarie/Webbredaktör'
  where title = 'Bibliotekarie/Webbredaktör)';
update generalized_titles set title = 'Ämneslärare (7-9, Franska)'
  where title = 'Ämneslärare (7-9,  Franska)';
update generalized_titles set title = 'Lärare (Trä-/Metallslöjd) - Obehörig/Outbildad'
  where title = 'Lärare (Trä-/Metallslöjd)  - Obehörig/Outbildad';
update generalized_titles set title = 'Stödassistent/Vårdare'
  where title = 'Stödassistent/Vårdare ';

-- ── Stavfel (Psykatrisk→Psykiatrisk, Adminisratör→Administratör, Modermål→Modersmål) ──
update generalized_titles set title = 'Handledare (Psykiatrisk Omvårdnad)'
  where title = 'Handledare (Psykatrisk Omvårdnad)';
update generalized_titles set title = 'HR- och Löneadministratör'
  where title = 'HR- och Löneadminisratör';
update generalized_titles set title = 'Lärarassistent/Modersmålslärare'
  where title = 'Lärarassistent/Modermålslärare';
update generalized_titles set title = 'Modersmålslärare (Förskola)'
  where title = 'Modermålslärare (Förskola)';
update generalized_titles set title = 'Modersmålslärare/Studiehandledare'
  where title = 'Modermålslärare/Studiehandledare';
update generalized_titles set title = 'Modersmålslärare/Tolk'
  where title = 'Modermålslärare/Tolk';

-- ── Kvalite→Kvalité (godkänd) ──
update generalized_titles set title = 'Chef (Kvalité/Utveckling)'
  where title = 'Chef (Kvalite/Utveckling)';
