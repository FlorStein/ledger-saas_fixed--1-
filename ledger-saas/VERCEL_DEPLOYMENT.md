# Vercel Deployment Guide

## Arquitectura del Monorepo

Este proyecto usa una estructura de monorepo con múltiples componentes:

```
ledger-saas/
├── frontend/          → Vite + React (se sirve en /)
├── api/              → Funciones serverless (se sirven en /api/*)
├── backend/          → FastAPI local (NO se deploya en Vercel)
└── vercel.json       → Configuración de deployment
```

## Configuración de Vercel

### vercel.json

El archivo `vercel.json` en la raíz controla todo el deployment:

```json
{
  "version": 2,
  "public": true,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "dist" }
    },
    {
      "src": "api/**/*.js",
      "use": "@vercel/node"
    }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/$1" },
    { "src": "/(.*)", "dest": "/frontend/$1" }
  ]
}
```

**Clave:**
- `builds`: Define cómo construir frontend (Vite) y funciones (Node.js)
- `routes`: Mapea URLs públicas a builds internos
- `/api/*` → funciones serverless
- `/*` → frontend estático

### Settings de Vercel Dashboard

**IMPORTANTE:** NO cambiar estas configuraciones en el dashboard:

- **Root Directory:** `.` (raíz) - NO cambiar a `frontend/`
- **Build Command:** (dejar vacío - `vercel.json` lo controla)
- **Output Directory:** (dejar vacío - `vercel.json` lo controla)
- **Install Command:** (dejar vacío - auto-detectado)

Si cambiás Root Directory, las funciones en `api/` dejarán de funcionar.

## Deployment

### Primera vez

1. **Install Vercel CLI:**
   ```powershell
   npm install -g vercel
   ```

2. **Login:**
   ```powershell
   vercel login
   ```

3. **Deploy:**
   ```powershell
   cd "ruta\al\proyecto\ledger-saas"
   vercel --prod
   ```

### Updates posteriores

```powershell
cd "ruta\al\proyecto\ledger-saas"
vercel --prod
```

## Variables de Entorno

Configurá estas variables en Vercel (todas son secrets):

```powershell
# Backend URL (túnel ngrok/cloudflare)
vercel env add BACKEND_INGEST_URL production
# Ejemplo: https://abc123.ngrok.io/webhooks/whatsapp/meta/cloud

# Secret compartido (debe coincidir con backend)
vercel env add BACKEND_SHARED_SECRET production
# Ejemplo: ledger_saas_backend_secret

# WhatsApp Meta Token (opcional si solo probás con simulate)
vercel env add META_WA_TOKEN production

# Phone Number ID de Meta (opcional)
vercel env add META_WA_PHONE_NUMBER_ID production
```

Después de agregar variables, redeploy:
```powershell
vercel --prod
```

## Verificación

Después del deploy, verificá:

1. **Frontend:** `https://tu-app.vercel.app/`
   - Debería mostrar la aplicación React
   
2. **API Simulate:** `https://tu-app.vercel.app/api/simulate-whatsapp`
   - Usar POST con body JSON para simular mensajes
   
3. **API Webhook:** `https://tu-app.vercel.app/api/whatsapp-webhook`
   - Endpoint que Meta llama cuando llegan mensajes reales

## Troubleshooting

### Frontend no se ve (404 o página en blanco)

**Causa:** Root Directory mal configurado o `vercel.json` incorrecto.

**Solución:**
1. Verificá que `vercel.json` esté en la raíz (no en subdirectorio)
2. En Vercel dashboard → Project Settings → General:
   - Root Directory: `.` (punto solo)
   - Build Command: (vacío)
   - Output Directory: (vacío)
3. Redeploy: `vercel --prod`

### Funciones /api/* devuelven 404

**Causa:** Root Directory apunta a `frontend/`, ocultando `api/`.

**Solución:**
1. Cambiá Root Directory a `.` en settings
2. Verificá que `api/` esté en la raíz del repo
3. Redeploy

### Frontend se ve pero CSS/assets no cargan

**Causa:** Rutas relativas en Vite mal configuradas.

**Solución:**
1. Verificá `frontend/vite.config.js`:
   ```js
   export default defineConfig({
     base: '/',  // no './' ni '/frontend/'
     plugins: [react()]
   });
   ```
2. Rebuild: `cd frontend && npm run build`
3. Redeploy: `vercel --prod`

### Variables de entorno no funcionan

**Causa:** No se redeploy después de agregar variables.

**Solución:**
```powershell
vercel env pull  # descarga .env.local para dev
vercel --prod    # redeploy con nuevas variables
```

## Arquitectura de Producción

```
Usuario
  ↓
Vercel (https://tu-app.vercel.app)
  ├── / → frontend (Vite static)
  ├── /api/simulate-whatsapp → función Node.js
  └── /api/whatsapp-webhook → función Node.js
        ↓
      [reenvía a]
        ↓
Backend FastAPI (ngrok/cloudflare tunnel)
  └── POST /webhooks/whatsapp/meta/cloud
        ↓
      [procesa mensaje]
        ↓
      SQLite DB local
```

**Notas:**
- Frontend y funciones API se deployean en Vercel (edge)
- Backend FastAPI queda local y se expone con túnel público
- Meta → Vercel → Backend (vía túnel) → DB

## Logs y Debugging

```powershell
# Ver logs en tiempo real
vercel logs tu-app.vercel.app --follow

# Ver logs de una función específica
vercel logs tu-app.vercel.app --follow | Select-String "api/whatsapp-webhook"

# Ver deployments recientes
vercel ls

# Ver info del deployment actual
vercel inspect
```

## Rollback

Si un deploy rompe algo:

```powershell
# Listar deployments
vercel ls

# Promover deployment anterior a producción
vercel promote <deployment-url>
```

## Referencias

- [Vercel Monorepo](https://vercel.com/docs/concepts/monorepos)
- [Vercel Build Configuration](https://vercel.com/docs/build-step)
- [Vercel Routes](https://vercel.com/docs/configuration#routes)
