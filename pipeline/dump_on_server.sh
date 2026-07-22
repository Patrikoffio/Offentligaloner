#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# PLAN C – körs MANUELLT PÅ gamla servern (Docker Swarm, offlon_prod_*).
#
#   scp pipeline/dump_on_server.sh root@65.21.55.235:/tmp/
#   ssh root@65.21.55.235 'bash /tmp/dump_on_server.sh'
#   scp root@65.21.55.235:'/tmp/fresh_salaries_*.dump' ./data/dump/
#
# Db-containerns env är TOM (default-postgres-image). Anslutningsstrategi, i ordning:
#   1. PEER-AUTH som OS-postgres:  docker exec -u postgres $PGC ...  (kräver ofta
#      inget lösenord). Hittar databasen som innehåller salary_salary och dumpar.
#   2. FALLBACK – läs appens riktiga creds (appen ansluter dagligen = facit):
#      (a) app-containerns env (docker exec <app> env | grep POSTGRE/DATABASE),
#      (b) compose-.env i /home/*/ (t.ex. /home/samhun/.env),
#      (c) Django settings.py DATABASES.
# Lösenord maskas i utskrifter; diagnostik → stderr, dumpen → stdout → /tmp-fil.
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin${PATH:+:$PATH}"
OUT="/tmp/fresh_salaries_$(date +%Y%m%d).dump"

# ── db-container ─────────────────────────────────────────────────────────────
PGC=$(docker ps --format '{{.Names}}\t{{.Image}}' \
  | awk 'tolower($0) ~ /postgres|postgis|timescale/ && tolower($0) !~ /exporter|pgbouncer|umami/ {print $1; exit}')
[ -z "${PGC:-}" ] && { echo "[server] ingen db-container" >&2; docker ps --format '{{.Names}} | {{.Image}}' >&2; exit 1; }
echo "[server] DB-container: $PGC" >&2

finish() {  # $1 = beskrivning; kräver att $OUT redan skrivits
  if [ ! -s "$OUT" ]; then rm -f "$OUT"; echo "[server] $1: tom dump, kasseras" >&2; return 1; fi
  echo "Klar: $OUT ($(du -h "$OUT" | cut -f1)) [$1]"
  echo "Hämta hem (lokalt):  scp root@65.21.55.235:'$OUT' ./data/dump/"
  exit 0
}

# ── 1. PEER-AUTH som OS-postgres ─────────────────────────────────────────────
pexec() { docker exec -u postgres "$PGC" "$@"; }
if pexec psql -tAc "select 1" >/dev/null 2>&1; then
  echo "[server] peer-auth (OS-postgres) fungerar – letar databas med salary_salary" >&2
  DBN=""
  for d in $(pexec psql -tAc "select datname from pg_database where datistemplate=false and datname not in ('postgres','template0','template1')" 2>/dev/null); do
    has=$(pexec psql -d "$d" -tAc "select to_regclass('public.salary_salary') is not null" 2>/dev/null | tr -d '[:space:]')
    echo "[server]   $d → salary_salary? ${has:-nej}" >&2
    [ "$has" = "t" ] && { DBN="$d"; break; }
  done
  if [ -n "$DBN" ]; then
    echo "[server] ── Radantal (jämför mot 501517 / 9383), db=$DBN ──" >&2
    echo "[server] salary_salary=$(pexec psql -d "$DBN" -tAc 'select count(*) from salary_salary')" >&2
    echo "[server] salary_generalizedtitle=$(pexec psql -d "$DBN" -tAc 'select count(*) from salary_generalizedtitle')" >&2
    echo "[server] Dumpar $DBN via peer-auth …" >&2
    pexec pg_dump -Fc "$DBN" > "$OUT" && finish "peer:$DBN"
  else
    echo "[server] peer fungerade men ingen db hade salary_salary" >&2
  fi
else
  echo "[server] peer-auth gav ingen anslutning – går till creds-fallback" >&2
fi

# ── 2. FALLBACK: hitta appens riktiga creds ──────────────────────────────────
CU=""; CD=""; CW=""
note() { echo "[server] $1" >&2; }

# (a) app-containerns env
APPC=$(docker ps --format '{{.Names}}' | grep -iE 'offlon|samhun' \
       | grep -viE 'db|exporter|umami|nginx|certbot|redis|pgbouncer|proxy' | head -1)
