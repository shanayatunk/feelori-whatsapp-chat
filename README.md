# 🤖 Feelori AI WhatsApp Assistant

A production-ready AI-powered WhatsApp assistant for e-commerce customer service, built with FastAPI, React, and MongoDB.

## 🚀 Features

### 🤖 AI-Powered Customer Service
- **Dual AI System**: Google Gemini (primary) + OpenAI GPT-4 (fallback)
- **Context-Aware Conversations**: Remembers customer history and preferences
- **Intelligent Intent Recognition**: Product search, order tracking, customer support
- **Multi-language Support**: Expandable for international customers

### 📱 WhatsApp Business API Integration
- **Real-time Message Processing**: Instant responses to customer inquiries
- **Webhook Support**: Secure message handling with verification
- **Rich Media Support**: Text, images, and structured messages
- **Rate Limiting**: Protection against spam and abuse

### 🛍️ Shopify E-commerce Integration
- **Product Catalog Access**: Real-time product information and availability
- **Order Tracking**: Automatic order status updates and tracking information
- **Inventory Management**: Live stock status and product recommendations
- **Customer Data Sync**: Seamless integration with existing customer database

### 📊 Advanced Admin Dashboard
- **Real-time Analytics**: Message statistics, customer metrics, performance insights
- **Conversation Monitoring**: Live view of AI-customer interactions
- **System Health Dashboard**: Monitor all integrations and service status
- **Message Testing**: Send test messages directly from the admin panel

### 🔒 Production-Ready Security
- **API Key Authentication**: Secure access to protected endpoints
- **Rate Limiting**: Comprehensive protection against abuse
- **Input Validation**: Strict validation for phone numbers and messages
- **CORS Protection**: Secure cross-origin resource sharing
- **Error Handling**: Graceful failure handling with logging

## 🏗️ Architecture

### Backend (FastAPI)
- **Asynchronous Processing**: High-performance async/await patterns
- **Structured Logging**: JSON-formatted logs for production monitoring
- **Health Checks**: Comprehensive system monitoring endpoints
- **Database Integration**: MongoDB with async Motor driver
- **External APIs**: WhatsApp, Shopify, Gemini, OpenAI integrations

### Frontend (React)
- **Modern UI/UX**: Professional dashboard with Tailwind CSS
- **Error Boundaries**: Robust error handling and user feedback
- **Real-time Updates**: Live status monitoring and notifications
- **Responsive Design**: Mobile-first approach with desktop optimization
- **Accessibility**: WCAG compliant with ARIA labels and keyboard navigation

### Database (MongoDB)
- **Customer Management**: Persistent conversation history and preferences
- **Performance Optimization**: Indexed queries and data validation
- **Scalable Schema**: Flexible document structure for growth

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB 5.0+
- Docker (optional)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/feelori-ai-assistant.git
   cd feelori-ai-assistant
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API keys
   uvicorn server:app --reload --port 8001
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Database Setup**
   ```bash
   # Start MongoDB locally or use Docker
   mongod --dbpath /data/db
   ```

### Environment Variables

Create a `.env` file in the backend directory with the following:

```env
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_ID=your_phone_id
WHATSAPP_VERIFY_TOKEN=your_verify_token

# Shopify API
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_shopify_token

# AI Models
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Database
MONGO_URL=mongodb://localhost:27017/feelori_assistant

# Security
ADMIN_API_KEY=your_secure_admin_key
```

## 📚 API Documentation

### Endpoints

#### Public Endpoints
- `GET /` - API information
- `GET /api/health` - System health check
- `GET /api/products` - Product catalog (rate limited)
- `GET /api/webhook` - WhatsApp webhook verification
- `POST /api/webhook` - WhatsApp message processing

#### Protected Endpoints (Require API Key)
- `POST /api/send-message` - Send WhatsApp message
- `GET /api/customers/{phone}` - Customer information
- `GET /api/orders/{phone}` - Customer orders
- `GET /api/metrics` - System metrics

### Authentication

Protected endpoints require an `Authorization` header:
```
Authorization: Bearer your_admin_api_key
```

### Rate Limits
- Health endpoint: 60 requests/minute
- Products endpoint: 30 requests/minute
- Send message: 10 requests/minute
- Webhook: 100 requests/minute

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/test_api.py -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
python tests/test_integration.py
```

## 🚀 Production Deployment

### Docker Deployment
```bash
docker-compose -f deployment/docker-compose.prod.yml up -d
```

### Manual Deployment
1. **Build Frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy Backend**
   ```bash
   cd backend
   gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Configure Nginx**
   ```bash
   cp deployment/nginx/nginx.conf /etc/nginx/sites-available/feelori-ai
   ln -s /etc/nginx/sites-available/feelori-ai /etc/nginx/sites-enabled/
   systemctl reload nginx
   ```

### WhatsApp Webhook Setup
1. Configure webhook URL in WhatsApp Business API dashboard:
   ```
   https://your-domain.com/api/webhook
   ```
2. Set verify token to match `WHATSAPP_VERIFY_TOKEN`
3. Subscribe to `messages` events

## 📊 Monitoring & Observability

### Structured Logging
All logs are in JSON format for easy parsing:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "Message processed successfully",
  "module": "server"
}
```

### Health Monitoring
The `/api/health` endpoint provides comprehensive system status:
- Database connectivity
- External API status
- AI model availability
- Service health metrics

### Performance Metrics
- Response times
- Error rates
- Message processing volume
- Customer engagement metrics

## 🔧 Configuration

### AI Model Configuration
The system supports multiple AI providers with automatic failover:
1. **Primary**: Google Gemini (fast, cost-effective)
2. **Fallback**: OpenAI GPT-4 (reliable, high-quality)
3. **Error Handling**: Graceful degradation with helpful messages

### Customization Options
- **AI Prompts**: Modify system prompts in `server.py`
- **UI Themes**: Customize colors and styling in `App.css`
- **Business Logic**: Extend intent recognition and response generation
- **Integrations**: Add new e-commerce platforms or communication channels

## 🛡️ Security Best Practices

### Implemented Security Measures
- **API Key Authentication**: Secure endpoint protection
- **Rate Limiting**: DDoS and abuse protection
- **Input Validation**: Comprehensive data sanitization
- **HTTPS Only**: Encrypted communication
- **CORS Protection**: Secure cross-origin requests
- **Security Headers**: XSS, clickjacking protection

### Security Checklist
- [ ] Change default API keys
- [ ] Configure proper CORS origins
- [ ] Set up SSL certificates
- [ ] Enable firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs

## 📈 Scaling Considerations

### Horizontal Scaling
- **Backend**: Multiple FastAPI instances behind load balancer
- **Database**: MongoDB replica sets or sharding
- **Cache**: Redis cluster for session management
- **CDN**: Static asset distribution

### Performance Optimization
- **Database Indexing**: Optimize query performance
- **Caching**: Redis for frequently accessed data
- **Message Queuing**: For high-volume message processing
- **Connection Pooling**: Efficient database connections

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- **Python**: Follow PEP 8, use type hints
- **JavaScript**: Use ESLint and Prettier
- **Git**: Conventional commit messages
- **Documentation**: Update README for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **WhatsApp Business API** for messaging infrastructure
- **Shopify** for e-commerce integration
- **Google Gemini** and **OpenAI** for AI capabilities
- **FastAPI** and **React** communities for excellent frameworks

## 📞 Support

For technical support or questions:
- **Email**: support@feelori.com
- **Issues**: GitHub Issues
- **Documentation**: [Wiki](https://github.com/your-username/feelori-ai-assistant/wiki)

---

**Built with ❤️ for Feelori customers**