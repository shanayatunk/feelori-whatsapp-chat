#!/bin/bash

# Feelori AI WhatsApp Assistant - GitHub Setup Script
# This script helps you save your production-ready AI assistant to GitHub

echo "🤖 Feelori AI WhatsApp Assistant - GitHub Setup"
echo "=============================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Initialize git repository if not already done
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore file..."
    cat > .gitignore << 'EOF'
# Environment variables (IMPORTANT: Never commit API keys!)
.env
**/.env
*.env

# Dependencies
node_modules/
venv/
__pycache__/
*.pyc

# Build outputs
build/
dist/
.next/

# Logs
*.log
logs/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite

# Backup files
backups/

# SSL certificates
ssl/
*.pem
*.key
*.crt

# Docker volumes
mongo_data/
redis_data/
prometheus_data/
grafana_data/
elasticsearch_data/
EOF
    echo "✅ .gitignore created"
fi

# Create environment template
echo "📝 Creating environment template..."
cat > .env.example << 'EOF'
# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN=your_whatsapp_business_api_token
WHATSAPP_PHONE_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token

# Shopify API Configuration
SHOPIFY_STORE_URL=yourstore.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_shopify_access_token

# AI Model API Keys
GEMINI_API_KEY=your_google_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
MONGO_URL=mongodb://localhost:27017/feelori_assistant

# Security Configuration
ADMIN_API_KEY=your_secure_admin_api_key_change_in_production

# Frontend Configuration
REACT_APP_BACKEND_URL=http://localhost:8001
EOF

# Stage all files
echo "📦 Staging files for commit..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "🚀 Initial commit: Feelori AI WhatsApp Assistant v2.0

✨ Features:
- AI-powered WhatsApp customer service with Gemini + OpenAI
- Shopify e-commerce integration for products and orders
- Professional React admin dashboard with real-time monitoring
- Production-ready FastAPI backend with authentication
- Comprehensive security: rate limiting, input validation, API keys
- Enterprise features: structured logging, health checks, metrics

🔧 Technical Stack:
- Backend: FastAPI + MongoDB + Python 3.11
- Frontend: React + Tailwind CSS + shadcn/ui
- AI: Google Gemini (primary) + OpenAI (fallback)
- Integrations: WhatsApp Business API + Shopify Admin API
- Deployment: Docker + Nginx + monitoring stack

🛡️ Production Ready:
- Authentication & authorization
- Rate limiting & security headers  
- Error handling & logging
- Comprehensive testing suite
- Docker deployment configuration
- Monitoring & alerting setup

Built with ❤️ for Feelori customers"

echo ""
echo "✅ Repository is ready! Next steps:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Name: feelori-ai-whatsapp-assistant"
echo "   - Description: AI-powered WhatsApp assistant for Feelori e-commerce"
echo "   - Make it Private (recommended for production keys)"
echo ""
echo "2. Connect to your GitHub repository:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/feelori-ai-whatsapp-assistant.git"
echo ""
echo "3. Push your code:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "🔐 SECURITY REMINDER:"
echo "   - Never commit .env files with real API keys"
echo "   - Use .env.example as a template"
echo "   - Set up GitHub Secrets for production deployment"
echo ""
echo "📚 Documentation:"
echo "   - Complete README.md included"
echo "   - API documentation in the code"
echo "   - Deployment guides in /deployment folder"
echo ""
echo "🎉 Your production-ready AI assistant is ready for GitHub!"