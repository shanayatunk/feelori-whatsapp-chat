import React from 'react';
import { BarChart3, Clock, CheckCircle2, TrendingUp, Users, MessageSquare, Package, Star } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const AnalyticsTab: React.FC = () => {
  const performanceMetrics = [
    {
      title: 'Average Response Time',
      value: '1.2s',
      trend: '+5% faster',
      trendPositive: true,
      icon: Clock,
    },
    {
      title: 'Success Rate',
      value: '94%',
      trend: '+2% this month',
      trendPositive: true,
      icon: CheckCircle2,
    },
    {
      title: 'Customer Satisfaction',
      value: '4.8/5',
      trend: '+0.2 this month',
      trendPositive: true,
      icon: Star,
    },
    {
      title: 'Daily Active Users',
      value: '156',
      trend: '+12% this week',
      trendPositive: true,
      icon: Users,
    },
  ];

  const popularProducts = [
    { name: 'Vitamin C Serum', requests: 45, trend: '+15%' },
    { name: 'Hydrating Moisturizer', requests: 32, trend: '+8%' },
    { name: 'Retinol Night Cream', requests: 28, trend: '+12%' },
    { name: 'Gentle Cleanser', requests: 24, trend: '+6%' },
    { name: 'SPF 50 Sunscreen', requests: 19, trend: '+22%' },
  ];

  const commonQueries = [
    { query: 'Order tracking', count: 156, percentage: 28 },
    { query: 'Product information', count: 134, percentage: 24 },
    { query: 'Return policy', count: 89, percentage: 16 },
    { query: 'Shipping details', count: 76, percentage: 14 },
    { query: 'Product recommendations', count: 65, percentage: 12 },
    { query: 'Other', count: 35, percentage: 6 },
  ];

  const timeData = [
    { hour: '9AM', messages: 12 },
    { hour: '12PM', messages: 28 },
    { hour: '3PM', messages: 45 },
    { hour: '6PM', messages: 38 },
    { hour: '9PM', messages: 22 },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white mb-2">Analytics & Insights</h2>
        <p className="text-white/70">Monitor AI assistant performance and customer interactions</p>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {performanceMetrics.map((metric, index) => {
          const Icon = metric.icon;
          return (
            <Card key={index} className="card-feelori">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-feelori-primary/20 rounded-lg">
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <Badge 
                    className={
                      metric.trendPositive 
                        ? "bg-green-500/20 text-green-400 border-green-500/30" 
                        : "bg-red-500/20 text-red-400 border-red-500/30"
                    }
                  >
                    {metric.trend}
                  </Badge>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white mb-1">{metric.value}</h3>
                  <p className="text-white/70 text-sm">{metric.title}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Popular Products */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Package className="w-5 h-5" />
              Popular Products
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {popularProducts.map((product, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                <div>
                  <p className="text-white font-medium">{product.name}</p>
                  <p className="text-white/60 text-sm">{product.requests} requests</p>
                </div>
                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                  {product.trend}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Common Queries */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Common Queries
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {commonQueries.map((query, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-white font-medium">{query.query}</span>
                  <span className="text-white/60 text-sm">{query.count}</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div
                    className="bg-feelori-primary h-2 rounded-full transition-all duration-500"
                    style={{ width: `${query.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Hourly Activity */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Hourly Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {timeData.map((data, index) => (
                <div key={index} className="flex items-center gap-4">
                  <span className="text-white/70 text-sm w-12">{data.hour}</span>
                  <div className="flex-1 bg-white/10 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-feelori-primary to-feelori-accent h-3 rounded-full transition-all duration-500"
                      style={{ width: `${(data.messages / Math.max(...timeData.map(d => d.messages))) * 100}%` }}
                    />
                  </div>
                  <span className="text-white text-sm w-8">{data.messages}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* AI Performance */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              AI Performance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-white/80">Gemini Model</span>
                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                  Active
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/80">OpenAI Fallback</span>
                <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                  Standby
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/80">Response Quality</span>
                <span className="text-feelori-primary font-semibold">94.2%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/80">Fallback Usage</span>
                <span className="text-white">2.1%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Health Overview */}
      <Card className="card-feelori">
        <CardHeader>
          <CardTitle className="text-white">System Health Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <h4 className="text-white font-semibold">Database</h4>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                <span className="text-white/80 text-sm">Connected</span>
              </div>
              <p className="text-white/60 text-xs">Response time: 12ms</p>
            </div>
            
            <div className="space-y-2">
              <h4 className="text-white font-semibold">WhatsApp API</h4>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                <span className="text-white/80 text-sm">Connected</span>
              </div>
              <p className="text-white/60 text-xs">Last message: 2 min ago</p>
            </div>
            
            <div className="space-y-2">
              <h4 className="text-white font-semibold">Shopify Integration</h4>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                <span className="text-white/80 text-sm">Limited</span>
              </div>
              <p className="text-white/60 text-xs">API rate limit: 85% used</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsTab;