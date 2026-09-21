param(
  [Parameter(Mandatory=$true)][string]$Bucket,
  [string]$Output = "$PSScriptRoot\iam-service-policy.rendered.json"
)
$Template = Get-Content "$PSScriptRoot\iam-service-policy.json.template" -Raw
$Template.Replace("REPLACE_BUCKET_NAME", $Bucket) | Set-Content $Output -Encoding UTF8
Write-Host "Rendered IAM policy: $Output"
