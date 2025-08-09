# 🤖 Feelori AI WhatsApp Assistant

A production-ready AI-powered WhatsApp assistant for e-commerce customer service, built with FastAPI, React, and MongoDB.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Node](https://img.shields.io/badge/node-18+-green)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)

## 🚀 Features

### 🤖 AI-Powered Customer Service
- **Dual AI System**: Google Gemini (primary) + OpenAI GPT-4 (fallback)
- **Context-Aware Conversations**: Remembers customer history and preferences
- **Intelligent Intent Recognition**: Product search, order tracking, customer support
- **Multi-language Support**: Expandable for international customers
- **Fallback Responses**: Rule-based responses when AI services are unavailable

### 📱 WhatsApp Business API Integration
- **Real-time Message Processing**: Instant responses to customer inquiries
- **Webhook Support**: Secure message handling with signature verification
- **Rich Media Support**: Text, images, and structured messages
- **Rate Limiting**: Protection against spam and abuse
- **Interactive Lists**: Product catalogs and quick replies

### 🛍️ Shopify E-commerce Integration
- **Product Catalog Access**: Real-time product information and availability
- **Order Tracking**: Automatic order status updates and tracking information
- **Inventory Management**: Live stock status and product recommendations
- **Customer Data Sync**: Seamless integration with existing customer database

### 📊 Advanced Admin Dashboard
- **Real-time Analytics**: Message statistics, customer metrics, performance insights
- **Conversation Monitoring**: Live view of AI-customer interactions
- **System Health Dashboard**: Monitor all integrations and service status
- **User Management**: Secure admin authentication with JWT tokens
- **Product Management**: View and manage product catalog

### 🔒 Production-Ready Security
- **JWT Authentication**: Secure admin access with token-based authentication
- **Rate Limiting**: Comprehensive protection against abuse and DDoS
- **Input Validation**: Strict validation for phone numbers and messages
- **CORS Protection**: Secure cross-origin resource sharing
- **Security Headers**: XSS and clickjacking protection
- **Circuit Breakers**: Automatic service protection and graceful degradation

### 🏗️ Robust Architecture
- **Microservices Ready**: Modular design with service containers
- **Database Integration**: MongoDB with async Motor driver
- **Caching Layer**: Redis for performance optimization
- **Message Queuing**: Redis Streams for reliable message processing
- **Monitoring & Logging**: Structured JSON logging with multiple levels
- **Health Checks**: Comprehensive system monitoring endpoints

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │     Admin       │    │   External      │
│   Business API  │    │   Dashboard     │    │   Services      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│  Authentication │  Rate Limiting │  Security │  Circuit Breaker│
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   WhatsApp      │      AI         │     Shopify     │   Admin   │
│   Service       │    Service      │    Service      │  Service  │
└─────────┬───────┴─────────┬───────┴─────────┬───────┴───────┬───┘
          │                 │                 │               │
          ▼                 ▼                 ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌──────┐
│     Redis       │ │    MongoDB      │ │  External APIs  │ │ Logs │
│   (Caching &    │ │  (Customer &    │ │  (Gemini, GPT,  │ │      │
│   Queuing)      │ │   Messages)     │ │   Shopify)      │ │      │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └──────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance async Python web framework
- **Python 3.11+**: Modern Python with type hints and async support
- **MongoDB**: NoSQL database with Motor async driver
- **Redis**: In-memory caching and message queuing
- **Pydantic**: Data validation and settings management
- **JWT**: Token-based authentication
- **OpenTelemetry**: Distributed tracing and monitoring

### Frontend
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe JavaScript development
- **Vite**: Fast development server and build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Axios**: HTTP client for API communications

### Infrastructure
- **Docker**: Containerization support
- **Supervisor**: Process management
- **Nginx**: Reverse proxy and load balancing
- **Let's Encrypt**: SSL certificate management

### External Integrations
- **Google Gemini**: Primary AI service
- **OpenAI GPT-4**: Fallback AI service
- **WhatsApp Business API**: Messaging platform
- **Shopify API**: E-commerce platform integration

## 📋 Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- MongoDB 5.0 or higher
- Redis 6.0 or higher
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/feelori-ai-assistant.git
cd feelori-ai-assistant
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Environment is already configured
```

### 4. Database Setup

```bash
# Start MongoDB (if not already running)
sudo systemctl start mongod

# Start Redis (if not already running)
sudo systemctl start redis
```

### 5. Run the Application

```bash
# Start backend (in backend directory)
uvicorn app.server:app --host 0.0.0.0 --port 8001 --reload

# Start frontend (in frontend directory)
yarn dev
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Admin Login**: Use password from your .env file

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Database
MONGO_ATLAS_URI=mongodb://localhost:27017/feelori_assistant

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_ID=your_phone_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret

# Shopify API
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_shopify_token

# AI Services
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Security
JWT_SECRET_KEY=your_secure_jwt_secret_key_minimum_32_characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
ADMIN_PASSWORD=your_secure_admin_password
SESSION_SECRET_KEY=your_secure_session_secret_key_minimum_32_characters
API_KEY=your_api_key_for_metrics_access

# Redis
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=production
```

### Security Configuration

1. **Generate Secure Keys**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Set Strong Admin Password**: Minimum 12 characters with mixed case, numbers, and symbols

3. **Configure CORS**: Update `CORS_ALLOWED_ORIGINS` for your domain

### WhatsApp Business API Setup

1. **Create WhatsApp Business Account**
2. **Set up Webhook URL**: `https://your-domain.com/api/v1/webhook`
3. **Configure Verification Token**: Set in WhatsApp dashboard
4. **Subscribe to Message Events**

### Shopify Integration Setup

1. **Create Private App in Shopify**
2. **Generate Access Token** with required permissions:
   - Products: Read access
   - Orders: Read access
   - Customers: Read access

## 📖 API Documentation

### Authentication Endpoints

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "password": "your_admin_password"
}
```

Response:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Admin Endpoints

All admin endpoints require Bearer token authentication:
```http
Authorization: Bearer your_jwt_token
```

#### Get Admin Profile
```http
GET /api/v1/admin/me
```

#### Get System Statistics
```http
GET /api/v1/admin/stats
```

#### Get Products
```http
GET /api/v1/admin/products
```

### WhatsApp Webhook Endpoints

#### Webhook Verification
```http
GET /api/v1/webhook?hub.mode=subscribe&hub.challenge=challenge&hub.verify_token=token
```

#### Message Processing
```http
POST /api/v1/webhook
Content-Type: application/json
```

### Health Check Endpoints

#### Basic Health Check
```http
GET /health
```

#### Readiness Probe
```http
GET /health/ready
```

#### Liveness Probe
```http
GET /health/live
```

For complete API documentation, visit: http://localhost:8001/docs

## 🚀 Deployment

### Docker Deployment

```bash
# Build and start services
docker-compose -f deployment/docker-compose.prod.yml up -d
```

### Manual Production Deployment

1. **Build Frontend**:
   ```bash
   cd frontend
   yarn build
   ```

2. **Configure Nginx**:
   ```bash
   sudo cp deployment/nginx/nginx.conf /etc/nginx/sites-available/feelori-ai
   sudo ln -s /etc/nginx/sites-available/feelori-ai /etc/nginx/sites-enabled/
   sudo systemctl reload nginx
   ```

3. **Start Backend with Gunicorn**:
   ```bash
   cd backend
   gunicorn app.server:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

