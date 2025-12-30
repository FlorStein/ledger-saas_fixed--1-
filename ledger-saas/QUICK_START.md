# Ledger SaaS - Guía Rápida de Uso (Mejoras)

## Inicio Rápido

### 1. Setup Inicial

```bash
# Backend
cd backend
pip install -r requirements.txt

# Instalar Tesseract OCR (requerido para ingest de imágenes)
# Windows: Descargar desde https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract

# Copiar configuración
cp .env.example .env

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Frontend
cd frontend
npm install
npm run dev
```

Acceder a: `http://localhost:5173`

---

## Características Nuevas

### A) Auto-Matching Inteligente

El sistema ahora resuelve automáticamente transacciones ambiguas basándose en:

1. **ID Fuerte**: Si `operation_id` coincide exactamente con `external_ref` de una venta
2. **Gap Suficiente**: Si hay diferencia de 10+ puntos entre mejor y segundo candidato
3. **Único Candidato**: Si solo hay una venta viable con score alto
4. **Tie-break Inteligente**: Si hay empate, elige por:
   - Evidencia fuerte (CUIT > Teléfono > Nombre)
   - Cercanía de fecha
   - ID menor

**Resultado**: Menos transacciones marcadas como ambiguas, menos confirmación manual.

### B) Ingest de Ventas por Imagen/PDF

En la pestaña **"Ventas"**, nuevo bloque: **"Subir venta (Imagen/PDF)"**

#### Flujo:
1. Haz click o arrastra una foto/PDF del comprobante
2. El sistema extrae automáticamente:
   - Monto
   - Fecha
   - Nombre del cliente
   - Teléfono
   - CUIT
   - Referencia (pedido/orden)
3. Aparece un formulario prellenado
4. Revisa y ajusta si es necesario
5. Haz click "Guardar venta"

#### Formatos soportados:
- Imágenes: JPG, PNG, GIF, BMP
- PDFs: Cualquier PDF con texto

---

## Configuración

En `backend/.env`:

```ini
# Valores por defecto, ajusta según tu lógica de negocio:

# Score mínimo para auto-match (0-100)
AUTO_MATCH_THRESHOLD=85

# Gap mínimo entre top y segundo candidato
AUTO_MATCH_GAP=10

# Ventana temporal para búsqueda de candidatos (horas)
DATE_WINDOW_HOURS=72

# CORS (sin cambios)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# OCR (si está en Windows, ajusta la ruta)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## API Endpoints

### Nuevos

#### POST `/v1/sales/ingest`
Ingest de venta desde imagen/PDF.

```bash
curl -X POST http://localhost:8000/v1/sales/ingest \
  -F "file=@comprobante.jpg" \
  -H "Authorization: Bearer <token>"
```

**Respuesta**:
```json
{
  "draft": true,
  "amount": 1234.56,
  "datetime": "2025-12-29T10:30:00",
  "customer_name": "Juan Pérez",
  "customer_phone": "1123456789",
  "customer_cuit": "20123456789",
  "external_ref": "OP-12345",
  "raw_text": "...",
  "currency": "ARS"
}
```

### Actualizados

#### GET `/v1/transactions`
Ahora incluye `match_method`:

```json
{
  "id": 1,
  "match_status": "matched",
  "match_score": 90,
  "match_method": "gap",
  "needs_review": false,
  ...
}
```

---

## Ejemplos de Uso

### Ejemplo 1: Auto-Match por Strong ID

**Scenario**:
- Venta creada con `external_ref="INV-2025-001"`
- Transacción con `operation_id="INV-2025-001"`

**Resultado**:
```json
{
  "status": "matched",
  "method": "strong_id",
  "score": 100,
  "needs_review": false
}
```

### Ejemplo 2: Auto-Match por Gap

**Scenario**:
- Dos ventas del mismo monto (ARS 1.000)
- Venta 1: Con CUIT exacto (score 90)
- Venta 2: Solo nombre similar (score 70)
- Transacción: Mismo CUIT que Venta 1

**Resultado**:
```json
{
  "status": "matched",
  "method": "gap",
  "score": 90,
  "needs_review": false
}
```

**Razón**: Gap de 20 puntos (90-70) >= AUTO_MATCH_GAP (10)

### Ejemplo 3: Tie-Break por Evidencia

**Scenario**:
- Dos ventas idénticas en monto y fecha
- Venta 1: Con CUIT (evidencia 100)
- Venta 2: Solo teléfono (evidencia 80)
- Transacción: Con CUIT

**Resultado**:
```json
{
  "status": "matched",
  "method": "tiebreak",
  "score": 85,
  "needs_review": false,
  "sale_id": 1
}
```

**Razón**: Venta 1 gana por mejor evidencia

### Ejemplo 4: Ambiguous (Revisión Manual)

**Scenario**:
- Dos ventas idénticas (mismo monto, fecha, cliente)
- Transacción coincide con ambas

**Resultado**:
```json
{
  "status": "ambiguous",
  "method": "needs_review",
  "needs_review": true,
  "candidates": [
    {"sale_id": 1, "score": 85, "reasons": ["Mismo día", "Nombre coincide"]},
    {"sale_id": 2, "score": 85, "reasons": ["Mismo día", "Nombre coincide"]}
  ]
}
```

**Acción requerida**: Usuario revisa en UI y confirma cuál es la correcta

---

## Testing

Ejecutar suite de tests:

```bash
cd backend
pytest tests/test_match.py -v
```

Cubre:
- Strong ID Match
- Gap Match
- Single Candidate
- Tie-break por evidencia
- Tie-break por fecha
- Casos ambiguous
- Low score unmatched

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'pytesseract'"
```bash
pip install pytesseract
```

### "pytesseract.TesseractNotFoundError"
Tesseract-OCR no está instalado. Ver instrucciones arriba según tu SO.

### "Error: 'file' field required"
POST a `/v1/sales/ingest` sin archivo. Verificar que `Content-Type: multipart/form-data` y `file` esté presente.

### OCR no extrae bien del PDF
Probar con imagen (foto del comprobante) en lugar de PDF. A veces es más confiable.

### Transacción quedó como ambiguous pero esperaba matched
Revisar `AUTO_MATCH_THRESHOLD` y `AUTO_MATCH_GAP` en `.env`. Si scores son muy bajos o hay mucho empate, es correcto.

---

## Notas Importantes

1. **OCR con imágenes**: Calidad depende de la claridad del documento. Fotos de comprobantes físicos con buena iluminación funcionan mejor.

2. **Ventana de fechas**: `DATE_WINDOW_HOURS=72` significa ±72 horas desde la transacción. Ajustar si tu lógica es diferente.

3. **Persistencia**: El ingest devuelve un "draft" sin guardar. Solo se persiste cuando confirmas.

4. **CORS**: Si accedes desde una IP/puerto diferente, actualizar `CORS_ORIGINS` en `.env`.

5. **Producción**: En producción:
   - Cambiar `SECRET_KEY` en `.env`
   - Cambiar `SEED_DEMO=false`
   - Usar base de datos PostgreSQL en lugar de SQLite
   - Configurar servicio de OCR en la nube

---

**Última actualización**: 29 de diciembre de 2025
