#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# READ-ONLY: extraherar de Django-källfiler som styr rapport-/betalflödet ur
# app-containern, för att låsa Stripe-detaljerna i v2-bryggan. Ändrar/raderar
# INGET. Hemligheter (Stripe secret, lösenord, API-nycklar) MASKAS i utdatan.
# Skriver till /tmp-loggfil som du scp:ar hem.
#
#   scp pipeline/extract_django_source.sh root@65.21.55.235:/tmp/
#   ssh root@65.21.55.235 'bash /tmp/extract_django_source.sh'
#   scp root@65.21.55.235:'/tmp/offlon_source_*.txt' ./
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin${PATH:+:$PATH}"
LOG="/tmp/offlon_source_$(date +%Y%m%d_%H%M%S).txt"

# Maskning: redigera bort värden efter känsliga nycklar + Stripe-nyckelmönster.
mask() {
  sed -E \
    -e 's/((SECRET|PASSWORD|PASSWD|API_?KEY|ACCESS_?KEY|TOKEN|DSN|WEBHOOK_SECRET)[A-Z_]*["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"']?)[^"'"'"'[:space:]]+/\1***MASK***/Ig' \
    -e 's/(sk|rk|whsec)_[A-Za-z0-9_]+/\1_***MASK***/g'
}

{
  echo "===== APP-CONTAINER ====="
  APPC=$(docker ps --format '{{.Names}} {{.Image}}' \
    | awk 'tolower($0) ~ /web|django|app|celery/ && tolower($0) !~ /db|nginx|redis|exporter|umami|proxy|_ssh|grafana|loki|prom/ {print $1; exit}')
  echo "app-container: ${APPC:-<hittades ej>}"
  [ -z "${APPC:-}" ] && { docker ps --format '{{.Names}} | {{.Image}}'; exit 1; }

  # Rot = katalogen där settings.py ligger
  SET=$(docker exec "$APPC" sh -c 'find /app /code /srv /usr/src -maxdepth 4 -name settings.py 2>/dev/null | grep -viE "site-packages|dist-packages" | head -1')
  ROOT=$(dirname "$(dirname "$SET")" 2>/dev/null)
  echo "settings.py: $SET"
  echo "projektrot (gissad): $ROOT"

  echo; echo "===== ALLA URLCONF (urls.py) ====="
  for f in $(docker exec "$APPC" sh -c "find ${ROOT:-/app} -maxdepth 4 -name urls.py 2>/dev/null | grep -viE 'site-packages|dist-packages' | head -10"); do
    echo "--- $f ---"; docker exec "$APPC" cat "$f" 2>/dev/null | mask
  done

  echo; echo "===== FILER MED stripe/checkout/rapport/report/mail (maskade) ====="
  RELEVANT=$(docker exec "$APPC" sh -c "grep -rliE 'stripe|checkout|create-checkout|rapport|report|send_mail|EmailMessage|payment' ${ROOT:-/app} --include='*.py' 2>/dev/null | grep -viE 'site-packages|dist-packages|/migrations/' | head -20")
  for f in $RELEVANT; do
    echo "--- $f ---"; docker exec "$APPC" cat "$f" 2>/dev/null | mask
  done

  echo; echo "===== settings.py (maskad – för Stripe/mejl-konfig) ====="
  echo "--- $SET ---"; docker exec "$APPC" cat "$SET" 2>/dev/null | mask

  echo; echo "===== RAPPORT-TEMPLATES (LÖNERAPPORT/rapport) ====="
  for f in $(docker exec "$APPC" sh -c "grep -rliE 'LÖNERAPPORT|lönerapport|exempel-rapport|create-checkout-session' ${ROOT:-/app} --include='*.html' 2>/dev/null | head -6"); do
    echo "--- $f ---"; docker exec "$APPC" cat "$f" 2>/dev/null | head -200 | mask
  done

  echo; echo "===== INSTALLERADE PAKET (stripe-version m.m.) ====="
  docker exec "$APPC" sh -c 'pip freeze 2>/dev/null | grep -iE "stripe|django|mail|sendgrid|anymail|celery" || pip list 2>/dev/null | grep -iE "stripe|django|mail|sendgrid|anymail|celery"'

  echo; echo "===== SLUT ====="
} 2>&1 | tee "$LOG"

echo
echo "LOGG SPARAD: $LOG (hemligheter maskade)"
echo "Hämta hem:   scp root@65.21.55.235:'$LOG' ./"
