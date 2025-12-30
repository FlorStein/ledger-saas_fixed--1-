# 🔐 SECURITY CHECKLIST - Pre-Production

Verifica estos items antes de desplegar a producción.

---

## 🔑 Secrets & Credentials

### META_APP_SECRET
- [ ] Obtenido de Meta Developer Dashboard (Settings → Basic)
- [ ] No compartido públicamente en GitHub
- [ ] No hardcodeado en código (usa Vercel env vars)
- [ ] Diferentes para Development/Staging/Production
- [ ] Guardado en lugar seguro (password manager)

**Verificar:**
```bash
# NO debe estar en código
grep -r "META_APP_SECRET=.*" .

# Debe estar en Vercel
vercel env list | grep META_APP_SECRET
```

---

### BACKEND_SHARED_SECRET
- [ ] Generado aleatoriamente (mínimo 32 caracteres)
- [ ] Idéntico en backend/.env y Vercel
- [ ] No el mismo que otros secretos
- [ ] Rotado cada 3-6 meses

**Generar un nuevo secret:**
```bash
# Linux/macOS
openssl rand -hex 32

# Windows PowerShell
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

**Verificar sincronización:**
```bash
# Backend
grep BACKEND_SHARED_SECRET backend/.env

# Vercel
vercel env list | grep BACKEND_SHARED_SECRET

# Deben ser IDÉNTICOS
```

---

### WHATSAPP_VERIFY_TOKEN
- [ ] Único (no reutilizado en otros proyectos)
- [ ] Mínimo 16 caracteres
- [ ] Sin caracteres especiales problemáticos
- [ ] Configurado en Meta Dashboard

---

## 🌐 Network & Infrastructure

### BACKEND_INGEST_URL
- [ ] Usa HTTPS (no HTTP)
- [ ] Apunta a dominio correcto (staging vs prod)
- [ ] No expone puertos internos (8000, 3000)
- [ ] Requiere autenticación (Bearer token)

**Verificar:**
```bash
# Debe ser HTTPS
echo $BACKEND_INGEST_URL | grep -c "^https://"  # Debe retornar 1

# Testear acceso
curl -I $BACKEND_INGEST_URL
```

---

### TENANT_ROUTING_JSON
- [ ] Contiene mapping correcto de phone_number_id → tenant_id
- [ ] No incluye datos sensibles del tenant
- [ ] Actualizado para todos los tenants activos
- [ ] Validado con JSON lint

**Validar JSON:**
```bash
# Windows PowerShell
$json = Get-Content '.env.vercel.example' | Select-String 'TENANT_ROUTING_JSON' | ForEach-Object { $_ -replace '.*=', '' }
$json | ConvertFrom-Json

# Linux/macOS
echo '{"1234567890":"tenant_demo"}' | jq .
```

---

## 🔒 Code Security

### HMAC Validation
- [ ] Usa `crypto.timingSafeEqual()` (no == comparación)
- [ ] Lee raw body (no parsed JSON) para validar firma
- [ ] Valida header `X-Hub-Signature` antes de procesar payload

**Verificar en código:**
```bash
grep -A5 "timingSafeEqual" api/whatsapp-webhook.js
```

---

### Bearer Token Validation
- [ ] Compara token completo (no substring match)
- [ ] Retorna 401 en fallo
- [ ] No loguea el token en logs

**Verificar en código:**
```bash
grep -A5 "Bearer" backend/app/routers/whatsapp.py
```

---

### Sensitive Data Logging
- [ ] No loguea full phone numbers
- [ ] No loguea payloads completos
- [ ] No loguea tokens/secrets
- [ ] Loguea IDs y transacciones de forma safe

**Auditar logs:**
```bash
grep -r "logger\." backend/app/routers/whatsapp.py

# Verificar: No hay "+55", "Bearer", "sha256=" en logs
```

---

## 🚀 Vercel Deployment

### Environment Variables
- [ ] Todas las 5 variables agregadas en Vercel
- [ ] Protegidas (encryption at rest)
- [ ] Diferentes values para preview vs production
- [ ] No accesibles desde browser (solo backend functions)

**Verificar:**
```bash
vercel env list

# Debe mostrar:
# WHATSAPP_VERIFY_TOKEN
# META_APP_SECRET
# BACKEND_INGEST_URL
# BACKEND_SHARED_SECRET
# TENANT_ROUTING_JSON
```

---

### Build & Deploy
- [ ] Build sucesivo (sin errores de build)
- [ ] Deploy a preview funciona (staging test)
- [ ] Deploy a production sucesivo
- [ ] Rollback procedure testeado

**Vercel logs:**
```bash
vercel logs --follow

# Debe ser limpio (sin errores)
```

---

## 🛡️ API Security

### Rate Limiting
- [ ] Implementado en Vercel o backend (o ambos)
- [ ] Límite: 10 requests/minuto por IP
- [ ] Responde 429 (Too Many Requests)

**Futuro:** Implementar después de MVP

---

### CORS & CSP
- [ ] CORS configurado (solo dominios permitidos)
- [ ] Content-Security-Policy headers
- [ ] No permite wildcard (*) en CORS

**Verificar:**
```bash
curl -i https://tu-vercel-app.vercel.app/api/whatsapp-webhook

