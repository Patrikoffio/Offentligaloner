#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Hämtar en färsk pg_dump av Django-databasen från gamla servern (Hetzner).
#
# SÄKERHET: SSH-lösenordet anges INTERAKTIVT vid ssh-prompten och sparas ALDRIG
# i denna fil, i git eller i miljövariabler. Skriptet innehåller inga hemligheter.
# Diagnostik skrivs till din TERMINAL (stderr), aldrig till filen. Databas-
# lösenord som hittas i serverns config maskas i utskrifter. Utdatan (custom-
# format-dumpen) skrivs till data/dump/ som är gitignorad (persondata).
#
# Miljön på servern är okänd → skriptet kartlägger först (docker / systemd /
# port 5432 / Django-config) och dumpar sedan rätt väg automatiskt. Om det inte
# lyckas skrivs en diagnos ut så att metoden kan justeras, och ingen halv fil
# lämnas kvar.
#
# Användning:
#   bash pipeline/fetch_hetzner_dump.sh [user@host] [utfil]
#   (standard: root@65.21.55.235 → data/dump/<datum>_fresh_salaries.dump)
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

HOST="${1:-root@65.21.55.235}"
OUT="${2:-data/dump/$(date +%Y%m%d)_fresh_salaries.dump}"
DBG="${DBG:-0}"   # kör med DBG=1 för bash -x-spårning på fjärrsidan
mkdir -p "$(dirname "$OUT")"

echo "Ansluter till $HOST – skriv lösenordet om du blir tillfrågad (nyckel-auth kan redan gälla)…"

# Allt fjärrarbete i EN ssh-session (ett lösenord). Fjärrskriptet kartlägger
# miljön, dumpar till /tmp/fresh.dump och cat:ar den till stdout (→ lokal fil)
# ENDAST vid lyckad dump. Diagnostik → stderr.
ssh -o StrictHostKeyChecking=accept-new "$HOST" "DBG=${DBG} bash -s" > "$OUT" <<'REMOTE'
set -uo pipefail
# Icke-inloggad SSH-shell har avskalad PATH → docker/psql/systemctl kan saknas.
# Sätt en robust PATH så verktygen hittas (grundorsaken till tidigare misslyckanden).
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/opt/bin${PATH:+:$PATH}"
[ "${DBG:-0}" = 1 ] && { export PS4='+[rad ${LINENO}] '; set -x; }
log(){ echo "[probe] $*" >&2; }
log "PATH=$PATH"
log "verktyg: docker=$(command -v docker || echo SAKNAS)  psql=$(command -v psql || echo saknas)  pg_dump=$(command -v pg_dump || echo saknas)"
TMP=/tmp/fresh_salaries.dump
ERR=/tmp/fresh_dumperr.txt
rm -f "$TMP" "$ERR"

log "whoami=$(whoami)  host=$(hostname)  $(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-okänt OS}")"

# Hjälpare: verifiera att en db innehåller salary_salary
has_tbl_local(){ psql -d "$1" -tAc "select to_regclass('public.salary_salary') is not null" 2>/dev/null | grep -q t; }
has_tbl_dock(){ docker exec "$1" psql -U "$2" -d "$3" -tAc "select to_regclass('public.salary_salary') is not null" 2>/dev/null | grep -q t; }

# ── 1. Docker ────────────────────────────────────────────────────────────────
HAVE_DOCKER=0
if command -v docker >/dev/null 2>&1 && docker ps >/dev/null 2>&1; then
  HAVE_DOCKER=1
  log "Docker-containrar:"
  docker ps --format '  {{.Names}} | {{.Image}} | {{.Ports}}' >&2
else
  log "docker ej tillgängligt (command -v docker: $(command -v docker || echo nej), docker ps rc: $?)"
fi

# ── 2. systemd / port 5432 ───────────────────────────────────────────────────
if command -v systemctl >/dev/null 2>&1; then
  U=$(systemctl list-units --type=service --no-pager 2>/dev/null | grep -i postgre || true)
  [ -n "$U" ] && log "postgres-tjänster:$(printf '\n%s' "$U")" || log "inga postgres-systemd-tjänster"
fi
P=$( (ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null) | grep -E ':5432\b' || true)
[ -n "$P" ] && log "lyssnar på 5432:$(printf '\n%s' "$P")" || log "inget lyssnar på 5432 (host-nät)"

# ── 3. Django-config (paths + maskade DB-nycklar) ────────────────────────────
ROOTS="/root /home /srv /opt /var/www /app /usr/src"
CFG=$(grep -rlsI --include='settings*.py' 'DATABASES' $ROOTS 2>/dev/null | head -5 || true)
[ -n "$CFG" ] && log "Django settings m. DATABASES:$(printf '\n  %s' $CFG)"
ENVF=$( { grep -rlsI -E 'POSTGRES_|DATABASE_URL' $ROOTS --include='*.env' --include='.env' 2>/dev/null; \
          grep -rlsI -E 'postgres|POSTGRES_' $ROOTS --include='docker-compose*.yml' --include='compose*.yml' 2>/dev/null; } | sort -u | head -5 || true)
