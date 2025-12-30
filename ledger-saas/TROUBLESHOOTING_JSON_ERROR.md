# 🔧 Troubleshooting: "Unexpected end of JSON input"

## Causa Principal
El backend está retornando una respuesta vacía, malformada o no-JSON.

---

## Soluciones Rápidas

### 1. Verificar Backend está corriendo
```powershell
# Verificar que el backend responde
curl http://127.0.0.1:8000/health

# Debe retornar: {"ok": true}
```

Si no responde:
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Verificar Token JWT
El error puede ocurrir si el token expiró o no está siendo enviado.

En DevTools (F12) → Network → ver headers de la request:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

Si no está presente, hacer login nuevamente:
```javascript
// En DevTools → Console
localStorage.setItem("token", "");
// Recarga la página
// Login nuevamente
```

### 3. Verificar Requirements
Las librerías nuevas deben estar instaladas:

```bash
cd backend
pip install -r requirements.txt
pip list | grep -E "pdfplumber|pytesseract|Pillow|PyMuPDF"
```

Debe mostrar:
```
Pillow==10.4.0
PyMuPDF==1.24.0
pdfplumber==0.11.4
pytesseract==0.3.10
```

Si falta algo:
```bash
pip install pdfplumber PyMuPDF pytesseract Pillow
```

### 4. Verificar .env
```bash
cd backend
cat .env
```

Debe tener mínimo:
```
AUTO_MATCH_THRESHOLD=85
AUTO_MATCH_GAP=10
DATE_WINDOW_HOURS=72
UPLOAD_DIR=./uploads
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Si falta:
```bash
cp .env.example .env
```

---

## Debug Específico por Endpoint

### Problema con GET /v1/transactions

```bash
# Verificar en terminal del backend
curl -H "Authorization: Bearer TOKEN" http://127.0.0.1:8000/v1/transactions

# Si retorna error, revisar logs del backend
```

**Solución**: Restart backend
```bash
Ctrl+C en terminal del backend
uvicorn app.main:app --reload
```

### Problema con POST /v1/sales/ingest

**Error**: Abrir DevTools (F12) → Console → ver error exacto

**Caso 1**: "Formato no soportado"
- ✅ Soportados: .jpg, .jpeg, .png, .gif, .bmp, .pdf
- ❌ No soportados: .doc, .docx, .xlsx, .txt

**Caso 2**: "Nombre de archivo requerido"
- Asegúrate de seleccionar un archivo válido

**Caso 3**: "Tesseract couldn't recognize OCR"
- Es OK. El backend intentó OCR pero falló
- Intenta con una imagen más clara
- O intenta con PDF en lugar de imagen

**Caso 4**: "Invalid JSON response"
- El backend retornó algo que no es JSON
- Revisar logs del backend (stderr)
- Restart backend

### Problema con POST /v1/sales

Cuando haces "Guardar venta" después de ingest:

**Error**: "amount must be a number"
- Verifica que el monto está prellenado correctamente
- Si muestra NaN, hay problema con OCR
- Edita manualmente el monto

**Error**: "datetime is required"
- Asegúrate de tener fecha/hora prellenada
- Si está vacía, edita manualmente

**Error**: "Invalid JSON"
- Frontend payload está malformado
- Abre DevTools → Network → ver request body
- Debería ser:
```json
{
  "datetime": "2025-12-29T10:30",
  "amount": 1234.56,
  "currency": "ARS",
  "customer_name": "...",
  ...
}
```

---

## Debug Avanzado

### Ver Logs del Backend

En PowerShell (terminal del backend):
```
Uvicorn running on http://127.0.0.1:8000
...
[logs aquí]
```

Si ves error rojo, copiar y buscar en [CHANGELOG_MEJORAS.md](../CHANGELOG_MEJORAS.md)

### Ver Logs del Frontend

En DevTools (F12) → Console:
```javascript
// Si ves el error exacto, copiar al clipboard
// Luego buscar en este documento o en troubleshooting
```

### Reinstalar desde 0

```bash
# Backend
cd backend
rm -r .venv __pycache__ app/__pycache__ app/routers/__pycache__
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
pytest tests/test_match.py -v  # Verificar tests
uvicorn app.main:app --reload

# Frontend (otra terminal)
cd frontend
rm -r node_modules
npm install
npm run dev
```

---

## Problemas Específicos del Ingest

### "Tesseract is not installed"

**Windows**:
1. Descargar: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar `tesseract-ocr-w64-setup-v5.3.exe`
3. En `.env` agregar:
   ```
   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```
4. Restart backend

**Linux**:
```bash
sudo apt-get install tesseract-ocr
```

**Mac**:
```bash
brew install tesseract
```

### "pytesseract.TesseractNotFoundError"

Tesseract está instalado pero Python no lo encuentra.

**Solución 1**: Agregar a PATH (Windows)
```powershell
# PowerShell como Admin
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\Program Files\Tesseract-OCR", "User")
# Reinicia terminal y backend
```

**Solución 2**: Configurar en Python
En `backend/app/ingest.py` (línea 9):
```python
import os
import pytesseract

tesseract_path = os.getenv("TESSERACT_PATH")
if tesseract_path:
    pytesseract.pytesseract.pytesseract_cmd = tesseract_path
```

### OCR retorna texto vacío

Probable causa: Imagen de mala calidad, borrosa o muy pequeña

**Soluciones**:
1. Prueba con imagen más clara
2. Prueba con imagen en color (no blanco y negro)
3. Prueba con imagen con mejor resolución
4. Usa PDF en lugar de imagen

---

## Checklist de Verificación

Antes de reportar error, verificar:

- [ ] Backend ejecutándose sin errores
- [ ] `pip list` muestra las 4 nuevas librerías
- [ ] `.env` contiene las 3 variables de matching
- [ ] CORS configurado para localhost:5173
- [ ] Token JWT válido (login reciente)
- [ ] Archivo de test existe y formatos soportados
- [ ] Si usas OCR de imagen: Tesseract instalado
- [ ] Terminal del backend no muestra errores rojos

---

## Si Aún Hay Error

1. **Captura pantalla del error** (DevTools → Console)
2. **Copia logs del backend** (ventana de PowerShell)
3. **Describe qué action dispara el error**:
   - ¿Crear venta?
   - ¿Subir comprobante?
   - ¿Ingest imagen?
   - ¿Otra?
4. **Incluye versiones**:
   ```bash
   python --version
   node --version
   npm --version
   ```

---

## Reinicio Rápido (Nuclear Option)

```bash
# 1. Matar procesos
taskkill /IM node.exe /F 2>$null
taskkill /IM python.exe /F 2>$null

# 2. Limpiar
cd backend
rm -r .venv __pycache__ app/__pycache__ app/routers/__pycache__
cd ../frontend
rm -r node_modules

# 3. Reinstalar
cd ../backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd ../frontend
npm install

# 4. Reiniciar
# Terminal 1
cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

---

**Si el error persiste después de esto, es un bug específico del sistema.**

Reporta con:
- OS (Windows 10/11)
- Python version
- Node version
- npm version
- Screenshot del error
- Logs del backend (copiar/pegar)