# Buscar headers:
# access-control-allow-origin
# content-security-policy
```

---

### Input Validation
- [ ] Payloads > 10MB rechazados
- [ ] JSON payloads validados
- [ ] phone_number_id en formato válido
- [ ] Caracteres de control no permitidos

---

## 📝 Logging & Monitoring

### Logs
- [ ] Logs habilitados en Vercel
- [ ] Logs habilitados en backend
- [ ] Rotación de logs (no llenan disco)
- [ ] Retención: 30 días mínimo

**Ver logs:**
```bash
vercel logs --prod --follow
```

---

### Monitoring
- [ ] Error rate < 1% (monitoreado)
- [ ] Response time < 1s (95th percentile)
- [ ] Uptime > 99.5% (monitoreado)
- [ ] Alertas configuradas para errors

**Herramientas sugeridas:**
- Sentry (error tracking)
- DataDog (monitoring)
- New Relic (APM)
- CloudFlare (analytics)

---

## 🔄 Incident Response

### Rollback Plan
- [ ] Documentado qué hacer si bug en producción
- [ ] Proceso de rollback testeado
- [ ] Comunicación plan en lugar

**Checklist de rollback:**
```
1. Detectar problema en vercel logs --prod
2. Revertir cambios en GitHub (git revert)
3. Vercel re-deploy automático
4. Testear: curl https://prod.vercel.app/api/...
5. Notificar al equipo
6. Post-mortem
```

---

### Compromise Plan
- [ ] Qué hacer si secret comprometido
- [ ] Contacto de Meta (incident report)
- [ ] Rotation de todos los secrets
- [ ] Audit de logs

**Contacto Meta:**
```
https://developers.facebook.com/support
→ Security Issue Report
```

---

## 📋 Database Security

### Backend Database
- [ ] Usa HTTPS para conectar (si remota)
- [ ] Credenciales en env vars (no hardcoded)
- [ ] Backups automáticos habilitados
- [ ] Read replicas para solo-lectura

---

### Data Retention
- [ ] Policy clara de cuándo borrar data
- [ ] GDPR compliance (si aplica)
- [ ] Derecho al olvido implementado
- [ ] Encriptación en reposo

---

## 🧪 Testing Pre-Producción

### Seguridad
- [ ] Test: Signature validation (false positives)
- [ ] Test: Bearer token validation (false positives)
- [ ] Test: Rate limiting
- [ ] Test: XSS injection prevention

**Ejecutar tests:**
```bash
python test_whatsapp_integration.py -v

# Verificar: 6/6 tests PASS
```

---

### Load Testing
- [ ] Simular 100 webhooks/segundo
- [ ] Backend aguanta carga
- [ ] No hay memory leaks
- [ ] Respuesta sigue siendo < 1s

**Herramientas:**
- Apache JMeter
- Locust
- k6
- Artillery

---

## 📞 Communication Plan

### Before Launch
- [ ] Equipo informado de deployment
- [ ] Stakeholders notificados
- [ ] Runbook compartido
- [ ] On-call person designado

---

### During Incident
- [ ] Slack channel #incidents
- [ ] Postmortem en 24 horas
- [ ] Root cause analysis
- [ ] Prevention plan

---

## ✅ Final Checklist

Marcar TODOS los items antes de production:

**Secrets:**
- [ ] META_APP_SECRET seguro
- [ ] BACKEND_SHARED_SECRET 32+ chars
- [ ] WHATSAPP_VERIFY_TOKEN único
- [ ] Ningún secret en GitHub

**Code:**
- [ ] HMAC validation correcto
- [ ] Bearer token validation correcto
- [ ] Sin datos sensibles en logs
- [ ] Input validation funcionando

**Infrastructure:**
- [ ] BACKEND_INGEST_URL HTTPS
- [ ] TENANT_ROUTING_JSON válido
- [ ] Vercel env vars todas configuradas
- [ ] Build/Deploy exitoso

**Monitoring:**
- [ ] Logs habilitados y monitoreados
- [ ] Alertas configuradas
- [ ] Rollback procedure testeado
- [ ] Incident response plan listo

**Testing:**
- [ ] 6/6 tests PASANDO
- [ ] Load testing completado
- [ ] Security testing completado
- [ ] End-to-end testing OK

---

## 🚨 Red Flags (NO Deploy si...)

❌ **NO deployes si:**
- [ ] Algún secret en GitHub
- [ ] Tests no pasan (< 6/6)
- [ ] Error logs > 0
- [ ] HMAC validation no testeado
- [ ] Bearer token validation no testeado
- [ ] Backend no responde en HTTPS
- [ ] No hay monitoring/alertas
- [ ] No hay rollback plan
- [ ] No hay incident response plan

---

## ✨ Green Light

✅ **OK para producción si:**
- [ ] Todos los items arriba están checked
- [ ] Zero warnings en logs
- [ ] Tests passing 6/6
- [ ] Load testing OK
- [ ] Security audit passed
- [ ] Team sign-off
- [ ] Runbook listo

---

**Fecha de deployment:** _______________

**Responsable:** _______________

**Aprobado por:** _______________

---

**Después del deployment:**
```bash
# 1. Verificar
curl https://prod-app.vercel.app/api/whatsapp-webhook?hub.mode=subscribe&hub.verify_token=...

# 2. Monitorear
vercel logs --prod --follow

# 3. Testear end-to-end
# Enviar mensaje WhatsApp y ver en logs

# 4. Esperar 24 horas sin incidentes
# Luego considerar "successful launch"
```

