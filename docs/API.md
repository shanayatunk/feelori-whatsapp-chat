# API Reference Guide

## Overview

The Feelori AI WhatsApp Assistant provides a comprehensive REST API built with FastAPI. This guide covers all available endpoints, authentication, and usage examples.

**Base URL**: `http://localhost:8001` (development) or `https://your-domain.com` (production)

## Authentication

### JWT Authentication
Most admin endpoints require JWT token authentication.

#### Get Access Token
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "password": "your_admin_password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### Using Access Token
Include the token in the Authorization header:
```http
Authorization: Bearer your_jwt_token_here
```

### API Key Authentication
Some endpoints (like metrics) require API key authentication:
```http
Authorization: Bearer your_api_key
```

## Endpoints

### Health Check Endpoints

#### Basic Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-09T12:00:00.000000",
  "version": "2.0.0"
}
```

#### Readiness Probe
```http
GET /health/ready
```

Checks if all services (MongoDB, Redis, external APIs) are ready.

**Response**:
```json
{
  "status": "ready",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "ai_services": "healthy"
  }
}
```

#### Liveness Probe
```http
GET /health/live
```

Simple liveness check for Kubernetes.

**Response**:
```json
{
  "status": "alive",
  "timestamp": "2025-08-09T12:00:00.000000",
  "version": "2.0.0"
}
```

#### Comprehensive Health Check
```http
GET /health/comprehensive
Authorization: Bearer your_api_key
```

Detailed health information including all services and metrics.

### Root Endpoint

#### Service Information
```http
GET /
```

**Response**:
```json
{
  "service": "Feelori AI WhatsApp Assistant",
  "version": "2.0.0",
  "status": "operational",
  "environment": "development"
}
```

### Authentication Endpoints

#### Admin Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "password": "admin_password"
}
```

**Validation**:
- Password must be at least 12 characters
- Rate limited to 5 attempts per minute per IP

**Success Response**:
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer", 
  "expires_in": 86400
}
```

**Error Response**:
```json
{
  "detail": "Invalid credentials"
}
```

#### Admin Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer jwt_token
```

**Response**:
```json
{
  "message": "Successfully logged out"
}
```

### Admin Endpoints

All admin endpoints require JWT authentication.

#### Get Admin Profile
```http
GET /api/v1/admin/me
Authorization: Bearer jwt_token
```

**Response**:
```json
{
  "user": "admin"
}
```

#### Get System Statistics
```http
GET /api/v1/admin/stats
Authorization: Bearer jwt_token
```

**Response**:
```json
{
  "success": true,
  "data": {
    "total_customers": 150,
    "messages_today": 45,
    "active_conversations": 12,
    "ai_requests": {
      "gemini": 120,
      "openai": 25
    },
    "system_health": "healthy"
  }
}
```

#### Get Products
```http
GET /api/v1/admin/products
Authorization: Bearer jwt_token
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "12345",
      "title": "Premium T-Shirt",
      "description": "High-quality cotton t-shirt...",
      "price": 29.99,
      "currency": "USD",
      "availability": "in_stock",
      "image_url": "https://example.com/image.jpg"
    }
  ]
}
```

#### Get Customers
```http
GET /api/v1/admin/customers?limit=50&offset=0
Authorization: Bearer jwt_token
```

**Parameters**:
- `limit` (optional): Number of customers to return (default: 50)
- `offset` (optional): Number of customers to skip (default: 0)

**Response**:
```json
{
  "customers": [
    {
      "phone_number": "+1234567890",
      "first_interaction": "2025-01-01T10:00:00Z",
      "last_interaction": "2025-01-02T15:30:00Z",
      "total_messages": 15,
      "status": "active"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

#### Get Security Events
```http
GET /api/v1/admin/security/events?limit=50&offset=0
Authorization: Bearer jwt_token
```

**Response**:
```json
{
  "events": [
    {
      "event_type": "failed_login",
      "ip_address": "192.168.1.1",
      "timestamp": "2025-01-01T10:00:00Z",
      "details": {
        "reason": "invalid_password"
      }
    }
  ]
}
```

### WhatsApp Webhook Endpoints

#### Webhook Verification (GET)
```http
GET /api/v1/webhook?hub.mode=subscribe&hub.challenge=challenge_string&hub.verify_token=verify_token
```

Used by WhatsApp to verify webhook URL.

**Parameters**:
- `hub.mode`: Must be "subscribe"
- `hub.challenge`: Challenge string from WhatsApp
- `hub.verify_token`: Must match your configured verify token

**Response**: Returns the challenge string if verification succeeds.

#### Message Processing (POST)
```http
POST /api/v1/webhook
Content-Type: application/json
X-Hub-Signature-256: sha256=signature

