import os
import sys
import logging
import json
import hashlib
import uuid
import re
import asyncio
import secrets
import time
import hmac
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Annotated
from enum import Enum

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import httpx
import redis.asyncio as redis
import bcrypt
import structlog
import tenacity
from collections import defaultdict
from jose import JWTError, jwt
from fastapi import FastAPI, HTTPException, Request, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, validator, BaseSettings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import google.generativeai as genai


# Class for login attempt tracking
class LoginAttemptTracker:
    def __init__(self):
        self.attempts = defaultdict(list)
        self.lockout_duration = 900  # 15 minutes
        self.max_attempts = 5
    
    def is_locked_out(self, ip: str) -> bool:
        now = datetime.utcnow()
        # Clean old attempts
        self.attempts[ip] = [
            attempt_time for attempt_time in self.attempts[ip]
            if now - attempt_time < timedelta(seconds=self.lockout_duration)
        ]
        return len(self.attempts[ip]) >= self.max_attempts
    
    def record_attempt(self, ip: str):
        self.attempts[ip].append(datetime.utcnow())

login_tracker = LoginAttemptTracker()


# ==================== CONFIGURATION ====================
class Settings(BaseSettings):
    # Database
    mongo_uri: str = Field(..., env="MONGO_ATLAS_URI")
    
    # WhatsApp
    whatsapp_token: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_id: str = Field(..., env="WHATSAPP_PHONE_ID")
    whatsapp_verify_token: str = Field(..., env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_webhook_secret: str = Field(..., env="WHATSAPP_WEBHOOK_SECRET")
    whatsapp_catalog_id: Optional[str] = Field(None, env="WHATSAPP_CATALOG_ID")
    
    # Shopify
    shopify_store_url: str = Field(default="feelori.myshopify.com", env="SHOPIFY_STORE_URL")
    shopify_access_token: str = Field(..., env="SHOPIFY_ACCESS_TOKEN")
    
    # AI Services
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Security
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_hours: int = Field(default=24, env="JWT_ACCESS_TOKEN_EXPIRE_HOURS")
    admin_password: str = Field(..., env="ADMIN_PASSWORD")
    session_secret: str = Field(..., env="SESSION_SECRET_KEY")
    api_key: Optional[str] = Field(None, env="API_KEY")
    
    # SSL/HTTPS
    https_only: bool = Field(default=True, env="HTTPS_ONLY")
    ssl_cert_path: Optional[str] = Field(None, env="SSL_CERT_PATH")
    ssl_key_path: Optional[str] = Field(None, env="SSL_KEY_PATH")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    
    # CORS and Hosts
    cors_allowed_origins: str = Field(default="https://feelori.com", env="CORS_ALLOWED_ORIGINS")
    allowed_hosts: str = Field(default="feelori.com,*.feelori.com", env="ALLOWED_HOSTS")
    
    # Performance
    max_pool_size: int = Field(default=10, env="MONGO_MAX_POOL_SIZE")
    min_pool_size: int = Field(default=1, env="MONGO_MIN_POOL_SIZE")
    mongo_ssl: bool = Field(default=True, env="MONGO_SSL")
    
    # Monitoring
    jaeger_endpoint: Optional[str] = Field(None, env="JAEGER_ENDPOINT")
    alerting_webhook_url: Optional[str] = Field(None, env="ALERTING_WEBHOOK_URL")
    
    # API Versioning
    api_version: str = Field(default="v1", env="API_VERSION")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    auth_rate_limit_per_minute: int = Field(default=5, env="AUTH_RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_file = ".env"

def validate_environment():
    """Enhanced environment validation with security checks"""
    try:
        settings = Settings()
        
        # Security validations
        if len(settings.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        
        if len(settings.session_secret) < 32:
            raise ValueError("SESSION_SECRET_KEY must be at least 32 characters long")
        
        if len(settings.whatsapp_webhook_secret) < 16:
            raise ValueError("WHATSAPP_WEBHOOK_SECRET must be at least 16 characters long")
        
        # Add this validation
        if not settings.whatsapp_verify_token:
            raise ValueError("WHATSAPP_VERIFY_TOKEN is required")
        
        # AI service validation
        if not settings.gemini_api_key and not settings.openai_api_key:
            raise ValueError("At least one AI API key (GEMINI_API_KEY or OPENAI_API_KEY) must be provided")
        
        # Phone number validation
        if not re.match(r'^\d+$', settings.whatsapp_phone_id):
            raise ValueError("WHATSAPP_PHONE_ID must contain only digits")
        
        # Password strength validation
        if len(settings.admin_password) < 12:
            raise ValueError("ADMIN_PASSWORD must be at least 12 characters long")
        
        return settings
    except Exception as e:
        print(f"❌ Environment validation failed: {str(e)}")
        sys.exit(1)

settings = validate_environment()

# ==================== JWT SERVICE ====================
class JWTService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_access_token_expire_hours)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

jwt_service = JWTService(settings.jwt_secret_key, settings.jwt_algorithm)

# ==================== SECURITY SERVICES ====================
class SecurityService:
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify WhatsApp webhook signature"""
        if not signature or not signature.startswith('sha256='):
            return False
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        received_signature = signature[7:]  # Remove 'sha256=' prefix
        return hmac.compare_digest(expected_signature, received_signature)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Hash admin password for comparison
ADMIN_PASSWORD_HASH = SecurityService.hash_password(settings.admin_password)

# ==================== LOGGING ====================
def setup_logging():
    """Setup structured logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer() if os.getenv("ENVIRONMENT") == "development" 
            else structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

setup_logging()
logger = structlog.get_logger(__name__)

# ==================== METRICS ====================
# Business Logic Metrics
message_counter = Counter('whatsapp_messages_total', 'Total messages processed', ['status', 'message_type'])
response_time_histogram = Histogram('response_time_seconds', 'Response time in seconds', ['endpoint'])
active_customers_gauge = Gauge('active_customers', 'Number of active customers')
ai_requests_counter = Counter('ai_requests_total', 'Total AI requests', ['model', 'status'])
database_operations_counter = Counter('database_operations_total', 'Database operations', ['operation', 'status'])

# Security Metrics
auth_attempts_counter = Counter('auth_attempts_total', 'Authentication attempts', ['status', 'method'])
webhook_signature_counter = Counter('webhook_signature_verifications_total', 'Webhook signature verifications', ['status'])

# Performance Metrics
cache_operations = Counter('cache_operations_total', 'Cache operations', ['operation', 'status'])
product_searches = Counter('product_search_total', 'Product searches', ['result_count'])

# ==================== CIRCUIT BREAKER ====================
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("circuit_breaker_half_open", func=func.__name__)
                else:
                    logger.warning("circuit_breaker_blocked", func=func.__name__)
                    raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info("circuit_breaker_closed")
            else:
                self.failure_count = 0
    
    async def _on_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error("circuit_breaker_opened", failure_count=self.failure_count)

# ==================== ALERTING SERVICE ====================
class AlertingService:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=5.0) if webhook_url else None
    
    async def send_critical_alert(self, error: str, context: Dict[str, Any]):
        """Send critical alerts to external systems"""
        if not self.webhook_url or not self.client:
            logger.warning("alert_webhook_not_configured", error=error)
            return
        
        try:
            alert_data = {
                "severity": "critical",
                "service": "feelori-whatsapp-assistant",
                "error": error,
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
                "environment": os.getenv("ENVIRONMENT", "production")
            }
            
            await self.client.post(
                self.webhook_url,
                json=alert_data,
                timeout=5.0
            )
            
            logger.info("critical_alert_sent", error=error)
        except Exception as e:
            logger.error("failed_to_send_alert", error=str(e))
    
    async def cleanup(self):
        if self.client:
            await self.client.aclose()

alerting = AlertingService(settings.alerting_webhook_url)

# ==================== MODELS ====================
def validate_phone_number(phone: str) -> str:
    """Enhanced phone number validation"""
    clean_phone = re.sub(r'[^\d+]', '', phone)
    if not clean_phone.startswith('+'):
        clean_phone = '+' + clean_phone
    if not re.match(r'^\+\d{10,15}$', clean_phone):
        raise ValueError("Invalid phone number format")
    return clean_phone

class LoginRequest(BaseModel):
    password: str = Field(..., min_length=12, max_length=255)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default=settings.api_version)

