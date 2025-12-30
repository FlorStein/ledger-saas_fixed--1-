#!/bin/bash
# Setup script para WhatsApp Cloud API integration

set -e

echo "======================================================"
echo "  WhatsApp Cloud API Setup Script"
echo "======================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}⚠️  Vercel CLI not found. Installing...${NC}"
    npm install -g vercel
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

echo ""
echo "Step 1: Verify Local Setup"
echo "---"

# Check backend
if [ ! -d "backend" ]; then
    echo -e "${RED}❌ /backend directory not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend directory exists${NC}"

# Check frontend
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ /frontend directory not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend directory exists${NC}"

# Check api
if [ ! -d "api" ]; then
    echo -e "${YELLOW}⚠️  Creating /api directory...${NC}"
    mkdir -p api
fi
echo -e "${GREEN}✅ API directory exists${NC}"

# Check whatsapp-webhook.js
if [ ! -f "api/whatsapp-webhook.js" ]; then
    echo -e "${RED}❌ api/whatsapp-webhook.js not found${NC}"
    echo "This file should already exist. Please check your repo."
    exit 1
fi
echo -e "${GREEN}✅ api/whatsapp-webhook.js exists${NC}"

echo ""
echo "Step 2: Check Backend Environment"
echo "---"

if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Creating backend/.env from template...${NC}"
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
    else
        echo "BACKEND_SHARED_SECRET=ledger_saas_backend_secret" > backend/.env
        echo "TENANT_ROUTING_JSON={}" >> backend/.env
    fi
fi

# Add WhatsApp variables to backend .env
if ! grep -q "BACKEND_SHARED_SECRET" backend/.env; then
    echo "BACKEND_SHARED_SECRET=ledger_saas_backend_secret" >> backend/.env
fi
if ! grep -q "TENANT_ROUTING_JSON" backend/.env; then
    echo "TENANT_ROUTING_JSON={}" >> backend/.env
fi

echo -e "${GREEN}✅ Backend .env configured${NC}"

echo ""
echo "Step 3: Install Python Dependencies"
echo "---"

cd backend

# Create venv if not exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null

# Install/upgrade requirements
if grep -q "requests" requirements.txt; then
    echo -e "${GREEN}✅ requests already in requirements.txt${NC}"
else
    echo -e "${YELLOW}Adding 'requests' to requirements.txt...${NC}"
    echo "requests>=2.31.0" >> requirements.txt
fi

pip install -q -r requirements.txt
echo -e "${GREEN}✅ Python dependencies installed${NC}"

cd ..

echo ""
echo "Step 4: Configure Vercel"
echo "---"

read -p "Link Vercel project? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    vercel link
    echo -e "${GREEN}✅ Vercel project linked${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping Vercel link${NC}"
fi

echo ""
echo "Step 5: Test Local Setup"
echo "---"

if python3 test_whatsapp_integration.py 2>/dev/null; then
    echo -e "${GREEN}✅ Tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Tests need manual verification${NC}"
    echo "Run: python3 test_whatsapp_integration.py"
fi

echo ""
echo "======================================================"
echo "  Setup Complete!"
echo "======================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Get Meta App Secret:"
echo "   → https://developers.facebook.com"
echo "   → Your App → Settings → Basic"
echo "   → Copy 'App Secret'"
echo ""
echo "2. Add environment variables to Vercel:"
echo "   → vercel env add WHATSAPP_VERIFY_TOKEN"
echo "   → vercel env add META_APP_SECRET"
echo "   → vercel env add BACKEND_INGEST_URL"
echo "   → vercel env add BACKEND_SHARED_SECRET"
echo "   → vercel env add TENANT_ROUTING_JSON"
echo ""
echo "3. Configure webhook in Meta Dashboard:"
echo "   → WhatsApp → Configuration"
echo "   → Callback URL: https://your-vercel-app.vercel.app/api/whatsapp-webhook"
echo "   → Verify Token: ledger_saas_verify_123"
echo "   → Click 'Verify and Save'"
echo ""
echo "4. Deploy to Vercel:"
echo "   → vercel --prod"
echo ""
echo "5. Run local tests:"
echo "   → python3 test_whatsapp_integration.py"
echo ""
echo "Documentation:"
echo "   → WHATSAPP_SETUP.md (setup completo)"
echo "   → DEPLOYMENT_GUIDE.md (deploy a producción)"
echo ""
