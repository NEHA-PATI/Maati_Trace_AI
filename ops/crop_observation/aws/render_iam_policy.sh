#!/usr/bin/env bash
set -euo pipefail
BUCKET="${1:?usage: render_iam_policy.sh <bucket> [output]}"
OUT="${2:-$(dirname "$0")/iam-service-policy.rendered.json}"
sed "s/REPLACE_BUCKET_NAME/${BUCKET}/g" "$(dirname "$0")/iam-service-policy.json.template" > "$OUT"
echo "Rendered IAM policy: $OUT"
