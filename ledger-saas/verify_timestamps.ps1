#!/usr/bin/env pwsh
# Test rápido de los cambios de timestamps
# Uso: .\verify_timestamps.ps1

param(
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [switch]$VerboseOutput
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔍 Verificación de Timestamps" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check Health Endpoint
Write-Host "1️⃣ Probando Health Endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod "$BackendUrl/webhooks/whatsapp/meta/cloud/health" -ErrorAction Stop
    
    if ($health.status -eq "healthy") {
        Write-Host "✅ Backend está healthy" -ForegroundColor Green
        
        # Check timestamps en response
        if ($health.database.tenants -and $health.database.tenants.Count -gt 0) {
            $tenant = $health.database.tenants[0]
            
            Write-Host "`n📊 Tenant encontrado:" -ForegroundColor Cyan
            Write-Host "   ID: $($tenant.id)" -ForegroundColor Gray
            Write-Host "   Nombre: $($tenant.name)" -ForegroundColor Gray
            
            if ($tenant.created_at) {
                Write-Host "   ✅ created_at: $($tenant.created_at)" -ForegroundColor Green
            } else {
                Write-Host "   ❌ created_at: NO ENCONTRADO" -ForegroundColor Red
            }
            
            if ($tenant.updated_at) {
                Write-Host "   ✅ updated_at: $($tenant.updated_at)" -ForegroundColor Green
            } else {
                Write-Host "   ❌ updated_at: NO ENCONTRADO" -ForegroundColor Red
            }
            
            if ($tenant.channels -and $tenant.channels.Count -gt 0) {
                $channel = $tenant.channels[0]
                Write-Host "`n📱 Channel encontrado:" -ForegroundColor Cyan
                Write-Host "   ID Externo: $($channel.external_id)" -ForegroundColor Gray
                
                if ($channel.created_at) {
                    Write-Host "   ✅ created_at: $($channel.created_at)" -ForegroundColor Green
                } else {
                    Write-Host "   ❌ created_at: NO ENCONTRADO" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "⚠️  No tenants encontrados en DB" -ForegroundColor Yellow
        }
        
        if ($VerboseOutput) {
            Write-Host "`n📄 Full Health Response:" -ForegroundColor Cyan
            $health | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ Backend no está healthy: $($health.status)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error conectando a backend: $_" -ForegroundColor Red
    Write-Host "   Asegúrate de que el backend esté corriendo en $BackendUrl" -ForegroundColor Yellow
    exit 1
}

# 2. Test de Python - Check modelos
Write-Host "`n2️⃣ Verificando modelos Python..." -ForegroundColor Yellow

$pythonScript = @"
import sys
sys.path.insert(0, 'backend')

try:
    from app.models import TimestampMixin, Tenant, Channel, Transaction, Counterparty, WhatsAppEvent, IncomingMessage
    
    models_with_mixin = [
        'Tenant',
        'Channel', 
        'Transaction',
        'Counterparty',
        'WhatsAppEvent',
        'IncomingMessage'
    ]
    
    print('✅ TimestampMixin importado correctamente')
    print('✅ Modelos con timestamps:')
    for model in models_with_mixin:
        print(f'   ✓ {model}')
    
    # Check que TimestampMixin tiene los atributos
    if hasattr(TimestampMixin, '__annotations__'):
        attrs = TimestampMixin.__annotations__
        if 'created_at' in attrs and 'updated_at' in attrs:
            print('✅ TimestampMixin tiene created_at y updated_at')
        else:
            print('❌ TimestampMixin falta atributos')
    
except ImportError as e:
    print(f'❌ Error importando modelos: {e}')
    sys.exit(1)
"@

try {
    cd backend -ErrorAction Stop
    $result = .\.venv\Scripts\python.exe -c $pythonScript 2>&1
    Write-Host $result -ForegroundColor Gray
    cd ..
} catch {
    Write-Host "⚠️  No se pudo verificar modelos Python" -ForegroundColor Yellow
}

# 3. Test de DB
Write-Host "`n3️⃣ Verificando columnas en DB..." -ForegroundColor Yellow

$sqliteTest = @"
import sqlite3
import sys

try:
    db = sqlite3.connect('backend/app.db')
    cursor = db.cursor()
    
    # Check tabla tenants
    cursor.execute("PRAGMA table_info(tenants)")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    
    print('📋 Columnas en tabla "tenants":')
    for col in col_names:
        print(f'   ✓ {col}')
    
    if 'created_at' in col_names:
        print('✅ Columna created_at existe')
    else:
        print('❌ Columna created_at NO existe - recrear DB')
    
    if 'updated_at' in col_names:
        print('✅ Columna updated_at existe')
    else:
        print('❌ Columna updated_at NO existe - recrear DB')
    
    db.close()
except Exception as e:
    print(f'⚠️  Error accediendo DB: {e}')
    print('   (DB puede no existir aún)')
"@

try {
    $result = python -c $sqliteTest 2>&1
    Write-Host $result -ForegroundColor Gray
} catch {
    Write-Host "⚠️  No se pudo verificar DB (puede no existir)" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Verificación completada" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📝 Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Si no ves timestamps, borra backend/app.db y relanza el backend"
Write-Host "2. Ejecuta: Remove-Item backend/app.db -ErrorAction SilentlyContinue" -ForegroundColor Gray
Write-Host "3. Luego: cd backend" -ForegroundColor Gray
Write-Host "4. Y: .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "Para más detalles, ve: TIMESTAMP_IMPLEMENTATION.md" -ForegroundColor Cyan
