import os
import sys
import logging
import json
import hashlib
import uuid
import re
import asyncio
import secrets


from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Annotated

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import httpx
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, validator, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Global variables for AI models
gemini_model = None
openai_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize AI models and HTTP client on startup"""
    global gemini_model, openai_client
    
    logger.info("Initializing AI models and HTTP client...")

    # Initialize shared httpx client
    app.state.http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    
    # Initialize Gemini
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
    else:
        logger.warning("GEMINI_API_KEY not found")
    
    # Initialize OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            openai_client = AsyncOpenAI(api_key=openai_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    else:
        logger.warning("OPENAI_API_KEY not found")
    
    if not gemini_model and not openai_client:
        logger.error("No AI models available - application may not function properly")
    
    yield
    
    logger.info("Shutting down application and closing HTTP client...")
    await app.state.http_client.aclose()

app = FastAPI(
    title="Feelori AI WhatsApp Assistant",
    version="2.0.0",
    description="Production-ready AI WhatsApp assistant with enhanced security and performance",
    lifespan=lifespan
)

# Security middleware
allowed_hosts = os.environ.get("ALLOWED_HOSTS", "").split(",")
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[host for host in allowed_hosts if host]
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in cors_origins if origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Database connection
mongo_uri = os.environ.get("MONGO_ATLAS_URI") or os.environ.get("MONGO_URL")
if not mongo_uri:
    logger.critical("MONGO_ATLAS_URI or MONGO_URL environment variable not set. Application will not start.")
    sys.exit(1)

client = AsyncIOMotorClient(mongo_uri)
db = client.get_default_database()

# Security
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    logger.critical("ADMIN_PASSWORD environment variable not set. Application will not start.")
    sys.exit(1)

# WhatsApp Business API Configuration
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"

# Shopify Configuration
SHOPIFY_STORE_URL = os.environ.get("SHOPIFY_STORE_URL", "feelori.myshopify.com")
SHOPIFY_ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01"

# Validation Models
def validate_phone_number(phone: str) -> str:
    """Validate and format phone number"""
    # Remove all non-digit characters except +
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # If no + at start, add it (WhatsApp sends without + sometimes)
    if not clean_phone.startswith('+'):
        clean_phone = '+' + clean_phone
    
    # Check if it's in valid international format
    if not re.match(r'^\+\d{10,15}$', clean_phone):
        raise ValueError("Invalid phone number format. Must be +[country_code][number] with 10-15 digits.")
    
    return clean_phone

from pydantic import field_validator, ValidationInfo

class PhoneNumber(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> Any:
        from pydantic_core import core_schema
        return core_schema.str_schema(min_length=1, max_length=20)

class WhatsAppMessage(BaseModel):
    from_number: str = Field(..., pattern=r'^\+\d{10,15}$')
    message_text: str = Field(..., min_length=1, max_length=4096)
    message_id: str = Field(..., min_length=1, max_length=255)
    timestamp: str

class WebhookEntry(BaseModel):
    id: str
    changes: List[Dict[str, Any]]

class WebhookData(BaseModel):
    object: str
    entry: List[WebhookEntry]

class Customer(BaseModel):
    id: Optional[str] = None
    phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    created_at: Optional[datetime] = None
    conversation_history: List[Dict] = Field(default_factory=list)
    preferences: Dict = Field(default_factory=dict)

class Product(BaseModel):
    id: str
    title: str = Field(..., max_length=255)
    handle: str
    description: str
    price: str
    images: List[str] = Field(default_factory=list)
    variants: List[Dict] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    available: bool = True

class SendMessageRequest(BaseModel):
    phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')
    message: str = Field(..., min_length=1, max_length=4096)

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Authentication
async def verify_session(request: Request):
    """Verify if the user is authenticated via session"""
    if "authenticated" not in request.session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return True

async def get_database():
    """Get database dependency"""
    return db

def get_http_client(request: Request) -> httpx.AsyncClient:
    """Get shared httpx client from application state"""
    return request.app.state.http_client

# Utility Functions
async def send_whatsapp_message(client: httpx.AsyncClient, to_number: str, message: str) -> bool:
    """Send message via WhatsApp Business API with enhanced error handling"""
    try:
        if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
            logger.error("WhatsApp credentials not configured")
            return False
            
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }
        
        response = await client.post(WHATSAPP_API_URL, headers=headers, json=payload)
            
        if response.status_code == 200:
            logger.info(f"Message sent successfully to {to_number}")
            return True
        else:
            logger.error(f"Failed to send message to {to_number}: {response.status_code} - {response.text}")
            return False
            
    except httpx.TimeoutException:
        logger.error(f"Timeout sending message to {to_number}")
        return False
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to_number}: {str(e)}")
        return False

async def get_shopify_products(client: httpx.AsyncClient, query: str = "", limit: int = 10, max_price: Optional[float] = None) -> List[Product]:
    """Fetch products from Shopify with enhanced error handling and proper search"""
    try:
        if not SHOPIFY_ACCESS_TOKEN:
            logger.error("Shopify access token not configured")
            return []
            
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        
        params = {"limit": min(limit, 250)}  # Shopify max limit
        
        # Use the 'fields' parameter to limit response size and improve performance
        params["fields"] = "id,title,handle,body_html,variants,images,tags,vendor,product_type"
        
        response = await client.get(
            f"{SHOPIFY_API_URL}/products.json",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            products = []
            
            for product_data in data.get("products", []):
                try:
                    variants = product_data.get("variants", [])
                    price = variants[0].get("price", "0.00") if variants else "0.00"
                    
                    # Clean HTML from description
                    description = re.sub(r'<[^>]+>', '', product_data.get("body_html", ""))
                    
                    product = Product(
                        id=str(product_data["id"]),
                        title=product_data["title"][:255],
                        handle=product_data["handle"],
                        description=description[:1000],  # Limit description length
                        price=str(price),
                        images=[img["src"] for img in product_data.get("images", [])[:5]],  # Limit images
                        variants=variants[:10],  # Limit variants
                        tags=product_data.get("tags", "").split(",")[:20] if product_data.get("tags") else [],
                        available=any(v.get("inventory_quantity", 0) > 0 for v in variants) if variants else False
                    )
                    add_product = False
                    # If there's a query, filter products locally
                    if query:
                        query_lower = query.lower()
                        product_text = f"{product.title} {product.description} {' '.join(product.tags)} {product_data.get('vendor', '')} {product_data.get('product_type', '')}".lower()
                        
                        # Check if any word in the query matches the product
                        query_words = query_lower.split()
                        if any(word in product_text for word in query_words if len(word) > 2):
                            add_product = True
                    else:
                        add_product = True
                    # --- New Price Filtering Logic ---
                    if add_product and max_price is not None:
                        # If the product's price is higher than the limit, don't add it
                        if float(product.price) > max_price:
                            add_product = False
                    # --- End of New Logic ---
                    if add_product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error processing product {product_data.get('id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(products)} products from Shopify (filtered: {bool(query)})")
            return products
        else:
            logger.error(f"Failed to fetch Shopify products: {response.status_code} - {response.text}")
            return []
            
    except httpx.TimeoutException:
        logger.error("Timeout fetching Shopify products")
        return []
    except Exception as e:
        logger.error(f"Error fetching Shopify products: {str(e)}")
        return []

async def get_shopify_order(client: httpx.AsyncClient, order_id: str) -> Optional[Dict]:
    """Get order details from Shopify"""
    try:
        if not SHOPIFY_ACCESS_TOKEN:
            return None
            
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        
        response = await client.get(
            f"{SHOPIFY_API_URL}/orders/{order_id}.json",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()["order"]
        else:
            logger.warning(f"Order {order_id} not found: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {str(e)}")
        return None

async def search_orders_by_phone(client: httpx.AsyncClient, phone_number: str) -> List[Dict]:
    """Search orders by phone number with enhanced matching"""
    try:
        if not SHOPIFY_ACCESS_TOKEN:
            return []
            
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        
        response = await client.get(
            f"{SHOPIFY_API_URL}/orders.json",
            headers=headers,
            params={"status": "any", "limit": 50}
        )
        
        if response.status_code == 200:
            orders = response.json()["orders"]
            matching_orders = []
            
            for order in orders:
                billing_phone = order.get("billing_address", {}).get("phone", "")
                shipping_phone = order.get("shipping_address", {}).get("phone", "")
                
                # Clean and compare phone numbers
                clean_billing = re.sub(r'[^\d]', '', billing_phone)
                clean_shipping = re.sub(r'[^\d]', '', shipping_phone)
                
                if (clean_phone in clean_billing or clean_phone in clean_shipping or
                    clean_billing.endswith(clean_phone[-10:]) or clean_shipping.endswith(clean_phone[-10:])):
                    matching_orders.append(order)
            
            logger.info(f"Found {len(matching_orders)} orders for phone {phone_number}")
            return matching_orders[:10]  # Limit results
        else:
            logger.error(f"Failed to search orders: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error searching orders for {phone_number}: {str(e)}")
        return []

async def get_or_create_customer(phone_number: str) -> Customer:
    """Get or create customer in database with validation"""
    try:
        # Validate phone number
        clean_phone = validate_phone_number(phone_number)
        
        customer_data = await db.customers.find_one({"phone_number": clean_phone})
        
        if customer_data:
            return Customer(**customer_data)
        else:
            new_customer = Customer(
                id=str(uuid.uuid4()),
                phone_number=clean_phone,
                created_at=datetime.utcnow(),
                conversation_history=[],
                preferences={}
            )
            
            await db.customers.insert_one(new_customer.dict())
            logger.info(f"Created new customer: {clean_phone}")
            return new_customer
            
    except Exception as e:
        logger.error(f"Error managing customer {phone_number}: {str(e)}")
        # Return a basic customer object for fallback
        return Customer(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            created_at=datetime.utcnow()
        )

async def update_conversation_history(phone_number: str, message: str, response: str):
    """Update customer conversation history with limits"""
    try:
        clean_phone = validate_phone_number(phone_number)
        
        # Limit conversation history to last 50 exchanges
        await db.customers.update_one(
            {"phone_number": clean_phone},
            {
                "$push": {
                    "conversation_history": {
                        "$each": [{
                            "timestamp": datetime.utcnow(),
                            "user_message": message[:1000],  # Limit message length
                            "ai_response": response[:2000]   # Limit response length
                        }],
                        "$slice": -50  # Keep only last 50 conversations
                    }
                }
            }
        )
    except Exception as e:
        logger.error(f"Error updating conversation history for {phone_number}: {str(e)}")

import json
import httpx
from typing import List, Dict, Optional

async def send_product_catalog_message(client: httpx.AsyncClient, to_number: str, products: List[Product], header_text: str = "Here are some products you might like:") -> bool:
    """Send interactive product catalog message via WhatsApp Business API"""
    try:
        if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
            logger.error("WhatsApp credentials not configured")
            return False
        
        # Check if catalog is configured
        catalog_id = os.environ.get("WHATSAPP_CATALOG_ID")
        if not catalog_id:
            logger.info("WhatsApp catalog not configured, falling back to interactive list")
            return await send_interactive_product_list(client, to_number, products, "Products")
            
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Create interactive message with product list
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "product_list",
                "header": {
                    "type": "text",
                    "text": header_text
                },
                "body": {
                    "text": "Browse our collection and tap on any product to see more details:"
                },
                "footer": {
                    "text": "Powered by Feelori"
                },
                "action": {
                    "catalog_id": catalog_id,
                    "sections": [
                        {
                            "title": "Featured Products",
                            "product_items": [
                                {
                                    "product_retailer_id": product.id
                                } for product in products[:10]  # WhatsApp limits to 10 products per section
                            ]
                        }
                    ]
                }
            }
        }
        
        response = await client.post(WHATSAPP_API_URL, headers=headers, json=payload)
            
        if response.status_code == 200:
            logger.info(f"Product catalog message sent successfully to {to_number}")
            return True
        else:
            logger.error(f"Failed to send product catalog to {to_number}: {response.status_code} - {response.text}")
            # Fallback to interactive list
            return await send_interactive_product_list(client, to_number, products, "Products")
            
    except Exception as e:
        logger.error(f"Error sending product catalog to {to_number}: {str(e)}")
        # Fallback to interactive list
        return await send_interactive_product_list(client, to_number, products, "Products")

async def send_product_images_sequence(client: httpx.AsyncClient, to_number: str, products: List[Product]) -> bool:
    """Send a sequence of product images with details (WhatsApp-compatible alternative to carousel)"""
    try:
        if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
            return False
            
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Send up to 3 products as individual image messages
        for product in products[:3]:
            if product.images:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to_number,
                    "type": "image",
                    "image": {
                        "link": product.images[0],
                        "caption": f"🏷️ *{product.title}*\n💰 *₹{product.price}*\n\n{product.description[:200]}...\n\n🔗 https://feelori.com/products/{product.handle}"
                    }
                }
                
                await client.post(WHATSAPP_API_URL, headers=headers, json=payload)
                await asyncio.sleep(1)  # Small delay between images
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending product images sequence: {str(e)}")
        return False

async def send_interactive_product_list(client: httpx.AsyncClient, to_number: str, products: List[Product], category: str = "Products") -> bool:
    """Send interactive list message with products"""
    try:
        if not products:
            return False
            
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Create interactive list rows
        rows = []
        for i, product in enumerate(products[:10]):  # WhatsApp limits to 10 items
            rows.append({
                "id": f"product_{product.id}",
                "title": product.title[:24],  # 24 char limit
                "description": f"₹{product.price} • {product.description[:55]}"  # 55 char limit
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": f"🛍️ {category}"
                },
                "body": {
                    "text": "Here are some great products for you! Tap 'View Products' to see the full list:"
                },
                "footer": {
                    "text": "Tap any product to learn more"
                },
                "action": {
                    "button": "View Products",
                    "sections": [
                        {
                            "title": category,
                            "rows": rows
                        }
                    ]
                }
            }
        }
        
        response = await client.post(WHATSAPP_API_URL, headers=headers, json=payload)
            
        if response.status_code == 200:
            logger.info(f"Interactive product list sent to {to_number}")
            return True
        else:
            logger.error(f"Failed to send interactive list: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending interactive product list: {str(e)}")
        return False

async def send_product_with_media(client: httpx.AsyncClient, to_number: str, product: Product) -> bool:
    """Send individual product with image and details"""
    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # First send the product image
        if product.images:
            image_payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "image",
                "image": {
                    "link": product.images[0],
                    "caption": f"🏷️ *{product.title}*\n💰 *₹{product.price}*\n\n🔗 View: https://feelori.com/products/{product.handle}"
                }
            }
            
            await client.post(WHATSAPP_API_URL, headers=headers, json=image_payload)
        
        # Then send interactive buttons
        button_payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": "What would you like to do?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"buy_{product.id}",
                                "title": "🛒 Buy Now"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"details_{product.id}",
                                "title": "ℹ️ More Info"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "more_products",
                                "title": "🔍 Browse More"
                            }
                        }
                    ]
                }
            }
        }
        
        response = await client.post(WHATSAPP_API_URL, headers=headers, json=button_payload)
            
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Error sending product with media: {str(e)}")
        return False

async def send_quick_product_summary(client: httpx.AsyncClient, to_number: str, products: List[Product]) -> bool:
    """Send a quick text summary with emojis and formatting for better readability"""
    try:
        if not products:
            return False
            
        # Create formatted message
        message = "🛍️ *Here are some great products for you:*\n\n"
        
        for i, product in enumerate(products[:5], 1):  # Limit to 5 for readability
            # Truncate title and description for WhatsApp
            title = product.title[:40] + "..." if len(product.title) > 40 else product.title
            desc = product.description[:80] + "..." if len(product.description) > 80 else product.description
            
            message += f"*{i}. {title}*\n"
            message += f"💰 ₹{product.price}\n"
            message += f"📝 {desc}\n"
            message += f"🔗 https://feelori.com/products/{product.handle}\n\n"
        
        message += "💬 *Reply with the product number to learn more, or ask me anything!*"
        
        return await send_whatsapp_message(client, to_number, message)
        
    except Exception as e:
        logger.error(f"Error sending quick product summary: {str(e)}")
        return False

async def enhanced_process_message(client: httpx.AsyncClient, phone_number: str, message: str) -> str:
    """Enhanced message processing with rich product display"""
    try:
        logger.info(f"Processing message: '{message}' from {phone_number}")
        
        customer = await get_or_create_customer(phone_number)
        message_lower = message.lower()
        
        # Handle interactive button responses
        if message.startswith("product_"):
            product_id = message.split("_")[1]
            # Get specific product and send detailed view
            products = await get_shopify_products(client, limit=50)
            product = next((p for p in products if p.id == product_id), None)
            if product:
                await send_product_with_media(client, phone_number, product)
                return ""  # Don't send additional text message
        
        elif message.startswith("buy_"):
            product_id = message.split("_")[1]
            products = await get_shopify_products(client, limit=50)
            product = next((p for p in products if p.id == product_id), None)
            if product:
                buy_message = f"🛒 Great choice! To purchase *{product.title}* for *₹{product.price}*, please visit:\n\n🔗 https://feelori.com/products/{product.handle}\n\nNeed help with your order? Just ask! 😊"
                await send_whatsapp_message(client, phone_number, buy_message)
                return ""  # Return an empty string so the old code doesn't send a second message
            else:
                await send_whatsapp_message(client, phone_number, "Sorry, I couldn't find that product. Let me show you our latest items!")
                return "" # Return an empty string
        
        elif message.startswith("details_"):
            product_id = message.split("_")[1]
            products = await get_shopify_products(client, limit=50)
            product = next((p for p in products if p.id == product_id), None)
            if product:
                details_message = f"ℹ️ *Product Details*\n\n*{product.title}*\n💰 *₹{product.price}*\n\n📝 {product.description[:300]}...\n\n"
                if product.tags:
                    details_message += f"🏷️ Tags: {', '.join(product.tags[:5])}\n\n"
                details_message += f"🔗 Full details: https://feelori.com/products/{product.handle}"
                return details_message
            else:
                return "Sorry, I couldn't find details for that product. Let me show you our featured items!"
        
        elif message == "more_products":
            products = await get_shopify_products(client, limit=8)
            if products:
                success = await send_interactive_product_list(client, phone_number, products, "More Products")
                if not success:
                    await send_quick_product_summary(client, phone_number, products)
                return "Here are more great products for you! ✨"
            else:
                return "Let me know what you're looking for and I'll help you find it! 🔍"
        
        # Handle numeric responses (from quick product summary)
        elif message.isdigit() and 1 <= int(message) <= 5:
            products = await get_shopify_products(client, limit=5)
            if products and int(message) <= len(products):
                product = products[int(message) - 1]
                await send_product_with_media(client, phone_number, product)
                return ""  # Don't send additional text message
        
        # Analyze message intent for new conversations
        context = {}
        product_keywords = [
            "product", "item", "buy", "purchase", "show", "looking for", "need", "want", 
            "recommend", "sell", "available", "have", "find", "search", "browse",
            "catalog", "store", "shop", "price", "cost", "cheap", "expensive",
            "new", "latest", "popular", "best", "good", "quality"
        ]
        
        if any(word in message_lower for word in product_keywords):
            logger.info(f"Product search detected for message: {message}")

            # --- New Price Extraction Logic ---
            price_limit = None
            # Find numbers in the message
            price_match = re.search(r'(\d+)', message)
            if price_match:
                price_limit = float(price_match.group(1))

            # --- End of New Logic ---
    
            # Extract search terms
            search_words = [word for word in message_lower.split() 
                          if word not in ["i", "want", "to", "buy", "looking", "for", "show", "me", "can", "you", "please", "need", "a", "an", "the", "under", "below", "rupees"] 
                          and not word.isdigit() # Exclude numbers from the text query
                          and len(word) > 2]
            search_query = " ".join(search_words[:5])
    
            # Pass the price limit to the function
            products = await get_shopify_products(client, query=search_query, limit=20, max_price=price_limit)
            
            if products:
                # Try interactive list first
                success = await send_interactive_product_list(client, phone_number, products, "Search Results")
                if not success:
                    # Fallback: Send product images sequence (2-3 products with images)
                    if any(p.images for p in products[:3]):
                        await send_product_images_sequence(client, phone_number, products)
                    # Always send quick summary as backup
                    await send_quick_product_summary(client, phone_number, products)
                
                return f"Found {len(products)} products for you! ✨"
            else:
                return "I couldn't find any products matching your request. Could you try describing what you're looking for differently? 🤔"
        
        # Default greeting with featured products
        elif any(word in message_lower for word in ["hello", "hi", "hey", "help", "start", "begin"]):
            products = await get_shopify_products(client, limit=5)
            if products:
                success = await send_interactive_product_list(client, phone_number, products, "Featured Products")
                if not success:
                    await send_quick_product_summary(client, phone_number, products)
                return "Welcome to Feelori! 👋 Check out our featured products above. How can I help you today?"
            else:
                return "Welcome to Feelori! 👋 How can I help you today?"
        
        # Order tracking
        elif any(word in message_lower for word in ["order", "tracking", "delivery", "shipping", "status", "track"]):
            orders = await search_orders_by_phone(client, phone_number)
            context["orders"] = orders
            if orders:
                order_info = "📦 *Your Recent Orders:*\n\n"
                for order in orders[:3]:
                    order_info += f"🛍️ Order #{order['order_number']}\n"
                    order_info += f"💰 ₹{order['total_price']}\n"
                    order_info += f"📋 Status: {order['financial_status']}\n"
                    if order.get('fulfillment_status'):
                        order_info += f"🚚 Fulfillment: {order['fulfillment_status']}\n"
                    order_info += f"📅 {order['created_at'][:10]}\n\n"
                
                order_info += "Need more details about any order? Just let me know! 😊"
                return order_info
            else:
                return "I couldn't find any orders associated with your phone number. If you've placed an order recently, please check your email for order confirmation or contact our support team."
        
        # Generate AI response for other messages
        response = await generate_ai_response(message, customer, context)
        await update_conversation_history(phone_number, message, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing message from {phone_number}: {str(e)}", exc_info=True)
        return "I'm sorry, I encountered an error processing your request. Please try again or contact our support team."


async def generate_ai_response(message: str, customer: Customer, context: Dict = None) -> str:
    """Generate AI response using initialized models with enhanced error handling"""
    global gemini_model, openai_client
    
    if not gemini_model and not openai_client:
        logger.error("No AI models available")
        return "I'm sorry, our AI service is temporarily unavailable. Please contact our support team for assistance."
    
    # Build context for AI
    conversation_context = ""
    if customer.conversation_history:
        recent_history = customer.conversation_history[-3:]
        for conv in recent_history:
            conversation_context += f"User: {conv['user_message']}\nAI: {conv['ai_response']}\n"
    
    # Build product context
    product_context = ""
    if context and context.get("products"):
        product_context = "\nAvailable products:\n"
        for product in context["products"][:5]:
            product_context += f"- {product.title}: ₹{product.price} - {product.description[:100]}...\n"
    
    # Build order context
    order_context = ""
    if context and context.get("orders"):
        order_context = "\nCustomer's recent orders:\n"
        for order in context["orders"][:3]:
            order_context += f"- Order #{order['order_number']}: {order['financial_status']} - ₹{order['total_price']}\n"
    
    # Create the prompt
    system_prompt = f"""You are Feelori's AI customer service assistant. You're helpful, friendly, and knowledgeable about Feelori's products.

