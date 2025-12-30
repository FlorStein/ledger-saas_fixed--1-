#!/usr/bin/env python3
"""
Script de testing para WhatsApp Cloud API integration
Verifica conectividad Vercel ↔ Backend
"""

import requests
import json
import hmac
import hashlib
import sys
import os
from datetime import datetime

# Configuración
VERCEL_ENDPOINT = os.getenv("VERCEL_ENDPOINT", "http://localhost:3000")
BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://localhost:8000")
META_APP_SECRET = os.getenv("META_APP_SECRET", "test_secret_123")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ledger_saas_verify_123")
BACKEND_SHARED_SECRET = os.getenv("BACKEND_SHARED_SECRET", "ledger_saas_backend_secret")

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_ok(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

# Test 1: Verificación de Webhook
def test_verification():
    print_header("Test 1: GET Verification")
    
    url = f"{VERCEL_ENDPOINT}/api/whatsapp-webhook"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "test_challenge_value_12345"
    }
    
    print_info(f"GET {url}")
    print_info(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200 and response.text == "test_challenge_value_12345":
            print_ok("Verification successful")
            return True
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False

# Test 2: POST con firma válida
def test_post_valid_signature():
    print_header("Test 2: POST con Firma Válida")
    
    url = f"{VERCEL_ENDPOINT}/api/whatsapp-webhook"
    
    # Payload de prueba
    payload = {
        "entry": [
            {
                "id": "123456",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "16505551234",
                                "phone_number_id": "1234567890"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Juan Pérez"
                                    },
                                    "wa_id": "5491123456789"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "5491123456789",
                                    "id": "wamid.123456789",
                                    "timestamp": str(int(datetime.now().timestamp())),
                                    "type": "text",
                                    "text": {
                                        "body": "Hola, necesito reportar un comprobante"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    # Convertir a JSON string (raw body)
    raw_body = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    
    # Calcular firma HMAC SHA256
    signature = hmac.new(
        META_APP_SECRET.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "x-hub-signature-256": f"sha256={signature}"
    }
    
    print_info(f"POST {url}")
    print_info(f"Payload: {json.dumps(payload, indent=2)[:100]}...")
    print_info(f"Signature: sha256={signature[:20]}...")
    
    try:
        response = requests.post(
            url,
            data=raw_body,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print_ok("POST successful")
            print_info(f"Response: {response.json()}")
            return True
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False

# Test 3: POST con firma inválida
def test_post_invalid_signature():
    print_header("Test 3: POST con Firma Inválida")
    
    url = f"{VERCEL_ENDPOINT}/api/whatsapp-webhook"
    
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {
                                "phone_number_id": "1234567890"
                            },
                            "messages": [
                                {
                                    "id": "msg_123",
                                    "type": "text",
                                    "from": "5491123456789"
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    raw_body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "x-hub-signature-256": "sha256=invalid_signature_here"
    }
    
    print_info(f"POST {url}")
    print_info(f"Signature: invalid (esperamos 401)")
    
    try:
        response = requests.post(
            url,
            data=raw_body,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 401:
            print_ok("Correctly rejected invalid signature")
            return True
        else:
            print_error(f"Expected 401, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False

# Test 4: Backend Health Check
def test_backend_health():
    print_header("Test 4: Backend Health Check")
    
    url = f"{BACKEND_ENDPOINT}/health"
    
    print_info(f"GET {url}")
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print_ok("Backend is healthy")
            print_info(f"Response: {response.json()}")
            return True
        else:
            print_error(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Backend not responding: {str(e)}")
        return False

# Test 5: Backend Webhook Endpoint
def test_backend_webhook():
    print_header("Test 5: Backend Webhook Endpoint")
    
    url = f"{BACKEND_ENDPOINT}/webhooks/whatsapp/meta/cloud"
    
    payload = {
        "tenant_id": "tenant_demo",
        "phone_number_id": "1234567890",
        "payload": {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {
                                    "phone_number_id": "1234567890"
                                },
                                "messages": [
                                    {
                                        "id": "msg_123",
                                        "type": "text",
                                        "from": "5491123456789",
                                        "text": {
                                            "body": "Test message"
                                        }
                                    }
                                ],
                                "contacts": [
                                    {
                                        "profile": {
                                            "name": "Test User"
                                        },
                                        "wa_id": "5491123456789"
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
        "timestamp": datetime.now().isoformat()
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BACKEND_SHARED_SECRET}",
        "X-Tenant-ID": "tenant_demo",
        "X-Phone-Number-ID": "1234567890"
    }
    
    print_info(f"POST {url}")
    print_info(f"Authorization: Bearer {BACKEND_SHARED_SECRET[:20]}...")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print_ok("Backend webhook received successfully")
            print_info(f"Response: {response.json()}")
            return True
        else:
            print_error(f"Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False

# Test 6: Invalid Backend Auth
def test_backend_invalid_auth():
    print_header("Test 6: Backend con Auth Inválida")
    
    url = f"{BACKEND_ENDPOINT}/webhooks/whatsapp/meta/cloud"
    
    payload = {
        "tenant_id": "tenant_demo",
        "phone_number_id": "1234567890",
        "payload": {}
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer invalid_token_123"
    }
    
    print_info(f"POST {url} (esperamos 401)")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 401:
            print_ok("Correctly rejected invalid auth token")
            return True
        else:
            print_error(f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False

# Main
def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   WhatsApp Cloud API - Integration Test Suite              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    results = {
        "GET Verification": test_verification(),
        "POST Valid Signature": test_post_valid_signature(),
        "POST Invalid Signature": test_post_invalid_signature(),
        "Backend Health": test_backend_health(),
        "Backend Webhook": test_backend_webhook(),
        "Backend Invalid Auth": test_backend_invalid_auth(),
    }
    
    print_header("SUMMARY")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
