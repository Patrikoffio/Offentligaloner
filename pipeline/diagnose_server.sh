#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Serverdiagnos (läs-only) för att bygga rätt dumpkommando. Skriver ALLT till en
# loggfil i /tmp som du scp:ar hem. Inga ändringar görs. Lösenord maskas.
#
#   scp pipeline/diagnose_server.sh root@65.21.55.235:/tmp/
#   ssh root@65.21.55.235 'bash /tmp/diagnose_server.sh'
#   scp root@65.21.55.235:'/tmp/offlon_diag_*.txt' ./
# ─────────────────────────────────────────────────────────────────────────────
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin${PATH:+:$PATH}"
LOG="/tmp/offlon_diag_$(date +%Y%m%d_%H%M%S).txt"

{
  echo "===== (1) ALLA CONTAINRAR (namn | image) ====="
  docker ps --format '{{.Names}}  |  {{.Image}}'

  PGC=$(docker ps --format '{{.Names}} {{.Image}}' | awk 'tolower($0) ~ /postgres|postgis/ && tolower($0) !~ /exporter|umami|pgbouncer/ {print $1; exit}')
  echo; echo "===== (2) DB-CONTAINER = $PGC — env via docker inspect (maskat) ====="
  docker inspect "$PGC" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null \
    | grep -iE 'POSTGRE|^PG|DATABASE' | sed -E 's/(PASS[^=]*=|PASSWORD=)[^ ]+/\1***MASK***/Ig'

  echo; echo "===== (3) DB-CONTAINER: OS-användare, roller, databaser ====="
  echo "-- id postgres / whoami --"; docker exec "$PGC" sh -c 'id postgres 2>&1; echo "exec-user=$(whoami)"'
  echo "-- roller (peer-försök som OS-postgres) --"
  docker exec -u postgres "$PGC" psql -tAc "select rolname,rolsuper from pg_roles order by 1" 2>&1 | head -25
  echo "-- databaser (peer-försök) --"
  docker exec -u postgres "$PGC" psql -tAc "select datname from pg_database where not datistemplate" 2>&1 | head

  echo; echo "===== (4) pg_hba.conf i db-containern (varför peer/lösenord) ====="
  docker exec "$PGC" sh -c 'grep -vE "^[[:space:]]*#|^[[:space:]]*$" "${PGDATA:-/var/lib/postgresql/data}/pg_hba.conf" 2>/dev/null' | head -30

  echo; echo "===== (5) APP-CONTAINRAR: DB-creds i env (maskat) ====="
  for c in $(docker ps --format '{{.Names}}' | grep -viE 'exporter|umami|nginx|certbot|redis|proxy|_ssh'); do
    hit=$(docker exec "$c" sh -c 'env' 2>/dev/null | grep -iE 'POSTGRE|DATABASE_URL|DB_NAME|DB_USER|DB_HOST' \
          | sed -E 's/(PASS[^=]*=|PASSWORD=)[^ ]+/\1***MASK***/Ig; s#(://[^:]+:)[^@]+@#\1***@#g')
    [ -n "$hit" ] && { echo "--- $c ---"; echo "$hit"; }
  done

  echo; echo "===== (6) Django settings.py / .env i app-containrar ====="
  for c in $(docker ps --format '{{.Names}}' | grep -viE 'exporter|umami|nginx|certbot|redis|proxy|_ssh|_db'); do
    found=$(docker exec "$c" sh -c 'find / -maxdepth 6 \( -name settings.py -o -name ".env" \) 2>/dev/null | grep -viE "site-packages|dist-packages|node_modules" | head -4')
    [ -n "$found" ] && { echo "--- $c ---"; echo "$found"; }
  done

  echo; echo "===== (7) compose-.env på värden ====="
  for f in /home/*/.env /srv/*/.env /opt/*/.env /root/*/.env; do
    [ -f "$f" ] || continue
    echo "--- $f ---"
    grep -iE 'POSTGRE|DATABASE|DB_' "$f" | sed -E 's/(PASS[^=]*=|PASSWORD=)[^ ]+/\1***MASK***/Ig'
  done

  echo; echo "===== SLUT ====="
} 2>&1 | tee "$LOG"

echo
echo "LOGG SPARAD: $LOG"
echo "Hämta hem:   scp root@65.21.55.235:'$LOG' ./"
