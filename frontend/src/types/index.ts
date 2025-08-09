// frontend/src/types/index.ts - IMPROVED VERSION
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  timestamp: string;
  version?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user_id?: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  uptime?: number;
  services?: {
    database?: 'connected' | 'disconnected' | 'error';
    whatsapp?: 'connected' | 'not_configured' | 'error';
    shopify?: 'connected' | 'not_configured' | 'error';
    ai_models?: {
      gemini?: 'available' | 'not_available' | 'error';
      openai?: 'available' | 'not_available' | 'error';
    };
  };
}

export interface DashboardStats {
  customers: {
    total: number;
    active_24h: number;
    active_percentage: number;
  };
  messages: {
    total_24h: number;
    avg_per_customer: number;
  };
  system: {
    database_status: string;
    cache_status: string;
    queue_size: number;
  };
  uptime: number;
}

export interface Customer {
  _id: string;
  id: string;
  phone_number: string;
  created_at: string;
  conversation_history: ConversationMessage[];
  preferences: Record<string, any>;
  last_interaction: string;
  total_messages: number;
  is_active?: boolean;
  metadata?: Record<string, any>;
}

export interface ConversationMessage {
  timestamp: string;
  message: string;
  response: string;
  message_id: string;
  message_type?: 'text' | 'image' | 'document' | 'voice';
  status?: 'sent' | 'delivered' | 'read' | 'failed';
}

export interface Product {
  id: string;
  title: string;
  description: string;
  price: number;
  images: string[];
  available: boolean; // Fixed: was inconsistent with availability
  tags: string[];
  variants?: ProductVariant[];
  created_at?: string;
  updated_at?: string;
}

export interface ProductVariant {
  id: string;
  title: string;
  price: number;
  available: boolean;
  inventory_quantity?: number;
  sku?: string;
}

export interface CustomersResponse {
  customers: Customer[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ProductsResponse {
  products: Product[];
  total: number;
  page: number;
  limit: number;
}

export interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

export type TabType = 'dashboard' | 'products' | 'analytics' | 'settings';

// API Error types
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
  timestamp: string;
}

// Settings types
export interface SystemSettings {
  primaryModel: 'gemini' | 'openai';
  fallbackModel: 'gemini' | 'openai';
  responseTimeout: number;
  autoFallback: boolean;
  logLevel: 'debug' | 'info' | 'warning' | 'error';
  rateLimitEnabled: boolean;
  maintenanceMode: boolean;
}