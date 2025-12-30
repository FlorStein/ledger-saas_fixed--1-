# Script para configurar variables en Vercel
cd "c:\Users\mfrst\Downloads\ledger-saas_fixed (1)\ledger-saas"

Write-Host "Configurando variables de entorno en Vercel..." -ForegroundColor Green

# Instalar dependencias si no existen
npm install

# Configurar variables
Write-Host "`n[1/5] Agregando WHATSAPP_VERIFY_TOKEN..." -ForegroundColor Yellow
echo ledger_saas_verify_123 | vercel env add WHATSAPP_VERIFY_TOKEN

Write-Host "`n[2/5] Agregando META_APP_SECRET..." -ForegroundColor Yellow
echo 5e0c574f9bbfc25cf55529d49f26ee80 | vercel env add META_APP_SECRET

Write-Host "`n[3/5] Agregando BACKEND_INGEST_URL..." -ForegroundColor Yellow
echo http://localhost:8000/webhooks/whatsapp/meta/cloud | vercel env add BACKEND_INGEST_URL

Write-Host "`n[4/5] Agregando BACKEND_SHARED_SECRET..." -ForegroundColor Yellow
echo backend_secret_123 | vercel env add BACKEND_SHARED_SECRET

Write-Host "`n[5/5] Agregando TENANT_ROUTING_JSON..." -ForegroundColor Yellow
echo "{`"1234567890`":`"default`"}" | vercel env add TENANT_ROUTING_JSON

Write-Host "`n✅ Variables configuradas. Desplegando a Vercel..." -ForegroundColor Green
vercel --prod

Write-Host "`n✅ Despliegue completado!" -ForegroundColor Green
