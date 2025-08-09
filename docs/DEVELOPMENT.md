# Development Guide

This guide covers setting up a local development environment and contributing to the Feelori AI WhatsApp Assistant.

## Development Setup

### Prerequisites

- **Python 3.11+** with pip and venv
- **Node.js 18+** with npm/yarn
- **MongoDB 5.0+** (local or Docker)
- **Redis 6.0+** (local or Docker)
- **Git** for version control
- **VS Code** (recommended) with extensions

### Local Environment Setup

#### 1. Clone and Setup Repository
```bash
# Clone repository
git clone https://github.com/your-username/feelori-ai-assistant.git
cd feelori-ai-assistant

# Create development branch
git checkout -b feature/your-feature-name
```

#### 2. Backend Development Setup
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists

# Copy environment template
cp .env.example .env
```

#### 3. Frontend Development Setup
```bash
cd frontend

# Install dependencies
yarn install

# Install development tools globally (optional)
npm install -g typescript @vitejs/plugin-react
```

#### 4. Database Setup

##### MongoDB (Local)
```bash
# Install MongoDB
sudo apt install mongodb  # Ubuntu/Debian
brew install mongodb/brew/mongodb-community  # macOS

# Start MongoDB
sudo systemctl start mongodb  # Linux
brew services start mongodb-community  # macOS

# Create development database
mongo
> use feelori_assistant_dev
> db.createCollection("customers")
> exit
```

##### MongoDB (Docker)
```bash
# Start MongoDB container
docker run -d --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:5.0

# Update connection string in .env
MONGO_ATLAS_URI=mongodb://admin:password@localhost:27017/feelori_assistant_dev?authSource=admin
```

##### Redis (Local)
```bash
# Install Redis
sudo apt install redis-server  # Ubuntu/Debian
brew install redis  # macOS

# Start Redis
sudo systemctl start redis-server  # Linux
brew services start redis  # macOS
```

##### Redis (Docker)
```bash
# Start Redis container
docker run -d --name redis -p 6379:6379 redis:6-alpine

# Update connection string in .env
REDIS_URL=redis://localhost:6379
```

#### 5. Development Environment Variables

Create `backend/.env` for development:

```bash
# Development Environment Configuration

# Database
MONGO_ATLAS_URI=mongodb://localhost:27017/feelori_assistant_dev

# WhatsApp Business API (Mock/Test values for development)
WHATSAPP_ACCESS_TOKEN=mock_whatsapp_token_dev
WHATSAPP_PHONE_ID=1234567890
WHATSAPP_VERIFY_TOKEN=mock_verify_token_dev
WHATSAPP_WEBHOOK_SECRET=mock_webhook_secret_dev_123456

# Shopify API (Mock/Test values for development)
SHOPIFY_STORE_URL=dev-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=mock_shopify_token_dev

# AI Services (Mock values - will use fallback responses)
GEMINI_API_KEY=mock_gemini_key_dev
OPENAI_API_KEY=mock_openai_key_dev

# Security (Development values - not for production!)
JWT_SECRET_KEY=development_jwt_secret_key_not_for_production_use_minimum_32_chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
ADMIN_PASSWORD=dev_admin_password_123
SESSION_SECRET_KEY=development_session_secret_key_not_for_production_minimum_32_chars
API_KEY=dev_api_key_123

# Redis
REDIS_URL=redis://localhost:6379

# Development settings
ENVIRONMENT=development
HTTPS_ONLY=false
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOWED_HOSTS=localhost,127.0.0.1,*.localhost

# Debug settings
DEBUG=true
LOG_LEVEL=DEBUG

# Optional development services
SENTRY_DSN=
ALERTING_WEBHOOK_URL=
JAEGER_AGENT_HOST=
```

### Running the Application

#### Start Backend
```bash
cd backend
source venv/bin/activate

# Development server with auto-reload
uvicorn app.server:app --host 0.0.0.0 --port 8001 --reload

# Or using the development script
python -m uvicorn app.server:app --reload --port 8001
```

#### Start Frontend
```bash
cd frontend

# Development server with hot reload
yarn dev

# Or using npm
npm run dev
```

#### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Redoc Documentation**: http://localhost:8001/redoc

## Development Workflow

### Code Style and Standards

#### Python Code Style
We follow PEP 8 with some modifications:

```python
# Use type hints everywhere
from typing import Optional, List, Dict

def process_message(message: str, customer_id: Optional[str] = None) -> Dict[str, str]:
    """Process incoming message with proper typing."""
    pass

# Use async/await for I/O operations
async def fetch_customer_data(phone: str) -> Optional[dict]:
    """Fetch customer data asynchronously."""
    pass

# Use dataclasses or Pydantic models for data structures
from pydantic import BaseModel

class CustomerMessage(BaseModel):
    phone_number: str
    message: str
    timestamp: datetime
```

#### Frontend Code Style
We use TypeScript with strict mode:

```typescript
// Use proper TypeScript interfaces
interface Customer {
  phoneNumber: string;
  lastInteraction: Date;
  messageCount: number;
}