4. **Set up SSL with Let's Encrypt**:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

### Environment-Specific Configurations

#### Production
- Use production database (MongoDB Atlas recommended)
- Enable SSL/HTTPS
- Set up monitoring and alerting
- Configure backup strategies
- Use production-grade Redis cluster

#### Staging
- Use separate database instance
- Enable debug logging
- Test with production-like data
- Validate all integrations

## 📊 Monitoring & Maintenance

### Health Monitoring

The application provides several health check endpoints:

- `/health` - Basic application health
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Kubernetes liveness probe
- `/health/comprehensive` - Detailed system health (requires API key)

### Logging

Structured JSON logging is implemented with different levels:
- **ERROR**: Critical issues requiring immediate attention
- **WARNING**: Important events that need monitoring
- **INFO**: General application flow
- **DEBUG**: Detailed debugging information

### Metrics

Prometheus metrics available at `/metrics` endpoint (requires API key):
- Request rates and response times
- Error rates and types
- Database operation metrics
- AI service usage statistics
- WhatsApp message processing metrics

### Backup Strategy

1. **Database Backup**:
   ```bash
   mongodump --uri="mongodb://localhost:27017/feelori_assistant"
   ```

2. **Configuration Backup**:
   - Backup all `.env` files
   - Backup nginx configurations
   - Backup SSL certificates

