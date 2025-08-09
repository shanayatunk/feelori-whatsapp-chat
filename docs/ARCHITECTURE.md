# Architecture Overview

This document provides a detailed overview of the Feelori AI WhatsApp Assistant architecture, including system design, data flow, and component interactions.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │     Admin       │    │   External      │
│   Business API  │    │   Dashboard     │    │   Services      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │    Auth     │ │Rate Limiting│ │   CORS      │ │   Logging   ││
│  │Middleware   │ │ Middleware  │ │ Middleware  │ │ Middleware  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                    Service Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │  WhatsApp   │ │     AI      │ │   Shopify   │ │    Admin    ││
│  │   Service   │ │   Service   │ │   Service   │ │   Service   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                    Data Layer                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   MongoDB   │ │    Redis    │ │   Circuit   │ │   Message   ││
│  │  Database   │ │    Cache    │ │  Breakers   │ │   Queue     ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### Frontend (React Application)
```
Frontend (Port 3000)
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Basic UI primitives
│   │   └── features/       # Feature-specific components
│   ├── pages/              # Page components
│   │   ├── Login.tsx       # Authentication page
│   │   └── Dashboard.tsx   # Main dashboard
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.ts      # Authentication logic
│   │   ├── useApi.ts       # API communication
│   │   └── useToast.ts     # Notification system
│   ├── lib/                # Utility libraries
│   │   ├── api.ts          # API client configuration
│   │   └── utils.ts        # Helper functions
│   └── types/              # TypeScript definitions
```

#### Backend (FastAPI Application)
```
Backend (Port 8001)
├── app/
│   ├── server.py           # Main application entry point
│   ├── services/           # Business logic services
│   │   ├── whatsapp.py     # WhatsApp Business API
│   │   ├── shopify.py      # Shopify integration
│   │   ├── ai.py           # AI service (Gemini/OpenAI)
│   │   ├── database.py     # MongoDB operations
│   │   ├── cache.py        # Redis caching
│   │   └── auth.py         # Authentication service
│   ├── models/             # Data models
│   │   ├── customer.py     # Customer data structures
│   │   ├── message.py      # Message data structures
│   │   └── admin.py        # Admin data structures
│   └── middleware/         # Custom middleware
│       ├── auth.py         # Authentication middleware
│       ├── rate_limit.py   # Rate limiting
│       └── logging.py      # Request logging
```

## Data Flow

### Message Processing Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  WhatsApp   │    │   Webhook   │    │   Message   │    │     AI      │
│   Customer  │    │  Endpoint   │    │   Queue     │    │   Service   │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │                  │
       │ 1. Send Message  │                  │                  │
       ├─────────────────→│                  │                  │
       │                  │ 2. Queue Message │                  │
       │                  ├─────────────────→│                  │
       │                  │                  │ 3. Process       │
       │                  │                  ├─────────────────→│
       │                  │                  │ 4. AI Response   │
       │                  │                  │←─────────────────┤
       │                  │ 5. Send Response │                  │
       │                  │←─────────────────┤                  │
       │ 6. Receive Reply │                  │                  │
       │←─────────────────┤                  │                  │
```

### Authentication Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Admin     │    │  Frontend   │    │   Backend   │    │  Database   │
│    User     │    │Application  │    │     API     │    │  (MongoDB)  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │                  │
       │ 1. Enter Password│                  │                  │
       ├─────────────────→│                  │                  │
       │                  │ 2. Login Request │                  │
       │                  ├─────────────────→│                  │
       │                  │                  │ 3. Verify Password│
       │                  │                  ├─────────────────→│
       │                  │                  │ 4. Password Valid│
       │                  │                  │←─────────────────┤
       │                  │ 5. JWT Token     │                  │
       │                  │←─────────────────┤                  │
       │ 6. Access Dashboard                 │                  │
       │←─────────────────┤                  │                  │
       │                  │ 7. Protected API │                  │
       │                  ├─────────────────→│                  │
       │                  │ 8. Verify JWT    │                  │
       │                  │                  │ (In Memory)      │
       │                  │ 9. API Response  │                  │
       │                  │←─────────────────┤                  │
```

## Core Components

### 1. API Gateway (FastAPI)

The API Gateway serves as the central entry point for all requests.

