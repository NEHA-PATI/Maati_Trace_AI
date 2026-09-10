#!/usr/bin/env bash
set -euo pipefail

: "${BUCKET:?Set BUCKET, e.g. maatitrace-dev-crop-observation-123456789012}"
REGION="${REGION:-ap-south-1}"
CORS_FILE="${CORS_FILE:-$(dirname "$0")/cors.local.json}"
POLICY_TEMPLATE="${POLICY_TEMPLATE:-$(dirname "$0")/bucket-policy.json.template}"
LIFECYCLE_FILE="${LIFECYCLE_FILE:-$(dirname "$0")/lifecycle.json}"
TMP_POLICY="$(mktemp)"
trap 'rm -f "$TMP_POLICY"' EXIT

if aws s3api head-bucket --bucket "$BUCKET" >/dev/null 2>&1; then
  echo "Bucket already exists: $BUCKET"
else
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws s3api create-bucket \
      --bucket "$BUCKET" \
      --region "$REGION" \
      --create-bucket-configuration "LocationConstraint=$REGION"
  fi
fi

aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws s3api put-bucket-ownership-controls --bucket "$BUCKET" --ownership-controls \
  'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'

aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":false}]}'

aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-cors --bucket "$BUCKET" --cors-configuration "file://$CORS_FILE"
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration "file://$LIFECYCLE_FILE"

sed "s/REPLACE_BUCKET_NAME/$BUCKET/g" "$POLICY_TEMPLATE" > "$TMP_POLICY"
aws s3api put-bucket-policy --bucket "$BUCKET" --policy "file://$TMP_POLICY"

cat <<EOF
S3 bucket configured.
Bucket: $BUCKET
Region: $REGION
Next:
  1. Attach aws/iam-service-policy.json.template (replace bucket name) to the service IAM role/user.
  2. Set MEDIA_STORAGE_BACKEND=S3
  3. Set AWS_REGION=$REGION
  4. Set CROP_OBSERVATION_S3_BUCKET=$BUCKET
EOF
