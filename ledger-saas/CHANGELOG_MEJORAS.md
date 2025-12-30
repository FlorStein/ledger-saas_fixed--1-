# Ledger SaaS - Mejoras Implementadas

## Resumen de Cambios

Se ha mejorado significativamente el sistema de matching de transacciones con ventas y se ha agregado la capacidad de ingestar ventas desde imágenes/PDF. Los cambios minimizan la confirmación manual mediante lógica inteligente de auto-resolución.

---

## A) Sistema de Matching Mejorado

### 1. Configuración por Variables de Entorno

Se añadieron tres variables configurables en `.env`:

```
AUTO_MATCH_THRESHOLD=85      # Score mínimo para auto-match (default 85)
AUTO_MATCH_GAP=10            # Gap mínimo entre top y segundo candidato (default 10)
DATE_WINDOW_HOURS=72         # Ventana de fechas para búsqueda de candidatos (default 72h)
```

### 2. Modelo de Datos Actualizado

En `backend/app/models.py`, se agregó el campo `match_method` a la tabla `Transaction`:

```python
match_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
# Valores posibles: "strong_id" | "gap" | "single_candidate" | "tiebreak" | "needs_review"
```

### 3. Reglas de Matching Inteligente

**backend/app/match.py** implementa las siguientes reglas en orden de prioridad:

#### Regla 1: Strong ID Match
- **Condición**: `transaction.operation_id == sale.external_ref`
- **Acción**: Devuelve `status="matched"`, `method="strong_id"`, `score=100`, `needs_review=false`
- **Uso**: Cuando hay identificadores únicos que coinciden exactamente

#### Regla 2: Gap Match
- **Condición**: 
  - `top_score >= AUTO_MATCH_THRESHOLD` (default 85)
  - `(top_score - second_score) >= AUTO_MATCH_GAP` (default 10)
- **Acción**: Devuelve `status="matched"`, `method="gap"`, `needs_review=false`
- **Uso**: Hay diferencia clara entre mejor y segundo candidato

#### Regla 3: Single Candidate
- **Condición**: Solo hay un candidato dentro de la ventana de fechas y `score >= AUTO_MATCH_THRESHOLD`
- **Acción**: Devuelve `status="matched"`, `method="single_candidate"`, `needs_review=false`

#### Regla 4: Tie-Break Determinístico
Cuando los scores son muy cercanos (`gap < AUTO_MATCH_GAP`):

1. **Evidence Rank**: Ordena por fuerza de evidencia:
   - `cuit_exact` (100) > `ref_match` (90) > `phone_match` (80) > `name_match` (70) > `amount_exact` (60)
   
2. **Time Delta**: Si evidencia es igual, elige el candidato más cercano en fecha
   
3. **Sale ID**: Si sigue empatado, elige el ID menor

- **Acción**: Devuelve `status="matched"`, `method="tiebreak"`, `needs_review=false`

#### Fallback: Ambiguous
- **Condición**: No se puede romper empate o `top_score < AUTO_MATCH_THRESHOLD`
- **Acción**: Devuelve `status="ambiguous"`, `method="needs_review"`, `needs_review=true`

### 4. Estructura de Respuesta de Match

```python
@dataclass
class MatchResult:
    id: int | None
    sale_id: int | None
    score: int
    status: str              # "matched" | "ambiguous" | "unmatched"
    method: str | None       # "strong_id" | "gap" | "single_candidate" | "tiebreak" | "needs_review"
    needs_review: bool       # Flag de revisión manual
    candidates: list         # Top 3 candidatos con score y razones
```

### 5. Routers Actualizados

**backend/app/routers/receipts.py**: Al procesar un comprobante, se guarda `match_method` y se setea `needs_review` coherentemente.

**backend/app/routers/transactions.py**: El endpoint `GET /v1/transactions` ahora retorna `match_method`.

---

## B) Ingest de Ventas por Imagen/PDF

### 1. Módulo de Extracción

Se creó **backend/app/ingest.py** con funciones para extraer información desde imágenes y PDFs:

