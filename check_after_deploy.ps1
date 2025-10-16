param(
    [string]$Url = 'http://localhost:8000/health',
    [int]$Retries = 30,
    [int]$Sleep = 2
)

Write-Host "Checking health endpoint: $Url"

for ($i = 1; $i -le $Retries; $i++) {
    Write-Host "Attempt $i/$Retries..."
    try {
        $resp = Invoke-RestMethod -Uri $Url -TimeoutSec 5 -ErrorAction Stop
        Write-Host "OK: endpoint returned:`n" ($resp | ConvertTo-Json -Depth 4)
        exit 0
    } catch {
        Write-Host "Not ready yet, sleeping $Sleep seconds"
        Start-Sleep -Seconds $Sleep
    }
}

Write-Error "Service did not become healthy after $Retries attempts"
exit 2
