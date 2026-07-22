#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# PLAN B – körs MANUELLT PÅ gamla servern (Docker Swarm, offlon_prod_*).
#
#   scp pipeline/dump_on_server.sh root@65.21.55.235:/tmp/
#   ssh root@65.21.55.235 'bash /tmp/dump_on_server.sh'
#   scp root@65.21.55.235:'/tmp/fresh_salaries_*.dump' ./data/dump/
#
# ALLA databasanrop (radräkning + pg_dump -Fc) körs INUTI den identifierade
# db-containern via docker exec, med containerns egna POSTGRES_USER/POSTGRES_DB/
# POSTGRES_PASSWORD. Anslutningsmetoden auto-detekteras (containerns naturliga
# env som appen använder → TCP 127.0.0.1 → unix-socket), eftersom PGPORT/PGHOST
# kan peka på annat än standard-socketen. pg_dump streamas till stdout → /tmp-fil.
# Inga hemligheter i skriptet; diagnostik → stderr (din terminal), aldrig till filen.
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
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
echo "DB-container: $PGC" >&2

# Kör allt i EN docker exec-session: detektera anslutning, verifiera salary_salary,
# skriv radantal (stderr), streama pg_dump (stdout → värdens fil).
docker exec -i "$PGC" sh -s > "$OUT" <<'INNER'
set -u
U="${POSTGRES_USER:-postgres}"
DB="${POSTGRES_DB:-$U}"
export PGPASSWORD="${POSTGRES_PASSWORD:-}"

CONN=""; FOUND=0
# Testa i ordning: naturlig env (som appen) → TCP 127.0.0.1 → sockets.
for A in "" "-h 127.0.0.1 -p ${PGPORT:-5432}" "-h /var/run/postgresql -p ${PGPORT:-5432}" "-h /tmp -p ${PGPORT:-5432}"; do
  if psql $A -U "$U" -d "$DB" -tAc "select 1" >/dev/null 2>&1; then
    CONN="$A"; FOUND=1; break
  fi
done
if [ "$FOUND" != 1 ]; then
  echo "[server] INGEN psql-anslutning fungerade i containern (user=$U db=$DB)" >&2
  exit 7
fi
echo "[server] Anslutning OK: psql ${CONN:-<naturlig env>} -U $U -d $DB" >&2

HAS=$(psql $CONN -U "$U" -d "$DB" -tAc "select to_regclass('public.salary_salary') is not null" | tr -d '[:space:]')
if [ "$HAS" != "t" ]; then
  echo "[server] salary_salary saknas (svar: '$HAS') – fel container?" >&2
  exit 8
fi

echo "[server] ── Radantal (jämför mot 501517 / 9383) ──" >&2
echo "[server] salary_salary=$(psql $CONN -U "$U" -d "$DB" -tAc 'select count(*) from salary_salary')" >&2
echo "[server] salary_generalizedtitle=$(psql $CONN -U "$U" -d "$DB" -tAc 'select count(*) from salary_generalizedtitle')" >&2

echo "[server] Dumpar (pg_dump -Fc) …" >&2
pg_dump $CONN -U "$U" -Fc "$DB"
INNER
RC=$?

if [ "$RC" -ne 0 ] || [ ! -s "$OUT" ]; then
  rm -f "$OUT"
  echo "MISSLYCKADES (rc=$RC). Ingen dumpfil skapad – se [server]-raderna ovan." >&2
  exit "${RC:-1}"
fi

echo "Klar: $OUT ($(du -h "$OUT" | cut -f1))"
echo "Hämta hem (kör på din LOKALA dator):"
echo "  scp root@65.21.55.235:'$OUT' ./data/dump/"
