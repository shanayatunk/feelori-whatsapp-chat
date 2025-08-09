import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Users, Package, TrendingUp } from 'lucide-react';
import { DashboardStats } from '@/types';

interface StatsGridProps {
  stats: DashboardStats;
}

const statDetails = {
  totalMessages: { label: 'Total Messages', icon: MessageSquare, badgeClass: 'bg-green-500/20 text-green-400 border-green-500/30', change: '+12%' },
  activeCustomers: { label: 'Active Customers', icon: Users, badgeClass: 'bg-green-500/20 text-green-400 border-green-500/30', change: '+8%' },
  productsShown: { label: 'Products Shown', icon: Package, badgeClass: 'bg-green-500/20 text-green-400 border-green-500/30', change: '+15%' },
  ordersTracked: { label: 'Orders Tracked', icon: TrendingUp, badgeClass: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', change: '+3%' },
};

export const StatsGrid: React.FC<StatsGridProps> = ({ stats }) => {
  // Handle undefined stats
  if (!stats) {
    return <div className="text-white">Error: No stats provided</div>;
  }

  const statsArray = Object.entries(stats).map(([key, value]) => {
    const details = statDetails[key as keyof DashboardStats] || {
      label: key,
      icon: MessageSquare,
      badgeClass: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
      change: 'N/A',
    };
    return {
      ...details,
      value: value ?? 0, // Fallback to 0 if value is undefined
    };
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      {statsArray.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.label} className="card-feelori">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-white">{stat.label}</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-feelori-primary/20 rounded-xl">
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">
                    {stat.value.toLocaleString()}
                  </p>
                  <Badge className={`mt-1 ${stat.badgeClass}`}>
                    {stat.change} this week
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default StatsGrid;