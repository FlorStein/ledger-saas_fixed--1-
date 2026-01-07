# Test script para verificar health endpoint del backend
# Uso: .\test_health.ps1

$ErrorActionPreference = "Stop"

Write-Host "🏥 Testing Backend Health Endpoint" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$BACKEND_URL = "http://localhost:8000"
$HEALTH_ENDPOINT = "$BACKEND_URL/webhooks/whatsapp/meta/cloud/health"

Write-Host ""
Write-Host "📍 Endpoint: $HEALTH_ENDPOINT" -ForegroundColor Yellow

try {
    Write-Host "🔍 Sending GET request..." -ForegroundColor Gray
    $response = Invoke-WebRequest -Uri $HEALTH_ENDPOINT -Method Get -ContentType "application/json" -ErrorAction Stop
    
    $body = $response.Content | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "✅ Health Check Passed!" -ForegroundColor Green
    Write-Host ""
    
    # Print formatted response
    Write-Host "📊 Status: $($body.status)" -ForegroundColor Cyan
    Write-Host "⏰ Timestamp: $($body.timestamp)" -ForegroundColor Cyan
    Write-Host ""
    
    # Environment section
    Write-Host "🔐 Environment Configuration:" -ForegroundColor Cyan
    Write-Host "  - META_WA_TOKEN: $($body.environment.META_WA_TOKEN)"
    Write-Host "  - BACKEND_SHARED_SECRET: $($body.environment.BACKEND_SHARED_SECRET)"
    Write-Host "  - META_WA_PHONE_NUMBER_ID: $($body.environment.META_WA_PHONE_NUMBER_ID)"
    Write-Host ""
    
    # Database section
    Write-Host "💾 Database Status:" -ForegroundColor Cyan
    Write-Host "  - Total Tenants: $($body.database.total_tenants)"
    Write-Host "  - Meta Channels: $($body.database.meta_channels)"
    Write-Host ""
    
    # Tenants list
    if ($body.database.tenants.Count -gt 0) {
        Write-Host "👥 Tenants Details:" -ForegroundColor Cyan
        foreach ($tenant in $body.database.tenants) {
            Write-Host "  ├─ ID: $($tenant.id)" -ForegroundColor Gray
            Write-Host "  │  Name: $($tenant.name)"
            Write-Host "  │  Phone Number ID: $($tenant.phone_number_id)"
            Write-Host "  │  Created: $($tenant.created_at)"
            if ($tenant.channels.Count -gt 0) {
                Write-Host "  │  Channels:" -ForegroundColor Gray
                foreach ($channel in $tenant.channels) {
                    Write-Host "  │    - External ID: $($channel.external_id)"
                    Write-Host "  │      Kind: $($channel.kind)"
                    Write-Host "  │      Created: $($channel.created_at)"
                }
            }
        }
    } else {
        Write-Host "  ⚠️  No tenants found in database. Run backend seed.py to initialize." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "💡 Notes:" -ForegroundColor Cyan
    foreach ($note in $body.notes) {
        Write-Host "  • $note"
    }
    
    Write-Host ""
    Write-Host "✅ Backend is healthy and ready to receive webhooks!" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response.StatusCode) {
        Write-Host "   Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Verify backend is running: python app/main.py"
    Write-Host "  2. Check port 8000 is accessible"
    Write-Host "  3. Verify environment variables are set"
    Write-Host ""
    
    exit 1
}
