import React, { useState, useEffect } from 'react';
import { MessageSquare, Users, Package, TrendingUp, Phone, Clock, CheckCircle, Send, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useHealthCheck, useSendMessage } from '@/hooks/useApi';
import { useToast } from '@/hooks/useToast';
import { formatRelativeTime, validatePhoneNumber } from '@/lib/utils';
import { DashboardStats, RecentMessage, HealthStatus } from '@/types';

const DashboardTab: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalMessages: 1247,
    activeCustomers: 89,
    productsShown: 456,
    ordersTracked: 123,
  });

  const [messages, setMessages] = useState<RecentMessage[]>([
    {
      id: 1,
      phone: '+1234567890',
      message: 'Hi, I need help with tracking my recent order. Can you provide an update?',
      response: 'Hello! I\'d be happy to help you track your order. Could you please provide your order number or the email address associated with your purchase?',
      timestamp: new Date(Date.now() - 30000),
      status: 'completed'
    },
    {
      id: 2,
      phone: '+1987654321',
      message: 'What skincare products do you recommend for sensitive skin?',
      response: 'For sensitive skin, I recommend our Gentle Hydrating Moisturizer ($24.99) and Vitamin C Serum ($29.99). Both are formulated without harsh chemicals and are dermatologist-tested.',
      timestamp: new Date(Date.now() - 120000),
      status: 'completed'
    },
    {
      id: 3,
      phone: '+1555666777',
      message: 'What is your return policy for skincare products?',
      response: 'Our return policy allows returns within 30 days of purchase. Items must be unused and in original packaging. We offer free returns for any defective products. Visit feelori.com/returns for more details.',
      timestamp: new Date(Date.now() - 300000),
      status: 'completed'
    }
  ]);

  const [testPhone, setTestPhone] = useState('');
  const [testMessage, setTestMessage] = useState('');
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);

  const { checkHealth, loading: healthLoading } = useHealthCheck();
  const { sendMessage, loading: messageLoading } = useSendMessage();
  const { success, error } = useToast();

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await checkHealth();
        if (response.success && response.data) {
          setHealthStatus(response.data);
        }
      } catch (err) {
        console.error('Health check failed:', err);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [checkHealth]);

  const handleSendTestMessage = async () => {
    if (!testPhone || !testMessage) {
      error('Please enter both phone number and message');
      return;
    }

    if (!validatePhoneNumber(testPhone)) {
      error('Please enter a valid phone number with country code (e.g., +1234567890)');
      return;
    }

    try {
      const apiKey = 'feelori-admin-2024-secure-key-change-in-production'; // In production, get from secure storage
      await sendMessage(testPhone, testMessage, apiKey);
      success('Message sent successfully!');
      setTestPhone('');
      setTestMessage('');
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to send message');
    }
  };

  const getHealthIndicatorColor = (status?: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'unhealthy':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold feelori-gradient-text">
          Feelori AI Assistant Dashboard
        </h1>
        <p className="text-white/80 text-lg">
          Monitor and manage your WhatsApp AI customer service
        </p>
        
        {/* Health Indicator */}
        {healthStatus && (
          <div className="flex items-center justify-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getHealthIndicatorColor(healthStatus.status)}`} />
            <span className="text-white/90 font-medium">
              System {healthStatus.status || 'Unknown'}
            </span>
            {healthLoading && <Loader2 className="w-4 h-4 animate-spin text-white/60" />}
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <Card className="card-feelori">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-feelori-primary/20 rounded-xl">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {stats.totalMessages.toLocaleString()}
                </p>
                <p className="text-white/70 text-sm">Total Messages</p>
                <Badge className="mt-1 bg-green-500/20 text-green-400 border-green-500/30">
                  +12% this week
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-feelori">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-feelori-primary/20 rounded-xl">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{stats.activeCustomers}</p>
                <p className="text-white/70 text-sm">Active Customers</p>
                <Badge className="mt-1 bg-green-500/20 text-green-400 border-green-500/30">
                  +8% this week
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-feelori">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-feelori-primary/20 rounded-xl">
                <Package className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{stats.productsShown}</p>
                <p className="text-white/70 text-sm">Products Shown</p>
                <Badge className="mt-1 bg-green-500/20 text-green-400 border-green-500/30">
                  +15% this week
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-feelori">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-feelori-primary/20 rounded-xl">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{stats.ordersTracked}</p>
                <p className="text-white/70 text-sm">Orders Tracked</p>
                <Badge className="mt-1 bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
                  +3% this week
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Conversations */}
        <div className="lg:col-span-2">
          <Card className="card-feelori">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Recent Conversations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {messages.map((message) => (
                <div key={message.id} className="p-4 bg-white/5 rounded-xl border border-white/10">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-feelori-primary" />
                      <span className="text-white font-medium text-sm">{message.phone}</span>
                    </div>
                    <div className="flex items-center gap-2 text-white/60 text-xs">
                      <Clock className="w-3 h-3" />
                      {formatRelativeTime(message.timestamp)}
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
                    <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      {message.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <Card className="card-feelori">
            <CardHeader>
              <CardTitle className="text-white">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <h4 className="text-white font-semibold">Send Test Message</h4>
                
                <Input
                  placeholder="Phone number (e.g., +1234567890)"
                  value={testPhone}
                  onChange={(e) => setTestPhone(e.target.value)}
                  className="input-feelori"
                />
                
                <Textarea
                  placeholder="Test message..."
                  value={testMessage}
                  onChange={(e) => setTestMessage(e.target.value)}
                  className="input-feelori resize-none"
                  rows={3}
                />
                
                <Button
                  onClick={handleSendTestMessage}
                  disabled={messageLoading}
                  className="w-full btn-feelori"
                >
                  {messageLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4 mr-2" />
                  )}
                  {messageLoading ? 'Sending...' : 'Send Test Message'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DashboardTab;