- `extract_text_from_image()`: OCR con pytesseract
- `extract_text_from_pdf_ingest()`: Extracción de texto con pdfplumber
- `extract_amount()`: Detecta montos con regex (soporta formato argentino y internacional)
- `extract_phone()`: Detecta números de teléfono (+54 9, 11-xxxx-xxxx, etc.)
- `extract_cuit()`: Detecta CUIT/CUIL y extrae suffix
- `extract_reference()`: Detecta referencias de pedido (Pedido #, Ref:, etc.)
- `extract_customer_name()`: Heurística para detectar nombre del cliente
- `extract_datetime()`: Detecta fechas en múltiples formatos
- `parse_sale_from_text()`: Orquesta todas las extracciones

### 2. Endpoint POST /sales/ingest

**backend/app/routers/sales.py**:

```python
POST /sales/ingest
Content-Type: multipart/form-data

Parámetros:
- file (UploadFile): Imagen (JPG/PNG) o PDF

Respuesta:
{
  "draft": true,
  "amount": 1234.56,
  "datetime": "2025-12-29T10:30:00",
  "customer_name": "Juan Pérez",
  "customer_phone": "1123456789",
  "customer_cuit": "20123456789",
  "external_ref": "OP-12345",
  "raw_text": "...primeros 500 caracteres...",
  "currency": "ARS"
}
```

**Flujo**:
1. Usuario sube archivo (imagen o PDF)
2. Backend extrae texto con OCR/pdfplumber
3. Parsea información estructurada
4. Retorna draft **sin guardar en BD**
5. Frontend muestra formulario prellenado para revisión
6. Usuario confirma o modifica, luego hace POST a `/v1/sales` para guardar

### 3. Frontend: Componente UploadSaleImage

Se creó **frontend/src/components/UploadSaleImage.jsx**:

- Drag-and-drop zone para archivos
- Soporta JPG, PNG, GIF, BMP, PDF
- Muestra preview de datos extraídos
- Permite editar campos antes de guardar
- Feedback visual de éxito/error

### 4. Integración en Dashboard

En **frontend/src/pages/Dashboard.jsx**:

- Tab "Ventas" ahora muestra dos bloques:
  1. **Crear venta manual** (CreateSale)
  2. **Subir venta por imagen/PDF** (UploadSaleImage - nuevo)
  3. **Tabla de ventas** (SalesTable)

---

## C) Dependencias Añadidas

En **backend/requirements.txt**:

```
pdfplumber==0.11.4      # Extracción de PDF
PyMuPDF==1.24.0         # Alternativa para PDF (previamente: pdfminer)
pytesseract==0.3.10     # OCR de imágenes
Pillow==10.4.0          # Procesamiento de imágenes
```

**Nota**: `pytesseract` requiere que Tesseract-OCR esté instalado en el sistema:
- **Windows**: Descargar desde https://github.com/UB-Mannheim/tesseract/wiki
- **Linux**: `sudo apt-get install tesseract-ocr`
- **MacOS**: `brew install tesseract`

---

## D) Configuración CORS

**backend/app/main.py** ya contempla CORS con:

```python
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Se asegura que tanto localhost como 127.0.0.1 están permitidos para evitar problemas con Vite.

---

## E) Tests Unitarios

Se creó **backend/tests/test_match.py** con cobertura para:

1. **test_strong_id_match**: Verifica que Strong ID Match funciona
2. **test_gap_match**: Verifica el gap entre candidatos
3. **test_single_candidate_match**: Un solo candidato con score alto
4. **test_tiebreak_by_evidence**: Tie-break por evidencia (CUIT > Phone > Name)
5. **test_tiebreak_by_date_proximity**: Tie-break por cercanía de fecha
6. **test_ambiguous_when_cannot_break_tie**: Casos que quedan ambiguous
7. **test_low_score_unmatched**: Score bajo → unmatched
8. **test_normalize_name**: Normalización de nombres
9. **test_date_window_configuration**: Ventana de fechas

**Ejecutar tests**:
```bash
cd backend
pip install pytest
pytest tests/test_match.py -v
```

---

## F) Criterio de Aceptación - Verificación

### ✅ Auto-Resolución Inteligente

**Escenario**: Dos ventas del mismo monto, una con CUIT y otra con teléfono.

```
Venta 1: ARS 1.000, Cliente X, CUIT 20123456789
Venta 2: ARS 1.000, Cliente X, Teléfono 1123456789
Transacción: ARS 1.000, CUIT 20123456789
```

**Resultado esperado**: Sistema elige Venta 1 (mejor evidencia: CUIT > phone), retorna `method="tiebreak"`, `status="matched"`, `needs_review=false`.

**Actual**: ✅ Implementado

### ✅ Solo Ambiguous en Casos Reales

**Escenario**: Dos ventas idénticas (mismo monto, fecha, nombre, sin datos diferenciadores).

```
Venta 1: ARS 1.000, 2025-12-29 10:00, Cliente A
Venta 2: ARS 1.000, 2025-12-29 10:00, Cliente A
Transacción: ARS 1.000, 2025-12-29 10:00, Cliente A
```

**Resultado esperado**: `status="ambiguous"`, `method="needs_review"`, `needs_review=true`.

**Actual**: ✅ Implementado

### ✅ Ingest de Venta desde Imagen/PDF

**Escenario**: Usuario sube foto de comprobante con monto ARS 1.234,56, cliente "Juan Pérez", teléfono 1123456789.

**Resultado esperado**: 
- Endpoint extrae: amount=1234.56, customer_name="Juan Pérez", customer_phone="1123456789"
- Retorna draft sin guardar
- Frontend muestra formulario prellenado
- Usuario confirma o modifica y guarda

**Actual**: ✅ Implementado

---

## G) Instrucciones de Instalación/Actualización

### Backend

1. **Instalar nuevas dependencias**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Instalar Tesseract-OCR** (requerido para OCR de imágenes):
   - Windows: Descargar exe desde https://github.com/UB-Mannheim/tesseract/wiki
   - Después de instalar, en Python:
     ```python
     import pytesseract
     pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
     ```

3. **Configurar .env**:
   ```bash
   cp .env.example .env
   # Editar .env y asegurar:
   AUTO_MATCH_THRESHOLD=85
   AUTO_MATCH_GAP=10
   DATE_WINDOW_HOURS=72
   ```

4. **Ejecutar migrations** (si aplica):
   ```bash
   # El modelo ya incluye match_method, revisar con:
   # sqlite3 app.db ".schema transactions"
   ```

5. **Ejecutar tests**:
   ```bash
   pytest tests/test_match.py -v
   ```

### Frontend

Los cambios en frontend ya están integrados. Solo verificar que:
- `src/components/UploadSaleImage.jsx` existe
- `src/pages/Dashboard.jsx` importa el componente
- CORS_ORIGINS en backend incluye `http://localhost:5173`

---

## H) Notas Importantes

### Limitaciones Conocidas

1. **OCR**: Dependencia de calidad de imagen. Comprobantes borrosos pueden no extraer correctamente.
   
2. **Tesseract en Windows**: Requiere instalación manual del ejecutable.

3. **Montos en otros idiomas**: Regex optimizado para español/inglés. Otros idiomas pueden requerir ajuste.

4. **Fecha sin hora**: Si no hay hora en el documento, se asume 00:00:00.

### Mejoras Futuras

1. Implementar OCR más robusto con servicios en la nube (Google Vision, AWS Textract)
2. Machine Learning para clasificación automática de campos
3. Historial de revisiones (quién cambió qué, cuándo)
4. Webhooks para integración con sistemas externos
5. Soporte para múltiples monedas

---

## I) Archivos Modificados/Creados

### Modificados
- `backend/app/models.py` - Añadido `match_method` a Transaction
- `backend/app/match.py` - Reescrito `match_sale()` con nueva lógica
- `backend/app/routers/receipts.py` - Persistencia de `match_method`
- `backend/app/routers/transactions.py` - Retorna `match_method` en GET
- `backend/app/routers/sales.py` - Nuevo endpoint POST /sales/ingest
- `backend/requirements.txt` - Añadidas pytesseract, PyMuPDF, Pillow
- `backend/.env.example` - Nuevas variables de configuración
- `frontend/src/pages/Dashboard.jsx` - Integración de UploadSaleImage

### Creados
- `backend/app/ingest.py` - Módulo de extracción OCR/PDF
- `frontend/src/components/UploadSaleImage.jsx` - Componente de UI
- `backend/tests/test_match.py` - Suite de tests

---

## J) Preguntas Frecuentes

**P: ¿Qué pasa si hay múltiples PDFs en un folder?**
R: El endpoint `/sales/ingest` procesa un archivo por llamada. El frontend permite múltiples uploads secuenciales.

**P: ¿Cómo puedo cambiar AUTO_MATCH_THRESHOLD?**
R: Editar `backend/.env` y asignar nuevo valor. Se lee automáticamente al iniciar.

**P: ¿Qué pasa si el OCR falla?**
R: El endpoint retorna un error 500 con detalle. El usuario puede reintentar con mejor imagen.

**P: ¿Puedo usar PyMuPDF en lugar de pdfplumber?**
R: Sí, `ingest.py` importa `pdfplumber`. Para cambiar, modificar función `extract_text_from_pdf_ingest()`.

**P: ¿El sistema persiste la información del ingest?**
R: No. El ingest retorna un "draft" sin guardar. Solo se persiste cuando usuario confirma (POST a `/v1/sales`).

---

Implementado: 29 de diciembre de 2025