class Product(BaseModel):
    id: str
    title: str
    description: str
    price: float
    currency: str = "USD"
    image_url: Optional[str] = None
    availability: str = "in_stock"

# ==================== DATABASE SERVICE ====================
class DatabaseService:
    def __init__(self, mongo_uri: str):
        self.client = AsyncIOMotorClient(
            mongo_uri,
            maxPoolSize=settings.max_pool_size,
            minPoolSize=settings.min_pool_size,
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True,
            readPreference='secondaryPreferred'
        )
        self.db = self.client.get_default_database()
        self.circuit_breaker = CircuitBreaker()
    
    async def create_indexes(self):
        """Create database indexes"""
        try:
            # Customer indexes
            await self.db.customers.create_index("phone_number", unique=True)
            await self.db.customers.create_index("created_at")
            await self.db.customers.create_index([("conversation_history.timestamp", -1)])
            
            # Security events indexes
            await self.db.security_events.create_index([("timestamp", -1), ("event_type", 1)])
            await self.db.security_events.create_index("ip_address")
            
            logger.info("database_indexes_created")
        except Exception as e:
            logger.error("failed_to_create_indexes", error=str(e))
    
    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(Exception),
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def get_customer(self, phone_number: str):
        """Get customer with retry logic"""
        return await self.circuit_breaker.call(
            self.db.customers.find_one, {"phone_number": phone_number}
        )
    
    async def create_customer(self, customer_data: dict):
        """Create new customer"""
        try:
            result = await self.circuit_breaker.call(
                self.db.customers.insert_one, customer_data
            )
            database_operations_counter.labels(operation="create_customer", status="success").inc()
            return result
        except Exception as e:
            database_operations_counter.labels(operation="create_customer", status="error").inc()
            logger.error("create_customer_error", error=str(e))
            raise
    
    async def update_conversation_history(self, phone_number: str, message: str, response: str):
        """Update customer conversation history"""
        try:
            conversation_entry = {
                "timestamp": datetime.utcnow(),
                "message": message,
                "response": response,
                "message_id": str(uuid.uuid4())
            }
            
            await self.circuit_breaker.call(
                self.db.customers.update_one,
                {"phone_number": phone_number},
                {
                    "$push": {"conversation_history": conversation_entry},
                    "$set": {"last_interaction": datetime.utcnow()}
                }
            )
            database_operations_counter.labels(operation="update_conversation", status="success").inc()
        except Exception as e:
            database_operations_counter.labels(operation="update_conversation", status="error").inc()
            logger.error("update_conversation_error", error=str(e))
    
    async def log_security_event(self, event_type: str, ip_address: str, details: dict):
        """Log security events"""
        try:
            event_data = {
                "event_type": event_type,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow(),
                "details": details
            }
            
            await self.circuit_breaker.call(
                self.db.security_events.insert_one, event_data
            )
            database_operations_counter.labels(operation="log_security", status="success").inc()
        except Exception as e:
            database_operations_counter.labels(operation="log_security", status="error").inc()
            logger.error("log_security_event_error", error=str(e))

# ==================== CACHE SERVICE ====================
class CacheService:
    def __init__(self, redis_url: str):
        self.redis_pool = redis.ConnectionPool.from_url(
            redis_url, 
            max_connections=20
        )
        self.redis = redis.Redis(connection_pool=self.redis_pool)
        self.circuit_breaker = CircuitBreaker()
    
    async def get(self, key: str) -> Optional[str]:
        try:
            result = await self.circuit_breaker.call(self.redis.get, key)
            cache_operations.labels(operation="get", status="hit" if result else "miss").inc()
            return result.decode('utf-8') if result else None
        except Exception as e:
            cache_operations.labels(operation="get", status="error").inc()
            logger.warning("cache_get_failed", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: str, ttl: int = 300):
        try:
            await self.circuit_breaker.call(self.redis.setex, key, ttl, value)
            cache_operations.labels(operation="set", status="success").inc()
        except Exception as e:
            cache_operations.labels(operation="set", status="error").inc()
            logger.warning("cache_set_failed", key=key, error=str(e))
    
    async def get_or_set(self, key: str, fetch_func, ttl: int = 300):
        """Get from cache or fetch and set"""
        cached_value = await self.get(key)
        if cached_value is not None:
            try:
                return json.loads(cached_value)
            except json.JSONDecodeError:
                return cached_value
        
        # Fetch new value
        try:
            fetched_value = await fetch_func()
            await self.set(key, json.dumps(fetched_value, default=str), ttl)
            return fetched_value
        except Exception as e:
            logger.error("cache_get_or_set_error", key=key, error=str(e))
            return None

