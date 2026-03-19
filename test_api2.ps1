$body = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8090/api/auth/login" -Method POST -ContentType "application/json" -Body $body
Write-Host "Status Code: $($response.StatusCode)"
Write-Host "Response: $($response.Content)"
