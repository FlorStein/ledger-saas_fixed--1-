# 📦 Instalación de Tesseract-OCR para Windows

## Paso 1: Descargar el Instalador

1. Ve a: https://github.com/UB-Mannheim/tesseract/wiki

2. Descarga la versión más reciente (ejemplo: `tesseract-ocr-w64-setup-v5.3.exe`)

3. Ejecuta el instalador

## Paso 2: Configuración de Instalación

Cuando aparezca el instalador:

1. **Selecciona componentes**: Asegúrate de instalar:
   - ✅ Core OCR Engine
   - ✅ English
   - ✅ Spanish (importante para Argentina)
   - Otras lenguas que necesites

2. **Ubicación**: Por defecto se instala en:
   ```
   C:\Program Files\Tesseract-OCR
   ```
   
   (Puedes cambiar, pero recuerda la ruta)

3. **Completa la instalación**

## Paso 3: Configurar la Ruta en Python

### Opción A: Variable de Entorno (Recomendado)

En `backend/.env` o en tu script Python:

```bash
# .env
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

Luego en `backend/app/ingest.py` (línea 10 aprox):

```python
import os
import pytesseract

# Leer ruta desde .env
tesseract_path = os.getenv("TESSERACT_PATH")
if tesseract_path:
    pytesseract.pytesseract.pytesseract_cmd = tesseract_path
```

### Opción B: Directa en el Código

En `backend/app/ingest.py`:

```python
import pytesseract

pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path: str) -> str:
    """Extrae texto de una imagen usando pytesseract."""
    try:
        from PIL import Image
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='spa')
        return text
    except Exception as e:
        return f"[ERROR: {str(e)}]"
```

### Opción C: Agregar a PATH del Sistema

1. Abre **Variables de Entorno del Sistema**:
   - Windows: `Win + X` → Sistema → Configuración avanzada del sistema
   - O: Busca "Variables de entorno" en Windows

2. Haz click en **"Variables de entorno"**

3. En **"Variables del sistema"**, busca **PATH**

4. Edita y agrega una nueva entrada:
   ```
   C:\Program Files\Tesseract-OCR
   ```

5. Guarda y reinicia tu terminal/IDE

Con esto, pytesseract encontrará tesseract automáticamente sin configuración adicional.

## Paso 4: Verificar la Instalación

### Desde Línea de Comandos

```powershell
tesseract --version
```

Deberías ver algo como:
```
tesseract 5.3.0
```

### Desde Python

```python
import pytesseract
from PIL import Image

# Si está en PATH del sistema
try:
    text = pytesseract.image_to_string(Image.new('RGB', (100, 100)), lang='spa')
    print("✅ Tesseract funciona correctamente")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Troubleshooting

### Error: "tesseract is not installed or it's not in your PATH"

**Solución 1**: Configura la ruta manualmente (Opción B arriba)

**Solución 2**: Agrega a PATH del sistema (Opción C arriba)

**Solución 3**: Verifica que la ruta es correcta:
```powershell
Test-Path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Si retorna `False`, la ruta es incorrecta. Ajusta según tu instalación.

### Error: "Tesseract couldn't recognize OCR"

Esto puede pasar si:
1. La imagen está muy borrosa o de mala calidad
2. El idioma especificado no está instalado
3. El formato de imagen no es soportado

**Soluciones**:
- Prueba con una imagen más clara
- Instala el idioma (en el instalador de Tesseract, repite pasos anteriores)
- Convierte la imagen a JPG/PNG

### Error: "No module named 'PIL'"

Instala Pillow:
```bash
pip install Pillow
```

## Verificación Completa

### Backend Setup Completo

```bash
# 1. Navegar a backend
cd backend

# 2. Crear virtual environment (opcional pero recomendado)
python -m venv venv
.\venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar .env
copy .env.example .env
# Editar .env y agregar:
# TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# 5. Ejecutar tests
pytest tests/test_match.py -v

# 6. Iniciar servidor
uvicorn app.main:app --reload

# En otra terminal: Frontend
cd ../frontend
npm install
npm run dev
```

## Verificación en UI

1. Ir a http://localhost:5173
2. Ir a tab "Ventas"
3. Buscar sección "Subir venta (Imagen/PDF)"
4. Subir una imagen de comprobante
5. Si funciona, deberías ver los datos extraídos

---

## Notas

- **Idiomas**: Por defecto, instalamos español ('spa'). Si necesitas otros idiomas:
  - Repite el instalador
  - Selecciona idiomas adicionales
  - O descarga manualmente desde: https://github.com/UB-Mannheim/tesseract/wiki/Downloads

- **Performance**: La primera ejecución puede ser lenta mientras carga los modelos de OCR. Las siguientes son más rápidas.

- **Producción**: Considera usar servicios en la nube para mejor escalabilidad:
  - Google Cloud Vision
  - AWS Textract
  - Azure Computer Vision

---

**Última actualización**: 29 de diciembre de 2025
