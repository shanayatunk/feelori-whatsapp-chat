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
import redis as redis_package
from collections import defaultdict
from jose import JWTError, jwt
from fastapi import FastAPI, HTTPException, Request, Depends, Security, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator # Note: 'validator' is now 'field_validator'
from pydantic_settings import BaseSettings
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
    
    # Production settings
    workers: int = Field(default=4, env="UVICORN_WORKERS")
    worker_class: str = Field(default="uvicorn.workers.UvicornWorker", env="WORKER_CLASS")
    
    # Sentry configuration
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    sentry_environment: str = Field(default="production", env="SENTRY_ENVIRONMENT")
    
    # Alerting
    alerting_webhook_url: Optional[str] = Field(None, env="ALERTING_WEBHOOK_URL")

    # Enhanced Jaeger configuration
    jaeger_agent_host: str = Field(default="localhost", env="JAEGER_AGENT_HOST")
    jaeger_agent_port: int = Field(default=6831, env="JAEGER_AGENT_PORT")
    
    # Environment
    environment: str = Field(default="production", env="ENVIRONMENT")
    
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

# Enhanced Security Service
class EnhancedSecurityService(SecurityService):
    @staticmethod
    def sanitize_phone_number(phone: str) -> str:
        """Enhanced phone number sanitization"""
        if not phone or len(phone) > 20:
            raise ValueError("Invalid phone number length")
        
        # Remove all non-digit characters except +
        clean_phone = re.sub(r'[^\d+]', '', phone.strip())
        
        # Ensure it starts with +
        if not clean_phone.startswith('+'):
            clean_phone = '+' + clean_phone.lstrip('+')
        
        # Validate format
        if not re.match(r'^\+\d{10,15}$', clean_phone):
            raise ValueError("Invalid phone number format")
        
        return clean_phone
    
    @staticmethod
    def validate_message_content(message: str) -> str:
        """Validate and sanitize message content"""
        if not isinstance(message, str):
            raise ValueError("Message must be a string")
        
        # Length validation
        if len(message) > 4096:  # WhatsApp limit
            raise ValueError("Message too long")
        
        if len(message.strip()) == 0:
            raise ValueError("Message cannot be empty")
        
        # Basic content filtering (expand as needed)
        suspicious_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
        ]
        
        message_lower = message.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.warning("suspicious_message_content", 
                             pattern=pattern, 
                             message_preview=message[:100])
                raise ValueError("Suspicious message content detected")
        
        return message.strip()
    
    @staticmethod
    def validate_admin_session(request: Request, payload: dict):
        """Validate admin session security"""
        # IP binding validation
        token_ip = payload.get("ip")
        current_ip = get_remote_address(request)
        
        if token_ip and token_ip != current_ip:
            logger.warning("ip_mismatch_detected", 
                         token_ip=token_ip, 
                         current_ip=current_ip)
            raise HTTPException(
                status_code=401,
                detail="Token IP mismatch - please login again"
            )
        
        # Token age validation (additional security)
        issued_at = payload.get("iat")
        if issued_at:
            token_age = datetime.utcnow().timestamp() - issued_at
            max_age = settings.jwt_access_token_expire_hours * 3600
            
            if token_age > max_age:
                raise HTTPException(
                    status_code=401,
                    detail="Token expired"
                )

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

# ==================== SENTRY INITIALIZATION ====================
def initialize_sentry():
    """Initialize Sentry for error tracking"""
    if settings.sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.httpx import HttpxIntegration
            from sentry_sdk.integrations.redis import RedisIntegration
            from sentry_sdk.integrations.pymongo import PyMongoIntegration
            
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.sentry_environment,
                traces_sample_rate=0.1,  # Adjust based on traffic
                profiles_sample_rate=0.1,  # Adjust based on traffic
                integrations=[
                    FastApiIntegration(auto_enabling_integrations=False),
                    HttpxIntegration(),
                    RedisIntegration(),
                    PyMongoIntegration(),
                ],
                before_send=lambda event, hint: event if event.get("level") != "info" else None,
                attach_stacktrace=True,
                send_default_pii=False,  # Important for privacy
            )
            logger.info("sentry_initialized", environment=settings.sentry_environment)
            return True
        except Exception as e:
            logger.error("sentry_initialization_failed", error=str(e))
            return False
    return False

# ==================== TRACING SETUP ====================
def setup_tracing():
    """Setup OpenTelemetry tracing with configurable Jaeger"""
    if settings.jaeger_agent_host:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            
            trace.set_tracer_provider(TracerProvider())
            
            jaeger_exporter = JaegerExporter(
                agent_host_name=settings.jaeger_agent_host,
                agent_port=settings.jaeger_agent_port,
            )
            
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            logger.info("tracing_initialized", 
                       jaeger_host=settings.jaeger_agent_host,
                       jaeger_port=settings.jaeger_agent_port)
            return True
        except Exception as e:
            logger.error("tracing_initialization_failed", error=str(e))
            return False
    return False

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

# ==================== REDIS CIRCUIT BREAKER ====================
class RedisCircuitBreaker:
    """Redis-backed circuit breaker for multi-worker environments"""
    
    def __init__(self, redis_client, service_name: str, failure_threshold: int = 5, 
                 timeout: int = 60, success_threshold: int = 3):
        self.redis = redis_client
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.failure_key = f"cb_failures:{service_name}"
        self.success_key = f"cb_success:{service_name}"
        self.state_key = f"cb_state:{service_name}"
        self.last_failure_key = f"cb_last_failure:{service_name}"
    
    async def call(self, func, *args, **kwargs):
        state = await self._get_state()
        
        if state == "OPEN":
            last_failure = await self.redis.get(self.last_failure_key)
            if last_failure and time.time() - float(last_failure) > self.timeout:
                await self._set_state("HALF_OPEN")
                await self.redis.delete(self.success_key)
                logger.info("circuit_breaker_half_open", service=self.service_name)
            else:
                logger.warning("circuit_breaker_blocked", service=self.service_name)
                raise Exception(f"Circuit breaker is OPEN for {self.service_name}")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _get_state(self) -> str:
        state = await self.redis.get(self.state_key)
        return state.decode() if state else "CLOSED"
    
    async def _set_state(self, state: str):
        await self.redis.set(self.state_key, state, ex=self.timeout * 2)
    
    async def _on_success(self):
        state = await self._get_state()
        
        if state == "HALF_OPEN":
            success_count = await self.redis.incr(self.success_key)
            if success_count >= self.success_threshold:
                await self._set_state("CLOSED")
                await self.redis.delete(self.failure_key)
                await self.redis.delete(self.success_key)
                logger.info("circuit_breaker_closed", service=self.service_name)
        else:
            await self.redis.delete(self.failure_key)
    
    async def _on_failure(self):
        failure_count = await self.redis.incr(self.failure_key)
        await self.redis.set(self.last_failure_key, str(time.time()), ex=self.timeout * 2)
        
        if failure_count >= self.failure_threshold:
            await self._set_state("OPEN")
            logger.error("circuit_breaker_opened", 
                        service=self.service_name, 
                        failure_count=failure_count)

