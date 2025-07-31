from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import httpx
import json
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import google.generativeai as genai
from openai import AsyncOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Feelori AI WhatsApp Assistant", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
db = client.feelori_assistant

# AI Models Configuration - Initialize lazily
# Models are now initialized within the generate_ai_response function to handle missing API keys gracefully

# WhatsApp Business API Configuration
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"

# Shopify Configuration
SHOPIFY_STORE_URL = os.environ.get("SHOPIFY_STORE_URL", "feelori.myshopify.com")
SHOPIFY_ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01"

# Models
class WhatsAppMessage(BaseModel):
    from_number: str
    message_text: str
    message_id: str
    timestamp: str

class WebhookEntry(BaseModel):
    id: str
    changes: List[Dict[str, Any]]

class WebhookData(BaseModel):
    object: str
    entry: List[WebhookEntry]

class Customer(BaseModel):
    id: str = None
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = None
    conversation_history: List[Dict] = []
    preferences: Dict = {}

class Product(BaseModel):
    id: str
    title: str
    handle: str
    description: str
    price: str
    images: List[str] = []
    variants: List[Dict] = []
    tags: List[str] = []
    available: bool = True

# Helper Functions
async def get_database():
    return db

async def send_whatsapp_message(to_number: str, message: str) -> bool:
    """Send message via WhatsApp Business API"""
    try:
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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(WHATSAPP_API_URL, headers=headers, json=payload)
            
        if response.status_code == 200:
            logger.info(f"Message sent successfully to {to_number}")
            return True
        else:
            logger.error(f"Failed to send message: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return False

async def get_shopify_products(query: str = "", limit: int = 10) -> List[Product]:
    """Fetch products from Shopify"""
    try:
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        
        params = {
            "limit": limit,
        }
        
        if query:
            params["title"] = query
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SHOPIFY_API_URL}/products.json",
                headers=headers,
                params=params
            )
        
        if response.status_code == 200:
            data = response.json()
            products = []
            
            for product_data in data.get("products", []):
                # Get the first variant for pricing
                variants = product_data.get("variants", [])
                price = variants[0].get("price", "0.00") if variants else "0.00"
                
                product = Product(
                    id=str(product_data["id"]),
                    title=product_data["title"],
                    handle=product_data["handle"],
                    description=product_data.get("body_html", ""),
                    price=price,
                    images=[img["src"] for img in product_data.get("images", [])],
                    variants=variants,
                    tags=product_data.get("tags", "").split(",") if product_data.get("tags") else [],
                    available=any(v.get("inventory_quantity", 0) > 0 for v in variants) if variants else False
                )
                products.append(product)
            
            return products
        else:
            logger.error(f"Failed to fetch Shopify products: {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching Shopify products: {str(e)}")
        return []

async def get_shopify_order(order_id: str) -> Optional[Dict]:
    """Get order details from Shopify"""
    try:
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SHOPIFY_API_URL}/orders/{order_id}.json",
                headers=headers
            )
        
        if response.status_code == 200:
            return response.json()["order"]
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error fetching order: {str(e)}")
        return None

async def search_orders_by_phone(phone_number: str) -> List[Dict]:
    """Search orders by phone number"""
    try:
        headers = {
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        
        # Clean phone number for search
        clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SHOPIFY_API_URL}/orders.json",
                headers=headers,
                params={"status": "any", "limit": 50}
            )
        
        if response.status_code == 200:
            orders = response.json()["orders"]
            matching_orders = []
            
            for order in orders:
                # Check billing or shipping phone
                billing_phone = order.get("billing_address", {}).get("phone", "")
                shipping_phone = order.get("shipping_address", {}).get("phone", "")
                
                if (clean_phone in billing_phone.replace("+", "").replace("-", "").replace(" ", "") or
                    clean_phone in shipping_phone.replace("+", "").replace("-", "").replace(" ", "")):
                    matching_orders.append(order)
            
            return matching_orders
        else:
            return []
            
    except Exception as e:
        logger.error(f"Error searching orders: {str(e)}")
        return []

async def get_or_create_customer(phone_number: str) -> Customer:
    """Get or create customer in database"""
    customer_data = await db.customers.find_one({"phone_number": phone_number})
    
    if customer_data:
        return Customer(**customer_data)
    else:
        new_customer = Customer(
            id=str(uuid.uuid4()),
            phone_number=phone_number,
            created_at=datetime.utcnow(),
            conversation_history=[],
            preferences={}
        )
        
        await db.customers.insert_one(new_customer.dict())
        return new_customer

async def update_conversation_history(phone_number: str, message: str, response: str):
    """Update customer conversation history"""
    await db.customers.update_one(
        {"phone_number": phone_number},
        {
            "$push": {
                "conversation_history": {
                    "timestamp": datetime.utcnow(),
                    "user_message": message,
                    "ai_response": response
                }
            }
        }
    )

