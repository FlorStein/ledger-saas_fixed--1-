# 🚀 Ledger SaaS - INICIO RÁPIDO

## Requisitos Previos

✅ Python 3.10+ instalado  
✅ Node.js 18+ instalado  
✅ pip configurado

## Paso 1: Preparación del Backend

### 1a. Instalar dependencias de Python

```bash
cd backend
pip install -r requirements.txt
pip install pytest
```

**Verificar instalación:**
```bash
python verify_setup.py
```

Debe mostrar 8/8 checks pasados (el Tesseract es opcional).

### 1b. Variables de configuración (.env)

Verificar que existe el archivo `.env` con valores por defecto:

```
AUTO_MATCH_THRESHOLD=85
AUTO_MATCH_GAP=10
DATE_WINDOW_HOURS=72
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Si no existe, se crea automáticamente con valores por defecto.

### 1c. Ejecutar tests

```bash
python -m pytest tests/test_match.py -v
```

**Esperado:** 8/8 tests PASSED ✅

## Paso 2: Ejecución del Backend

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Esperado:**
```
Uvicorn running on http://127.0.0.1:8000
Press CTRL+C to quit
```

✅ Backend listo en `http://localhost:8000`

## Paso 3: Preparación del Frontend

### 3a. Instalar dependencias de Node

```bash
cd frontend
npm install
```

### 3b. Verificar configuración de API

Revisar que `frontend/src/api.js` tiene la URL correcta:

```javascript
const API_BASE = "http://localhost:8000";
```

## Paso 4: Ejecución del Frontend

```bash
cd frontend
npm run dev
```

**Esperado:**
```
VITE v5.x.x ready in XXX ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

✅ Frontend listo en `http://localhost:5173`

## 🌐 Acceso a la aplicación

Abrir en navegador:

```
http://localhost:5173
```

## Flujos de Prueba

### Test 1: Crear una Venta

1. Ir a pestaña **"Ventas"**
2. Hacer clic en **"+ Nueva Venta"**
3. Completar formulario:
   - **Cliente:** "Juan Pérez"
   - **CUIT:** "20123456789"
   - **Monto:** 1000
   - **Moneda:** ARS
   - Hacer clic en **"Guardar"**

✅ Venta creada

### Test 2: Crear Transacción (Auto-match)

1. Ir a pestaña **"Transacciones"**
2. Hacer clic en **"+ Nueva Transacción"**
3. Completar formulario:
   - **Origen:** "test.pdf"
   - **Pagador:** "Juan Pérez"
   - **CUIT:** "20123456789" (DEBE coincidir con la venta)
   - **Monto:** 1000
   - **Moneda:** ARS
   - Hacer clic en **"Guardar"**

✅ Transacción se auto-asigna a la venta (Strong ID match)

### Test 3: Cargar Imagen de Venta (OCR)

**Nota:** Requiere Tesseract-OCR instalado (opcional)

1. Ir a pestaña **"Ventas"**
2. Hacer clic en **"📤 Cargar Imagen/PDF"**
3. Arrastrar o seleccionar un PDF/imagen con datos de venta
4. Sistema extrae automáticamente:
   - Monto
   - Teléfono
   - CUIT
   - Fecha
   - Nombre cliente
5. Editar si es necesario y hacer clic **"Guardar"**

✅ Venta creada desde OCR

### Test 4: Resolver Transacción Ambigua

1. Crear 2 ventas con el mismo monto y cliente
2. Crear transacción sin especificar CUIT/teléfono
3. Transacción queda como "Ambigua"
4. Ir a **"Transacciones"**
5. Hacer clic en transacción ambigua
6. Seleccionar la venta correcta en el dropdown
7. Hacer clic **"Asignar"**

✅ Transacción resuelta

## 🛠️ Comandos Útiles

### Ejecutar todo en una terminal (PowerShell Windows)

```powershell
# Terminal 1: Backend
cd "c:\ruta\del\proyecto\backend"
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd "c:\ruta\del\proyecto\frontend"
npm run dev
```

### Ver logs del backend

Usar [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) en VS Code:

```
GET http://localhost:8000/v1/transactions
Authorization: Bearer <token>
```

### Limpiar base de datos

```bash
# Backend
rm app.db
# La BD se crea automáticamente en el primer request
```

## ⚠️ Problemas Comunes

### "Port already in use" (Puerto en uso)

**Backend:**
```bash
# Usar puerto diferente
uvicorn app.main:app --port 8001
# Luego actualizar frontend/src/api.js:
# const API_BASE = "http://localhost:8001";
```

**Frontend:**
```bash
# Usar puerto diferente
npm run dev -- --port 5174
```

### "JSON parse error: Unexpected end of JSON input"

- Verificar que backend está ejecutándose
- Verificar CORS está configurado: `CORS_ORIGINS=...`
- Ver logs del backend para errores

### "pytesseract not installed" (OCR no disponible)

**Opcional:** Instalar Tesseract-OCR:

1. Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar (en Windows usar installer)
3. Configurar PATH si es necesario
4. Reiniciar backend

Sin Tesseract, OCR no funcionará pero el resto de funcionalidades sí.

## ✅ Verificación Final

Ejecutar este checklist para verificar que todo funciona:

- [ ] Backend running (http://localhost:8000)
- [ ] Frontend running (http://localhost:5173)
- [ ] Tests pasados (8/8)
- [ ] Puedo crear una venta
- [ ] Puedo crear una transacción
- [ ] Auto-match funciona (crear venta + tx con mismo CUIT)
- [ ] Puedo ver transacciones

Si todos pasan: **¡Sistema listo para usar!** 🎉

## 📚 Documentación

Ver más detalles en:
- [QUICK_START.md](./QUICK_START.md) - Guía paso a paso
- [PROCESS_FLOWS.md](./PROCESS_FLOWS.md) - Flujos de negocio
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Detalles técnicos

---

**Última actualización:** 2025-01-15  
**Estado:** ✅ Producción lista