# ==================== WHATSAPP SERVICE ====================
class WhatsAppService:
    def __init__(self, access_token: str, phone_id: str, http_client: httpx.AsyncClient):
        self.access_token = access_token
        self.phone_id = phone_id
        self.http_client = http_client
        self.base_url = "https://graph.facebook.com/v18.0"
        self.circuit_breaker = CircuitBreaker()

    async def send_message(self, to_phone: str, message: str) -> bool:
        """Send text message via WhatsApp Business API"""
        try:
            url = f"{self.base_url}/{self.phone_id}/messages"

            # Validate phone number format
            if not to_phone:
                logger.error("send_message_invalid_phone", phone=to_phone)
                return False

            # Clean phone number (remove any formatting)
            clean_phone = re.sub(r'[^\d+]', '', to_phone)
            if not clean_phone.startswith('+'):
                clean_phone = '+' + clean_phone.lstrip('+')

            # Prepare message payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone,
                "type": "text",
                "text": {
                    "body": message[:4096]  # WhatsApp message limit
                }
            }

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            # Send message through circuit breaker
            response = await self.circuit_breaker.call(
                self.http_client.post, url, json=payload, headers=headers
            )

            # Check response status
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get("messages", [{}])[0].get("id", "unknown")

                logger.info("whatsapp_message_sent",
                            to=clean_phone,
                            message_length=len(message),
                            message_id=message_id)
                return True
            else:
                # Log detailed error information
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    error_code = error_data.get("error", {}).get("code", response.status_code)
                except:
                    error_message = response.text
                    error_code = response.status_code

                logger.error("whatsapp_send_failed",
                             to=clean_phone,
                             status_code=response.status_code,
                             error_code=error_code,
                             error_message=error_message,
                             response=response.text[:500])  # Limit response log

                # Handle specific error cases
                if response.status_code == 401:
                    logger.critical("whatsapp_auth_failed", token_prefix=self.access_token[:10])
                    await alerting.send_critical_alert(
                        "WhatsApp authentication failed",
                        {"phone": clean_phone, "error": "Invalid access token"}
                    )
                elif response.status_code == 429:
                    logger.warning("whatsapp_rate_limited", to=clean_phone)
                elif response.status_code >= 500:
                    logger.error("whatsapp_server_error", status=response.status_code)

                return False

        except asyncio.TimeoutError:
            logger.error("whatsapp_send_timeout", to=to_phone)
            return False
        except httpx.RequestError as e:
            logger.error("whatsapp_request_error", to=to_phone, error=str(e))
            return False
        except Exception as e:
            logger.error("whatsapp_send_error", to=to_phone, error=str(e), error_type=type(e).__name__)

            # Send critical alert for unexpected errors
            await alerting.send_critical_alert(
                "WhatsApp send message unexpected error",
                {
                    "phone": to_phone,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return False
    async def send_interactive_list(self, to_phone: str, products: List[Product], title: str = "Products") -> bool:
        """Send interactive list message"""
        try:
            if not products:
                return False
            
            url = f"{self.base_url}/{self.phone_id}/messages"
            
            # Build interactive list (max 10 items)
            sections = [{
                "title": "Available Products",
                "rows": []
            }]
            
            for product in products[:10]:  # WhatsApp limit
                sections[0]["rows"].append({
                    "id": f"product_{product.id}",
                    "title": product.title[:24],  # WhatsApp limit
                    "description": f"${product.price:.2f}"
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_phone,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "header": {"type": "text", "text": title},
                    "body": {"text": "Choose a product to learn more:"},
                    "footer": {"text": "Feelori - Your Fashion Assistant"},
                    "action": {
                        "button": "View Products",
                        "sections": sections
                    }
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await self.circuit_breaker.call(
                self.http_client.post, url, json=payload, headers=headers
            )
            
            success = response.status_code == 200
            if success:
                logger.info("whatsapp_interactive_sent", to=to_phone, products_count=len(products))
            else:
                logger.error("whatsapp_interactive_failed", 
                           to=to_phone, 
                           status_code=response.status_code)
            
            return success
            
        except Exception as e:
            logger.error("whatsapp_interactive_error", to=to_phone, error=str(e))
            return False

# ==================== AI SERVICE ====================
class AIService:
    def __init__(self, openai_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        self.gemini_client = None
        self.circuit_breaker = CircuitBreaker()
        
        # Initialize Gemini with new SDK
        if gemini_api_key:
            try:
                genai.configure(api_key=gemini_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("gemini_initialized_new_sdk")
            except Exception as e:
                logger.error("gemini_init_failed", error=str(e))
    
    async def generate_response(self, message: str, context: Dict = None) -> str:
        """Generate AI response using available models"""
        try:
            # Try OpenAI first if available
            if self.openai_client:
                return await self._generate_openai_response(message, context)
            
            # Try Gemini if available
            elif self.gemini_client:
                return await self._generate_gemini_response(message, context)
            
            # Fallback to basic rule-based response
            return self._generate_fallback_response(message, context)
            
        except Exception as e:
            logger.error("ai_generate_response_error", error=str(e))
            ai_requests_counter.labels(model="error", status="error").inc()
            return "I apologize, but I'm having trouble generating a response right now. How can I help you with our products?"
    
    async def _generate_gemini_response(self, message: str, context: Dict = None) -> str:
        """Generate response using Gemini with new SDK"""
        try:
            system_prompt = """You are Feelori's AI shopping assistant. You help customers find fashion products, answer questions about orders, and provide excellent customer service.

Key guidelines:
- Be friendly, helpful, and concise
- Focus on fashion and product recommendations
- If asked about orders, guide them to contact support
- Always try to help customers find what they're looking for
- Keep responses under 160 characters when possible for WhatsApp
- Use emojis sparingly but appropriately"""

            user_message = message
            if context:
                customer_history = context.get('conversation_history', [])
                if customer_history:
                    recent_history = customer_history[-3:]  # Last 3 exchanges
                    history_text = "\n".join([f"Customer: {h.get('message', '')}\nAssistant: {h.get('response', '')}" for h in recent_history])
                    user_message = f"Recent conversation:\n{history_text}\n\nCurrent message: {message}"
            
            full_prompt = f"{system_prompt}\n\nCustomer message: {user_message}"
            
            # Use the native async method for the Gemini call
            response = await self.gemini_client.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=150,
                    temperature=0.7,
                )
            )
            
            if response.text:
                ai_response = response.text.strip()
                ai_requests_counter.labels(model="gemini", status="success").inc()
                
                logger.info("gemini_response_generated", 
                           message_length=len(message),
                           response_length=len(ai_response))
                
                return ai_response
            else:
                raise Exception("Empty response from Gemini")
            
        except Exception as e:
            logger.error("gemini_response_error", error=str(e))
            ai_requests_counter.labels(model="gemini", status="error").inc()
            raise
    
    def _generate_fallback_response(self, message: str, context: Dict = None) -> str:
        """Generate rule-based fallback response"""
        message_lower = message.lower()
        
        # Greeting responses
        if any(word in message_lower for word in ["hello", "hi", "hey", "start"]):
            return "Hello! Welcome to Feelori! 👋 I'm here to help you find amazing fashion products. What are you looking for today?"
        
        # Product search responses
        if any(word in message_lower for word in ["product", "show", "looking", "find", "buy", "shop"]):
            return "I'd love to help you find the perfect products! Let me show you our latest collection. What style are you interested in?"
        
        # Order inquiry responses
        if any(word in message_lower for word in ["order", "delivery", "shipping", "track"]):
            return "For order inquiries, please contact our support team at support@feelori.com or call us. They'll help you track your order! 📦"
        
        # Support responses
        if any(word in message_lower for word in ["help", "support", "problem", "issue"]):
            return "I'm here to help! You can browse our products, or contact support@feelori.com for detailed assistance. What can I help you with? 🛍️"
        
        # Thank you responses
        if any(word in message_lower for word in ["thank", "thanks"]):
            return "You're very welcome! Happy to help with anything else you need. Feel free to ask about our products anytime! ✨"
        
        # Default response
        return "Thanks for your message! I'm here to help you discover amazing fashion products. Would you like to see our latest collection or are you looking for something specific?"

# ==================== MESSAGE QUEUE ====================
class MessageQueue:
    def __init__(self, max_workers: int = 5):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers
        self.workers = []
        self.running = False
    
    async def start_workers(self):
        """Start message processing workers"""
        self.running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        logger.info("message_queue_workers_started", count=self.max_workers)
    
    async def stop_workers(self):
        """Stop message processing workers"""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("message_queue_workers_stopped")
    
    async def _worker(self, name: str):
        """Message processing worker"""
        while self.running:
            try:
                # Wait for message with timeout
                message_data = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                await self._process_message(message_data)
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("worker_error", worker=name, error=str(e))
    
    async def _process_message(self, message_data: Dict):
        """Process individual message"""
        try:
            from_number = message_data["from_number"]
            message_text = message_data["message_text"]
            message_type = message_data.get("message_type", "text")
            
            # Process the message
            response = await process_message(from_number, message_text, message_type)
            
            # Send response if generated
            if response:
                success = await services.whatsapp_service.send_message(from_number, response)
                if success:
                    message_counter.labels(status="success", message_type=message_type).inc()
                else:
                    message_counter.labels(status="send_failed", message_type=message_type).inc()
            
        except Exception as e:
            logger.error("message_processing_error", error=str(e))
            message_counter.labels(status="error", message_type="processing_error").inc()
    
    async def add_message(self, message_data: Dict):
        """Add message to processing queue"""
        await self.queue.put(message_data)

# ==================== SERVICE CONTAINER ====================
class ServiceContainer:
    def __init__(self):
        self.db_service = None
        self.cache_service = None
        self.whatsapp_service = None
        self.shopify_service = None
        self.ai_service = None
        self.message_queue = None
        self.http_client = None
    
    async def initialize(self):
        """Initialize all services"""
        try:
            # HTTP Client
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
            timeout = httpx.Timeout(30.0, connect=10.0)
            
            self.http_client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                verify=True
            )
            
            # Database Service
            self.db_service = DatabaseService(settings.mongo_uri)
            await self.db_service.create_indexes()
            
            # Cache Service
            self.cache_service = CacheService(settings.redis_url)
            
            # WhatsApp Service
            self.whatsapp_service = WhatsAppService(
                settings.whatsapp_token,
                settings.whatsapp_phone_id,
                self.http_client
            )
            
            # Shopify Service
            self.shopify_service = ShopifyService(
                settings.shopify_store_url,
                settings.shopify_access_token,
                self.http_client
            )
            
            # AI Service
            self.ai_service = AIService(
                settings.openai_api_key,
                settings.gemini_api_key
            )
            
            # Message Queue
            self.message_queue = MessageQueue(max_workers=5)
            await self.message_queue.start_workers()
            
            logger.info("all_services_initialized")
            
        except Exception as e:
            logger.error("service_initialization_failed", error=str(e))
            await alerting.send_critical_alert("Service initialization failed", {"error": str(e)})
            raise
    
    async def cleanup(self):
        """Cleanup all services"""
        try:
            if self.message_queue:
                await self.message_queue.stop_workers()
            
            if self.http_client:
                await self.http_client.aclose()
            
            if self.cache_service:
                await self.cache_service.redis.close()
            
            await alerting.cleanup()
            
            logger.info("all_services_cleaned_up")
            
        except Exception as e:
            logger.error("service_cleanup_error", error=str(e))

services = ServiceContainer()

# ==================== MESSAGE PROCESSING ====================
async def process_message(phone_number: str, message: str, message_type: str = "text") -> str:
    """Main message processing function"""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("process_message") as span:
        try:
            span.set_attribute("message.phone", phone_number)
            span.set_attribute("message.length", len(message))
            span.set_attribute("message.type", message_type)
            
            # Get or create customer
            customer = await get_or_create_customer(phone_number)
            
            # Analyze message intent
            intent = analyze_intent(message.lower(), message_type)
            span.set_attribute("message.intent", intent)
            
            # Route to appropriate handler
            response = await route_message(intent, phone_number, message, customer)
            
            # Update conversation history (async)
            asyncio.create_task(
                services.db_service.update_conversation_history(phone_number, message, response)
            )
            
            return response
            
        except Exception as e:
            logger.error("message_processing_error", 
                        phone=phone_number, 
                        error=str(e))
            await alerting.send_critical_alert(
                "Message processing failed",
                {"phone": phone_number, "error": str(e)}
            )
            return "I'm sorry, I'm experiencing technical difficulties. Please try again or contact support@feelori.com"

async def get_or_create_customer(phone_number: str) -> Dict:
    """Get or create customer with caching"""
    try:
        clean_phone = validate_phone_number(phone_number)
        cache_key = f"customer:{clean_phone}"
        
        async def fetch_customer():
            # Try database first
            customer_data = await services.db_service.get_customer(clean_phone)
            if customer_data:
                return customer_data
            
            # Create new customer
            new_customer = {
                "id": str(uuid.uuid4()),
                "phone_number": clean_phone,
                "created_at": datetime.utcnow(),
                "conversation_history": [],
                "preferences": {},
                "last_interaction": datetime.utcnow()
            }
            
            await services.db_service.create_customer(new_customer)
            active_customers_gauge.inc()
            
            return new_customer
        
        customer = await services.cache_service.get_or_set(
            cache_key, fetch_customer, ttl=600
        )
        
        return customer
        
    except Exception as e:
        logger.error("get_or_create_customer_error", phone=phone_number, error=str(e))
        # Return minimal customer for fallback
        return {
            "id": str(uuid.uuid4()),
            "phone_number": phone_number,
            "created_at": datetime.utcnow(),
            "conversation_history": []
        }

def analyze_intent(message_lower: str, message_type: str) -> str:
    """Analyze message intent"""
    # Interactive messages
    if message_lower.startswith(("product_", "buy_", "details_")):
        return "product_interaction"
    
    if message_type == "interactive":
        return "interactive_response"
    
    # Greetings
    if any(word in message_lower for word in ["hello", "hi", "hey", "start", "begin"]):
        return "greeting"
    
    # Product search
    if any(word in message_lower for word in ["product", "show", "looking", "find", "buy", "shop", "browse"]):
        return "product_search"
    
    # Order inquiry
    if any(word in message_lower for word in ["order", "delivery", "shipping", "track", "status"]):
        return "order_inquiry"
    
    # Support
    if any(word in message_lower for word in ["help", "support", "problem", "issue", "complaint"]):
        return "support"
    
    return "general_chat"

async def route_message(intent: str, phone_number: str, message: str, customer: Dict) -> str:
    """Route message based on intent"""
    handlers = {
        "product_interaction": handle_product_interaction,
        "greeting": handle_greeting,
        "product_search": handle_product_search,
        "order_inquiry": handle_order_inquiry,
        "support": handle_support,
        "general_chat": handle_general_chat
    }
    
    handler = handlers.get(intent, handle_general_chat)
    return await handler(phone_number, message, customer)

# ==================== MESSAGE HANDLERS ====================
async def handle_product_interaction(phone_number: str, message: str, customer: Dict) -> str:
    """Handle product-specific interactions"""
    try:
        if message.startswith("product_"):
            product_id = message.split("_", 1)[1]
            return await show_product_details(phone_number, product_id)
        
        return "I didn't understand that selection. Please try choosing from the menu again!"
        
    except Exception as e:
        logger.error("product_interaction_error", error=str(e))
        return "Sorry, I had trouble with that selection. Please try again!"

async def handle_greeting(phone_number: str, message: str, customer: Dict) -> str:
    """Handle greeting messages"""
    try:
        # Check if returning customer
        is_returning = len(customer.get("conversation_history", [])) > 0
        greeting = "Welcome back to Feelori! 👋" if is_returning else "Welcome to Feelori! 👋"
        
        # Get featured products
        products = await get_featured_products()
        
        if products:
            # Try to send interactive list
            success = await services.whatsapp_service.send_interactive_list(
                phone_number, products, "Featured Products"
            )
            
            if success:
                return f"{greeting} Check out our featured products above! What catches your eye?"
            else:
                # Fallback to text list
                product_list = "\n".join([f"• {p.title} - ${p.price:.2f}" for p in products[:5]])
                return f"{greeting} Here are some featured products:\n\n{product_list}\n\nWhat would you like to know more about?"
        
        return f"{greeting} I'm here to help you find amazing fashion products! What are you looking for today?"
        
    except Exception as e:
        logger.error("greeting_handler_error", error=str(e))
        return "Welcome to Feelori! 👋 How can I help you today?"

async def handle_product_search(phone_number: str, message: str, customer: Dict) -> str:
    """Handle product search requests"""
    try:
        # Extract search query
        query = extract_search_query(message)
        
        # Search products
        products = await search_products(query)
        
        if not products:
            # Use AI to generate helpful response
            ai_response = await services.ai_service.generate_response(
                f"Customer is looking for: {message}. No products found. Be helpful and suggest alternatives."
            )
            return ai_response
        
        # Try interactive list first
        success = await services.whatsapp_service.send_interactive_list(
            phone_number, products, f"Search Results: {query}"
        )
        
        if success:
            return f"Found {len(products)} products for '{query}'! Click on any item to learn more."
        
        # Fallback to text
        product_list = "\n".join([f"• {p.title} - ${p.price:.2f}" for p in products[:5]])
        return f"Found {len(products)} products for '{query}':\n\n{product_list}\n\nWould you like details on any of these?"
        
    except Exception as e:
        logger.error("product_search_error", error=str(e))
        return "I'd love to help you find products! Could you tell me more about what you're looking for?"

async def handle_order_inquiry(phone_number: str, message: str, customer: Dict) -> str:
    """Handle order-related inquiries"""
    try:
        # Search for orders
        orders = await services.shopify_service.search_orders_by_phone(phone_number)
        
        if not orders:
            return "I couldn't find any orders associated with this number. For order support, please contact us at support@feelori.com or provide your order number. 📦"
        
        # Format order summary
        recent_orders = orders[:3]  # Show last 3 orders
        order_summary = []
        
        for order in recent_orders:
            order_number = order.get("order_number", order.get("id", "Unknown"))
            status = order.get("fulfillment_status", "pending").title()
            total = order.get("total_price", "0")
            created = order.get("created_at", "")[:10]  # Date only
            
            order_summary.append(f"Order #{order_number}: {status} - ${total} ({created})")
        
        summary_text = "\n".join(order_summary)
        
        return f"Here are your recent orders:\n\n{summary_text}\n\nFor detailed tracking, contact support@feelori.com with your order number! 📦"
        
    except Exception as e:
        logger.error("order_inquiry_error", error=str(e))
        return "For order inquiries, please contact support@feelori.com or call our customer service. They'll help you track your order! 📦"

async def handle_support(phone_number: str, message: str, customer: Dict) -> str:
    """Handle support requests"""
    return """I'm here to help! For detailed support:

📧 Email: support@feelori.com
📞 Call: Available on our website
💬 Chat: I can help with product questions

What specific issue can I assist you with?"""

async def handle_general_chat(phone_number: str, message: str, customer: Dict) -> str:
    """Handle general chat with AI"""
    try:
        # Use AI service for natural conversation
        context = {
            "conversation_history": customer.get("conversation_history", [])[-5:],  # Last 5 exchanges
            "customer_phone": phone_number
        }
        
        response = await services.ai_service.generate_response(message, context)
        return response
        
    except Exception as e:
        logger.error("general_chat_error", error=str(e))
        return "Thanks for your message! I'm here to help you find amazing products. What can I show you today?"

# ==================== HELPER FUNCTIONS ====================
async def get_featured_products() -> List[Product]:
    """Get featured products with caching"""
    cache_key = "featured_products"
    
    async def fetch_products():
        return await services.shopify_service.get_products(limit=8)
    
    try:
        products = await services.cache_service.get_or_set(
            cache_key, fetch_products, ttl=1800  # 30 minutes
        )
        return products or []
    except Exception as e:
        logger.error("get_featured_products_error", error=str(e))
        return []

async def search_products(query: str) -> List[Product]:
    """Search products with caching"""
    cache_key = f"search:{query.lower()[:50]}"
    
    async def fetch_search_results():
        return await services.shopify_service.get_products(query=query, limit=10)
    
    try:
        products = await services.cache_service.get_or_set(
            cache_key, fetch_search_results, ttl=900  # 15 minutes
        )
        
        # Track search metrics
        result_count = "many" if len(products) > 5 else str(len(products))
        product_searches.labels(result_count=result_count).inc()
        
        return products or []
    except Exception as e:
        logger.error("search_products_error", error=str(e))
        return []

async def show_product_details(phone_number: str, product_id: str) -> str:
    """Show detailed product information"""
    try:
        product = await services.shopify_service.get_product_by_id(product_id)
        
        if not product:
            return "Sorry, I couldn't find that product. Would you like to see our latest collection instead?"
        
        details = f"""✨ *{product.title}*

💰 Price: ${product.price:.2f}
📦 Availability: {product.availability.replace('_', ' ').title()}

{product.description[:200]}{'...' if len(product.description) > 200 else ''}

Would you like to know more or see similar products?"""
        
        return details
        
    except Exception as e:
        logger.error("show_product_details_error", error=str(e))
        return "Sorry, I couldn't load that product's details. Please try again or browse our collection!"

def extract_search_query(message: str) -> str:
    """Extract search query from message"""
    # Remove common words
    stop_words = {"looking", "for", "find", "show", "me", "want", "need", "buy", "product", "products"}
    
    words = message.lower().split()
    query_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return " ".join(query_words[:3])  # Max 3 words for search

# ==================== AUTHENTICATION ====================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/{settings.api_version}/auth/login")
security = HTTPBearer()
async def verify_jwt_token(token: str = Depends(oauth2_scheme)) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt_service.verify_token(token)
        auth_attempts_counter.labels(status="success", method="jwt").inc()
        return payload
    except HTTPException as e:
        auth_attempts_counter.labels(status="failure", method="jwt").inc()
        raise e

# ==================== RATE LIMITING ====================
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url
)

# ==================== TRACING SETUP ====================
if settings.jaeger_endpoint:
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

# ==================== FASTAPI APPLICATION ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("application_starting", version="2.0.0")
    
    try:
        await services.initialize()
        logger.info("application_ready")
        yield
    except Exception as e:
        logger.error("application_startup_failed", error=str(e))
        await alerting.send_critical_alert("Application startup failed", {"error": str(e)})
        raise
    finally:
        logger.info("application_shutting_down")
        await services.cleanup()

app = FastAPI(
    title="Feelori AI WhatsApp Assistant",
    version="2.0.0",
    description="Production-ready AI WhatsApp assistant with enterprise features",
    lifespan=lifespan,
    openapi_url=f"/api/{settings.api_version}/openapi.json",
    docs_url=f"/api/{settings.api_version}/docs",
    redoc_url=f"/api/{settings.api_version}/redoc",
)

# ==================== MIDDLEWARE ====================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Add other middleware
allowed_hosts = [host.strip() for host in settings.allowed_hosts.split(",") if host.strip()]
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    max_age=3600,
    same_site="strict",
    https_only=settings.https_only
)

cors_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# ==================== API ROUTES ====================
from fastapi import APIRouter

v1_router = APIRouter(prefix=f"/api/{settings.api_version}", tags=[f"{settings.api_version}"])

@v1_router.post("/auth/login", response_model=TokenResponse)
@limiter.limit(f"{settings.auth_rate_limit_per_minute}/minute")
async def login(request: Request, login_data: LoginRequest):
    """JWT-based authentication with enhanced security"""
    client_ip = get_remote_address(request)
    
    try:
        # Check if IP is locked out
        if login_tracker.is_locked_out(client_ip):
            logger.warning("login_attempt_lockout", ip=client_ip)
            auth_attempts_counter.labels(status="lockout", method="password").inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )
        
        if not SecurityService.verify_password(login_data.password, ADMIN_PASSWORD_HASH):
            # Record failed attempt
            login_tracker.record_attempt(client_ip)
            
            logger.warning("login_attempt_failed", ip=client_ip)
            auth_attempts_counter.labels(status="failure", method="password").inc()
            
            await services.db_service.log_security_event(
                "failed_login", client_ip, {"reason": "invalid_password"}
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create JWT token
        access_token = jwt_service.create_access_token(
            data={"sub": "admin", "type": "access", "ip": client_ip}
        )
        
        logger.info("login_successful", ip=client_ip)
        auth_attempts_counter.labels(status="success", method="password").inc()
        
        await services.db_service.log_security_event(
            "successful_login", client_ip, {"method": "jwt"}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_hours * 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", error=str(e), ip=client_ip)
        await alerting.send_critical_alert("Login system error", {"error": str(e)})
        raise HTTPException(status_code=500, detail="Authentication system error")


@v1_router.get("/webhook")
@limiter.limit("60/minute")
async def verify_webhook(request: Request):
    """WhatsApp webhook verification"""
    with response_time_histogram.labels(endpoint="webhook_verify").time():
        try:
            mode = request.query_params.get("hub.mode")
            token = request.query_params.get("hub.verify_token")
            challenge = request.query_params.get("hub.challenge")
            
            client_ip = get_remote_address(request)
            logger.info("webhook_verification_attempt", 
                       mode=mode, 
                       token=token[:10] + "..." if token else None,
                       ip=client_ip)
            
            if mode == "subscribe" and token == settings.whatsapp_verify_token:
                logger.info("webhook_verification_successful", ip=client_ip)
                return PlainTextResponse(challenge)
            else:
                logger.warning("webhook_verification_failed", 
                             mode=mode, ip=client_ip)
                raise HTTPException(status_code=403, detail="Verification failed")
                
        except Exception as e:
            logger.error("webhook_verification_error", error=str(e))
            raise HTTPException(status_code=500, detail="Verification error")
    
    

# ==================== SHOPIFY SERVICE ====================
class ShopifyService:
    def __init__(self, store_url: str, access_token: str, http_client: httpx.AsyncClient):
        self.store_url = store_url.replace('https://', '').replace('http://', '')
        self.access_token = access_token
        self.http_client = http_client
        self.base_url = f"https://{self.store_url}/admin/api/2023-10"
        self.circuit_breaker = CircuitBreaker()
    
    async def get_products(self, query: str = "", limit: int = 10) -> List[Product]:
        """Get products from Shopify"""
        try:
            url = f"{self.base_url}/products.json"
            params = {
                "limit": min(limit, 50),
                "status": "active"
            }
            
            if query:
                params["title"] = query
            
            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }
            
            response = await self.circuit_breaker.call(
                self.http_client.get, url, params=params, headers=headers
            )
            
            if response.status_code != 200:
                logger.error("shopify_products_failed", 
                           status_code=response.status_code,
                           response=response.text)
                return []
            
            data = response.json()
            products = []
            
            for item in data.get("products", []):
                # Get first variant for pricing
                variants = item.get("variants", [])
                if not variants:
                    continue
                
                first_variant = variants[0]
                
                # Get first image
                images = item.get("images", [])
                image_url = images[0]["src"] if images else None
                
                product = Product(
                    id=str(item["id"]),
                    title=item["title"],
                    description=item.get("body_html", "")[:200] + "..." if item.get("body_html", "") else "",
                    price=float(first_variant.get("price", 0)),
                    currency="USD",
                    image_url=image_url,
                    availability="in_stock" if int(first_variant.get("inventory_quantity", 0)) > 0 else "out_of_stock"
                )
                
                products.append(product)
            
            logger.info("shopify_products_fetched", count=len(products), query=query)
            return products
            
        except Exception as e:
            logger.error("shopify_products_error", error=str(e), query=query)
            return []
    
    async def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Get single product by ID"""
        try:
            url = f"{self.base_url}/products/{product_id}.json"
            
            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }
            
            response = await self.circuit_breaker.call(
                self.http_client.get, url, headers=headers
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            item = data.get("product", {})
            
            if not item:
                return None
            
            variants = item.get("variants", [])
            if not variants:
                return None
            
            first_variant = variants[0]
            images = item.get("images", [])
            image_url = images[0]["src"] if images else None
            
            return Product(
                id=str(item["id"]),
                title=item["title"],
                description=item.get("body_html", "")[:500] + "..." if item.get("body_html", "") else "",
                price=float(first_variant.get("price", 0)),
                currency="USD",
                image_url=image_url,
                availability="in_stock" if int(first_variant.get("inventory_quantity", 0)) > 0 else "out_of_stock"
            )
            
        except Exception as e:
            logger.error("shopify_product_by_id_error", error=str(e), product_id=product_id)
            return None
    
    async def search_orders_by_phone(self, phone_number: str) -> List[Dict]:
        """Search orders by phone number"""
        try:
            url = f"{self.base_url}/orders.json"
            params = {
                "status": "any",
                "limit": 50
            }
            
            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }
            
            response = await self.circuit_breaker.call(
                self.http_client.get, url, params=params, headers=headers
            )
            
            if response.status_code != 200:
                logger.error("shopify_orders_failed", 
                           status_code=response.status_code)
                return []
            
            data = response.json()
            orders = []
            
            # Filter orders by phone number
            clean_phone = validate_phone_number(phone_number)
            for order in data.get("orders", []):
                # Check billing and shipping phone
                billing_phone = order.get("billing_address", {}).get("phone", "")
                shipping_phone = order.get("shipping_address", {}).get("phone", "")
                
                if billing_phone:
                    try:
                        if validate_phone_number(billing_phone) == clean_phone:
                            orders.append(order)
                            continue
                    except:
                        pass
                
                if shipping_phone:
                    try:
                        if validate_phone_number(shipping_phone) == clean_phone:
                            orders.append(order)
                    except:
                        pass
            
            logger.info("shopify_orders_found", phone=phone_number, count=len(orders))
            return orders
            
        except Exception as e:
            logger.error("shopify_orders_error", error=str(e), phone=phone_number)
            return []

# ==================== WEBHOOK HANDLER ====================
@v1_router.post("/webhook")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def handle_webhook(request: Request):
    """Handle WhatsApp webhook messages"""
    with response_time_histogram.labels(endpoint="webhook_handler").time():
        try:
            # Get raw body for signature verification
            body = await request.body()
            signature = request.headers.get("x-hub-signature-256", "")
            
            # Verify webhook signature
            if not SecurityService.verify_webhook_signature(
                body, signature, settings.whatsapp_webhook_secret
            ):
                webhook_signature_counter.labels(status="invalid").inc()
                logger.warning("webhook_signature_invalid", 
                             signature=signature[:20] + "...",
                             ip=get_remote_address(request))
                
                await services.db_service.log_security_event(
                    "invalid_webhook_signature",
                    get_remote_address(request),
                    {"signature": signature[:50]}
                )
                
                raise HTTPException(status_code=403, detail="Invalid signature")
            
            webhook_signature_counter.labels(status="valid").inc()
            
            # Parse webhook data
            try:
                data = await request.json()
            except Exception:
                logger.error("webhook_json_parse_error", body=body[:200])
                return JSONResponse({"status": "error", "message": "Invalid JSON"})
            
            # Process webhook entries
            entries = data.get("entry", [])
            
            for entry in entries:
                changes = entry.get("changes", [])
                
                for change in changes:
                    if change.get("field") != "messages":
                        continue
                    
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    # Process each message
                    for message in messages:
                        await process_webhook_message(message, value)
            
            return JSONResponse({"status": "success"})
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("webhook_handler_error", error=str(e))
            await alerting.send_critical_alert(
                "Webhook handler error", 
                {"error": str(e), "ip": get_remote_address(request)}
            )
            return JSONResponse({"status": "error"}, status_code=500)

async def process_webhook_message(message: Dict, webhook_data: Dict):
    """Process individual webhook message"""
    try:
        message_id = message.get("id")
        from_number = message.get("from")
        timestamp = message.get("timestamp")
        
        # Skip if no sender
        if not from_number:
            return
        
        # Get message content based on type
        message_type = message.get("type", "text")
        message_text = ""
        
        if message_type == "text":
            message_text = message.get("text", {}).get("body", "")
        elif message_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "list_reply":
                message_text = interactive.get("list_reply", {}).get("id", "")
            elif interactive.get("type") == "button_reply":
                message_text = interactive.get("button_reply", {}).get("id", "")
        elif message_type in ["image", "document", "audio", "video"]:
            message_text = f"[{message_type.upper()}] received"
        else:
            logger.info("unsupported_message_type", type=message_type)
            return
        
        # Add to processing queue
        await services.message_queue.add_message({
            "message_id": message_id,
            "from_number": from_number,
            "message_text": message_text,
            "message_type": message_type,
            "timestamp": timestamp
        })
        
        logger.info("message_queued", 
                   from_number=from_number,
                   message_type=message_type,
                   message_id=message_id)
        
    except Exception as e:
        logger.error("process_webhook_message_error", error=str(e), message=message)

# ==================== ADMIN ENDPOINTS ====================
@v1_router.get("/admin/stats")
@limiter.limit("10/minute")
async def get_admin_stats(request: Request, current_user: dict = Depends(verify_jwt_token)):
    """Get system statistics (admin only)"""
    try:
        # Database stats
        db_stats = {
            "total_customers": await services.db_service.db.customers.count_documents({}),
            "active_today": await services.db_service.db.customers.count_documents({
                "last_interaction": {"$gte": datetime.utcnow() - timedelta(days=1)}
            }),
            "total_conversations": await services.db_service.db.customers.aggregate([
                {"$group": {"_id": None, "total": {"$sum": {"$size": "$conversation_history"}}}}
            ]).to_list(1)
        }
        
        if db_stats["total_conversations"]:
            db_stats["total_conversations"] = db_stats["total_conversations"][0]["total"]
        else:
            db_stats["total_conversations"] = 0
        
        # System stats
        system_stats = {
            "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0,
            "queue_size": services.message_queue.queue.qsize(),
            "cache_status": "connected" if await services.cache_service.redis.ping() else "disconnected"
        }
        
        return APIResponse(
            success=True,
            message="Statistics retrieved",
            data={
                "database": db_stats,
                "system": system_stats,
                "timestamp": datetime.utcnow()
            }
        )
        
    except Exception as e:
        logger.error("admin_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@v1_router.get("/admin/customers")
@limiter.limit("10/minute")
async def get_customers(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(verify_jwt_token)  # Changed from token_data
):
    """Get customer list (admin only)"""
    try:
        cursor = services.db_service.db.customers.find(
            {},
            {"conversation_history": {"$slice": -5}}  # Only last 5 messages
        ).skip(skip).limit(min(limit, 100)).sort("last_interaction", -1)
        
        customers = await cursor.to_list(length=limit)
        total_count = await services.db_service.db.customers.count_documents({})
        
        # Sanitize customer data
        for customer in customers:
            customer["_id"] = str(customer["_id"])
            # Mask phone number for privacy
            phone = customer.get("phone_number", "")
            if len(phone) > 4:
                customer["phone_number"] = phone[:3] + "*" * (len(phone) - 6) + phone[-3:]
        
        return APIResponse(
            success=True,
            message=f"Found {len(customers)} customers",
            data={
                "customers": customers,
                "total_count": total_count,
                "skip": skip,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error("get_customers_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve customers")

# ==================== HEALTH CHECKS ====================
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0",
        "checks": {}
    }
    
    try:
        # Check database
        await services.db_service.db.command("ping")
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    try:
        # Check cache
        await services.cache_service.redis.ping()
        health_status["checks"]["cache"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["cache"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    try:
        # Check message queue
        queue_size = services.message_queue.queue.qsize()
        health_status["checks"]["message_queue"] = {
            "status": "healthy" if queue_size < 1000 else "warning",
            "queue_size": queue_size
        }
    except Exception as e:
        health_status["checks"]["message_queue"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Set overall status
    unhealthy_checks = [check for check in health_status["checks"].values() 
                       if check["status"] == "unhealthy"]
    
    if unhealthy_checks:
        health_status["status"] = "unhealthy"
    
    return health_status

# ==================== METRICS ENDPOINT ====================
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain"
    )

# ==================== ERROR HANDLERS ====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning("http_exception", 
                  status_code=exc.status_code,
                  detail=exc.detail,
                  path=request.url.path)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error("unhandled_exception", 
                error=str(exc),
                path=request.url.path,
                method=request.method)
    
    await alerting.send_critical_alert(
        "Unhandled exception",
        {
            "error": str(exc),
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ==================== INCLUDE ROUTERS ====================
app.include_router(v1_router)

# ==================== STARTUP EVENT ====================
@app.on_event("startup")
async def startup_event():
    """Record application start time"""
    app.state.start_time = time.time()
    logger.info("application_startup_complete", timestamp=datetime.utcnow())

# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    import uvicorn
    
    # SSL configuration
    ssl_keyfile = settings.ssl_key_path
    ssl_certfile = settings.ssl_cert_path
    
    if settings.https_only and ssl_keyfile and ssl_certfile:
        logger.info("starting_https_server", port=8000)
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            reload=False,
            workers=1,
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["default"],
                },
            }
        )
    else:
        logger.info("starting_http_server", port=8000)
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            workers=1
        )