// Use React function components with proper typing
import React from 'react';

interface Props {
  customer: Customer;
  onSelect: (customer: Customer) => void;
}

const CustomerCard: React.FC<Props> = ({ customer, onSelect }) => {
  // Component implementation
};
```

### Development Tools

#### VS Code Extensions (Recommended)
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.isort",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "ms-vscode.vscode-json"
  ]
}
```

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0-alpha.4
    hooks:
      - id: prettier
        files: \.(js|jsx|ts|tsx|json|css|md)$
```

### Testing

#### Backend Testing

##### Unit Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_services.py -v

# Run with debug output
pytest tests/unit/test_services.py -v -s
```

Example unit test:
```python
# tests/unit/test_ai_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services import AIService

@pytest.mark.asyncio
async def test_ai_service_fallback_response():
    """Test AI service fallback when external APIs fail."""
    ai_service = AIService(gemini_api_key=None, openai_api_key=None)
    
    response = await ai_service.generate_response(
        "Hello", 
        context={"conversation_history": []}
    )
    
    assert "hello" in response.lower()
    assert len(response) > 0
```

##### Integration Tests
```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.server import app

client = TestClient(app)

def test_health_endpoint():
    """Test health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_admin_login():
    """Test admin login with correct password."""
    response = client.post(
        "/api/v1/auth/login",
        json={"password": "dev_admin_password_123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

#### Frontend Testing

##### Unit Tests with Vitest
```bash
cd frontend

# Run tests
yarn test

# Run with coverage
yarn test:coverage

# Run specific test
yarn test src/hooks/useAuth.test.ts
```

Example frontend test:
```typescript
// src/hooks/useAuth.test.ts
import { renderHook, act } from '@testing-library/react';
import { useAuth } from './useAuth';

describe('useAuth', () => {
  test('should login successfully with correct password', async () => {
    const { result } = renderHook(() => useAuth());
    
    await act(async () => {
      await result.current.login('dev_admin_password_123');
    });
    
    expect(result.current.isAuthenticated).toBe(true);
  });
});
```

##### End-to-End Tests with Playwright
```bash
cd frontend

# Run E2E tests
yarn test:e2e

# Run in headed mode (visible browser)
yarn test:e2e --headed

# Run specific test
npx playwright test tests/auth.spec.ts
```

### Database Development

#### Migrations
Since we use MongoDB, schema changes are handled through code. Create migration scripts for major changes:

```python
# backend/migrations/001_create_indexes.py
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate():
    """Create initial database indexes."""
    client = AsyncIOMotorClient(os.getenv("MONGO_ATLAS_URI"))
    db = client.get_default_database()
    
    # Create indexes
    await db.customers.create_index("phone_number", unique=True)
    await db.customers.create_index("created_at")
    
    print("Migration 001 completed")

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate())
```

#### Database Seeding
Create development data:

```python
# backend/scripts/seed_dev_data.py
import asyncio
from datetime import datetime
from app.services import DatabaseService

async def seed_data():
    """Seed development database with test data."""
    db_service = DatabaseService(os.getenv("MONGO_ATLAS_URI"))
    
    # Create test customers
    test_customers = [
        {
            "phone_number": "+1234567890",
            "created_at": datetime.utcnow(),
            "conversation_history": [],
            "preferences": {"language": "en"}
        }
    ]
    
    for customer in test_customers:
        await db_service.create_customer(customer)
    
    print("Development data seeded")

if __name__ == "__main__":
    asyncio.run(seed_data())
```

### API Development

#### Adding New Endpoints

1. **Define Pydantic Models**:
```python
# app/models.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CreateCustomerRequest(BaseModel):
    phone_number: str
    name: Optional[str] = None
    language: str = "en"

class CustomerResponse(BaseModel):
    phone_number: str
    name: Optional[str]
    created_at: datetime
    last_interaction: Optional[datetime]
```

2. **Implement Service Logic**:
```python
# app/services/customer_service.py
class CustomerService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def create_customer(self, customer_data: CreateCustomerRequest) -> CustomerResponse:
        """Create a new customer."""
        # Validation and business logic
        customer_doc = {
            "phone_number": customer_data.phone_number,
            "name": customer_data.name,
            "created_at": datetime.utcnow(),
            "language": customer_data.language
        }
        
        await self.db_service.create_customer(customer_doc)
        return CustomerResponse(**customer_doc)
```

3. **Create API Endpoint**:
```python
# app/server.py
@v1_router.post("/customers", response_model=CustomerResponse)
@limiter.limit("10/minute")
async def create_customer(
    request: Request,
    customer_data: CreateCustomerRequest,
    current_user: dict = Depends(verify_jwt_token)
):
    """Create a new customer."""
    try:
        customer = await services.customer_service.create_customer(customer_data)
        return customer
    except Exception as e:
        logger.error("create_customer_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create customer")