IMPORTANT GUIDELINES:
- Always be warm and professional
- Help customers find products, track orders, and answer questions
- If you don't know something specific, politely say so and offer to connect them with human support
- For product recommendations, be specific about features and benefits
- Keep responses concise but informative (max 500 characters)
- Always include relevant product links when recommending products

Store Information:
- Store: Feelori (feelori.com)
- We sell high-quality products with focus on customer satisfaction

Previous conversation:
{conversation_context}

{product_context}

{order_context}

Customer message: {message}

Respond helpfully and naturally:"""

    try:
        # Try Gemini first if available
        if gemini_model:
            response = await asyncio.to_thread(
                gemini_model.generate_content, system_prompt
            )
            return response.text[:1000]  # Limit response length
        else:
            raise Exception("Gemini model not available")
        
    except Exception as e:
        logger.warning(f"Gemini failed: {str(e)}")
        
        try:
            # Fallback to OpenAI if available
            if openai_client:
                response = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are Feelori's AI customer service assistant. Be helpful, friendly, and professional."},
                        {"role": "user", "content": system_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content[:1000]
            else:
                raise Exception("OpenAI client not available")
            
        except Exception as e2:
            logger.error(f"Both AI models failed: {str(e2)}")
            return "I'm sorry, I'm having technical difficulties right now. Please try again in a moment, or contact our human support team at support@feelori.com for immediate assistance."

# Routes
@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information"""
    return APIResponse(
        success=True,
        message="Feelori AI WhatsApp Assistant v2.0 - Production Ready",
        data={
            "version": "2.0.0",
            "status": "running",
            "features": ["WhatsApp Integration", "Shopify Integration", "AI Chat", "Customer Management"]
        }
    )

