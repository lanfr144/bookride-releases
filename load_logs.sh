#!/bin/bash
# ==============================================================================
# load_logs.sh - loads the 20 log entries into the index bookride-logs (2.3)
# ==============================================================================
# curl runs INSIDE the Elasticsearch container: nothing to install on the machine
# and the password stays in the container (variable ELASTIC_PASSWORD).
# The file is sent on standard input: "--data-binary @-" is the same as
# "--data-binary @bookride_logs.bulk.ndjson" run next to the file.
# The index is deleted first, so running the script twice still gives 20 documents.
# ==============================================================================
set -euo pipefail
cd "$(dirname "$0")"
docker compose ps --status running --services 2>/dev/null | grep -qx elasticsearch \
  || { echo "The stack is not running. Start it first:  ./start.sh" >&2; exit 1; }

es() { docker compose exec -T elasticsearch bash -c "curl -s -u \"elastic:\$ELASTIC_PASSWORD\" $1"; }

echo "== Delete the index (if it exists)"
es "-X DELETE 'http://localhost:9200/bookride-logs?ignore_unavailable=true'"; echo
echo "== Bulk load"
es "-H 'Content-Type: application/x-ndjson' -X POST 'http://localhost:9200/_bulk?refresh=true&filter_path=errors,took' --data-binary @-" < bookride_logs.bulk.ndjson; echo
echo "== Number of documents in bookride-logs (expected: 20)"
es "'http://localhost:9200/bookride-logs/_count?pretty'"
