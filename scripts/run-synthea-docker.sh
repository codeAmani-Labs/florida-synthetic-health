#!/usr/bin/env bash
# Optional: generate richer clinical CSV via MITRE Synthea in Docker.
# Output is still synthetic. Default 100 lives — raise -p only on a fat machine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/data/synthea"
mkdir -p "$OUT"
N="${1:-100}"
echo "Synthea docker generate n=$N -> $OUT"
docker run --rm \
  -e JAVA_OPTS="-Xmx4g" \
  -v "$OUT":/out \
  eclipse-temurin:17-jdk \
  bash -lc "set -e
    apt-get update -qq && apt-get install -y -qq git >/dev/null
    git clone --depth 1 https://github.com/synthetichealth/synthea.git /tmp/synthea
    cd /tmp/synthea
    ./gradlew -q check -x test || true
    ./run_synthea -p $N -s 42 Florida --exporter.csv.export true --exporter.fhir.export false
    cp -r output/csv /out/"
echo "done $OUT"