#### Key Features:
- **Route Management**: Centralizes all API endpoints
- **Middleware Pipeline**: Handles authentication, CORS, rate limiting
- **Error Handling**: Standardized error responses
- **Request Logging**: Structured logging for all requests
- **Health Checks**: Multiple health check endpoints

#### Implementation:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Initialize services
    await services.initialize()
    yield
    # Cleanup
    await services.cleanup()

app = FastAPI(
    title="Feelori AI WhatsApp Assistant",
    version="2.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(SessionMiddleware, ...)
app.add_middleware(SlowAPIMiddleware)
```

### 2. Service Layer

The service layer contains the core business logic.

#### WhatsApp Service
```python
class WhatsAppService:
    async def send_message(self, to_phone: str, message: str) -> bool:
        """Send message via WhatsApp Business API"""
        
    async def send_interactive_list(self, to_phone: str, products: List[Product]) -> bool:
        """Send interactive product list"""
```

#### AI Service
```python
class AIService:
    async def generate_response(self, message: str, context: Dict = None) -> str:
        """Generate AI response with fallback logic"""
        # Try Gemini first
        # Fall back to OpenAI
        # Fall back to rule-based responses
```

#### Shopify Service
```python
class ShopifyService:
    async def get_products(self, query: str = "", limit: int = 10) -> List[Product]:
        """Fetch products from Shopify"""
        
    async def search_orders_by_phone(self, phone: str) -> List[Dict]:
        """Search customer orders"""
```

### 3. Data Layer

#### MongoDB Database
Primary data storage for:
- Customer information and conversation history
- Security events and audit logs
- System metrics and analytics

**Collections:**
- `customers`: Customer profiles and interaction history
- `security_events`: Authentication and security logs
- `system_metrics`: Performance and usage metrics

#### Redis Cache
Used for:
- Session management
- Rate limiting
- Message queuing
- Circuit breaker states
- Temporary data caching

### 4. Authentication System

JWT-based authentication with the following flow:

1. **Password Verification**: Admin enters password
2. **Token Generation**: JWT token created with expiration
3. **Token Storage**: Frontend stores token securely
4. **Request Authentication**: Token included in API requests
5. **Token Validation**: Backend verifies token on each request

#### Security Features:
- **IP Binding**: Tokens tied to originating IP
- **Expiration**: Configurable token lifetime
- **Refresh**: Automatic token refresh
- **Lockout**: Failed attempt tracking

### 5. Circuit Breaker Pattern

Implements circuit breaker pattern for external services:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.state = CircuitState.CLOSED
        
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            # Fail fast if still in timeout
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
```

## Data Models

### Customer Model
```python
class Customer(BaseModel):
    phone_number: str
    name: Optional[str] = None
    created_at: datetime
    last_interaction: Optional[datetime] = None
    conversation_history: List[ConversationEntry] = []
    preferences: Dict[str, Any] = {}
    status: CustomerStatus = CustomerStatus.ACTIVE

class ConversationEntry(BaseModel):
    timestamp: datetime
    message: str
    response: str
    message_id: str
    ai_model_used: Optional[str] = None
```

### Message Models
```python
class IncomingMessage(BaseModel):
    from_number: str
    message_text: str
    message_type: str = "text"
    timestamp: datetime
    message_id: str

class OutgoingMessage(BaseModel):
    to_number: str
    message_text: str
    message_type: str = "text"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Product Model
```python
class Product(BaseModel):
    id: str
    title: str
    description: str
    price: float
    currency: str = "USD"
    image_url: Optional[str] = None
    availability: str = "in_stock"
    tags: List[str] = []
```

## Security Architecture

### Multi-Layer Security

1. **Network Layer**:
   - HTTPS only in production
   - CORS configuration
   - Rate limiting
   - DDoS protection

2. **Application Layer**:
   - JWT authentication
   - Input validation
   - SQL injection prevention
   - XSS protection

3. **Data Layer**:
   - Database authentication
   - Encrypted connections
   - Data validation
   - Access logging

### Authentication & Authorization

```
Request → Rate Limiter → CORS Check → JWT Validation → Route Handler
    ↓           ↓            ↓             ↓              ↓
  Block      Block       Block        Block        Process
if exceed  if invalid  if invalid   if invalid    & Response
 limit     origin      token        permissions
```

### Security Middleware Pipeline

1. **TrustedHostMiddleware**: Validates request hosts
2. **CORSMiddleware**: Handles cross-origin requests
3. **RateLimitMiddleware**: Prevents abuse
4. **AuthenticationMiddleware**: Validates JWT tokens
5. **LoggingMiddleware**: Logs security events

## Performance Architecture

### Caching Strategy

```
Request Flow:
1. Check Redis cache for data
2. If cache miss, query database
3. Store result in cache with TTL
4. Return data to client

Cache Invalidation:
- Time-based expiration (TTL)
- Event-based invalidation
- Manual cache clearing
```

### Async Processing

All I/O operations use async/await:
- Database queries
- External API calls
- File operations
- Network requests

### Connection Pooling

- **MongoDB**: Connection pool with min/max limits
- **Redis**: Connection pool for cache operations
- **HTTP**: Persistent connections for external APIs

## Monitoring Architecture

### Logging Strategy

**Structured Logging** with JSON format:
```json
{
  "timestamp": "2025-08-09T12:00:00Z",
  "level": "INFO",
  "message": "Message processed",
  "module": "whatsapp_service",
  "customer_phone": "+1234567890",
  "processing_time_ms": 150,
  "ai_model": "gemini"
}
```

### Metrics Collection

**Prometheus Metrics**:
- Request rates and response times
- Error rates by endpoint
- AI service usage
- Database operation metrics
- Custom business metrics

### Health Checks

Multiple health check levels:
1. **Basic** (`/health`): Simple liveness check
2. **Ready** (`/health/ready`): Service readiness
3. **Live** (`/health/live`): Kubernetes liveness probe
4. **Comprehensive** (`/health/comprehensive`): Detailed system status

## Scalability Considerations

### Horizontal Scaling

**Backend Scaling**:
- Multiple FastAPI instances
- Load balancer (nginx/AWS ALB)
- Shared Redis for state
- Database read replicas

**Frontend Scaling**:
- CDN for static assets
- Multiple frontend instances
- API load balancing

### Database Scaling

**MongoDB Scaling**:
- Replica sets for high availability
- Sharding for large datasets
- Read preference optimization
- Index optimization

**Redis Scaling**:
- Redis Cluster for high availability
- Separate instances for different uses
- Memory optimization

### Message Queue Scaling

**Redis Streams**:
- Consumer groups for parallel processing
- Multiple workers for high throughput
- Dead letter queues for failed messages
- Monitoring and alerting

## Deployment Architecture

### Container Architecture

```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as backend
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "app.server:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]

FROM node:18-alpine as frontend
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile
COPY . .
RUN yarn build
CMD ["npx", "serve", "-s", "build"]
```

### Service Discovery

**Development**: Direct connection via localhost
**Production**: 
- Docker Compose: Service names
- Kubernetes: Service discovery
- Load balancers: Health check based routing

## Error Handling Architecture

### Error Propagation

```
Component Error → Service Layer → API Gateway → Client
     ↓               ↓              ↓           ↓
Log locally → Structured log → HTTP status → User message
Transform     Add context    Standard fmt   User-friendly
```

### Circuit Breaker Pattern

External service failures are handled gracefully:
1. **Closed**: Normal operation
2. **Open**: Fail fast, return cached/fallback data
3. **Half-Open**: Test service recovery

### Retry Logic

```python
@tenacity.retry(
    retry=tenacity.retry_if_exception_type(ConnectionError),
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10)
)
async def external_api_call():
    # API call implementation
```

## Configuration Management

### Environment-Based Configuration

```python
class Settings(BaseSettings):
    # Environment detection
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Database configuration
    mongo_atlas_uri: str
    
    # Feature flags
    enable_ai_fallback: bool = True
    enable_rate_limiting: bool = True
    
    class Config:
        env_file = '.env'
```

### Feature Flags

Runtime feature control:
- AI service selection
- Rate limiting toggles
- Debug mode switches
- Experimental feature flags

---

This architecture provides a robust, scalable foundation for the Feelori AI WhatsApp Assistant, with clear separation of concerns, comprehensive error handling, and production-ready security features.