# ==================== REDIS LOGIN ATTEMPT TRACKER ====================
class RedisLoginAttemptTracker:
    """Redis-backed login attempt tracker for multi-worker environments"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.lockout_duration = 900  # 15 minutes
        self.max_attempts = 5
    
    async def is_locked_out(self, ip: str) -> bool:
        key = f"login_attempts:{ip}"
        attempts = await self.redis.lrange(key, 0, -1)
        
        # Clean old attempts and count recent ones
        now = time.time()
        recent_attempts = []
        
        for attempt in attempts:
            attempt_time = float(attempt.decode())
            if now - attempt_time < self.lockout_duration:
                recent_attempts.append(attempt_time)
        
        # Update Redis with only recent attempts
        if len(recent_attempts) != len(attempts):
            await self.redis.delete(key)
            if recent_attempts:
                await self.redis.lpush(key, *recent_attempts)
                await self.redis.expire(key, self.lockout_duration)
        
        return len(recent_attempts) >= self.max_attempts
    
    async def record_attempt(self, ip: str):
        key = f"login_attempts:{ip}"
        await self.redis.lpush(key, str(time.time()))
        await self.redis.expire(key, self.lockout_duration)

# ==================== RATE LIMITING ====================
class AdvancedRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_phone_rate_limit(self, phone_number: str, 
                                   limit: int = 10, window: int = 60) -> bool:
        """Rate limit per phone number"""
        key = f"rate_limit:phone:{phone_number}"
        
        try:
            # Sliding window rate limiting
            now = time.time()
            pipeline = self.redis.pipeline()
            
            # Remove old entries
            pipeline.zremrangebyscore(key, 0, now - window)
            
            # Count current requests in window
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(uuid.uuid4()): now})
            
            # Set expiry
            pipeline.expire(key, window)
            
            results = await pipeline.execute()
            current_count = results[1]
            
            if current_count >= limit:
                logger.warning("phone_rate_limit_exceeded", 
                             phone=phone_number, 
                             count=current_count, 
                             limit=limit)
                return False
            
            return True
            
        except Exception as e:
            logger.error("rate_limit_check_error", error=str(e))
            return True  # Allow on error (fail open)
    
    async def check_ip_rate_limit(self, ip_address: str, 
                                limit: int = 50, window: int = 60) -> bool:
        """Rate limit per IP address"""
        key = f"rate_limit:ip:{ip_address}"
        
        try:
            current_count = await self.redis.incr(key)
            if current_count == 1:
                await self.redis.expire(key, window)
            
            if current_count > limit:
                logger.warning("ip_rate_limit_exceeded", 
                             ip=ip_address, 
                             count=current_count, 
                             limit=limit)
                return False
            
            return True
            
        except Exception as e:
            logger.error("ip_rate_limit_check_error", error=str(e))
            return True  # Allow on error

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


# ==================== REDIS MESSAGE QUEUE ====================
class RedisMessageQueue:
    """Redis-backed message queue using Redis Streams"""

    def __init__(self, redis_client, stream_name: str = "webhook_messages", max_workers: int = 5):
        self.redis = redis_client
        self.stream_name = stream_name
        self.consumer_group = "webhook_processors"
        self.max_workers = max_workers
        self.workers = []
        self.running = False

    async def initialize(self):
        """Create consumer group if it doesn't exist"""
        try:
            await self.redis.xgroup_create(self.stream_name, self.consumer_group, id="0", mkstream=True)
        except redis_package.exceptions.ResponseError as e:
            # This is the corrected exception handling
            if "BUSYGROUP Consumer Group name already exists" in str(e):
                # Group already exists, which is perfectly fine.
                logger.info("redis_consumer_group_exists", group=self.consumer_group)
                pass
            else:
                # Re-raise any other Redis errors
                logger.error("redis_group_create_failed", error=str(e))
                raise

    async def start_workers(self):
        """Start message processing workers"""
        await self.initialize()
        self.running = True
        
        for i in range(self.max_workers):
            consumer_name = f"worker-{i}-{uuid.uuid4().hex[:8]}"
            worker = asyncio.create_task(self._worker(consumer_name))
            self.workers.append(worker)
        
        logger.info("redis_message_queue_workers_started", count=self.max_workers)

    async def stop_workers(self):
        """Stop message processing workers"""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("redis_message_queue_workers_stopped")

    async def _worker(self, consumer_name: str):
        """Message processing worker using Redis Streams with self-healing for NOGROUP error."""
        while self.running:
            try:
                messages = await self.redis.xreadgroup(
                    self.consumer_group,
                    consumer_name,
                    {self.stream_name: ">"},
                    count=1,
                    block=1000
                )
                
                if messages:
                    stream_messages = messages[0][1]
                    for message_id, fields in stream_messages:
                        try:
                            message_data = {k.decode(): v.decode() for k, v in fields.items()}
                            message_data = json.loads(message_data.get('data', '{}'))
                            await self._process_message(message_data)
                            await self.redis.xack(self.stream_name, self.consumer_group, message_id)
                        except Exception as e:
                            logger.error("redis_worker_message_error", worker=consumer_name, message_id=message_id.decode(), error=str(e))
            
            except redis_package.exceptions.ResponseError as e:
                if "NOGROUP" in str(e):
                    logger.warning("redis_worker_nogroup_error", detail="Stream/group not found, attempting to re-create...")
                    try:
                        await self.initialize()
                        await asyncio.sleep(1)
                    except Exception as init_e:
                        logger.error("redis_worker_init_failed", error=str(init_e))
                        await asyncio.sleep(5)
                else:
                    logger.error("redis_worker_response_error", worker=consumer_name, error=str(e))
                    await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.running:
                    logger.error("redis_worker_error", worker=consumer_name, error=str(e))
                    await asyncio.sleep(5)

    async def _process_message(self, message_data: Dict):
        """Process individual message"""
        try:
            from_number = message_data["from_number"]
            message_text = message_data["message_text"]
            message_type = message_data.get("message_type", "text")
            
            response = await process_message(from_number, message_text, message_type)
            
            if response:
                success = await services.whatsapp_service.send_message(from_number, response)
                if success:
                    message_counter.labels(status="success", message_type=message_type).inc()
                else:
                    message_counter.labels(status="send_failed", message_type=message_type).inc()
        
        except Exception as e:
            logger.error("redis_message_processing_error", error=str(e))
            message_counter.labels(status="error", message_type="processing_error").inc()

    async def add_message(self, message_data: Dict):
        """Add message to Redis stream"""
        try:
            await self.redis.xadd(
                self.stream_name,
                {"data": json.dumps(message_data, default=str)},
                maxlen=10000
            )
        except Exception as e:
            logger.error("redis_add_message_error", error=str(e))

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
    
    async def _generate_openai_response(self, message: str, context: Dict = None) -> str:
        """Generate response using OpenAI"""
        try:
            system_prompt = """You are Feelori's AI shopping assistant. You help customers find fashion products, answer questions about orders, and provide excellent customer service.

Key guidelines:
- Be friendly, helpful, and concise
- Focus on fashion and product recommendations
- If asked about orders, guide them to contact support
- Always try to help customers find what they're looking for
- Keep responses under 160 characters when possible for WhatsApp
- Use emojis sparingly but appropriately"""

            messages = [{"role": "system", "content": system_prompt}]
            
            if context and context.get('conversation_history'):
                # Add recent conversation history
                recent_history = context['conversation_history'][-3:]
                for exchange in recent_history:
                    messages.append({"role": "user", "content": exchange.get('message', '')})
                    messages.append({"role": "assistant", "content": exchange.get('response', '')})
            
            messages.append({"role": "user", "content": message})
            
            response = await self.circuit_breaker.call(
                self.openai_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            ai_requests_counter.labels(model="openai", status="success").inc()
            
            logger.info("openai_response_generated", 
                       message_length=len(message),
                       response_length=len(ai_response))
            
            return ai_response
            
        except Exception as e:
            logger.error("openai_response_error", error=str(e))
            ai_requests_counter.labels(model="openai", status="error").inc()
            raise
    
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
        self.login_tracker = None
        self.rate_limiter = None
    
    async def initialize(self):
        """Initialize all services with Redis-backed components"""
        try:
            # HTTP Client with enhanced configuration
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50,
                keepalive_expiry=30.0
            )
            timeout = httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=10.0,
                pool=5.0
            )
            
            self.http_client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                verify=True,
                http2=True
            )
            
            # Enhanced Cache Service
            self.cache_service = CacheService(settings.redis_url)
            
            # Advanced Rate Limiter
            self.rate_limiter = AdvancedRateLimiter(self.cache_service.redis)
            
            # Redis-backed login tracker
            self.login_tracker = RedisLoginAttemptTracker(self.cache_service.redis)
            
            # Database Service with Redis circuit breaker
            self.db_service = DatabaseService(settings.mongo_uri)
            self.db_service.circuit_breaker = RedisCircuitBreaker(
                self.cache_service.redis, "database"
            )
            await self.db_service.create_indexes()
            
            # WhatsApp Service with Redis circuit breaker
            self.whatsapp_service = WhatsAppService(
                settings.whatsapp_token,
                settings.whatsapp_phone_id,
                self.http_client
            )
            self.whatsapp_service.circuit_breaker = RedisCircuitBreaker(
                self.cache_service.redis, "whatsapp"
            )
            
            # Shopify Service with Redis circuit breaker
            self.shopify_service = ShopifyService(
                settings.shopify_store_url,
                settings.shopify_access_token,
                self.http_client
            )
            self.shopify_service.circuit_breaker = RedisCircuitBreaker(
                self.cache_service.redis, "shopify"
            )
            
            # AI Service
            self.ai_service = AIService(
                settings.openai_api_key,
                settings.gemini_api_key
            )
            
            # Redis Message Queue
            self.message_queue = RedisMessageQueue(
                self.cache_service.redis, 
                "webhook_messages", 
                max_workers=int(os.getenv("MESSAGE_QUEUE_WORKERS", "5"))
            )
            await self.message_queue.start_workers()
            
            logger.info("all_services_initialized_with_redis_backing")
            
        except Exception as e:
            logger.error("service_initialization_failed", error=str(e))
            await alerting.send_critical_alert("Service initialization failed", {"error": str(e)})
            raise
    
    async def cleanup(self):
        """Cleanup all services"""
        try:
            # Stop message queue workers
            if self.message_queue:
                await self.message_queue.stop_workers()
            
            # Close HTTP client
            if self.http_client:
                await self.http_client.aclose()
            
            # Close Redis connections
            if self.cache_service:
                await self.cache_service.redis.close()
            
            # Close database connections
            if self.db_service:
                self.db_service.client.close()
            
            # Cleanup alerting
            await alerting.cleanup()
            
            logger.info("services_cleaned_up_successfully")
            
        except Exception as e:
            logger.error("service_cleanup_error", error=str(e))

