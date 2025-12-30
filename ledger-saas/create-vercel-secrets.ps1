#!/usr/bin/env powershell
# Script para crear secrets en Vercel via API

# Obtener token de Vercel
$vercelToken = Read-Host "Ingresa tu token de Vercel (https://vercel.com/account/tokens)"

$projectId = "prj_oyE9FFVgwx4LiKK4J8Zm8Uj6KB28"
$teamId = "team_xzlo1SV0D10Deia7SUDh3vXy"

$headers = @{
    "Authorization" = "Bearer $vercelToken"
    "Content-Type" = "application/json"
}

$secrets = @{
    "whatsapp_verify_token" = "ledger_saas_verify_123"
    "meta_app_secret" = "5e0c574f9bbfc25cf55529d49f26ee80"
    "backend_ingest_url" = "http://localhost:8000/webhooks/whatsapp/meta/cloud"
    "backend_shared_secret" = "backend_secret_123"
    "tenant_routing_json" = '{"1234567890":"default"}'
}

Write-Host "Creando secrets en Vercel..." -ForegroundColor Green

foreach ($secret in $secrets.GetEnumerator()) {
    $body = @{
        name = $secret.Key
        value = $secret.Value
    } | ConvertTo-Json

    $url = "https://api.vercel.com/v10/projects/$projectId/env"
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method POST -Headers $headers -Body $body
        Write-Host "✅ $($secret.Key) creado" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error creando $($secret.Key): $_" -ForegroundColor Red
    }
}

Write-Host "`n✅ Secrets creados. Ahora ejecuta: vercel --prod" -ForegroundColor Green