```

4. **Add Tests**:
```python
# tests/test_customers.py
def test_create_customer():
    """Test customer creation endpoint."""
    customer_data = {
        "phone_number": "+1234567890",
        "name": "Test Customer",
        "language": "en"
    }
    
    response = client.post(
        "/api/v1/customers",
        json=customer_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["phone_number"] == customer_data["phone_number"]
```

### Frontend Development

#### Component Development
Use the established patterns:

```typescript
// src/components/CustomerList.tsx
import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useCustomers } from '@/hooks/useCustomers';

interface Props {
  onSelectCustomer?: (customer: Customer) => void;
}

export const CustomerList: React.FC<Props> = ({ onSelectCustomer }) => {
  const { customers, loading, error } = useCustomers();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div className="grid gap-4">
      {customers.map((customer) => (
        <Card key={customer.phoneNumber} className="p-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-semibold">{customer.name || customer.phoneNumber}</h3>
              <p className="text-sm text-gray-500">
                Last interaction: {customer.lastInteraction?.toLocaleDateString()}
              </p>
            </div>
            {onSelectCustomer && (
              <Button onClick={() => onSelectCustomer(customer)}>
                View
              </Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
};
```

#### State Management
Use React Query for server state:

```typescript
// src/hooks/useCustomers.ts
import { useQuery } from 'react-query';
import { api } from '@/lib/api';

export const useCustomers = () => {
  return useQuery(
    'customers',
    async () => {
      const response = await api.get('/api/v1/admin/customers');
      return response.data.customers;
    },
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    }
  );
};
```

### Debugging

#### Backend Debugging

##### Using Python Debugger
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

##### VS Code Debug Configuration
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/venv/bin/uvicorn",
      "args": ["app.server:app", "--reload", "--port", "8001"],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

##### Logging Debug Info
```python
import structlog
logger = structlog.get_logger(__name__)

# Debug logging
logger.debug("processing_message", 
            phone=phone_number, 
            message_length=len(message))

# Error logging with context
logger.error("ai_service_failed", 
            error=str(e), 
            service="gemini",
            message_id=message_id)
```

#### Frontend Debugging

##### Browser Developer Tools
```typescript
// Debug API calls
console.log('API Request:', { url, data, headers });

// Debug component state
console.log('Component State:', { loading, error, data });

// Debug renders
useEffect(() => {
  console.log('Component rendered', { props, state });
});
```

##### React Developer Tools
Install React DevTools browser extension for component debugging.

### Environment Management

#### Development vs Production

Use environment-specific configurations:

```python
# backend/app/config.py
from enum import Enum
from pydantic import BaseSettings

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def log_level(self) -> str:
        return "DEBUG" if self.is_development else "INFO"
```

#### Feature Flags
```python
# backend/app/feature_flags.py
class FeatureFlags:
    def __init__(self, environment: str):
        self.environment = environment
    
    @property
    def enable_ai_fallback(self) -> bool:
        return True  # Always enabled
    
    @property
    def enable_message_queue(self) -> bool:
        return self.environment != "development"
    
    @property
    def enable_rate_limiting(self) -> bool:
        return self.environment == "production"
```

### Performance Monitoring

#### Development Profiling
```python
import cProfile
import pstats
import io

def profile_endpoint():
    """Profile an endpoint for performance."""
    pr = cProfile.Profile()
    pr.enable()
    
    # Your code here
    
    pr.disable()
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
```

#### Memory Monitoring
```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Your code here

# Get current memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
```

### Contributing Guidelines

#### Pull Request Process

1. **Create Feature Branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make Changes with Tests**:
   - Write tests for new functionality
   - Ensure all tests pass
   - Follow code style guidelines

3. **Commit Changes**:
```bash
# Use conventional commit format
git commit -m "feat: add customer search functionality"
git commit -m "fix: resolve authentication token expiry"
git commit -m "docs: update API documentation"
```

4. **Push and Create PR**:
```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

#### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact is acceptable
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate

#### Release Process

1. **Update Version**:
   - Update version in `package.json` and `pyproject.toml`
   - Update CHANGELOG.md

2. **Tag Release**:
```bash
git tag v2.1.0
git push origin v2.1.0
```

3. **Create Release Notes**:
   - Document new features
   - List bug fixes
   - Note breaking changes

### Troubleshooting Development Issues

#### Common Issues

##### Backend Issues
```bash
# Port already in use
sudo lsof -i :8001
sudo kill -9 <PID>

# Virtual environment issues
deactivate
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database connection issues
mongo $MONGO_ATLAS_URI --eval "db.adminCommand('ping')"
```

##### Frontend Issues
```bash
# Node modules issues
rm -rf node_modules package-lock.json
yarn install

# Port conflicts
lsof -ti :3000 | xargs kill -9

# TypeScript errors
yarn tsc --noEmit
```

##### Environment Issues
```bash
# Check environment variables
printenv | grep -E "(MONGO|REDIS|WHATSAPP)"

# Test external services
curl -s https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

*Happy coding! 🚀*