# ==================== GLOBAL SERVICES ====================
services = ServiceContainer()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)

# OAuth2 scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/{settings.api_version}/auth/login")

# ==================== APPLICATION LIFECYCLE ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("application_starting", 
               version="2.0.0",
               environment=settings.environment)
    
    # Initialize monitoring
    sentry_enabled = initialize_sentry()
    tracing_enabled = setup_tracing()
    
    try:
        await services.initialize()
        logger.info("application_ready", 
                   sentry_enabled=sentry_enabled,
                   tracing_enabled=tracing_enabled)
        yield
    except Exception as e:
        logger.error("application_startup_failed", error=str(e))
        await alerting.send_critical_alert("Application startup failed", {"error": str(e)})
        raise
    finally:
        logger.info("application_shutting_down")
        await services.cleanup()

# ==================== FASTAPI APPLICATION ====================
app = FastAPI(
    title="Feelori AI WhatsApp Assistant",
    version="2.0.0",
    description="Production-ready AI WhatsApp assistant with enterprise features",
    lifespan=lifespan,
    openapi_url=f"/api/{settings.api_version}/openapi.json" if settings.environment != "production" else None,
    docs_url=f"/api/{settings.api_version}/docs" if settings.environment != "production" else None,
    redoc_url=f"/api/{settings.api_version}/redoc" if settings.environment != "production" else None,
)

