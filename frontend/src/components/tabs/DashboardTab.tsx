import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { useHealthCheck, useDashboardStats, useRecentMessages } from '@/hooks/useApi';
import { HealthStatus, DashboardStats, RecentMessage } from '@/types';
import { StatsGrid } from '../dashboard/StatsGrid';
import { RecentConversations } from '../dashboard/RecentConversations';
import { QuickActions } from '../dashboard/QuickActions';

const DashboardTab: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalMessages: 0,
    activeCustomers: 0,
    productsShown: 0,
    ordersTracked: 0,
  });
  const [messages, setMessages] = useState<RecentMessage[]>([]);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);

  const { checkHealth, loading: healthLoading } = useHealthCheck();
  const { getStats, loading: statsLoading, error: statsError } = useDashboardStats();
  const { getMessages, loading: messagesLoading, error: messagesError } = useRecentMessages();

  useEffect(() => {
    // Fetch all necessary data for the dashboard when the component mounts
    const fetchData = async () => {
      try {
        const statsResponse = await getStats();
        if (statsResponse.success && statsResponse.data) {
          setStats(statsResponse.data);
        }
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      }

      try {
        const messagesResponse = await getMessages();
        if (messagesResponse.success && messagesResponse.data) {
          setMessages(messagesResponse.data.messages);
        }
      } catch (err) {
        console.error('Failed to fetch messages:', err);
      }
    };

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

    fetchData();
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [checkHealth, getStats, getMessages]);

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
      {statsLoading || messagesLoading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-white" />
        </div>
      ) : statsError || messagesError ? (
        <div className="text-center text-red-500">
          <p>Error loading dashboard data. Please try again later.</p>
          <p>{statsError || messagesError}</p>
        </div>
      ) : (
        <>
          <StatsGrid stats={stats} />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <RecentConversations messages={messages} />
            <QuickActions />
          </div>
        </>
      )}
    </div>
  );
};

export default DashboardTab;