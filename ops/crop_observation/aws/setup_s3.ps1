param(
  [Parameter(Mandatory=$true)][string]$Bucket,
  [string]$Region = "ap-south-1",
  [string]$CorsFile = "$PSScriptRoot\cors.local.json"
)

$ErrorActionPreference = "Stop"
$PolicyTemplate = "$PSScriptRoot\bucket-policy.json.template"
$LifecycleFile = "$PSScriptRoot\lifecycle.json"
$TempPolicy = Join-Path $env:TEMP "maatitrace-crop-observation-bucket-policy.json"

aws s3api head-bucket --bucket $Bucket 2>$null
if ($LASTEXITCODE -ne 0) {
  if ($Region -eq "us-east-1") {
    aws s3api create-bucket --bucket $Bucket --region $Region
  } else {
    aws s3api create-bucket --bucket $Bucket --region $Region --create-bucket-configuration "LocationConstraint=$Region"
  }
}

aws s3api put-public-access-block --bucket $Bucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
aws s3api put-bucket-ownership-controls --bucket $Bucket --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'
aws s3api put-bucket-encryption --bucket $Bucket --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":false}]}'
aws s3api put-bucket-versioning --bucket $Bucket --versioning-configuration Status=Enabled
aws s3api put-bucket-cors --bucket $Bucket --cors-configuration "file://$CorsFile"
aws s3api put-bucket-lifecycle-configuration --bucket $Bucket --lifecycle-configuration "file://$LifecycleFile"

(Get-Content $PolicyTemplate -Raw).Replace("REPLACE_BUCKET_NAME", $Bucket) | Set-Content $TempPolicy -Encoding UTF8
aws s3api put-bucket-policy --bucket $Bucket --policy "file://$TempPolicy"
Remove-Item $TempPolicy -ErrorAction SilentlyContinue

Write-Host "S3 bucket configured: $Bucket ($Region)"
Write-Host "Now attach iam-service-policy.json.template (replace bucket name) to the service IAM principal."
