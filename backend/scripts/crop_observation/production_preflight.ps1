param(
  [string]$BaseUrl = "http://127.0.0.1:8015",
  [Parameter(Mandatory=$true)][string]$Bucket
)
$ErrorActionPreference = "Stop"
Invoke-RestMethod "$BaseUrl/health/ready" | Out-Host
aws s3api get-public-access-block --bucket $Bucket | Out-Host
aws s3api get-bucket-ownership-controls --bucket $Bucket | Out-Host
aws s3api get-bucket-encryption --bucket $Bucket | Out-Host
aws s3api get-bucket-versioning --bucket $Bucket | Out-Host
aws s3api get-bucket-cors --bucket $Bucket | Out-Host
Write-Host "Crop Observation production preflight completed." -ForegroundColor Green