if [ -n "$APPC" ]; then
  AENV=$(docker exec "$APPC" env 2>/dev/null | grep -iE 'POSTGRE|DATABASE' || true)
  note "app-container $APPC env (maskat):"
  printf '%s\n' "$AENV" | sed -E 's/(PASS[^=]*=|PASSWORD=)[^ ]+/\1***/Ig' | sed 's/^/[server]   /' >&2
  geta() { printf '%s\n' "$AENV" | sed -n "s/^$1=//p" | head -1; }
  CU=$(geta 'POSTGRE_USER'); [ -z "$CU" ] && CU=$(geta 'POSTGRES_USER'); [ -z "$CU" ] && CU=$(geta 'DB_USER')
  CD=$(geta 'POSTGRE_DATABASE'); [ -z "$CD" ] && CD=$(geta 'POSTGRES_DB'); [ -z "$CD" ] && CD=$(geta 'DB_NAME')
  CW=$(geta 'POSTGRE_PASSWORD'); [ -z "$CW" ] && CW=$(geta 'POSTGRES_PASSWORD'); [ -z "$CW" ] && CW=$(geta 'DB_PASSWORD')
  # DATABASE_URL=postgres://user:pass@host:port/db
  DU=$(geta 'DATABASE_URL')
  if [ -n "$DU" ]; then
    [ -z "$CU" ] && CU=$(printf '%s' "$DU" | sed -E 's#.*://([^:/@]+).*#\1#')
    [ -z "$CW" ] && CW=$(printf '%s' "$DU" | sed -E 's#.*://[^:]+:([^@]+)@.*#\1#')
    [ -z "$CD" ] && CD=$(printf '%s' "$DU" | sed -E 's#.*/([^/?]+)(\?.*)?$#\1#')
  fi
fi

# (b) compose-.env
if [ -z "$CU" ] || [ -z "$CW" ]; then
  for envf in /home/*/.env /srv/*/.env /opt/*/.env /root/*/.env; do
    [ -f "$envf" ] || continue
    grep -qiE 'POSTGRE_?(USER|DATABASE|PASSWORD)' "$envf" || continue
    gete() { sed -n "s/^[[:space:]]*$1=//p" "$envf" | head -1 | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//'; }
    [ -z "$CU" ] && { CU=$(gete 'POSTGRE_USER'); [ -z "$CU" ] && CU=$(gete 'POSTGRES_USER'); }
    [ -z "$CD" ] && { CD=$(gete 'POSTGRE_DATABASE'); [ -z "$CD" ] && CD=$(gete 'POSTGRES_DB'); }
    [ -z "$CW" ] && { CW=$(gete 'POSTGRE_PASSWORD'); [ -z "$CW" ] && CW=$(gete 'POSTGRES_PASSWORD'); }
    [ -n "$CU" ] && { note "creds ur $envf"; break; }
  done
fi

# (c) Django settings.py DATABASES
if [ -z "$CU" ] || [ -z "$CW" ]; then
  SET=$(grep -rlsI --include='settings*.py' 'DATABASES' /home /srv /opt /root 2>/dev/null | head -1)
  if [ -n "$SET" ]; then
    note "läser $SET"
    val() { grep -iE "['\"]$1['\"]" "$SET" | head -1 | sed -E "s/.*['\"]$1['\"][^'\"]*['\"]([^'\"]*)['\"].*/\1/I"; }
    [ -z "$CU" ] && CU=$(val 'USER'); [ -z "$CD" ] && CD=$(val 'NAME'); [ -z "$CW" ] && CW=$(val 'PASSWORD')
  fi
fi

: "${CD:=offentliga_loner}"
echo "[server] FALLBACK-creds: USER='${CU:-?}' DB='$CD' PW=$([ -n "$CW" ] && echo '***satt***' || echo '<tomt>')" >&2
[ -z "$CU" ] && { echo "[server] Kunde inte hitta användarnamn någonstans." >&2; exit 7; }

docker exec -i -e RU="$CU" -e RD="$CD" -e RW="$CW" "$PGC" sh -s > "$OUT" <<'INNER'
set -u
U="$RU"; DB="$RD"; export PGPASSWORD="$RW"
CONN=""; FOUND=0
for A in "" "-h 127.0.0.1 -p ${PGPORT:-5432}" "-h /var/run/postgresql -p ${PGPORT:-5432}" "-h /tmp -p ${PGPORT:-5432}"; do
  if psql $A -U "$U" -d "$DB" -tAc "select 1" >/dev/null 2>&1; then CONN="$A"; FOUND=1; break; fi
done
[ "$FOUND" = 1 ] || { echo "[server] fallback-anslutning misslyckades (user=$U db=$DB)" >&2; exit 7; }
echo "[server] Anslutning OK: psql ${CONN:-<naturlig>} -U $U -d $DB" >&2
echo "[server] salary_salary=$(psql $CONN -U "$U" -d "$DB" -tAc 'select count(*) from salary_salary')" >&2
echo "[server] salary_generalizedtitle=$(psql $CONN -U "$U" -d "$DB" -tAc 'select count(*) from salary_generalizedtitle')" >&2
pg_dump $CONN -U "$U" -Fc "$DB"
INNER
RC=$?
[ "$RC" -eq 0 ] && finish "fallback:$CU@$CD"
rm -f "$OUT"
echo "MISSLYCKADES (rc=$RC) – se [server]-raderna ovan." >&2
exit "${RC:-1}"