# ==================== MIDDLEWARE SETUP ====================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'",
        "X-Robots-Tag": "noindex, nofollow",
        "Server": "Feelori-API"
    })
    return response

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info("request_processed",
               method=request.method,
               path=request.url.path,
               status_code=response.status_code,
               process_time=process_time,
               user_agent=request.headers.get("user-agent", ""),
               remote_addr=get_remote_address(request))
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# CORS middleware
cors_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# Other middleware
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
    https_only=settings.https_only,
    session_cookie="feelori_session"
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==================== AUTHENTICATION DEPENDENCIES ====================
async def verify_jwt_token(token: str = Depends(oauth2_scheme)) -> dict:
    """Verify JWT token with enhanced security"""
    try:
        payload = jwt_service.verify_token(token)
        
        # Verify admin role
        if payload.get("sub") != "admin":
            auth_attempts_counter.labels(status="unauthorized", method="jwt").inc()
            logger.warning("unauthorized_access_attempt", 
                         user=payload.get("sub"), 
                         token_type=payload.get("type"))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized for this resource"
            )
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type"
            )
        
        auth_attempts_counter.labels(status="success", method="jwt").inc()
        return payload
    except HTTPException:
        raise
    except JWTError as e:
        auth_attempts_counter.labels(status="failure", method="jwt").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def verify_webhook_signature(request: Request):
    """Webhook signature verification dependency"""
    try:
        body = await request.body()
        signature = request.headers.get("x-hub-signature-256", "")
        
        if not EnhancedSecurityService.verify_webhook_signature(
            body, signature, settings.whatsapp_webhook_secret
        ):
            webhook_signature_counter.labels(status="invalid").inc()
            
            await services.db_service.log_security_event(
                "invalid_webhook_signature",
                get_remote_address(request),
                {
                    "signature": signature[:50],
                    "body_length": len(body),
                    "user_agent": request.headers.get("user-agent", "")
                }
            )
            
            logger.warning("webhook_signature_invalid",
                         signature_prefix=signature[:20],
                         ip=get_remote_address(request))
            
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        webhook_signature_counter.labels(status="valid").inc()
        request.state.verified_body = body
        return body
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("webhook_signature_verification_error", error=str(e))
        raise HTTPException(status_code=500, detail="Signature verification failed")

async def verify_metrics_access(request: Request):
    """Optional API key protection for metrics endpoint"""
    if settings.api_key:
        auth_header = request.headers.get("authorization", "")
        api_key = request.headers.get("x-api-key", "")
        
        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:]
        elif api_key:
            provided_key = api_key
        else:
            raise HTTPException(
                status_code=401, 
                detail="API key required for metrics access"
            )
        
        if not secrets.compare_digest(provided_key, settings.api_key):
            logger.warning("invalid_metrics_access_attempt", 
                         ip=get_remote_address(request))
            raise HTTPException(status_code=403, detail="Invalid API key")
    
    return True

# ==================== ROUTERS ====================
v1_router = APIRouter(prefix=f"/api/{settings.api_version}")

