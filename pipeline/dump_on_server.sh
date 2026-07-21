#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# PLAN B – körs MANUELLT PÅ gamla servern (efter att du ssh:at in själv).
#
#   ssh root@65.21.55.235          # du loggar in interaktivt
#   # klistra in / kör detta skript på servern:
#   bash dump_on_server.sh
#   # hämta sedan hem från din lokala dator:
#   scp root@65.21.55.235:/tmp/fresh_salaries_*.dump ./data/dump/
#
# Servern kör Docker Swarm (offlon_prod_*). Django-DB:n har en egen POSTGRES_USER
# (inte 'postgres'). Vi kör pg_dump INNE i db-containern med dess egna
# POSTGRES_USER/POSTGRES_DB via lokal socket (trust, inget lösenord), och skriver
# ut radantalen direkt så jämförelsen kan göras utan att ens hämta hem filen.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin${PATH:+:$PATH}"

OUT="/tmp/fresh_salaries_$(date +%Y%m%d).dump"

# Postgres-DATABAS-container (uteslut exporter/pooler/umami-analytics).
PGC=$(docker ps --format '{{.Names}}\t{{.Image}}' \
  | awk 'tolower($0) ~ /postgres|postgis|timescale/ && tolower($0) !~ /exporter|pgbouncer|umami/ {print $1; exit}')

if [ -z "${PGC:-}" ]; then
  echo "Hittade ingen postgres-db-container. Kör-lista:" >&2
  docker ps --format '{{.Names}} | {{.Image}}' >&2
  exit 1
fi
echo "DB-container: $PGC"

# Bekräfta att salary_salary finns (annars fel container).
HAS=$(docker exec "$PGC" sh -c 'PGHOST= PGPORT= psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-$POSTGRES_USER}" -tAc "select to_regclass('"'"'public.salary_salary'"'"') is not null"' | tr -d '[:space:]')
if [ "$HAS" != "t" ]; then
  echo "salary_salary saknas i $PGC (svar: '$HAS'). Fel container?" >&2
  exit 2
fi

echo "Dumpar → $OUT …"
docker exec "$PGC" sh -c 'PGHOST= PGPORT= pg_dump -U "${POSTGRES_USER:-postgres}" -Fc "${POSTGRES_DB:-$POSTGRES_USER}"' > "$OUT"
echo "Klar: $OUT ($(du -h "$OUT" | cut -f1))"

echo "── Radantal (för jämförelse mot 501517 / 9383) ──"
docker exec "$PGC" sh -c 'PGHOST= PGPORT= psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-$POSTGRES_USER}" -tAc "select '"'"'salary_salary='"'"'||count(*) from salary_salary"'
docker exec "$PGC" sh -c 'PGHOST= PGPORT= psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-$POSTGRES_USER}" -tAc "select '"'"'salary_generalizedtitle='"'"'||count(*) from salary_generalizedtitle"'

echo "── Hämta hem (kör på din LOKALA dator) ──"
echo "scp root@65.21.55.235:$OUT ./data/dump/"
