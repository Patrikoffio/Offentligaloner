#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Färsk pg_dump av Django-databasen (Docker Swarm, offlon_prod_db, postgres:16).
#
#   scp pipeline/dump_on_server.sh root@65.21.55.235:/tmp/
#   ssh root@65.21.55.235 'bash /tmp/dump_on_server.sh'
#   scp root@65.21.55.235:'/tmp/fresh_salaries_*.dump' ./data/dump/
#
# Byggt på faktisk serverdiagnos:
#   * DB lyssnar på PGPORT=5454 (socket .s.PGSQL.5454) – INTE 5432.
#   * Användarnamnet ligger i Docker-secret POSTGRES_USER_FILE (/run/secrets/…),
#     inte i env – därför var POSTGRES_USER tomt och rollen 'postgres' saknas.
#   * pg_hba: 'local all all trust' + 'host 127.0.0.1/32 trust' → inget lösenord
#     behövs lokalt. Rätt roll (ur secret) + rätt port räcker.
# Allt körs INUTI db-containern (läser sina egna secrets); dump → stdout → /tmp-fil.
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin${PATH:+:$PATH}"
OUT="/tmp/fresh_salaries_$(date +%Y%m%d).dump"

PGC=$(docker ps --format '{{.Names}} {{.Image}}' \
  | awk 'tolower($0) ~ /postgres|postgis/ && tolower($0) !~ /exporter|umami|pgbouncer/ {print $1; exit}')
[ -z "${PGC:-}" ] && { echo "[server] ingen db-container" >&2; docker ps --format '{{.Names}} | {{.Image}}' >&2; exit 1; }
echo "[server] DB-container: $PGC" >&2

# Kör allt inuti containern: läs port/user/db/lösenord ur env+secrets, anslut via
# lokal trust, verifiera salary_salary, skriv radantal (stderr), streama pg_dump.
docker exec -i "$PGC" sh -s > "$OUT" <<'INNER'
set -u
PORT="${PGPORT:-5432}"
U="${POSTGRES_USER:-}"
[ -z "$U" ] && [ -n "${POSTGRES_USER_FILE:-}" ] && [ -f "$POSTGRES_USER_FILE" ] && U="$(cat "$POSTGRES_USER_FILE")"
DB="${POSTGRES_DB:-${POSTGRE_DATABASE:-}}"
[ -n "${POSTGRES_PASSWORD_FILE:-}" ] && [ -f "$POSTGRES_PASSWORD_FILE" ] && export PGPASSWORD="$(cat "$POSTGRES_PASSWORD_FILE")"
echo "[server] port=$PORT user=$U db=$DB (pg_hba local=trust)" >&2
[ -n "$U" ] && [ -n "$DB" ] || { echo "[server] saknar user/db" >&2; exit 6; }

CONN=""
for A in "-h /var/run/postgresql -p $PORT" "-h 127.0.0.1 -p $PORT" "-h /tmp -p $PORT" "-p $PORT"; do
  if psql $A -U "$U" -d "$DB" -tAc "select 1" >/dev/null 2>&1; then CONN="$A"; break; fi
done
[ -n "$CONN" ] || { echo "[server] ingen anslutning (user=$U db=$DB port=$PORT)" >&2; exit 7; }
echo "[server] Anslutning OK: psql $CONN -U $U -d $DB" >&2

HAS=$(psql $CONN -U "$U" -d "$DB" -tAc "select to_regclass('public.salary_salary') is not null" | tr -d '[:space:]')
[ "$HAS" = "t" ] || { echo "[server] salary_salary saknas (svar '$HAS')" >&2; psql $CONN -U "$U" -l >&2; exit 8; }

echo "[server] ── Radantal (jämför mot 501517 / 9383) ──" >&2
echo "[server] salary_salary=$(psql $CONN -U "$U" -d "$DB" -tAc 'select count(*) from salary_salary')" >&2
echo "[server] salary_generalizedtitle=$(psql $CONN -U "$U" -d "$DB" -tAc 'select count(*) from salary_generalizedtitle')" >&2
echo "[server] Dumpar (pg_dump -Fc) …" >&2
pg_dump $CONN -U "$U" -Fc "$DB"
INNER
RC=$?

if [ "$RC" -ne 0 ] || [ ! -s "$OUT" ]; then
  rm -f "$OUT"; echo "MISSLYCKADES (rc=$RC) – se [server]-raderna ovan." >&2; exit "${RC:-1}"
fi
echo "Klar: $OUT ($(du -h "$OUT" | cut -f1))"
echo "Hämta hem (lokalt):  scp root@65.21.55.235:'$OUT' ./data/dump/"