@app.get("/api/webhook")
@limiter.limit("60/minute")
async def verify_webhook(request: Request):
    """Webhook verification for WhatsApp with rate limiting"""
    print("Inside verify_webhook")
    try:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        logger.info(f"Webhook verification attempt - mode: {mode}, token: {token}, challenge: {challenge}, verify_token: {WHATSAPP_VERIFY_TOKEN}")
        
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            # Return the challenge as plain text, not JSON
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            logger.warning("Webhook verification failed")
            return JSONResponse(content={"detail": "Verification failed"}, status_code=403)
    except Exception as e:
        logger.error(f"Webhook verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/webhook")
@limiter.limit("100/minute")
async def handle_webhook(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Handle incoming WhatsApp messages with enhanced interactive support"""
    try:
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")
        
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        
                        # Process incoming messages
                        for message in value.get("messages", []):
                            from_number = message.get("from")
                            message_text = ""
                            
                            # Handle different message types
                            if message.get("text"):
                                message_text = message.get("text", {}).get("body", "")
                            elif message.get("image"):
                                message_text = message.get("image", {}).get("caption", "")
                            elif message.get("interactive"):
                                # Handle interactive button/list responses
                                interactive = message.get("interactive", {})
                                if interactive.get("type") == "button_reply":
                                    message_text = interactive.get("button_reply", {}).get("id", "")
                                elif interactive.get("type") == "list_reply":
                                    message_text = interactive.get("list_reply", {}).get("id", "")
                            
                            if from_number and message_text:
                                logger.info(f"Processing message from {from_number}: {message_text}")
                                
                                # Use enhanced processing with interactive features
                                response = await enhanced_process_message(client, from_number, message_text)
                                
                                # Send text response only if needed (interactive messages are sent within enhanced_process_message)
                                if response and not message_text.startswith(("product_", "buy_", "details_", "more_products")):
                                    await send_whatsapp_message(client, from_number, response)
        
        return APIResponse(success=True, message="Webhook processed successfully")
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return APIResponse(success=False, message="Webhook processing failed")

@app.get("/api/products", response_model=APIResponse)
@limiter.limit("30/minute")
async def get_products(request: Request, query: str = "", limit: int = 10, client: httpx.AsyncClient = Depends(get_http_client)):
    """Get products from Shopify with rate limiting"""
    try:
        products = await get_shopify_products(client, query=query, limit=min(limit, 50))
        return APIResponse(
            success=True,
            message=f"Retrieved {len(products)} products",
            data={"products": [product.dict() for product in products]}
        )
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch products")

@app.get("/api/orders/{phone_number}", response_model=APIResponse)
@limiter.limit("20/minute")
async def get_customer_orders(request: Request, phone_number: str, _is_auth: bool = Depends(verify_session), client: httpx.AsyncClient = Depends(get_http_client)):
    """Get orders for a customer by phone number - Protected endpoint"""
    try:
        clean_phone = validate_phone_number(phone_number)
        orders = await search_orders_by_phone(client, clean_phone)
        return APIResponse(
            success=True,
            message=f"Found {len(orders)} orders",
            data={"orders": orders}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching orders for {phone_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")

@app.get("/api/customers/{phone_number}", response_model=APIResponse)
@limiter.limit("20/minute")
async def get_customer(request: Request, phone_number: str, _is_auth: bool = Depends(verify_session)):
    """Get customer information - Protected endpoint"""
    try:
        customer = await get_or_create_customer(phone_number)
        return APIResponse(
            success=True,
            message="Customer retrieved successfully",
            data={"customer": customer.dict()}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching customer {phone_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer")

@app.post("/api/send-message", response_model=APIResponse)
@limiter.limit("10/minute")
async def send_message(request: Request, data: SendMessageRequest, _is_auth: bool = Depends(verify_session), client: httpx.AsyncClient = Depends(get_http_client)):
    """Send a message via WhatsApp API - Protected endpoint"""
    try:
        success = await send_whatsapp_message(client, data.phone_number, data.message)
        
        if success:
            return APIResponse(success=True, message="Message sent successfully")
        else:
            return APIResponse(success=False, message="Failed to send message")
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@app.post("/api/login", response_model=APIResponse)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """Authenticate and create a session"""
    if secrets.compare_digest(login_data.password, ADMIN_PASSWORD):
        request.session["authenticated"] = True
        logger.info("Admin login successful")
        return APIResponse(success=True, message="Login successful")
    else:
        logger.warning("Failed admin login attempt")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@app.post("/api/logout", response_model=APIResponse)
async def logout(request: Request):
    """Clear the session"""
    request.session.clear()
    return APIResponse(success=True, message="Logout successful")

@app.get("/api/session", response_model=APIResponse)
async def get_session(request: Request):
    """Check if a session is active"""
    if "authenticated" in request.session:
        return APIResponse(success=True, message="Session is active")
    else:
        return APIResponse(success=False, message="No active session")

@app.get("/api/health", response_model=APIResponse)
@limiter.limit("60/minute")
async def health_check(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    """Enhanced health check endpoint"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": "2.0.0",
            "services": {}
        }
        
        # Test database connection
        try:
            await db.customers.count_documents({})
            health_data["services"]["database"] = "connected"
        except Exception as e:
            health_data["services"]["database"] = f"error: {str(e)}"
            health_data["status"] = "degraded"
        
        # Test Shopify API
        try:
            products = await get_shopify_products(client, limit=1)
            health_data["services"]["shopify"] = "connected" if products or SHOPIFY_ACCESS_TOKEN else "not_configured"
        except Exception as e:
            health_data["services"]["shopify"] = f"error: {str(e)}"
            health_data["status"] = "degraded"
        
        # Test AI models
        global gemini_model, openai_client
        health_data["services"]["ai_models"] = {
            "gemini": "available" if gemini_model else "not_available",
            "openai": "available" if openai_client else "not_available"
        }
        
        if not gemini_model and not openai_client:
            health_data["status"] = "degraded"
        
        # WhatsApp configuration
        health_data["services"]["whatsapp"] = "configured" if WHATSAPP_TOKEN and WHATSAPP_PHONE_ID else "not_configured"
        
        return APIResponse(
            success=health_data["status"] in ["healthy", "degraded"],
            message=f"System is {health_data['status']}",
            data=health_data
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return APIResponse(
            success=False,
            message="Health check failed",
            data={"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow()}
        )

@app.get("/api/dashboard/stats", response_model=APIResponse)
@limiter.limit("20/minute")
async def get_dashboard_stats(request: Request, _is_auth: bool = Depends(verify_session)):
    """Get dashboard statistics - Protected endpoint"""
    try:
        # This is a simplified version of get_metrics, tailored for the dashboard
        customer_count = await db.customers.count_documents({})

        pipeline = [
            {"$project": {"conversation_count": {"$size": "$conversation_history"}}},
            {"$group": {"_id": None, "total_conversations": {"$sum": "$conversation_count"}}}
        ]
        conversation_result = await db.customers.aggregate(pipeline).to_list(1)
        total_conversations = conversation_result[0]["total_conversations"] if conversation_result else 0

        # These are dummy values for now, as we are not tracking them
        products_shown = 0
        orders_tracked = 0

        stats_data = {
            "totalMessages": total_conversations,
            "activeCustomers": customer_count,
            "productsShown": products_shown,
            "ordersTracked": orders_tracked,
        }

        return APIResponse(
            success=True,
            message="Dashboard stats retrieved successfully",
            data=stats_data
        )
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard stats")

@app.get("/api/dashboard/recent-messages", response_model=APIResponse)
@limiter.limit("20/minute")
async def get_recent_messages(request: Request, _is_auth: bool = Depends(verify_session)):
    """Get recent messages from conversations - Protected endpoint"""
    try:
        pipeline = [
            {"$unwind": "$conversation_history"},
            {"$sort": {"conversation_history.timestamp": -1}},
            {"$limit": 10},
            {"$project": {
                "id": "$conversation_history.timestamp",
                "phone": "$phone_number",
                "message": "$conversation_history.user_message",
                "response": "$conversation_history.ai_response",
                "timestamp": "$conversation_history.timestamp",
                "status": "completed" # This is a dummy value
            }}
        ]
        messages = await db.customers.aggregate(pipeline).to_list(10)

        return APIResponse(
            success=True,
            message="Recent messages retrieved successfully",
            data={"messages": messages}
        )
    except Exception as e:
        logger.error(f"Error fetching recent messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent messages")

@app.get("/api/metrics", response_model=APIResponse)
@limiter.limit("10/minute")
async def get_metrics(request: Request, _is_auth: bool = Depends(verify_session)):
    """Get application metrics - Protected endpoint"""
    try:
        # Get customer count
        customer_count = await db.customers.count_documents({})
        
        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_customers = await db.customers.count_documents({
            "created_at": {"$gte": yesterday}
        })
        
        # Calculate total conversations
        pipeline = [
            {"$project": {"conversation_count": {"$size": "$conversation_history"}}},
            {"$group": {"_id": None, "total_conversations": {"$sum": "$conversation_count"}}}
        ]
        conversation_result = await db.customers.aggregate(pipeline).to_list(1)
        total_conversations = conversation_result[0]["total_conversations"] if conversation_result else 0
        
        metrics_data = {
            "customers": {
                "total": customer_count,
                "new_24h": recent_customers
            },
            "conversations": {
                "total": total_conversations
            },
            "system": {
                "uptime": "available",
                "ai_models_active": bool(gemini_model or openai_client)
            }
        }
        
        return APIResponse(
            success=True,
            message="Metrics retrieved successfully",
            data=metrics_data
        )
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True
    )