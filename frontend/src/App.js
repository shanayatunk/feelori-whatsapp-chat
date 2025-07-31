import React, { useState, useEffect } from 'react';
import { MessageSquare, ShoppingBag, Users, BarChart3, Settings, Send, Phone, Package, TrendingUp, Clock, CheckCircle } from 'lucide-react';
import './App.css';

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
  const [loading, setLoading] = useState(false);
  const [testMessage, setTestMessage] = useState('');
  const [testPhone, setTestPhone] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load products
      const productsResponse = await fetch(`${backendUrl}/api/products?limit=10`);
      const productsData = await productsResponse.json();
      setProducts(productsData.products || []);

      // Simulate stats (in real implementation, these would come from the backend)
      setStats({
        totalMessages: 1247,
        activeCustomers: 89,
        productsShown: 456,
        ordersTracked: 123
      });

      // Simulate recent messages
      setMessages([
        {
          id: 1,
          phone: '+1234567890',
          message: 'Hi, I need help with my order',
          response: 'Hello! I\'d be happy to help you track your order. Could you please provide your order number?',
          timestamp: new Date(Date.now() - 30000),
          status: 'completed'
        },
        {
          id: 2,
          phone: '+1987654321',
          message: 'Show me your skincare products',
          response: 'Here are our popular skincare products: Vitamin C Serum ($29.99), Retinol Cream ($39.99), Hydrating Moisturizer ($24.99)...',
          timestamp: new Date(Date.now() - 120000),
          status: 'completed'
        },
        {
          id: 3,
          phone: '+1555666777',
          message: 'What are your return policies?',
          response: 'Our return policy allows returns within 30 days of purchase. Items must be unused and in original packaging...',
          timestamp: new Date(Date.now() - 300000),
          status: 'completed'
        }
      ]);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendTestMessage = async () => {
    if (!testPhone || !testMessage) {
      alert('Please enter both phone number and message');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: testPhone,
          message: testMessage
        })
      });

      const result = await response.json();
      
      if (result.success) {
        alert('Message sent successfully!');
        setTestMessage('');
        setTestPhone('');
      } else {
        alert('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Error sending message');
    } finally {
      setLoading(false);
    }
  };

  const DashboardTab = () => (
    <div className="dashboard-content">
      <div className="dashboard-header">
        <h1>Feelori AI Assistant Dashboard</h1>
        <p>Monitor and manage your WhatsApp AI customer service</p>
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
                    <strong>AI:</strong> {msg.response.substring(0, 100)}...
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
                  placeholder="Phone number (with country code)"
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
                  <Send size={16} />
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
      </div>

      <div className="products-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            {product.images && product.images.length > 0 && (
              <div className="product-image">
                <img src={product.images[0]} alt={product.title} />
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

      {products.length === 0 && (
        <div className="empty-state">
          <ShoppingBag size={48} />
          <h3>No products found</h3>
          <p>Check your Shopify connection or add some products to your store.</p>
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
            <span className="status-badge active">Active</span>
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
        </div>

        <div className="settings-section">
          <h4>Shopify Integration</h4>
          <div className="setting-item">
            <label>Store Domain</label>
            <input type="text" value="feelori.myshopify.com" disabled />
          </div>
          <div className="setting-item">
            <label>API Status</label>
            <span className="status-badge active">Connected</span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="app">
      <div className="sidebar">
        <div className="logo">
          <h2>Feelori AI</h2>
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
    </div>
  );
};

export default App;