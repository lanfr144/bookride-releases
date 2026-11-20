#!/bin/bash
# ==============================================================================
# create_dashboard.sh - creates the Kibana data view and dashboard (2.3)
# ==============================================================================
# Imports kibana/bookride-dashboard.ndjson with the Kibana Saved Objects API:
#   - data view  "bookride-logs"            (time field @timestamp)
#   - panel      "Book&Ride - Logs per service"
#   - panel      "Book&Ride - Logs per level"
#   - dashboard  "Book&Ride - Logs dashboard" (time range 2 and 3 November 2026)
# overwrite=true: safe to run again. curl runs inside the Kibana container; the
# password is read from .env and passed as an environment variable.
# The same objects can be built by hand in Kibana (Stack Management > Data Views,
# then Dashboards > Create).
# ==============================================================================
set -euo pipefail
cd "$(dirname "$0")"
docker compose ps --status running --services 2>/dev/null | grep -qx kibana \
  || { echo "The stack is not running. Start it first:  ./start.sh" >&2; exit 1; }

ELASTIC_PASSWORD=$(grep '^ELASTIC_PASSWORD=' .env | cut -d= -f2-); export ELASTIC_PASSWORD
PORT=$(grep '^KIBANA_PORT_EXPOSE=' .env | cut -d= -f2-)

docker compose exec -T -e ELASTIC_PASSWORD kibana bash -c \
  'curl -s -u "elastic:$ELASTIC_PASSWORD" -H "kbn-xsrf: true" -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" --form "file=@-;filename=bookride-dashboard.ndjson"' \
  < kibana/bookride-dashboard.ndjson
echo
echo "Open: http://localhost:$PORT/app/dashboards#/view/bookride-dashboard"
echo "Login: elastic / ELASTIC_PASSWORD of .env. Then save a screenshot in screenshots/kibana_dashboard.png"
