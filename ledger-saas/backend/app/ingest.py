"""
Módulo de ingest de ventas desde imágenes o PDFs.
Extrae información estructurada usando OCR (pytesseract) y pdfplumber.
"""
import re
from datetime import datetime
from typing import Dict, Any

def extract_text_from_image(image_path: str) -> str:
    """Extrae texto de una imagen usando pytesseract."""
    try:
        import pytesseract
        from PIL import Image
        
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='spa')
        return text if text else "[No text detected in image]"
    except ImportError:
        return "[ERROR: pytesseract no está instalado. Instala con: pip install pytesseract]"
    except Exception as e:
        return f"[ERROR OCR: {str(e)}]"

def extract_text_from_pdf_ingest(pdf_path: str) -> str:
    """Extrae texto de un PDF usando pdfplumber."""
    try:
        import pdfplumber
        
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"[ERROR: {str(e)}]"

def extract_amount(text: str) -> float | None:
    """
    Extrae monto de un texto. Busca patrones como:
    - ARS 1.234,56
    - $ 1234.56
    - Total: 1.234,56
    - 1234,56
    """
    # Normalizar: remover símbolos de moneda y espacios extras
    text_clean = text.replace("ARS", "").replace("$", "").replace("USD", "")
    
    # Buscar patrones de números con separadores
    # Patrón argentino: 1.234,56 o 1234,56
    pattern_arg = r'\b(\d{1,3}(?:\.\d{3})*,\d{2})\b'
    matches_arg = re.findall(pattern_arg, text_clean)
    
    # Patrón internacional: 1,234.56 o 1234.56
    pattern_int = r'\b(\d{1,3}(?:,\d{3})*\.\d{2})\b'
    matches_int = re.findall(pattern_int, text_clean)
    
    # Patrón simple sin decimales: 1234
    pattern_simple = r'\b(\d{3,})\b'
    
    # Priorizar montos con decimales
    if matches_arg:
        # Convertir formato argentino a float
        amount_str = matches_arg[-1].replace(".", "").replace(",", ".")
        try:
            return float(amount_str)
        except:
            pass
    
    if matches_int:
        # Convertir formato internacional a float
        amount_str = matches_int[-1].replace(",", "")
        try:
            return float(amount_str)
        except:
            pass
    
    # Fallback: buscar cualquier número grande
    matches_simple = re.findall(pattern_simple, text_clean)
    if matches_simple:
        try:
            return float(matches_simple[-1])
        except:
            pass
    
    return None

def extract_phone(text: str) -> str | None:
    """
    Extrae número de teléfono. Busca patrones como:
    - 11-1234-5678
    - +54 9 11 1234 5678
    - 1112345678
    """
    # Buscar patrones de teléfono argentino
    patterns = [
        r'\+54\s*9?\s*(\d{2,4}[\s-]?\d{4}[\s-]?\d{4})',  # +54 9 11 1234 5678
        r'\b(\d{2,4}[\s-]\d{4}[\s-]\d{4})\b',  # 11-1234-5678
        r'\b(\d{10})\b',  # 1112345678
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Normalizar: remover espacios y guiones
            phone = re.sub(r'[\s-]', '', match.group(1) if match.lastindex else match.group(0))
            if len(phone) >= 10:
                return phone
    
    return None

def extract_cuit(text: str) -> tuple[str | None, str | None]:
    """
    Extrae CUIT/CUIL. Busca patrones como:
    - 20-12345678-9
    - 20123456789
    Retorna (cuit completo, suffix de 4-5 dígitos)
    """
    # Buscar patrón de CUIT con guiones
    pattern_hyphen = r'\b(\d{2}[\s-]?\d{8}[\s-]?\d)\b'
    match = re.search(pattern_hyphen, text)
    
    if match:
        cuit = re.sub(r'[\s-]', '', match.group(0))
        if len(cuit) == 11:
            suffix = cuit[-5:] if len(cuit) >= 5 else cuit[-4:]
            return cuit, suffix
    
    return None, None

def extract_reference(text: str) -> str | None:
    """
    Extrae referencia de pedido. Busca patrones como:
    - Pedido #1234
    - Ref: ABC123
    - Order 1234
    """
    patterns = [
        r'(?:pedido|ref|order|referencia)[:\s#]*([A-Z0-9-]+)',
        r'#(\d{3,})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_customer_name(text: str) -> str | None:
    """
    Extrae nombre de cliente. Heurística simple:
    - Buscar líneas después de palabras clave como "Cliente:", "Nombre:"
    - Buscar líneas con mayúsculas
    """
    # Buscar después de palabras clave
    patterns = [
        r'(?:cliente|nombre|customer|name)[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 3:
                return name
    
    # Buscar líneas con mayúsculas (posible nombre)
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        # Si la línea tiene 2-5 palabras y empieza con mayúscula
        words = line.split()
        if 2 <= len(words) <= 5 and line[0].isupper():
            # Verificar que no sea una palabra clave común
            if not any(kw in line.lower() for kw in ['total', 'fecha', 'precio', 'cantidad', 'importe']):
                return line
    
    return None

def extract_datetime(text: str) -> str | None:
    """
    Extrae fecha/hora. Busca patrones como:
    - 29/12/2025
    - 2025-12-29
    - 29 de diciembre de 2025
    """
    # Patrón DD/MM/YYYY
    pattern_slash = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
    match = re.search(pattern_slash, text)
    if match:
        date_str = match.group(0)
        try:
            # Intentar parsear
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except:
                    continue
        except:
            pass
    
    # Patrón ISO YYYY-MM-DD
    pattern_iso = r'\b(\d{4}-\d{2}-\d{2})\b'
    match = re.search(pattern_iso, text)
    if match:
        return match.group(0) + "T00:00:00"
    
    return None

def parse_sale_from_text(raw_text: str) -> Dict[str, Any]:
    """
    Parsea un texto completo y extrae información de venta.
    Retorna un diccionario con los campos detectados.
    """
    amount = extract_amount(raw_text)
    phone = extract_phone(raw_text)
    cuit, cuit_suffix = extract_cuit(raw_text)
    ref = extract_reference(raw_text)
    name = extract_customer_name(raw_text)
    dt = extract_datetime(raw_text)
    
    return {
        "amount": amount,
        "datetime": dt,
        "customer_name": name,
        "customer_phone": phone,
        "customer_cuit": cuit,
        "external_ref": ref,
        "raw_text": raw_text[:500],  # Primeros 500 caracteres
    }