# ==================== MESSAGE PROCESSING ====================
async def process_message(phone_number: str, message: str, message_type: str = "text") -> str:
    """Enhanced message processing with better error handling"""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("process_message") as span:
        try:
            span.set_attribute("message.phone", phone_number)
            span.set_attribute("message.length", len(message))
            span.set_attribute("message.type", message_type)
            
            # Validate inputs
            clean_phone = EnhancedSecurityService.sanitize_phone_number(phone_number)
            clean_message = EnhancedSecurityService.validate_message_content(message)
            
            # Get or create customer with caching
            customer = await get_or_create_customer(clean_phone)
            
            # Analyze message intent
            intent = await analyze_intent(clean_message.lower(), message_type, customer)
            span.set_attribute("message.intent", intent)
            
            # Route to appropriate handler
            response = await route_message(intent, clean_phone, clean_message, customer)
            
            # Validate response
            if not response or len(response.strip()) == 0:
                response = "I'm here to help! What can I assist you with today?"
            
            # Update conversation history (fire and forget)
            asyncio.create_task(
                update_conversation_history_safe(clean_phone, clean_message, response)
            )
            
            # Update metrics
            message_counter.labels(status="processed", message_type=message_type).inc()
            
            return response[:4096]  # Ensure WhatsApp limit
            
        except ValueError as e:
            logger.warning("message_validation_error", 
                         phone=phone_number, 
                         error=str(e))
            return "I'm sorry, but I couldn't process your message. Please try again with a different format."
        
        except Exception as e:
            logger.error("message_processing_error", 
                        phone=phone_number, 
                        error=str(e),
                        error_type=type(e).__name__)
            
            await alerting.send_critical_alert(
                "Message processing failed",
                {
                    "phone": phone_number,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            message_counter.labels(status="error", message_type=message_type).inc()
            return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment or contact support@feelori.com"

async def get_or_create_customer(phone_number: str) -> Dict:
    """Enhanced customer management with better caching"""
    try:
        cache_key = f"customer:v2:{phone_number}"
        
        # Try cache first
        cached_customer = await services.cache_service.get(cache_key)
        if cached_customer:
            return json.loads(cached_customer)
        
        # Fetch from database
        customer_data = await services.db_service.get_customer(phone_number)
        
        if customer_data:
            # Convert ObjectId to string for JSON serialization
            customer_data["_id"] = str(customer_data["_id"])
            
            # Cache customer data
            await services.cache_service.set(cache_key, json.dumps(customer_data, default=str), ttl=1800)
            return customer_data
        
        # Create new customer
        new_customer = {
            "id": str(uuid.uuid4()),
            "phone_number": phone_number,
            "created_at": datetime.utcnow(),
            "conversation_history": [],
            "preferences": {},
            "last_interaction": datetime.utcnow(),
            "total_messages": 0,
            "favorite_categories": []
        }
        
        await services.db_service.create_customer(new_customer)
        
        # Cache new customer
        await services.cache_service.set(cache_key, json.dumps(new_customer, default=str), ttl=1800)
        
        active_customers_gauge.inc()
        return new_customer
        
    except Exception as e:
        logger.error("get_or_create_customer_error", 
                   phone=phone_number, 
                   error=str(e))
        
        # Return minimal customer for fallback
        return {
            "id": str(uuid.uuid4()),
            "phone_number": phone_number,
            "created_at": datetime.utcnow(),
            "conversation_history": [],
            "preferences": {},
            "last_interaction": datetime.utcnow()
        }

async def analyze_intent(message: str, message_type: str, customer: Dict) -> str:
    """Analyze message intent for routing"""
    message_lower = message.lower()
    
    # Interactive button/list responses
    if message_type == "interactive":
        if message.startswith("product_"):
            return "product_detail"
        elif "order" in message:
            return "order_inquiry"
        elif "support" in message:
            return "support"
        return "interactive_response"
    
    # Greeting patterns
    if any(word in message_lower for word in ["hello", "hi", "hey", "start", "good morning", "good afternoon"]):
        return "greeting"
    
    # Product search patterns
    if any(word in message_lower for word in ["product", "show", "looking", "find", "buy", "shop", "dress", "shirt", "pants", "shoes", "fashion"]):
        return "product_search"
    
    # Order inquiry patterns
    if any(word in message_lower for word in ["order", "delivery", "shipping", "track", "status", "when", "receipt"]):
        return "order_inquiry"
    
    # Support patterns
    if any(word in message_lower for word in ["help", "support", "problem", "issue", "complaint", "refund", "return"]):
        return "support"
    
    # Thank you patterns
    if any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
        return "thank_you"
    
    # Size/fit inquiries
    if any(word in message_lower for word in ["size", "fit", "fitting", "measurement", "small", "medium", "large"]):
        return "size_inquiry"
    
    # Price inquiries
    if any(word in message_lower for word in ["price", "cost", "cheap", "expensive", "discount", "sale"]):
        return "price_inquiry"
    
    return "general"

async def route_message(intent: str, phone_number: str, message: str, customer: Dict) -> str:
    """Route message to appropriate handler based on intent"""
    try:
        if intent == "greeting":
            return await handle_greeting(phone_number, customer)
        elif intent == "product_search":
            return await handle_product_search(message, customer)
        elif intent == "product_detail":
            return await handle_product_detail(message, customer)
        elif intent == "order_inquiry":
            return await handle_order_inquiry(phone_number, customer)
        elif intent == "support":
            return await handle_support_request(message, customer)
        elif intent == "thank_you":
            return await handle_thank_you(customer)
        elif intent == "size_inquiry":
            return await handle_size_inquiry(message, customer)
        elif intent == "price_inquiry":
            return await handle_price_inquiry(message, customer)
        else:
            return await handle_general_inquiry(message, customer)
            
    except Exception as e:
        logger.error("route_message_error", intent=intent, error=str(e))
        return "I'm here to help! Let me connect you with our support team or show you our latest products."

async def handle_greeting(phone_number: str, customer: Dict) -> str:
    """Handle greeting messages"""
    # Check if returning customer
    conversation_count = len(customer.get("conversation_history", []))
    
    if conversation_count > 5:
        return f"Welcome back! 👋 I'm here to help you find amazing fashion products. What are you looking for today?"
    else:
        return f"Hello! Welcome to Feelori! 👋 I'm your AI shopping assistant. I can help you discover our latest fashion collection, answer questions about products, or assist with orders. What would you like to explore today?"

async def handle_product_search(message: str, customer: Dict) -> str:
    """Handle product search requests"""
    try:
        # Extract search terms from message
        search_terms = extract_search_terms(message)
        
        # Get products from Shopify
        products = await services.shopify_service.get_products(query=search_terms, limit=5)
        
        if products:
            # Send interactive list if multiple products
            if len(products) > 1:
                success = await services.whatsapp_service.send_interactive_list(
                    customer["phone_number"], 
                    products, 
                    f"Found {len(products)} products for '{search_terms}'"
                )
                
                if success:
                    product_searches.labels(result_count=str(len(products))).inc()
                    return f"Here are {len(products)} products I found for '{search_terms}'. Tap to view details! ✨"
            
            # Single product response
            product = products[0]
            response = f"Found this perfect match! 🎯\n\n"
            response += f"**{product.title}**\n"
            response += f"💰 ${product.price:.2f}\n"
            response += f"📝 {product.description[:100]}...\n\n"
            response += f"Would you like more details or see similar items?"
            
            product_searches.labels(result_count="1").inc()
            return response
        else:
            product_searches.labels(result_count="0").inc()
            return f"I couldn't find products matching '{search_terms}' right now. Let me show you our popular items instead! Would you like to see our latest arrivals or bestsellers?"
            
    except Exception as e:
        logger.error("handle_product_search_error", error=str(e))
        return "I'm having trouble searching products right now. Let me connect you with our support team who can help you find exactly what you're looking for!"

async def handle_product_detail(message: str, customer: Dict) -> str:
    """Handle product detail requests"""
    try:
        # Extract product ID from interactive response
        product_id = message.replace("product_", "")
        
        # Get product details
        product = await services.shopify_service.get_product_by_id(product_id)
        
        if product:
            response = f"**{product.title}** ✨\n\n"
            response += f"💰 Price: ${product.price:.2f}\n"
            response += f"📦 Status: {product.availability.replace('_', ' ').title()}\n\n"
            response += f"📝 Description:\n{product.description[:300]}...\n\n"
            response += f"Would you like to:\n"
            response += f"• See size guide 📏\n"
            response += f"• View similar items 👗\n"
            response += f"• Get styling tips 💡\n"
            response += f"• Contact support for purchase 🛒"
            
            return response
        else:
            return "Sorry, I couldn't find details for that product. Let me show you some similar items instead!"
            
    except Exception as e:
        logger.error("handle_product_detail_error", error=str(e))
        return "I'm having trouble getting product details. Please try again or contact our support team!"

async def handle_order_inquiry(phone_number: str, customer: Dict) -> str:
    """Handle order inquiry requests"""
    try:
        # Search for orders by phone number
        orders = await services.shopify_service.search_orders_by_phone(phone_number)
        
        if orders:
            recent_orders = orders[:3]  # Show last 3 orders
            response = f"Found {len(orders)} order(s) for your number! 📦\n\n"
            
            for i, order in enumerate(recent_orders, 1):
                order_date = order.get("created_at", "")[:10]  # Get date part
                order_status = order.get("fulfillment_status", "pending")
                total_price = order.get("total_price", "0.00")
                
                response += f"**Order #{i}** (#{order.get('order_number', 'N/A')})\n"
                response += f"📅 Date: {order_date}\n"
                response += f"💰 Total: ${total_price}\n"
                response += f"📋 Status: {order_status.replace('_', ' ').title()}\n\n"
            
            response += f"For detailed tracking or support, please contact us at support@feelori.com with your order number."
            return response
        else:
            return "I couldn't find any recent orders for your phone number. If you've placed an order, please contact support@feelori.com with your order details for assistance! 📞"
            
    except Exception as e:
        logger.error("handle_order_inquiry_error", error=str(e))
        return "I'm having trouble accessing order information right now. Please contact support@feelori.com or call us for order assistance! 📞"

async def handle_support_request(message: str, customer: Dict) -> str:
    """Handle support requests"""
    return (
        "I'm here to help! 🤗 For detailed assistance, you can:\n\n"
        "📧 Email: support@feelori.com\n"
        "📞 Call: [Your phone number]\n"
        "💬 Live Chat: [Your website]\n\n"
        "Or let me know what specific help you need - I might be able to assist with:\n"
        "• Product information 🛍️\n"
        "• Size guidance 📏\n"
        "• Order questions 📦\n"
        "• Style recommendations ✨"
    )

async def handle_thank_you(customer: Dict) -> str:
    """Handle thank you messages"""
    responses = [
        "You're very welcome! Happy to help anytime! ✨",
        "My pleasure! Feel free to ask if you need anything else! 🛍️",
        "Glad I could help! Enjoy shopping with Feelori! 💖",
        "You're welcome! I'm always here for your fashion needs! 👗"
    ]
    return responses[hash(customer["phone_number"]) % len(responses)]

async def handle_size_inquiry(message: str, customer: Dict) -> str:
    """Handle size and fit inquiries"""
    return (
        "Great question about sizing! 📏\n\n"
        "For the best fit, I recommend:\n\n"
        "📐 **Size Guide**: Check our detailed size charts on each product page\n"
        "📏 **Measurements**: Bust, waist, and hip measurements are key\n"
        "👗 **Fit Notes**: Each item has specific fit information\n"
        "💡 **Tip**: When in doubt, size up for comfort!\n\n"
        "Need help with a specific item? Send me the product name and I can provide detailed sizing info! ✨"
    )

async def handle_price_inquiry(message: str, customer: Dict) -> str:
    """Handle price and discount inquiries"""
    return (
        "Looking for great deals? 💰 Here's what I can help with:\n\n"
        "🏷️ **Current Offers**: Check our latest promotions\n"
        "📬 **Newsletter**: Subscribe for exclusive discounts\n"
        "🛒 **Sale Section**: Browse discounted items\n"
        "💳 **First Order**: Special discount for new customers\n\n"
        "Would you like me to show you our current sale items or help you find products in a specific price range? ✨"
    )

async def handle_general_inquiry(message: str, customer: Dict) -> str:
    """Handle general inquiries with AI"""
    try:
        # Use AI service for general responses
        context = {
            "conversation_history": customer.get("conversation_history", [])[-5:],  # Last 5 exchanges
            "customer_preferences": customer.get("preferences", {}),
            "total_messages": len(customer.get("conversation_history", []))
        }
        
        ai_response = await services.ai_service.generate_response(message, context)
        return ai_response
        
    except Exception as e:
        logger.error("handle_general_inquiry_error", error=str(e))
        return "Thanks for your message! I'm here to help you discover amazing fashion products. Would you like to see our latest collection or are you looking for something specific? 🛍️"

def extract_search_terms(message: str) -> str:
    """Extract search terms from user message"""
    # Remove common words and extract product-related terms
    stop_words = {"i", "want", "looking", "for", "find", "show", "me", "can", "you", "please", "help", "need", "buy", "get"}
    words = message.lower().split()
    search_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # If no meaningful words found, return original message
    if not search_words:
        return message
    
    return " ".join(search_words[:3])  # Limit to 3 words for better search

async def update_conversation_history_safe(phone_number: str, message: str, response: str):
    """Safely update conversation history with error handling"""
    try:
        await services.db_service.update_conversation_history(phone_number, message, response)
        
        # Invalidate customer cache
        cache_key = f"customer:v2:{phone_number}"
        await services.cache_service.redis.delete(cache_key)
        
    except Exception as e:
        logger.error("conversation_history_update_error", 
                   phone=phone_number, 
                   error=str(e))
        # Don't raise - conversation history is not critical for user experience

# ==================== WEBHOOK ENDPOINTS ====================
@v1_router.get("/webhook")
async def verify_webhook(hub_mode: str = None, hub_verify_token: str = None, hub_challenge: str = None):
    """WhatsApp webhook verification"""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("webhook_verified_successfully")
        return PlainTextResponse(hub_challenge)
    
    logger.warning("webhook_verification_failed", 
                  mode=hub_mode, 
                  token=hub_verify_token[:10] if hub_verify_token else None)
    
    raise HTTPException(status_code=403, detail="Forbidden")

@v1_router.post("/webhook")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def handle_webhook(
    request: Request,
    verified_body: bytes = Depends(verify_webhook_signature)
):
    """Enhanced webhook handler with signature verification"""
    with response_time_histogram.labels(endpoint="webhook_handler").time():
        try:
            # Parse webhook data from verified body
            try:
                data = json.loads(verified_body.decode())
            except Exception:
                logger.error("webhook_json_parse_error", 
                           body_preview=verified_body[:200])
                return JSONResponse(
                    {"status": "error", "message": "Invalid JSON"}, 
                    status_code=400
                )
            
            client_ip = get_remote_address(request)
            
            # Check IP rate limit
            if not await services.rate_limiter.check_ip_rate_limit(client_ip, limit=100, window=60):
                return JSONResponse(
                    {"status": "rate_limited", "message": "Too many requests"}, 
                    status_code=429
                )
            
            # Process webhook entries
            entries = data.get("entry", [])
            processed_messages = 0
            
            for entry in entries:
                changes = entry.get("changes", [])
                
                for change in changes:
                    if change.get("field") != "messages":
                        continue
                    
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    # Process each message with additional validation
                    for message in messages:
                        try:
                            phone_number = message.get("from")
                            if not phone_number:
                                continue
                            
                            # Sanitize phone number
                            clean_phone = EnhancedSecurityService.sanitize_phone_number(phone_number)
                            
                            # Check per-phone rate limit
                            if not await services.rate_limiter.check_phone_rate_limit(clean_phone):
                                logger.warning("phone_rate_limited", phone=clean_phone)
                                continue
                            
                            # Process message with enhanced validation
                            await process_webhook_message_enhanced(message, value)
                            processed_messages += 1
                            
                        except ValueError as e:
                            logger.warning("message_validation_failed", 
                                         error=str(e), 
                                         message_id=message.get("id"))
                            continue
                        except Exception as e:
                            logger.error("message_processing_error", 
                                       error=str(e), 
                                       message_id=message.get("id"))
                            continue
            
            logger.info("webhook_processed", 
                       total_messages=processed_messages,
                       client_ip=client_ip)
            
            return JSONResponse({
                "status": "success", 
                "processed": processed_messages
            })
            
        except Exception as e:
            logger.error("webhook_handler_error", error=str(e))
            await alerting.send_critical_alert(
                "Webhook handler error", 
                {"error": str(e), "ip": get_remote_address(request)}
            )
            return JSONResponse({"status": "error"}, status_code=500)

async def process_webhook_message_enhanced(message: Dict, webhook_data: Dict):
    """Enhanced webhook message processing with validation"""
    try:
        message_id = message.get("id")
        from_number = message.get("from")
        timestamp = message.get("timestamp")
        
        # Enhanced validation
        if not all([message_id, from_number, timestamp]):
            logger.warning("incomplete_webhook_message", message_id=message_id)
            return
        
        # Sanitize phone number
        clean_phone = EnhancedSecurityService.sanitize_phone_number(from_number)
        
        # Get message content based on type
        message_type = message.get("type", "text")
        message_text = ""
        
        if message_type == "text":
            raw_text = message.get("text", {}).get("body", "")
            message_text = EnhancedSecurityService.validate_message_content(raw_text)
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
        
        # Add to processing queue with enhanced data
        await services.message_queue.add_message({
            "message_id": message_id,
            "from_number": clean_phone,
            "original_number": from_number,  # Keep original for reference
            "message_text": message_text,
            "message_type": message_type,
            "timestamp": timestamp,
            "webhook_timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("message_queued_enhanced", 
                   from_number=clean_phone,
                   message_type=message_type,
                   message_id=message_id,
                   text_length=len(message_text))
        
    except ValueError as e:
        logger.warning("message_validation_error", 
                     error=str(e), 
                     message_id=message.get("id"))
    except Exception as e:
        logger.error("process_webhook_message_enhanced_error", 
                   error=str(e), 
                   message=message)

# ==================== AUTHENTICATION ENDPOINTS ====================
@v1_router.post("/auth/login", response_model=TokenResponse)
@limiter.limit(f"{settings.auth_rate_limit_per_minute}/minute")
async def login(request: Request, login_data: LoginRequest):
    """JWT-based authentication with Redis-backed security"""
    client_ip = get_remote_address(request)
    
    try:
        # Check if IP is locked out (Redis-backed)
        if await services.login_tracker.is_locked_out(client_ip):
            logger.warning("login_attempt_lockout", ip=client_ip)
            auth_attempts_counter.labels(status="lockout", method="password").inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )
        
        if not EnhancedSecurityService.verify_password(login_data.password, ADMIN_PASSWORD_HASH):
            # Record failed attempt in Redis
            await services.login_tracker.record_attempt(client_ip)
            
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

@v1_router.post("/auth/logout")
@limiter.limit("10/minute")
async def logout(request: Request, current_user: dict = Depends(verify_jwt_token)):
    """Logout endpoint with session cleanup"""
    try:
        client_ip = get_remote_address(request)
        
        # Log security event
        await services.db_service.log_security_event(
            "logout", client_ip, {"user": current_user.get("sub")}
        )
        
        logger.info("user_logout", ip=client_ip, user=current_user.get("sub"))
        
        return APIResponse(
            success=True,
            message="Logged out successfully"
        )
        
    except Exception as e:
        logger.error("logout_error", error=str(e))
        raise HTTPException(status_code=500, detail="Logout failed")

# ==================== ADMIN ENDPOINTS ====================
@v1_router.get("/admin/stats")
@limiter.limit("10/minute")
async def get_admin_stats(
    request: Request, 
    current_user: dict = Depends(verify_jwt_token)
):
    """Get system statistics with enhanced security"""
    try:
        # Validate admin session
        EnhancedSecurityService.validate_admin_session(request, current_user)
        
        # Get statistics
        now = datetime.utcnow()
        
        # Customer statistics
        total_customers = await services.db_service.db.customers.count_documents({})
        
        # Active customers (last 24 hours)
        active_since = now - timedelta(hours=24)
        active_customers = await services.db_service.db.customers.count_documents({
            "last_interaction": {"$gte": active_since}
        })
        
        # Message statistics (last 24 hours)
        messages_pipeline = [
            {
                "$match": {
                    "conversation_history.timestamp": {"$gte": active_since}
                }
            },
            {
                "$unwind": "$conversation_history"
            },
            {
                "$match": {
                    "conversation_history.timestamp": {"$gte": active_since}
                }
            },
            {
                "$count": "total_messages"
            }
        ]
        
        message_stats = await services.db_service.db.customers.aggregate(messages_pipeline).to_list(1)
        total_messages_24h = message_stats[0]["total_messages"] if message_stats else 0
        
        # System health
        db_health = await services.db_service.health_check() if hasattr(services.db_service, 'health_check') else {"status": "unknown"}
        cache_health = await services.cache_service.health_check() if hasattr(services.cache_service, 'health_check') else {"status": "unknown"}
        
        # Queue statistics
        try:
            queue_size = await services.cache_service.redis.xlen("webhook_messages")
        except:
            queue_size = 0
        
        stats = {
            "customers": {
                "total": total_customers,
                "active_24h": active_customers,
                "active_percentage": round((active_customers / total_customers * 100) if total_customers > 0 else 0, 2)
            },
            "messages": {
                "total_24h": total_messages_24h,
                "avg_per_customer": round(total_messages_24h / active_customers if active_customers > 0 else 0, 2)
            },
            "system": {
                "database_status": db_health.get("status", "unknown"),
                "cache_status": cache_health.get("status", "unknown"),
                "queue_size": queue_size
            },
            "uptime": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
        }
        
        return APIResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("admin_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@v1_router.get("/admin/customers")
@limiter.limit("5/minute")
async def get_customers(
    request: Request,
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(verify_jwt_token)
):
    """Get paginated customer list"""
    try:
        EnhancedSecurityService.validate_admin_session(request, current_user)
        
        # Validate pagination parameters
        page = max(1, page)
        limit = max(1, min(limit, 100))  # Cap at 100
        skip = (page - 1) * limit
        
        # Get customers with pagination
        cursor = services.db_service.db.customers.find(
            {},
            {
                "conversation_history": 0,  # Exclude conversation history for performance
                "preferences": 0
            }
        ).sort("last_interaction", -1).skip(skip).limit(limit)
        
        customers = await cursor.to_list(length=limit)
        total_count = await services.db_service.db.customers.count_documents({})
        
        # Convert ObjectIds to strings
        for customer in customers:
            customer["_id"] = str(customer["_id"])
            # Mask phone numbers partially for privacy
            if "phone_number" in customer:
                phone = customer["phone_number"]
                if len(phone) > 8:
                    customer["phone_number"] = phone[:4] + "****" + phone[-4:]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(customers)} customers",
            data={
                "customers": customers,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": (total_count + limit - 1) // limit
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_customers_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve customers")

@v1_router.get("/admin/security/events")
@limiter.limit("5/minute")
async def get_security_events(
    request: Request,
    limit: int = 50,
    event_type: Optional[str] = None,
    current_user: dict = Depends(verify_jwt_token)
):
    """Get recent security events"""
    try:
        EnhancedSecurityService.validate_admin_session(request, current_user)
        
        query = {}
        if event_type:
            query["event_type"] = event_type
        
        cursor = services.db_service.db.security_events.find(query) \
            .sort("timestamp", -1) \
            .limit(min(limit, 100))
        
        events = await cursor.to_list(length=limit)
        
        # Sanitize sensitive data
        for event in events:
            event["_id"] = str(event["_id"])
            # Mask IP addresses partially
            if "ip_address" in event:
                ip = event["ip_address"]
                if "." in ip:  # IPv4
                    parts = ip.split(".")
                    event["ip_address"] = f"{parts[0]}.{parts[1]}.*.{parts[3]}"
        
        return APIResponse(
            success=True,
            message=f"Found {len(events)} security events",
            data={"events": events}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_security_events_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve security events")

@v1_router.post("/admin/broadcast")
@limiter.limit("1/minute")
async def broadcast_message(
    request: Request,
    message: str,
    target_type: str = "all",  # "all", "active", "recent"
    current_user: dict = Depends(verify_jwt_token)
):
    """Broadcast message to customers (use carefully!)"""
    try:
        EnhancedSecurityService.validate_admin_session(request, current_user)
        
        # Validate message
        if not message or len(message.strip()) == 0:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if len(message) > 1000:
            raise HTTPException(status_code=400, detail="Message too long (max 1000 characters)")
        
        # Get target customers based on type
        now = datetime.utcnow()
        query = {}
        
        if target_type == "active":
            # Customers active in last 24 hours
            query["last_interaction"] = {"$gte": now - timedelta(hours=24)}
        elif target_type == "recent":
            # Customers active in last 7 days
            query["last_interaction"] = {"$gte": now - timedelta(days=7)}
        # "all" uses empty query
        
        customers = await services.db_service.db.customers.find(
            query, 
            {"phone_number": 1}
        ).to_list(length=None)
        
        if not customers:
            return APIResponse(
                success=True,
                message="No customers found for the selected target type",
                data={"sent_count": 0}
            )
        
        # Send messages (with rate limiting)
        sent_count = 0
        failed_count = 0
        
        for customer in customers:
            try:
                success = await services.whatsapp_service.send_message(
                    customer["phone_number"], 
                    message
                )
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting between messages
                await asyncio.sleep(0.1)  # 100ms delay between messages
                
            except Exception as e:
                logger.error("broadcast_send_error", 
                           phone=customer["phone_number"], 
                           error=str(e))
                failed_count += 1
        
        # Log security event
        await services.db_service.log_security_event(
            "message_broadcast",
            get_remote_address(request),
            {
                "target_type": target_type,
                "message_length": len(message),
                "sent_count": sent_count,
                "failed_count": failed_count
            }
        )
        
        logger.info("message_broadcast_completed", 
                   target_type=target_type,
                   sent=sent_count,
                   failed=failed_count)
        
        return APIResponse(
            success=True,
            message=f"Broadcast completed: {sent_count} sent, {failed_count} failed",
            data={
                "sent_count": sent_count,
                "failed_count": failed_count,
                "target_type": target_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("broadcast_message_error", error=str(e))
        raise HTTPException(status_code=500, detail="Broadcast failed")

# ==================== PUBLIC ENDPOINTS ====================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Feelori AI WhatsApp Assistant",
        "version": "2.0.0",
        "status": "operational",
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes/Docker readiness probe"""
    try:
        # Quick checks that must pass for the app to be ready
        await services.db_service.db.command("ping")
        await services.cache_service.redis.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/health/live")
async def liveness_check():
    """Kubernetes/Docker liveness probe"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

@app.get("/health/comprehensive")
async def comprehensive_health_check(_: bool = Depends(verify_metrics_access)):
    """Comprehensive health check for production monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0",
        "environment": settings.environment,
        "checks": {}
    }
    
    start_time = time.time()
    
    try:
        # Database health check
        try:
            await services.db_service.db.command("ping")
            health_status["checks"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        
        # Cache health check
        try:
            await services.cache_service.redis.ping()
            health_status["checks"]["cache"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["cache"] = {"status": "unhealthy", "error": str(e)}
        
        # Message queue health check
        try:
            queue_size = await services.cache_service.redis.xlen("webhook_messages")
            health_status["checks"]["message_queue"] = {
                "status": "healthy" if queue_size < 1000 else "warning",
                "queue_size": queue_size,
                "max_recommended": 1000
            }
        except Exception as e:
            health_status["checks"]["message_queue"] = {"status": "unhealthy", "error": str(e)}
        
        # HTTP client health check
        try:
            test_response = await services.http_client.get(
                "https://httpbin.org/status/200", 
                timeout=5.0
            )
            health_status["checks"]["http_client"] = {
                "status": "healthy" if test_response.status_code == 200 else "unhealthy",
                "response_code": test_response.status_code
            }
        except Exception as e:
            health_status["checks"]["http_client"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # System resource check
        try:
            import psutil
            health_status["checks"]["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            health_status["checks"]["system"] = {"status": "error", "error": str(e)}
        
        # Set overall status based on critical components
        critical_unhealthy = []
        for service, check in health_status["checks"].items():
            if isinstance(check, dict) and check.get("status") == "unhealthy":
                if service in ["database", "cache"]:  # Critical services
                    critical_unhealthy.append(service)
        
        if critical_unhealthy:
            health_status["status"] = "unhealthy"
            health_status["critical_failures"] = critical_unhealthy
        elif any(check.get("status") == "unhealthy" for check in health_status["checks"].values() 
                if isinstance(check, dict)):
            health_status["status"] = "degraded"
        
        health_status["response_time"] = time.time() - start_time
        
    except Exception as e:
        health_status["status"] = "error"
        health_status["error"] = str(e)
        health_status["response_time"] = time.time() - start_time
    
    # Return appropriate HTTP status code
    if health_status["status"] == "unhealthy":
        return JSONResponse(health_status, status_code=503)
    elif health_status["status"] == "degraded":
        return JSONResponse(health_status, status_code=200)  # Still serving traffic
    else:
        return health_status

@app.get("/metrics")
async def metrics(request: Request, _: bool = Depends(verify_metrics_access)):
    """Secured Prometheus metrics endpoint"""
    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain"
    )

# Include the v1 router
app.include_router(v1_router)

# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    import uvicorn
    
    # Store start time for uptime calculation
    app.state.start_time = time.time()
    
    # Production configuration
    workers = int(os.getenv("UVICORN_WORKERS", "1"))  # Default to 1 for development
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    
    # SSL configuration
    ssl_keyfile = settings.ssl_key_path if settings.https_only else None
    ssl_certfile = settings.ssl_cert_path if settings.https_only else None
    
    if settings.environment == "production":
        if settings.https_only and ssl_keyfile and ssl_certfile:
            logger.info("starting_https_server", 
                       port=port, 
                       workers=workers,
                       ssl_enabled=True)
            uvicorn.run(
                "server:app",
                host=host,
                port=port,
                ssl_keyfile=ssl_keyfile,
                ssl_certfile=ssl_certfile,
                workers=workers if workers > 1 else None,  # Only use workers in production
                reload=False,
                access_log=False,  # Use structured logging instead
                log_config=None,   # Disable uvicorn's logging config
                server_header=False,
                date_header=False,
            )
        else:
            logger.info("starting_http_server", 
                       port=port, 
                       workers=workers,
                       ssl_enabled=False)
            uvicorn.run(
                "server:app",
                host=host,
                port=port,
                workers=workers if workers > 1 else None,
                reload=False,
                access_log=False,
                log_config=None,
                server_header=False,
                date_header=False,
            )
    else:
        # Development mode
        logger.info("starting_development_server", port=port)
        uvicorn.run(
            "server:app",
            host=host,
            port=port,
            reload=True,  # Enable reload in development
            access_log=True,
            log_level="info"
        )

