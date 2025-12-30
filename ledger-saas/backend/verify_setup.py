#!/usr/bin/env python3
"""
Script de verificación del Ledger SaaS
Verifica que todas las dependencias y configuraciones están correctas
"""

import os
import sys
import subprocess

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_ok(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def check_python_version():
    print_header("Python Version")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print_ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} (se recomienda 3.10+)")
        return False

def check_dependencies():
    print_header("Python Dependencies")
    required = {
        'fastapi': 'FastAPI framework',
        'sqlalchemy': 'SQLAlchemy ORM',
        'pydantic': 'Pydantic validation',
        'pdfplumber': 'PDF text extraction',
        'pytesseract': 'OCR for images',
        'PIL': 'Image processing',
    }
    
    all_ok = True
    for package, description in required.items():
        try:
            __import__(package)
            print_ok(f"{package} - {description}")
        except ImportError:
            print_error(f"{package} - {description} [NOT INSTALLED]")
            all_ok = False
    
    return all_ok

def check_env_file():
    print_header("Configuration (.env)")
    
    env_path = ".env"
    if not os.path.exists(env_path):
        print_warning(".env no existe, intentando crear desde .env.example")
        if os.path.exists(".env.example"):
            with open(".env.example") as src:
                with open(".env", "w") as dst:
                    dst.write(src.read())
            print_ok(".env creado desde .env.example")
        else:
            print_error(".env y .env.example no existen")
            return False
    
    # Leer .env
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    
    # Verificar variables críticas
    critical_vars = [
        'AUTO_MATCH_THRESHOLD',
        'AUTO_MATCH_GAP',
        'DATE_WINDOW_HOURS',
        'CORS_ORIGINS',
    ]
    
    all_ok = True
    for var in critical_vars:
        if var in env_vars:
            print_ok(f"{var} = {env_vars[var]}")
        else:
            print_warning(f"{var} no configurada (usando default)")
    
    return all_ok

def check_database():
    print_header("Database")
    
    db_path = "app.db"
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print_ok(f"Database existe ({size_mb:.2f} MB)")
        return True
    else:
        print_warning("Database no existe (se creará automáticamente)")
        return True

def check_tesseract():
    print_header("Tesseract-OCR (Opcional)")
    
    try:
        import pytesseract
        print_ok("pytesseract importable")
        
        # Verificar si Tesseract está instalado
        try:
            pytesseract.pytesseract.pytesseract_cmd = None
            pytesseract.get_tesseract_version()
            print_ok("Tesseract-OCR detectado en PATH")
            return True
        except pytesseract.TesseractNotFoundError:
            print_warning("Tesseract-OCR no instalado (ingest de imágenes no funcionará)")
            print_warning("Instalar desde: https://github.com/UB-Mannheim/tesseract/wiki")
            return False
    except ImportError:
        print_error("pytesseract no instalado (pip install pytesseract)")
        return False

def check_directories():
    print_header("Directory Structure")
    
    required_dirs = [
        "app",
        "app/routers",
        "tests",
        "uploads",
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print_ok(f"Directory {dir_path}")
        else:
            print_warning(f"Directory {dir_path} missing (will create)")
            os.makedirs(dir_path, exist_ok=True)
    
    return all_ok

def check_files():
    print_header("Critical Files")
    
    required_files = [
        "app/match.py",
        "app/ingest.py",
        "app/models.py",
        "app/main.py",
        "app/routers/sales.py",
        "tests/test_match.py",
    ]
    
    all_ok = True
    for file_path in required_files:
        if os.path.isfile(file_path):
            print_ok(f"File {file_path}")
        else:
            print_error(f"File {file_path} MISSING")
            all_ok = False
    
    return all_ok

def check_tests():
    print_header("Unit Tests")
    
    if not os.path.isfile("tests/test_match.py"):
        print_warning("tests/test_match.py no existe")
        return False
    
    try:
        import pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_match.py", "-v", "--tb=short"],
            capture_output=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Contar PASSes
            output = result.stdout.decode()
            if "passed" in output:
                print_ok("Todos los tests pasaron ✅")
                return True
            else:
                print_warning("Tests ejecutados pero sin output claro")
                return False
        else:
            print_error("Tests fallaron ❌")
            print(result.stdout.decode()[:500])
            return False
    except subprocess.TimeoutExpired:
        print_warning("Tests timeout (>30s)")
        return False
    except Exception as e:
        print_warning(f"No se pueden ejecutar tests: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("  LEDGER SAAS - VERIFICATION SCRIPT")
    print("="*60)
    
    # Cambiar a directorio backend si estamos en otro lugar
    if os.path.exists("backend"):
        os.chdir("backend")
    
    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Configuration (.env)": check_env_file(),
        "Database": check_database(),
        "Directory Structure": check_directories(),
        "Critical Files": check_files(),
        "Tesseract-OCR": check_tesseract(),
        "Unit Tests": check_tests(),
    }
    
    print_header("SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 Todos los checks pasaron! El sistema está listo.")
        print("\nPróximos pasos:")
        print("  1. Backend: uvicorn app.main:app --reload")
        print("  2. Frontend: cd ../frontend && npm run dev")
        print("  3. Acceder: http://localhost:5173")
        return 0
    else:
        print(f"\n⚠️  {total - passed} checks fallaron.")
        print("Ver arriba para los detalles y cómo resolverlos.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
