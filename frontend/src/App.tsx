import React, { useState } from 'react';
import { MessageSquare, Users, Package, TrendingUp, Settings, BarChart3, ShoppingBag, Phone, Clock, CheckCircle, Send } from 'lucide-react';

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState('dashboard');

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'products', label: 'Products', icon: ShoppingBag },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const stats = [
    { label: 'Total Messages', value: '1,247', icon: MessageSquare, change: '+12%', color: 'bg-green-500/20 text-green-400' },
    { label: 'Active Customers', value: '89', icon: Users, change: '+8%', color: 'bg-green-500/20 text-green-400' },
    { label: 'Products Shown', value: '456', icon: Package, change: '+15%', color: 'bg-green-500/20 text-green-400' },
    { label: 'Orders Tracked', value: '123', icon: TrendingUp, change: '+3%', color: 'bg-yellow-500/20 text-yellow-400' },
  ];

  const recentMessages = [
    {
      id: 1,
      phone: '+1234567890',
      message: 'Hi, I need help with tracking my recent order. Can you provide an update?',
      response: 'Hello! I\'d be happy to help you track your order. Could you please provide your order number?',
      timestamp: '2 min ago',
      status: 'completed'
    },
    {
      id: 2,
      phone: '+1987654321',
      message: 'What skincare products do you recommend for sensitive skin?',
      response: 'For sensitive skin, I recommend our Gentle Hydrating Moisturizer ($24.99) and Vitamin C Serum ($29.99).',
      timestamp: '5 min ago',
      status: 'completed'
    }
  ];

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-feelori-primary via-feelori-primary/80 to-feelori-secondary">
      {/* Sidebar */}
      <aside className="w-80 bg-white/10 backdrop-blur-lg border-r border-white/20">
        <div className="p-6">
          {/* Logo */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white">Feelori AI</h2>
              <span className="text-sm text-white/60 bg-white/10 px-2 py-1 rounded-md">v2.0</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-200 hover:bg-white/10 hover:transform hover:translate-x-1 ${
                    isActive ? 'bg-feelori-primary text-white shadow-lg' : 'text-white/80 hover:text-white'
                  }`}
                >
                  <Icon size={20} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-y-auto bg-white/5 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold text-white bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
              Feelori AI Assistant Dashboard
            </h1>
            <p className="text-white/80 text-lg">Monitor and manage your WhatsApp AI customer service</p>
            
            {/* Health Indicator */}
            <div className="flex items-center justify-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-white/90 font-medium">System Healthy</span>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div key={index} className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-300 hover:transform hover:scale-[1.02] hover:shadow-2xl">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-feelori-primary/20 rounded-xl">
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-white">{stat.value}</p>
                      <p className="text-white/70 text-sm">{stat.label}</p>
                      <span className={`mt-1 px-2 py-1 rounded text-xs ${stat.color} border border-current/30`}>
                        {stat.change} this week
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Recent Conversations */}
            <div className="lg:col-span-2">
              <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-300">
                <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Recent Conversations
                </h3>
                <div className="space-y-4">
                  {recentMessages.map((message) => (
                    <div key={message.id} className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                          <Phone className="w-4 h-4 text-feelori-primary" />
                          <span className="text-white font-medium text-sm">{message.phone}</span>
                        </div>
                        <div className="flex items-center gap-2 text-white/60 text-xs">
                          <Clock className="w-3 h-3" />
                          {message.timestamp}
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="text-white/90 text-sm">
                          <strong className="text-feelori-accent">Customer:</strong> {message.message}
                        </div>
                        <div className="text-white/80 text-sm">
                          <strong className="text-green-400">AI:</strong> {message.response}
                        </div>
                      </div>
                      
                      <div className="flex justify-end mt-3">
                        <span className="bg-green-500/20 text-green-400 border border-green-500/30 px-2 py-1 rounded text-xs flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          {message.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-300">
                <h3 className="text-xl font-semibold text-white mb-6">Quick Actions</h3>
                <div className="space-y-4">
                  <h4 className="text-white font-semibold">Send Test Message</h4>
                  
                  <input
                    type="text"
                    placeholder="Phone number (e.g., +1234567890)"
                    className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-feelori-primary focus:border-transparent transition-all duration-200"
                  />
                  
                  <textarea
                    placeholder="Test message..."
                    rows={3}
                    className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-feelori-primary focus:border-transparent transition-all duration-200 resize-none"
                  />
                  
                  <button className="w-full bg-feelori-primary hover:bg-feelori-dark text-white font-semibold py-3 px-4 rounded-xl transition-all duration-200 hover:shadow-lg hover:scale-105 active:scale-95 flex items-center justify-center gap-2">
                    <Send className="w-4 h-4" />
                    Send Test Message
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;