3. **Automated Backup Script**:
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   mongodump --uri="$MONGO_ATLAS_URI" --out="/backups/mongo_$DATE"
   tar -czf "/backups/config_$DATE.tar.gz" backend/.env frontend/.env
   ```

## 🔧 Troubleshooting

### Common Issues

#### Backend Won't Start
1. Check if MongoDB and Redis are running
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Check logs: `tail -f /var/log/supervisor/backend.err.log`

#### Authentication Failures
1. Verify JWT_SECRET_KEY is set and correct
2. Check admin password configuration
3. Ensure token hasn't expired
4. Verify CORS settings for frontend domain

#### WhatsApp Webhook Issues
1. Verify webhook URL is accessible from internet
2. Check WHATSAPP_VERIFY_TOKEN matches dashboard setting
3. Ensure webhook signature verification is working
4. Test with WhatsApp webhook tester

#### AI Service Failures
1. Verify API keys are valid and have sufficient quota
2. Check rate limiting on AI services
3. Ensure fallback responses are working
4. Monitor AI service status pages

### Debug Mode

Enable debug logging by setting:
```bash
ENVIRONMENT=development
```

### Performance Issues

1. **Check Database Performance**:
   ```bash
   # Monitor MongoDB operations
   mongostat
   
   # Check slow queries
   db.setProfilingLevel(2)
   db.system.profile.find().sort({ts:-1}).limit(5)
   ```

2. **Monitor Redis Performance**:
   ```bash
   redis-cli info stats
   redis-cli monitor
   ```

3. **Check Memory Usage**:
   ```bash
   ps aux | grep -E "(python|node)"
   free -h
   ```

### Getting Help

1. **Check Application Logs**:
   ```bash
   # Backend logs
   tail -f /var/log/supervisor/backend.out.log
   
   # Frontend logs
   tail -f /var/log/supervisor/frontend.out.log
   ```

2. **API Health Check**:
   ```bash
   curl -s http://localhost:8001/health | jq
   ```

3. **Test Database Connection**:
   ```bash
   mongo $MONGO_ATLAS_URI --eval "db.adminCommand('ping')"
   ```

## 🤝 Contributing

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Make Changes**: Follow code style and add tests
4. **Run Tests**: `pytest backend/tests/` and `yarn test`
5. **Commit Changes**: `git commit -m 'Add amazing feature'`
6. **Push to Branch**: `git push origin feature/amazing-feature`
7. **Open Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all new frontend code
- Add tests for new functionality
- Update documentation for API changes
- Follow semantic versioning

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **WhatsApp Business API** for messaging infrastructure
- **Shopify** for e-commerce integration capabilities
- **Google Gemini** and **OpenAI** for AI/ML capabilities
- **FastAPI** and **React** communities for excellent frameworks
- **MongoDB** and **Redis** for reliable data storage

## 📞 Support

- **Documentation**: See `docs/` directory for detailed guides
- **Issues**: Report bugs on GitHub Issues
- **Email**: support@feelori.com

---

**Built with ❤️ for enhanced customer experience**

*Last updated: August 2025*