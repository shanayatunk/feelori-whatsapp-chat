export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  timestamp: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  services: {
    database: string;
    shopify: string;
    whatsapp: string;
    ai_models: {
      gemini: string;
      openai: string;
    };
  };
}

export interface Product {
  id: string;
  title: string;
  handle: string;
  description: string;
  price: string;
  images: string[];
  variants: any[];
  tags: string[];
  available: boolean;
}

export interface Customer {
  id: string;
  phone_number: string;
  name?: string;
  email?: string;
  created_at: string;
  conversation_history: ConversationMessage[];
  preferences: Record<string, any>;
}

export interface ConversationMessage {
  timestamp: string;
  user_message: string;
  ai_response: string;
}

export interface Order {
  id: string;
  order_number: string;
  financial_status: string;
  total_price: string;
  created_at: string;
  line_items: any[];
}

export interface DashboardStats {
  totalMessages: number;
  activeCustomers: number;
  productsShown: number;
  ordersTracked: number;
}

export interface RecentMessage {
  id: number;
  phone: string;
  message: string;
  response: string;
  timestamp: Date;
  status: 'completed' | 'pending' | 'failed';
}

export interface SendMessageRequest {
  phone_number: string;
  message: string;
}

export interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

export type TabType = 'dashboard' | 'products' | 'analytics' | 'settings';