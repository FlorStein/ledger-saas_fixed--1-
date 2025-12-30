# ✅ VERIFICACIÓN RÁPIDA - WhatsApp Integration

Ejecuta este script para verificar que todo está en su lugar antes de configurar Meta.

```bash
#!/bin/bash

echo "🔍 Verificando estructura de archivos..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/"
        return 1
    fi
}

# Check directories
echo "📁 Directories:"
check_dir "api"
check_dir "backend"
check_dir "frontend"
echo ""

# Check Vercel files
echo "🌐 Vercel Configuration:"
check_file "vercel.json"
check_file "api/whatsapp-webhook.js"
check_file "api/README.md"
echo ""

# Check Backend files
echo "🔧 Backend:"
check_file "backend/app/routers/whatsapp.py"
check_file "backend/.env"
check_file "backend/app/main.py"
echo ""

# Check Documentation
echo "📚 Documentation:"
check_file "WHATSAPP_SETUP.md"
check_file "DEPLOYMENT_GUIDE.md"
check_file "WHATSAPP_INTEGRATION_SUMMARY.md"
check_file "DELIVERY_SUMMARY.md"
check_file ".env.vercel.example"
echo ""

# Check Testing
echo "🧪 Testing:"
check_file "test_whatsapp_integration.py"
check_file "setup_whatsapp.sh"
echo ""

# Check file sizes (should be substantial)
echo "📊 File Sizes:"
echo "api/whatsapp-webhook.js:"
wc -l api/whatsapp-webhook.js 2>/dev/null || echo "File not found"

echo "backend/app/routers/whatsapp.py:"
wc -l backend/app/routers/whatsapp.py 2>/dev/null || echo "File not found"

echo "test_whatsapp_integration.py:"
wc -l test_whatsapp_integration.py 2>/dev/null || echo "File not found"

echo ""
echo "🔐 Environment Variables Check:"
echo ""

# Check .env
if grep -q "BACKEND_SHARED_SECRET" backend/.env 2>/dev/null; then
    echo -e "${GREEN}✓${NC} BACKEND_SHARED_SECRET in backend/.env"
else
    echo -e "${RED}✗${NC} BACKEND_SHARED_SECRET missing in backend/.env"
fi

if grep -q "TENANT_ROUTING_JSON" backend/.env 2>/dev/null; then
    echo -e "${GREEN}✓${NC} TENANT_ROUTING_JSON in backend/.env"
else
    echo -e "${RED}✗${NC} TENANT_ROUTING_JSON missing in backend/.env"
fi

echo ""
echo "📝 Code Verification:"

# Check for key functions in whatsapp-webhook.js
if grep -q "validateSignature" api/whatsapp-webhook.js 2>/dev/null; then
    echo -e "${GREEN}✓${NC} HMAC validation function found"
else
    echo -e "${RED}✗${NC} HMAC validation function missing"
fi

# Check for Bearer token in FastAPI
if grep -q "Bearer" backend/app/routers/whatsapp.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Bearer token validation in whatsapp.py"
else
    echo -e "${RED}✗${NC} Bearer token validation missing"
fi

echo ""
echo "✨ Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total=0
found=0

# Count essential files
files=(
    "api/whatsapp-webhook.js"
    "api/README.md"
    "backend/app/routers/whatsapp.py"
    "backend/.env"
    "vercel.json"
    "WHATSAPP_SETUP.md"
    "DEPLOYMENT_GUIDE.md"
    "test_whatsapp_integration.py"
    ".env.vercel.example"
)

for file in "${files[@]}"; do
    total=$((total + 1))
    if [ -f "$file" ]; then
        found=$((found + 1))
    fi
done

echo "✅ Files: $found/$total"

if [ $found -eq $total ]; then
    echo -e "${GREEN}All systems go! Ready for Meta configuration.${NC}"
    echo ""
    echo "📖 Next steps:"
    echo "  1. Read WHATSAPP_SETUP.md"
    echo "  2. Get Meta App Secret"
    echo "  3. Run: bash setup_whatsapp.sh"
    echo "  4. Configure Vercel env vars"
    echo "  5. Deploy: vercel --prod"
else
    echo -e "${YELLOW}Missing $((total - found)) files. Check output above.${NC}"
fi
```

**O simplemente ejecuta:**

```bash
# Parado en la raíz del proyecto
./verify_whatsapp.sh
```

---

## 🎯 Qué verifica este script

✅ **Estructura de directorios** - /api, /backend, /frontend  
✅ **Archivos Vercel** - vercel.json, whatsapp-webhook.js  
✅ **Archivos Backend** - whatsapp.py router, .env  
✅ **Documentación** - 4 guías completas  
✅ **Testing** - test suite y setup script  
✅ **Código** - validación de funciones clave  
✅ **Variables de entorno** - variables requeridas en .env  

---

## ⚡ Quick Validation (sin script)

```bash
# Verificar archivos clave
ls -la api/whatsapp-webhook.js
ls -la backend/app/routers/whatsapp.py
ls -la vercel.json
ls -la WHATSAPP_SETUP.md

# Verificar contenido
grep "validateSignature" api/whatsapp-webhook.js
grep "Bearer" backend/app/routers/whatsapp.py
grep "BACKEND_SHARED_SECRET" backend/.env
```

---

**Si todo chequea ✅ → Procede a WHATSAPP_SETUP.md**