async def generate_ai_response(message: str, customer: Customer, context: Dict = None) -> str:
    """Generate AI response using Gemini with OpenAI fallback"""
    
    # Get AI models lazily
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    gemini_model = None
    openai_client = None
    
    if gemini_key:
        genai.configure(api_key=gemini_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
    if openai_key:
        openai_client = AsyncOpenAI(api_key=openai_key)
    
    # Build context for AI
    conversation_context = ""
    if customer.conversation_history:
        recent_history = customer.conversation_history[-3:]  # Last 3 exchanges
        for conv in recent_history:
            conversation_context += f"User: {conv['user_message']}\nAI: {conv['ai_response']}\n"
    
    # Build product context if available
    product_context = ""
    if context and context.get("products"):
        product_context = "\nAvailable products:\n"
        for product in context["products"][:5]:  # Limit to 5 products
            product_context += f"- {product.title}: ${product.price} - {product.description[:100]}...\n"
    
    # Build order context if available
    order_context = ""
    if context and context.get("orders"):
        order_context = "\nCustomer's recent orders:\n"
        for order in context["orders"][:3]:  # Last 3 orders
            order_context += f"- Order #{order['order_number']}: {order['financial_status']} - ${order['total_price']}\n"
    
    # Create the prompt
    system_prompt = f"""You are Feelori's AI customer service assistant. You're helpful, friendly, and knowledgeable about Feelori's products.

IMPORTANT GUIDELINES:
- Always be warm and professional
- Help customers find products, track orders, and answer questions
- If you don't know something specific, politely say so and offer to connect them with human support
- For product recommendations, be specific about features and benefits
- Keep responses concise but informative
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
            return response.text
        else:
            raise Exception("Gemini model not available")
        
    except Exception as e:
        logger.warning(f"Gemini failed, trying OpenAI: {str(e)}")
        
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
                return response.choices[0].message.content
            else:
                raise Exception("OpenAI client not available")
            
        except Exception as e2:
            logger.error(f"Both AI models failed: {str(e2)}")
            return "I'm sorry, I'm having technical difficulties right now. Please try again in a moment, or contact our human support team for immediate assistance."

async def process_message(phone_number: str, message: str) -> str:
    """Process incoming message and generate response"""
    customer = await get_or_create_customer(phone_number)
    
    # Analyze message intent
    message_lower = message.lower()
    context = {}
    
    # Product search intent
    if any(word in message_lower for word in ["product", "item", "buy", "purchase", "show", "looking for", "need", "want"]):
        # Extract potential product keywords
        keywords = message_lower
        products = await get_shopify_products(query=keywords, limit=5)
        context["products"] = products
    
    # Order tracking intent
    elif any(word in message_lower for word in ["order", "tracking", "delivery", "shipping", "status"]):
        orders = await search_orders_by_phone(phone_number)
        context["orders"] = orders
    
    # General product browsing
    elif any(word in message_lower for word in ["hello", "hi", "help", "browse", "catalog"]):
        products = await get_shopify_products(limit=5)
        context["products"] = products
    
    # Generate AI response
    response = await generate_ai_response(message, customer, context)
    
    # Update conversation history
    await update_conversation_history(phone_number, message, response)
    
    return response

# Routes
@app.get("/")
async def root():
    return {"message": "Feelori AI WhatsApp Assistant", "status": "running"}

@app.get("/api/webhook")
async def verify_webhook(request: Request):
    """Webhook verification for WhatsApp"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return int(challenge)
    else:
        logger.warning("Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/api/webhook")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"Received webhook: {data}")
        
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        
                        # Process incoming messages
                        for message in value.get("messages", []):
                            from_number = message.get("from")
                            message_text = message.get("text", {}).get("body", "")
                            message_id = message.get("id")
                            
                            if from_number and message_text:
                                logger.info(f"Processing message from {from_number}: {message_text}")
                                
                                # Process message and generate response
                                response = await process_message(from_number, message_text)
                                
                                # Send response back
                                await send_whatsapp_message(from_number, response)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/api/products")
async def get_products(query: str = "", limit: int = 10):
    """Get products from Shopify"""
    products = await get_shopify_products(query=query, limit=limit)
    return {"products": [product.dict() for product in products]}

@app.get("/api/orders/{phone_number}")
async def get_customer_orders(phone_number: str):
    """Get orders for a customer by phone number"""
    orders = await search_orders_by_phone(phone_number)
    return {"orders": orders}

@app.get("/api/customers/{phone_number}")
async def get_customer(phone_number: str):
    """Get customer information"""
    customer = await get_or_create_customer(phone_number)
    return customer.dict()

@app.post("/api/send-message")
async def send_message(data: dict):
    """Send a message via WhatsApp API"""
    phone_number = data.get("phone_number")
    message = data.get("message")
    
    if not phone_number or not message:
        raise HTTPException(status_code=400, detail="Phone number and message required")
    
    success = await send_whatsapp_message(phone_number, message)
    return {"success": success}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db.customers.count_documents({})
        
        # Test Shopify API
        products = await get_shopify_products(limit=1)
        
        return {
            "status": "healthy",
            "database": "connected",
            "shopify": "connected" if products else "error",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",  
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)