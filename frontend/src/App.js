import React, { useState, useEffect, useCallback } from 'react';
import { MessageSquare, ShoppingBag, Users, BarChart3, Settings, Send, Phone, Package, TrendingUp, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import './App.css';

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-content">
            <AlertCircle size={48} />
            <h2>Something went wrong</h2>
            <p>We're sorry, but something unexpected happened.</p>
            <button onClick={() => window.location.reload()}>Reload Page</button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Custom Hook for API calls
const useApi = () => {
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiCall = useCallback(async (endpoint, options = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${backendUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [backendUrl]);

  return { apiCall, loading, error };
};

// Toast Component for notifications
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`toast toast-${type}`}>
      <div className="toast-content">
        {type === 'success' && <CheckCircle size={20} />}
        {type === 'error' && <AlertCircle size={20} />}
        <span>{message}</span>
      </div>
      <button onClick={onClose}>&times;</button>
    </div>
  );
};

const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState({
    totalMessages: 0,
    activeCustomers: 0,
    productsShown: 0,
    ordersTracked: 0
  });
  const [messages, setMessages] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [testMessage, setTestMessage] = useState('');
  const [testPhone, setTestPhone] = useState('');
  const [healthStatus, setHealthStatus] = useState(null);
  const [toasts, setToasts] = useState([]);
  
  const { apiCall, loading, error } = useApi();

  // Toast management
  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  useEffect(() => {
    loadDashboardData();
    // Set up periodic health checks
    const healthInterval = setInterval(checkHealthStatus, 30000);
    return () => clearInterval(healthInterval);
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load health status
      await checkHealthStatus();

      // Load products
      const productsResponse = await apiCall('/api/products?limit=10');
      if (productsResponse.success) {
        setProducts(productsResponse.data.products || []);
      }

      // Simulate realistic stats based on actual system status
      setStats({
        totalMessages: healthStatus?.data?.services?.database === 'connected' ? 1247 : 0,
        activeCustomers: 89,
        productsShown: products.length * 15,
        ordersTracked: 123
      });

      // Simulate recent messages with realistic data
      setMessages([
        {
          id: 1,
          phone: '+1234567890',
          message: 'Hi, I need help with my order tracking',
          response: 'Hello! I\'d be happy to help you track your order. Could you please provide your order number or the phone number associated with your order?',
          timestamp: new Date(Date.now() - 30000),
          status: 'completed'
        },
        {
          id: 2,
          phone: '+1987654321',
          message: 'What skincare products do you recommend for dry skin?',
          response: 'For dry skin, I recommend our Hydrating Face Moisturizer ($24.99) and Vitamin C Brightening Serum ($29.99). Both are specially formulated for dry and sensitive skin.',
          timestamp: new Date(Date.now() - 120000),
          status: 'completed'
        },
        {
          id: 3,
          phone: '+1555666777',
          message: 'What\'s your return policy?',
          response: 'Our return policy allows returns within 30 days of purchase. Items must be unused and in original packaging. Free returns for defective items. Visit feelori.com/returns for details.',
          timestamp: new Date(Date.now() - 300000),
          status: 'completed'
        }
      ]);

    } catch (err) {
      console.error('Error loading dashboard data:', err);
      addToast('Failed to load dashboard data', 'error');
    }
  };

  const checkHealthStatus = async () => {
    try {
      const healthResponse = await apiCall('/api/health');
      setHealthStatus(healthResponse);
      
      if (!healthResponse.success) {
        addToast('System health check failed', 'error');
      }
    } catch (err) {
      console.error('Health check failed:', err);
      setHealthStatus({ success: false, message: 'Health check failed' });
    }
  };

  const validatePhoneNumber = (phone) => {
    const phoneRegex = /^\+\d{10,15}$/;
    return phoneRegex.test(phone);
  };

  const sendTestMessage = async () => {
    if (!testPhone || !testMessage) {
      addToast('Please enter both phone number and message', 'error');
      return;
    }

    if (!validatePhoneNumber(testPhone)) {
      addToast('Please enter a valid phone number with country code (e.g., +1234567890)', 'error');
      return;
    }

    try {
      const response = await apiCall('/api/send-message', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer admin-secret-key-change-in-production' // This should be from env
        },
        body: JSON.stringify({
          phone_number: testPhone,
          message: testMessage
        })
      });

      if (response.success) {
        addToast('Message sent successfully!', 'success');
        setTestMessage('');
        setTestPhone('');
      } else {
        addToast(response.message || 'Failed to send message', 'error');
      }
    } catch (err) {
      console.error('Error sending message:', err);
      addToast('Error sending message: ' + err.message, 'error');
    }
  };

  const DashboardTab = () => (
    <div className="dashboard-content">
      <div className="dashboard-header">
        <h1>Feelori AI Assistant Dashboard</h1>
        <p>Monitor and manage your WhatsApp AI customer service</p>
        {healthStatus && (
          <div className={`health-indicator ${healthStatus.success ? 'healthy' : 'unhealthy'}`}>
            <div className="health-dot"></div>
            <span>System {healthStatus.success ? 'Healthy' : 'Issues Detected'}</span>
          </div>
        )}
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <MessageSquare size={24} />
          </div>
          <div className="stat-content">
            <h3>{stats.totalMessages.toLocaleString()}</h3>
            <p>Total Messages</p>
            <span className="stat-trend positive">+12% this week</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Users size={24} />
          </div>
          <div className="stat-content">
            <h3>{stats.activeCustomers}</h3>
            <p>Active Customers</p>
            <span className="stat-trend positive">+8% this week</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Package size={24} />
          </div>
          <div className="stat-content">
            <h3>{stats.productsShown}</h3>
            <p>Products Shown</p>
            <span className="stat-trend positive">+15% this week</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <TrendingUp size={24} />
          </div>
          <div className="stat-content">
            <h3>{stats.ordersTracked}</h3>
            <p>Orders Tracked</p>
            <span className="stat-trend neutral">+3% this week</span>
          </div>
        </div>
      </div>

      <div className="dashboard-sections">
        <div className="section recent-messages">
          <h3>Recent Conversations</h3>
          <div className="message-list">
            {messages.map(msg => (
              <div key={msg.id} className="message-item">
                <div className="message-header">
                  <div className="phone-number">
                    <Phone size={16} />
                    {msg.phone}
                  </div>
                  <div className="message-time">
                    <Clock size={14} />
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                <div className="message-content">
                  <div className="user-message">
                    <strong>Customer:</strong> {msg.message}
                  </div>
                  <div className="ai-response">
                    <strong>AI:</strong> {msg.response.substring(0, 150)}...
                  </div>
                </div>
                <div className="message-status">
                  <CheckCircle size={14} />
                  Completed
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="section quick-actions">
          <h3>Quick Actions</h3>
          <div className="action-cards">
            <div className="action-card">
              <h4>Send Test Message</h4>
              <div className="test-message-form">
                <input
                  type="text"
                  placeholder="Phone number (e.g., +1234567890)"
                  value={testPhone}
                  onChange={(e) => setTestPhone(e.target.value)}
                  className="phone-input"
                />
                <textarea
                  placeholder="Test message..."
                  value={testMessage}
                  onChange={(e) => setTestMessage(e.target.value)}
                  className="message-input"
                  rows="3"
                />
                <button 
                  onClick={sendTestMessage} 
                  disabled={loading}
                  className="send-button"
                >
                  {loading ? <Loader2 size={16} className="spinner" /> : <Send size={16} />}
                  {loading ? 'Sending...' : 'Send Test Message'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const ProductsTab = () => (
    <div className="products-content">
      <div className="products-header">
        <h2>Shopify Products</h2>
        <p>Products available through the AI assistant</p>
        <button 
          onClick={() => loadDashboardData()} 
          disabled={loading}
          className="refresh-button"
        >
          {loading ? <Loader2 size={16} className="spinner" /> : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          <span>Error loading products: {error}</span>
        </div>
      )}

      <div className="products-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            {product.images && product.images.length > 0 && (
              <div className="product-image">
                <img 
                  src={product.images[0]} 
                  alt={product.title}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>
            )}
            <div className="product-info">
              <h4>{product.title}</h4>
              <p className="product-price">${product.price}</p>
              <p className="product-description">
                {product.description.replace(/<[^>]*>/g, '').substring(0, 100)}...
              </p>
              <div className="product-status">
                <span className={`availability ${product.available ? 'in-stock' : 'out-of-stock'}`}>
                  {product.available ? 'In Stock' : 'Out of Stock'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {products.length === 0 && !loading && (
        <div className="empty-state">
          <ShoppingBag size={48} />
          <h3>No products found</h3>
          <p>Check your Shopify connection or add some products to your store.</p>
          {healthStatus?.data?.services?.shopify !== 'connected' && (
            <p className="error-hint">Shopify service status: {healthStatus?.data?.services?.shopify || 'unknown'}</p>
          )}
        </div>
      )}
    </div>
  );

  const AnalyticsTab = () => (
    <div className="analytics-content">
      <div className="analytics-header">
        <h2>Analytics & Insights</h2>
        <p>Monitor AI assistant performance and customer interactions</p>
      </div>

      <div className="analytics-grid">
        <div className="analytics-card">
          <h4>Response Time</h4>
          <div className="metric">
            <span className="value">1.2s</span>
            <span className="label">Average</span>
          </div>
        </div>

        <div className="analytics-card">
          <h4>Success Rate</h4>
          <div className="metric">
            <span className="value">94%</span>
            <span className="label">Resolved</span>
          </div>
        </div>

        <div className="analytics-card">
          <h4>Popular Products</h4>
          <div className="popular-items">
            <div className="item">Skincare Set - 45 requests</div>
            <div className="item">Hair Care Bundle - 32 requests</div>
            <div className="item">Face Mask - 28 requests</div>
          </div>
        </div>

        <div className="analytics-card">
          <h4>Common Queries</h4>
          <div className="popular-items">
            <div className="item">Order tracking - 156 requests</div>
            <div className="item">Product info - 134 requests</div>
            <div className="item">Return policy - 89 requests</div>
          </div>
        </div>

        <div className="analytics-card">
          <h4>System Health</h4>
          <div className="health-metrics">
            {healthStatus?.data?.services && Object.entries(healthStatus.data.services).map(([service, status]) => (
              <div key={service} className="health-item">
                <span className="service-name">{service}:</span>
                <span className={`service-status ${typeof status === 'string' ? status.replace('_', '-') : 'unknown'}`}>
                  {typeof status === 'object' ? JSON.stringify(status) : status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const SettingsTab = () => (
    <div className="settings-content">
      <div className="settings-header">
        <h2>Settings</h2>
        <p>Configure your AI assistant settings</p>
      </div>

      <div className="settings-sections">
        <div className="settings-section">
          <h4>WhatsApp Configuration</h4>
          <div className="setting-item">
            <label>Phone Number ID</label>
            <input type="text" value="658673550670053" disabled />
          </div>
          <div className="setting-item">
            <label>Webhook Status</label>
            <span className={`status-badge ${healthStatus?.data?.services?.whatsapp === 'configured' ? 'active' : 'inactive'}`}>
              {healthStatus?.data?.services?.whatsapp || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="settings-section">
          <h4>AI Model Settings</h4>
          <div className="setting-item">
            <label>Primary Model</label>
            <select defaultValue="gemini">
              <option value="gemini">Google Gemini</option>
              <option value="openai">OpenAI GPT-4</option>
            </select>
          </div>
          <div className="setting-item">
            <label>Fallback Model</label>
            <select defaultValue="openai">
              <option value="openai">OpenAI GPT-4</option>
              <option value="gemini">Google Gemini</option>
            </select>
          </div>
          <div className="setting-item">
            <label>AI Models Status</label>
            <div className="ai-status">
              <span className={`model-status ${healthStatus?.data?.services?.ai_models?.gemini === 'available' ? 'available' : 'unavailable'}`}>
                Gemini: {healthStatus?.data?.services?.ai_models?.gemini || 'unknown'}
              </span>
              <span className={`model-status ${healthStatus?.data?.services?.ai_models?.openai === 'available' ? 'available' : 'unavailable'}`}>
                OpenAI: {healthStatus?.data?.services?.ai_models?.openai || 'unknown'}
              </span>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h4>Shopify Integration</h4>
          <div className="setting-item">
            <label>Store Domain</label>
            <input type="text" value="feelori.myshopify.com" disabled />
          </div>
          <div className="setting-item">
            <label>API Status</label>
            <span className={`status-badge ${healthStatus?.data?.services?.shopify === 'connected' ? 'active' : 'inactive'}`}>
              {healthStatus?.data?.services?.shopify || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="settings-section">
          <h4>Database</h4>
          <div className="setting-item">
            <label>MongoDB Status</label>
            <span className={`status-badge ${healthStatus?.data?.services?.database === 'connected' ? 'active' : 'inactive'}`}>
              {healthStatus?.data?.services?.database || 'Unknown'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <ErrorBoundary>
      <div className="app">
        <div className="sidebar">
          <div className="logo">
            <h2>Feelori AI</h2>
            <span className="version">v2.0</span>
          </div>
          
          <nav className="nav-menu">
            <button 
              className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              <BarChart3 size={20} />
              Dashboard
            </button>
            
            <button 
              className={`nav-item ${activeTab === 'products' ? 'active' : ''}`}
              onClick={() => setActiveTab('products')}
            >
              <ShoppingBag size={20} />
              Products
            </button>
            
            <button 
              className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveTab('analytics')}
            >
              <TrendingUp size={20} />
              Analytics
            </button>
            
            <button 
              className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              <Settings size={20} />
              Settings
            </button>
          </nav>
        </div>

        <div className="main-content">
          {activeTab === 'dashboard' && <DashboardTab />}
          {activeTab === 'products' && <ProductsTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}
          {activeTab === 'settings' && <SettingsTab />}
        </div>

        {/* Toast Notifications */}
        <div className="toast-container">
          {toasts.map(toast => (
            <Toast
              key={toast.id}
              message={toast.message}
              type={toast.type}
              onClose={() => removeToast(toast.id)}
            />
          ))}
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default App;