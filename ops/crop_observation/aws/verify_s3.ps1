param([Parameter(Mandatory=$true)][string]$Bucket)
$ErrorActionPreference = "Stop"
aws s3api get-public-access-block --bucket $Bucket
aws s3api get-bucket-ownership-controls --bucket $Bucket
aws s3api get-bucket-encryption --bucket $Bucket
aws s3api get-bucket-versioning --bucket $Bucket
aws s3api get-bucket-cors --bucket $Bucket
aws s3api get-bucket-policy-status --bucket $Bucket
Write-Host "S3 configuration read successfully."
