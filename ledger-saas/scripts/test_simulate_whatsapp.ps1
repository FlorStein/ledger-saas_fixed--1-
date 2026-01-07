<#
 Test script para verificar simulate-whatsapp endpoint en Vercel
 Uso:
   $env:VERCEL_URL="https://ledger-saas-fixed-1.vercel.app"
   .\scripts\test_simulate_whatsapp.ps1 -PhoneNumberId "1033008476552418" -Message "hola"
#>

param(
    [string]$Message = "Test message from PowerShell",
    [string]$PhoneNumberId = "123456789012345",
    [string]$SenderWaId = "5491123456789",
    [string]$VercelUrl = $env:VERCEL_URL,
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

# If VERCEL_URL env var not set, prompt user
if (-not $VercelUrl) {
    Write-Host "⚠️  VERCEL_URL environment variable not set" -ForegroundColor Yellow
    $VercelUrl = Read-Host "Enter your Vercel deployment URL (e.g., https://my-project.vercel.app)"
}

# Ensure URL starts with http/https and has no trailing slash
if ($VercelUrl -notmatch '^(?i)https?://') {
    $VercelUrl = "https://$VercelUrl"
}
$VercelUrl = $VercelUrl.TrimEnd('/')

Write-Host "🧪 Testing Simulate WhatsApp Endpoint" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Vercel URL: $VercelUrl" -ForegroundColor Yellow
Write-Host "📱 Phone Number ID: $PhoneNumberId" -ForegroundColor Yellow
Write-Host "💬 Message: $Message" -ForegroundColor Yellow
Write-Host "👤 Sender WA ID: $SenderWaId" -ForegroundColor Yellow
Write-Host ""

# Unix timestamp as string
$unixNow = [int]([DateTime]::UtcNow.Subtract([DateTime]::UnixEpoch).TotalSeconds)
$unixStr = $unixNow.ToString()

# Build the payload matching Meta Cloud API structure (fiel a Meta)
$payload = @{
    object = "whatsapp_business_account"
    entry = @(
        @{
            id = "entry_$(Get-Random)"
            changes = @(
                @{
                    value = @{
                        messaging_product = "whatsapp"
                        metadata = @{
                            display_phone_number = "1234567890"
                            phone_number_id      = $PhoneNumberId
                        }
                        contacts = @(
                            @{
                                profile = @{ name = "Test User" }
                                wa_id   = $SenderWaId
                            }
                        )
                        messages = @(
                            @{
                                from      = $SenderWaId
                                id        = "wamid.$(Get-Random)_$(Get-Random)"
                                timestamp = $unixStr
                                type      = "text"
                                text      = @{ body = $Message }
                            }
                        )
                        # statuses opcional; omitir por simplicidad del test
                    }
                    field     = "messages"
                    timestamp = $unixStr
                }
            )
        }
    )
}

if ($VerboseOutput) {
    Write-Host "🧾 Payload to send:" -ForegroundColor Cyan
    ($payload | ConvertTo-Json -Depth 10) | ForEach-Object { Write-Host $_ }
    Write-Host ""
}

$endpoint = "$VercelUrl/api/simulate-whatsapp"
Write-Host "🔗 Endpoint: $endpoint" -ForegroundColor Yellow
Write-Host "🔍 Sending POST request..." -ForegroundColor Gray
Write-Host ""

# Use HttpClient to control status code and raw body across PowerShell versions
$handler = New-Object System.Net.Http.HttpClientHandler
$http    = New-Object System.Net.Http.HttpClient($handler)
try {
    $jsonBody = $payload | ConvertTo-Json -Depth 10
    $content  = New-Object System.Net.Http.StringContent($jsonBody, [System.Text.Encoding]::UTF8, "application/json")

    $resp = $http.PostAsync($endpoint, $content).Result
    $statusCode = [int]$resp.StatusCode
    $respText   = $resp.Content.ReadAsStringAsync().Result

    Write-Host ("↩️  HTTP Status: {0}" -f $statusCode) -ForegroundColor Cyan

    # Try to parse JSON; if fails, print raw
    $parsed = $null
    try {
        if ($respText) { $parsed = $respText | ConvertFrom-Json -ErrorAction Stop }
    } catch { $parsed = $null }

    if ($parsed) {
        Write-Host "✅ Request Completed" -ForegroundColor Green
        if ($parsed.status)        { Write-Host "📊 Response Status: $($parsed.status)" -ForegroundColor Cyan }
        if ($parsed.request_id)    { Write-Host "🆔 Request ID: $($parsed.request_id)" -ForegroundColor Cyan }
        if ($parsed.messages_count){ Write-Host "📨 Messages Forwarded: $($parsed.messages_count)" -ForegroundColor Cyan }
        if ($parsed.backend_response) {
            Write-Host "🔄 Backend Response:" -ForegroundColor Cyan
            $br = $parsed.backend_response
            if ($br.status)              { Write-Host "   Status: $($br.status)" -ForegroundColor Gray }
            if ($br.tenant_id)           { Write-Host "   Tenant ID: $($br.tenant_id)" -ForegroundColor Gray }
            if ($br.messages_processed)  { Write-Host "   Messages Processed: $($br.messages_processed)" -ForegroundColor Gray }
        }
        if ($parsed.warning) {
            Write-Host "⚠️  Warning: $($parsed.warning)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "ℹ️  Raw Response:" -ForegroundColor Yellow
        Write-Host $respText
    }

    if (-not $resp.IsSuccessStatusCode) {
        Write-Host "⚠️  Non-success status returned by server" -ForegroundColor Yellow
        exit 1
    }

    Write-Host ""
    Write-Host "✅ Webhook simulation completed" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Check Vercel logs: vercel logs api/simulate-whatsapp.js"
    Write-Host "  2. Check backend logs for tenant resolution and message processing"
    Write-Host "  3. Verify transaction in SQLite: SELECT * FROM transactions WHERE source_system='whatsapp'"

} catch {
    Write-Host ""
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red

    # Try to extract status code and raw body from WebException response stream
    $rawError = $null
    $statusFromEx = $null
    try {
        if ($_.Exception.Response) {
            $statusFromEx = try { [int]$_.Exception.Response.StatusCode } catch { $null }
            $stream = $_.Exception.Response.GetResponseStream()
            if ($stream) {
                $reader = New-Object System.IO.StreamReader($stream)
                $rawError = $reader.ReadToEnd()
                $reader.Dispose()
                $stream.Dispose()
            }
        }
    } catch { }

    if ($statusFromEx) {
        Write-Host "   Status Code: $statusFromEx" -ForegroundColor Red
    }
    if ($rawError) {
        Write-Host "   Raw Error Body:" -ForegroundColor Red
        Write-Host $rawError
    }

    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check VERCEL_URL is correct: $VercelUrl"
    Write-Host "  2. Verify endpoint exists: $endpoint"
    Write-Host "  3. Check Vercel logs: vercel logs"
    Write-Host "  4. Verify BACKEND_INGEST_URL in Vercel env"
    Write-Host "  5. Verify backend is running and accessible"
    Write-Host ""

    # Show actual URL and payload for manual testing
    Write-Host "📝 Manual testing:" -ForegroundColor Cyan
    Write-Host "  POST $endpoint" -ForegroundColor Gray
    Write-Host "  Content-Type: application/json" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Payload:" -ForegroundColor Gray
    Write-Host (($payload | ConvertTo-Json -Depth 10) | ForEach-Object { "  $_" })

    exit 1
} finally {
    if ($content) { $content.Dispose() }
    if ($http)    { $http.Dispose() }
}
