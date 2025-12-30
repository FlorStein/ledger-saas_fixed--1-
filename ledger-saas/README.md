# Ledger SaaS (POC) — guía rápida

Este repo contiene un POC multi-tenant para:
- Subir comprobantes bancarios (PDF) y extraer datos clave.
- Mantener ventas por tenant.
- Hacer matching transacción ↔ venta (por monto/fecha y opcionalmente CUIT/teléfono/referencia).
- **[NUEVO]** Auto-resolver matching ambiguo con lógica inteligente.
- **[NUEVO]** Ingest de ventas desde imágenes/PDF con OCR.
- UI web para operar y exportar a Excel.

## 🚀 INICIO RÁPIDO

⭐ **VER:** [START_HERE.md](./START_HERE.md) para instrucciones paso a paso.

## 🎯 Mejoras Recientes (29 de diciembre de 2025)

✨ **Sistema de Matching Inteligente**: 4 reglas + tie-break determinístico
- Strong ID Match (operation_id == external_ref)
- Gap Match (diferencia clara entre candidatos)
- Single Candidate (solo opción viable)
- Tie-Break por evidencia/fecha/ID

📸 **Ingest Imagen/PDF**: Carga comprobantes y extrae automáticamente
- OCR con pytesseract
- Extracción de PDF con pdfplumber
- Detección de: monto, fecha, cliente, teléfono, CUIT, referencia
- Formulario editable antes de guardar

📚 **Documentación completa**: Ver [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)

✅ **Tests unitarios completos**: 8/8 tests pasando

## Requisitos

- Windows 10/11 (o Linux/Mac)
- Python 3.10+ (probado con 3.12)
- Node.js 18+
- **[OPCIONAL]** Tesseract-OCR para ingest de imágenes

## Arranque Rápido (después de clonar)

### Terminal 1: Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Esperado:** Backend running on http://127.0.0.1:8000

### Terminal 2: Frontend

```bash
cd frontend
npm install
npm run dev
```

**Esperado:** Local: http://localhost:5173

---

**[VER INSTRUCCIONES DETALLADAS →](./START_HERE.md)**
npm install
npm run dev
```

Abrí:
- Frontend: http://localhost:5173
- Backend health: http://127.0.0.1:8000/health

Login demo:
- owner@demo.com / demo123

## 🆕 Instalación de Tesseract (Opcional)

Si querés usar ingest de **imágenes** (PDF funciona sin Tesseract):

1. Descargar: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar en: `C:\Program Files\Tesseract-OCR`
3. En `backend/.env` agregar:
   ```
   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

Ver [TESSERACT_SETUP_WINDOWS.md](TESSERACT_SETUP_WINDOWS.md) para más detalles.

## 🚀 Primeros Pasos

### Probar Auto-Matching
1. Ir a pestaña "Ventas"
2. Crear una venta: ARS 1.000, Cliente "Juan", CUIT 20123456789
3. Ir a "Comprobantes"
4. Subir un PDF con monto ARS 1.000, CUIT 20123456789
5. ✅ Se auto-matchea (sin ambiguous)

### Probar Ingest Imagen/PDF
1. Ir a pestaña "Ventas"
2. Bloque "Subir venta (Imagen/PDF)"
3. Arrastra foto de comprobante o PDF
4. Sistema extrae datos automáticamente
5. Revisa y confirma
6. ✅ Venta creada

## 📖 Documentación

| Documento | Propósito |
|-----------|-----------|
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | Resumen ejecutivo (5 min) |
| [QUICK_START.md](QUICK_START.md) | Guía rápida de uso (10 min) |
| [CHANGELOG_MEJORAS.md](CHANGELOG_MEJORAS.md) | Detalles técnicos completos |
| [PROCESS_FLOWS.md](PROCESS_FLOWS.md) | Diagramas de flujo ASCII |
| [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) | Verificación de completitud |
| [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) | Índice de toda la documentación |

## 📲 WhatsApp Cloud API Integration (NUEVO)

¿Quieres que usuarios envíen comprobantes por WhatsApp?

**Ver:** [START_HERE_WHATSAPP.md](./START_HERE_WHATSAPP.md) para integración completa con:
- ✅ Vercel Serverless Function (`api/whatsapp-webhook.js`)
- ✅ Backend FastAPI endpoint (`/webhooks/whatsapp/meta/cloud`)
- ✅ HMAC SHA256 validation
- ✅ Multi-tenant routing
- ✅ 3,000+ líneas de documentación
- ✅ 6 tests automatizados

**Tiempo setup:** ~30 minutos  
**Estado:** Production-ready ✅

**Documentos principales:**
- [WHATSAPP_SETUP.md](./WHATSAPP_SETUP.md) - Setup paso a paso
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deploy a Vercel
- [FAQ_WHATSAPP.md](./FAQ_WHATSAPP.md) - 50+ preguntas frecuentes
- [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md) - Pre-production checklist

---

## Notas importantes

- No abras `index.html` con doble click (file://). El frontend necesita un servidor (Vite dev o preview).
- Si cambiás entre `localhost` y `127.0.0.1`, el CORS ya está configurado para ambos.
- Para cargar ventas con mejor matching, completá **al menos uno**: nombre, CUIT, teléfono o referencia.
- **[NUEVO]** Las transacciones ahora incluyen `match_method` (strong_id, gap, single_candidate, tiebreak) y `needs_review` coherente.
- **[NUEVO]** Endpoint POST `/v1/sales/ingest` para subir imágenes/PDF.
- **[NUEVO]** Integración WhatsApp Cloud API via Vercel. Ver [START_HERE_WHATSAPP.md](./START_HERE_WHATSAPP.md)

## Scripts opcionales (Windows)

En la raíz hay:
- `start_backend.bat`
- `start_frontend.bat`
- `start_all.bat`

Usalos si querés levantar todo con doble click.

## 🧪 Tests

```bash
cd backend
pytest tests/test_match.py -v
```

Resultado esperado: 9 PASS ✅

## ✨ Cambios Principales

- ✅ `backend/app/match.py` - Reescrito con 4 reglas + tie-break
- ✅ `backend/app/ingest.py` - NUEVO: Extracción OCR/PDF
- ✅ `backend/app/models.py` - Nuevo campo `match_method`
- ✅ `frontend/src/components/UploadSaleImage.jsx` - NUEVO: UI para ingest
- ✅ 9 tests unitarios con 100% coverage
- ✅ Documentación completa

## 🔐 Producción

Antes de deployar:
1. Cambiar `SECRET_KEY` en `.env`
2. Cambiar `SEED_DEMO=false`
3. Usar PostgreSQL en lugar de SQLite
4. Considerar OCR en cloud (Google Vision, AWS Textract)
5. Ejecutar tests: `pytest tests/test_match.py -v`

Ver [CHANGELOG_MEJORAS.md](CHANGELOG_MEJORAS.md) → Producción