{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "entry_id",
      "changes": [
        {
          "value": {
            "messages": [
              {
                "from": "1234567890",
                "id": "message_id",
                "timestamp": "1640995200",
                "text": {
                  "body": "Hello, I need help"
                },
                "type": "text"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

Processes incoming WhatsApp messages and generates AI responses.

### Message Processing Endpoints

#### Send Message
```http
POST /api/v1/admin/send-message
Content-Type: application/json
Authorization: Bearer jwt_token

{
  "phone_number": "+1234567890",
  "message": "Hello! How can I help you today?"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Message sent successfully",
  "message_id": "whatsapp_message_id"
}
```

#### Broadcast Message
```http
POST /api/v1/admin/broadcast
Content-Type: application/json
Authorization: Bearer jwt_token

{
  "phone_numbers": ["+1234567890", "+0987654321"],
  "message": "Important announcement for all customers"
}
```

**Response**:
```json
{
  "success": true,
  "sent": 2,
  "failed": 0,
  "results": [
    {
      "phone": "+1234567890",
      "status": "sent",
      "message_id": "msg_id_1"
    }
  ]
}
```

### Metrics Endpoint

#### Prometheus Metrics
```http
GET /metrics
Authorization: Bearer api_key
```

Returns Prometheus-compatible metrics:
```
# HELP whatsapp_messages_total Total messages processed
# TYPE whatsapp_messages_total counter
whatsapp_messages_total{status="success",message_type="text"} 1250

# HELP response_time_seconds Response time in seconds
# TYPE response_time_seconds histogram
response_time_seconds_sum{endpoint="/api/v1/webhook"} 45.2
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-08-09T12:00:00.000000"
}
```

### Common Error Codes

- `INVALID_CREDENTIALS`: Authentication failed
- `TOKEN_EXPIRED`: JWT token has expired
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_PHONE_NUMBER`: Phone number format invalid
- `SERVICE_UNAVAILABLE`: External service unavailable
- `WEBHOOK_VERIFICATION_FAILED`: WhatsApp webhook verification failed

## Rate Limiting

The API implements rate limiting to prevent abuse:

| Endpoint | Limit |
|----------|-------|
| `/health/*` | 60/minute |
| `/api/v1/auth/login` | 5/minute per IP |
| `/api/v1/webhook` | 100/minute |
| `/api/v1/admin/*` | 10/minute per user |
| `/metrics` | 10/minute |

When rate limit is exceeded:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60
}
```

## Request/Response Examples

### Curl Examples

#### Health Check
```bash
curl -X GET "http://localhost:8001/health"
```

#### Admin Login
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"password": "your_admin_password"}'
```

#### Get Statistics
```bash
TOKEN="your_jwt_token"
curl -X GET "http://localhost:8001/api/v1/admin/stats" \
     -H "Authorization: Bearer $TOKEN"
```

#### Send Message
```bash
TOKEN="your_jwt_token"
curl -X POST "http://localhost:8001/api/v1/admin/send-message" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "phone_number": "+1234567890",
       "message": "Hello from Feelori AI Assistant!"
     }'
```

### JavaScript/Axios Examples

#### Authentication
```javascript
const response = await axios.post('/api/v1/auth/login', {
  password: 'your_admin_password'
});

const token = response.data.access_token;
```

#### Get Products
```javascript
const response = await axios.get('/api/v1/admin/products', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const products = response.data.data;
```

### Python/Requests Examples

#### Health Check
```python
import requests

response = requests.get('http://localhost:8001/health')
health_data = response.json()
```

#### Admin Operations
```python
# Login
login_response = requests.post(
    'http://localhost:8001/api/v1/auth/login',
    json={'password': 'your_admin_password'}
)
token = login_response.json()['access_token']

# Get statistics
stats_response = requests.get(
    'http://localhost:8001/api/v1/admin/stats',
    headers={'Authorization': f'Bearer {token}'}
)
stats = stats_response.json()['data']
```

## Webhooks

### WhatsApp Webhook Setup

1. **Configure in WhatsApp Business Dashboard**:
   - Webhook URL: `https://your-domain.com/api/v1/webhook`
   - Verify Token: Your `WHATSAPP_VERIFY_TOKEN`

2. **Subscribe to Events**:
   - messages
   - message_deliveries
   - message_reads

3. **Security**:
   - All webhook requests are signature-verified
   - Invalid signatures are rejected

### Webhook Payload Structure

#### Message Received
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "business_account_id",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "1234567890",
              "phone_number_id": "phone_id"
            },
            "messages": [
              {
                "from": "sender_phone",
                "id": "message_id",
                "timestamp": "timestamp",
                "text": {
                  "body": "message_content"
                },
                "type": "text"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

## SDK and Client Libraries

### JavaScript Client
```javascript
class FeeloriAPIClient {
  constructor(baseURL, token = null) {
    this.baseURL = baseURL;
    this.token = token;
  }
  
  async login(password) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    const data = await response.json();
    this.token = data.access_token;
    return data;
  }
  
  async getStats() {
    const response = await fetch(`${this.baseURL}/api/v1/admin/stats`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }
}
```

### Python Client
```python
import requests

class FeeloriAPIClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
    
    def login(self, password):
        response = self.session.post(
            f'{self.base_url}/api/v1/auth/login',
            json={'password': password}
        )
        data = response.json()
        self.token = data['access_token']
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        return data
    
    def get_stats(self):
        response = self.session.get(f'{self.base_url}/api/v1/admin/stats')
        return response.json()
```

## Testing

### Health Check Test
```bash
# Test all health endpoints
curl -s http://localhost:8001/health | jq
curl -s http://localhost:8001/health/ready | jq
curl -s http://localhost:8001/health/live | jq
```

### Authentication Test
```bash
# Test login with correct password
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your_admin_password"}' | jq

# Test login with wrong password (should fail)
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "wrong_password"}' | jq
```

### Rate Limiting Test
```bash
# Test rate limiting (run multiple times quickly)
for i in {1..10}; do
  curl -s http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"password": "wrong"}' | jq .detail
done
```

---

*Last updated: August 2025*