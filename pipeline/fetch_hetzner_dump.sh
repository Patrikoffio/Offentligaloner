#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Hämtar en färsk pg_dump av Django-databasen från gamla servern (Hetzner).
#
# SÄKERHET: SSH-lösenordet anges INTERAKTIVT vid ssh-prompten och sparas
# ALDRIG i denna fil, i git eller i miljövariabler. Skriptet innehåller inga
# hemligheter. Utdatan skrivs till data/dump/ som är gitignorad (persondata).
#
# Användning:
#   bash pipeline/fetch_hetzner_dump.sh [user@host] [utfil]
#   (standard: root@65.21.55.235 → data/dump/<datum>_fresh_salaries.dump)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

HOST="${1:-root@65.21.55.235}"
OUT="${2:-data/dump/$(date +%Y%m%d)_fresh_salaries.dump}"
mkdir -p "$(dirname "$OUT")"

echo "Ansluter till $HOST – skriv lösenordet när du blir tillfrågad…"

# Fjärrskriptet körs som postgres, hittar databasen som innehåller salary_salary
# och dumpar den i custom-format till stdout (→ lokal fil). Statusrader → stderr.
ssh -o StrictHostKeyChecking=accept-new "$HOST" 'sudo -u postgres bash -s' > "$OUT" <<'REMOTE'
set -e
DB=""
for d in $(psql -tAc "select datname from pg_database where datistemplate=false and datname <> 'postgres'"); do
  if [ "$(psql -d "$d" -tAc "select to_regclass('public.salary_salary') is not null")" = "t" ]; then
    DB="$d"; break
  fi
done
if [ -z "$DB" ]; then
  echo "FEL: hittade ingen databas med tabellen salary_salary" >&2
  exit 3
fi
echo "Dumpar databas: $DB" >&2
pg_dump -Fc "$DB"
REMOTE

echo "Klar: $OUT ($(du -h "$OUT" | cut -f1))"