[ -n "$ENVF" ] && log "env/compose m. DB-creds:$(printf '\n  %s' $ENVF)"

# ── 4. Auto-dump: prioritet A) Docker-container ──────────────────────────────
dump_ok(){ log "DUMP OK ($1) – skickar $(du -h "$TMP" 2>/dev/null | cut -f1)"; cat "$TMP"; exit 0; }

if [ "$HAVE_DOCKER" = 1 ]; then
  # Postgres-DATABAS-containrar. Uteslut exporters (postgres_exporter saknar psql),
  # poolers och umami-analytics. Kör psql/pg_dump INNE i containern med dess egna
  # POSTGRES_USER/POSTGRES_DB via lokal socket (PGHOST/PGPORT tomma = trust, inget
  # lösenord). Django-DB:n har en egen användare, inte 'postgres'.
  PGCS=$(docker ps --format '{{.Names}}\t{{.Image}}' \
    | awk 'tolower($0) ~ /postgres|postgis|timescale/ && tolower($0) !~ /exporter|pgbouncer|umami/ {print $1}')
  log "postgres-db-containrar: $(echo $PGCS | tr '\n' ' ')"
  for PGC in $PGCS; do
    has=$(docker exec "$PGC" sh -c 'PGHOST= PGPORT= psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-$POSTGRES_USER}" -tAc "select to_regclass('"'"'public.salary_salary'"'"') is not null"' 2>/dev/null | tr -d '[:space:]')
    log "container $PGC → salary_salary? '${has:-<tomt/fel>}'"
    if [ "$has" = "t" ]; then
      log "dumpar $PGC (databas ur \$POSTGRES_DB)…"
      if docker exec "$PGC" sh -c 'PGHOST= PGPORT= pg_dump -U "${POSTGRES_USER:-postgres}" -Fc "${POSTGRES_DB:-$POSTGRES_USER}"' > "$TMP" 2>"$ERR"; then
        dump_ok "docker:$PGC"
      fi
      log "pg_dump-fel: $(head -3 "$ERR" 2>/dev/null)"
    fi
  done
  log "ingen postgres-db-container innehöll salary_salary"
fi

# ── 4B. Auto-dump: lokal psql/pg_dump (peer som current user) ────────────────
if command -v pg_dump >/dev/null 2>&1 && command -v psql >/dev/null 2>&1; then
  CANDS=$(psql -tAc "select datname from pg_database where datistemplate=false and datname<>'postgres'" 2>/dev/null || true)
  for d in $CANDS; do
    if has_tbl_local "$d"; then
      log "salary_salary finns i lokal db: $d – dumpar…"
      if pg_dump -Fc "$d" > "$TMP" 2>"$ERR"; then dump_ok "local/$d"; fi
      log "pg_dump-fel: $(head -3 "$ERR" 2>/dev/null)"
    fi
  done
  [ -n "$CANDS" ] && log "lokal psql nådde db men ingen hade salary_salary"
fi

# ── 5. Ingen väg lyckades: skriv diagnos (maskade lösenord) ──────────────────
log "──────────────────────────────────────────────────────────────"
log "AUTOMATISK DUMP MISSLYCKADES. DB-relevanta rader ur config (lösenord maskade):"
for f in $CFG $ENVF; do
  log "── $f ──"
  grep -inE "ENGINE|NAME|USER|HOST|PORT|POSTGRES_|DATABASE_URL|password" "$f" 2>/dev/null \
    | sed -E 's/((password|POSTGRES_PASSWORD)[^=:]*[=:] *)[^,}"[:space:]]+/\1***MASKAT***/Ig' \
    | head -20 1>&2
done
log "Skicka dessa rader till assistenten så justeras metoden."
exit 3
REMOTE
RC=$?

# Ingen halv/​tom fil får lämnas kvar
if [ "$RC" -ne 0 ] || [ ! -s "$OUT" ]; then
  rm -f "$OUT"
  if [ "$RC" = 255 ]; then
    echo "MISSLYCKADES: SSH-fel (rc=255) – anslutning/auth nådde aldrig fjärrskriptet. Kör diagnoskommandot med 'ssh -v'." >&2
  else
    echo "MISSLYCKADES: fjärrskriptet KÖRDES (SSH lyckades) men gav rc=$RC. Se [probe]-raderna ovan – särskilt PATH/verktygs-raden." >&2
  fi
  exit "${RC:-1}"
fi

echo "Klar: $OUT ($(du -h "$OUT" | cut -f1))"
