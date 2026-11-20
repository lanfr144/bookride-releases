#!/bin/bash
# ==============================================================================
# start.sh - starts Elasticsearch + Kibana for the Book&Ride logs (2.3)
# ==============================================================================
# Run it on the machine (WSL), in the folder of docker-compose.yml:   ./start.sh
#   1. checks that .env exists and that the two passwords are not placeholders
#   2. checks that the host ports of .env are free
#   3. docker compose up -d --wait   (waits until every healthcheck is green)
#   4. when the start fails: shows the last logs and STOPS everything
# ==============================================================================
set -uo pipefail
cd "$(dirname "$0")"

get() { grep "^$1=" .env | head -1 | cut -d= -f2-; }   # read ONE key of .env

command -v docker >/dev/null 2>&1 || { echo "docker not found: run this script on the machine (WSL), not in a container." >&2; exit 1; }

if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env created from .env.example."
  echo "Edit .env now: replace <password> of ELASTIC_PASSWORD and KIBANA_PASSWORD, then run ./start.sh again."
  exit 1
fi
for key in STACK_VERSION ELASTIC_PASSWORD KIBANA_PASSWORD ES_PORT_EXPOSE KIBANA_PORT_EXPOSE ES_JAVA_OPTS; do
  [ -n "$(get "$key")" ] || { echo "$key is missing in .env (see .env.example)." >&2; exit 1; }
done
for key in ELASTIC_PASSWORD KIBANA_PASSWORD; do
  value=$(get "$key")
  case "$value" in *"<"*|*">"*) echo "$key is still a placeholder in .env: choose a password (6 characters or more)." >&2; exit 1 ;; esac
  [ "${#value}" -ge 6 ] || { echo "$key must have 6 characters or more." >&2; exit 1; }
done

echo "== Checking the host ports of .env"
busy=0
for key in ES_PORT_EXPOSE KIBANA_PORT_EXPOSE; do
  port=$(get "$key")
  if docker compose ps --status running 2>/dev/null | grep -q "127.0.0.1:$port->"; then
    echo "OK    $key=$port (already used by this stack)"
  elif (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then
    echo "BUSY  $key=$port -> change $key in .env (or stop what uses the port)"; busy=1
  else
    echo "FREE  $key=$port"
  fi
done
[ "$busy" -eq 0 ] || exit 1

echo "== Starting (first start: 1 to 3 minutes)"
if docker compose up -d --wait --wait-timeout 400; then
  echo
  echo "Started. Elasticsearch: http://localhost:$(get ES_PORT_EXPOSE)   Kibana: http://localhost:$(get KIBANA_PORT_EXPOSE)"
  echo "Kibana login: user elastic, password = ELASTIC_PASSWORD of .env"
  echo "Next:  ./load_logs.sh   ./run_queries.sh   ./create_dashboard.sh"
else
  echo
  echo "START FAILED - last logs:" >&2
  docker compose ps -a
  docker compose logs --tail 30
  if [ "${KEEP_ON_FAILURE:-0}" = "1" ]; then
    echo "KEEP_ON_FAILURE=1: containers kept for inspection."
  else
    echo "Stopping everything (docker compose down). Use KEEP_ON_FAILURE=1 ./start.sh to keep the containers."
    docker compose down
  fi
  exit 1
fi
