#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# PLAN B – körs MANUELLT PÅ gamla servern (Docker Swarm, offlon_prod_*).
#
#   scp pipeline/dump_on_server.sh root@65.21.55.235:/tmp/
#   ssh root@65.21.55.235 'bash /tmp/dump_on_server.sh'
#   scp root@65.21.55.235:'/tmp/fresh_salaries_*.dump' ./data/dump/
#
# LÄSER containerns FAKTISKA miljö (inga gissade namn). POSTGRES_USER kan vara
# tomt i containern (då är den riktiga superusern inte 'postgres') – kompletteras
# då ur rätt compose-.env på servern, matchat på databasnamnet så offlon (inte
# samhun) väljs. Radräkning + pg_dump -Fc körs via docker exec med exakta creds;
# anslutningen auto-detekteras (naturlig env → TCP 127.0.0.1 → socket). Lösenord
# maskas i utskrifter; diagnostik → stderr (din terminal), aldrig till filen.
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin${PATH:+:$PATH}"

OUT="/tmp/fresh_salaries_$(date +%Y%m%d).dump"

# ── 1. Postgres-DATABAS-container (uteslut exporter/pooler/umami) ─────────────
PGC=$(docker ps --format '{{.Names}}\t{{.Image}}' \
  | awk 'tolower($0) ~ /postgres|postgis|timescale/ && tolower($0) !~ /exporter|pgbouncer|umami/ {print $1; exit}')
if [ -z "${PGC:-}" ]; then
  echo "[server] Hittade ingen postgres-db-container. Kör-lista:" >&2
  docker ps --format '{{.Names}} | {{.Image}}' >&2
  exit 1
fi
echo "[server] DB-container: $PGC" >&2

# ── 2. Läs containerns FAKTISKA env ──────────────────────────────────────────
CENV=$(docker exec "$PGC" env 2>/dev/null)
getc() { printf '%s\n' "$CENV" | sed -n "s/^$1=//p" | head -1; }
CU=$(getc POSTGRES_USER); CD=$(getc POSTGRES_DB); CW=$(getc POSTGRES_PASSWORD)
echo "[server] container-env: POSTGRES_USER='${CU}' POSTGRES_DB='${CD}' POSTGRES_PASSWORD=$([ -n "$CW" ] && echo '***satt***' || echo '<tomt>')" >&2

# ── 3. Komplettera ur compose-.env (matcha databasnamn → rätt projekt) ───────
if [ -z "$CU" ] || [ -z "$CW" ] || [ -z "$CD" ]; then
  for envf in /home/*/.env /srv/*/.env /opt/*/.env /root/*/.env; do
    [ -f "$envf" ] || continue
    grep -qiE 'POSTGRE_?(USER|DATABASE)' "$envf" || continue
    gete() { sed -n "s/^[[:space:]]*$1=//p" "$envf" | head -1 | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//'; }
    edb=$(gete 'POSTGRE_DATABASE'); [ -z "$edb" ] && edb=$(gete 'POSTGRES_DB')
    # Matcha rätt projekt om vi redan känner databasnamnet
    if [ -n "$CD" ] && [ -n "$edb" ] && [ "$edb" != "$CD" ]; then continue; fi
    [ -z "$CU" ] && { CU=$(gete 'POSTGRE_USER'); [ -z "$CU" ] && CU=$(gete 'POSTGRES_USER'); }
    [ -z "$CD" ] && CD="$edb"
    [ -z "$CW" ] && { CW=$(gete 'POSTGRE_PASSWORD'); [ -z "$CW" ] && CW=$(gete 'POSTGRES_PASSWORD'); }
    echo "[server] kompletterade creds ur $envf" >&2
    [ -n "$CU" ] && [ -n "$CW" ] && break
  done
fi
: "${CU:=postgres}"; : "${CD:=$CU}"
echo "[server] ANVÄNDER USER='$CU' DB='$CD' PW=$([ -n "$CW" ] && echo '***satt***' || echo '<tomt>')" >&2

# ── 4. Anslut + dumpa via docker exec med EXAKTA creds ───────────────────────
docker exec -i -e RU="$CU" -e RD="$CD" -e RW="$CW" "$PGC" sh -s > "$OUT" <<'INNER'
set -u
U="$RU"; DB="$RD"; export PGPASSWORD="$RW"
CONN=""; FOUND=0
for A in "" "-h 127.0.0.1 -p ${PGPORT:-5432}" "-h /var/run/postgresql -p ${PGPORT:-5432}" "-h /tmp -p ${PGPORT:-5432}"; do
  if psql $A -U "$U" -d "$DB" -tAc "select 1" >/dev/null 2>&1; then CONN="$A"; FOUND=1; break; fi
done
if [ "$FOUND" != 1 ]; then
  echo "[server] Anslutning misslyckades för user=$U db=$DB. Försöker lista databaser:" >&2
  for A in "" "-h 127.0.0.1 -p ${PGPORT:-5432}" "-h /var/run/postgresql -p ${PGPORT:-5432}"; do
    if psql $A -U "$U" -l 2>/dev/null; then break; fi
  done >&2
  exit 7
fi
echo "[server] Anslutning OK: psql ${CONN:-<naturlig env>} -U $U -d $DB" >&2
HAS=$(psql $CONN -U "$U" -d "$DB" -tAc "select to_regclass('public.salary_salary') is not null" | tr -d '[:space:]')
if [ "$HAS" != "t" ]; then
  echo "[server] salary_salary saknas i db=$DB (svar '$HAS'). Databaser:" >&2
  psql $CONN -U "$U" -l >&2
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
echo "Hämta hem (kör lokalt):  scp root@65.21.55.235:'$OUT' ./data/dump/"
