import React, { useState, Suspense, lazy } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { TabType } from '@/types';

// Lazy load tab components
const DashboardTab = lazy(() => import('@/components/tabs/DashboardTab'));
const ProductsTab = lazy(() => import('@/components/tabs/ProductsTab'));
const AnalyticsTab = lazy(() => import('@/components/tabs/AnalyticsTab'));
const SettingsTab = lazy(() => import('@/components/tabs/SettingsTab'));

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  const renderTabContent = () => {
    const tabComponents = {
      dashboard: DashboardTab,
      products: ProductsTab,
      analytics: AnalyticsTab,
      settings: SettingsTab,
    };

    const Component = tabComponents[activeTab];
    return (
      <Suspense fallback={<LoadingSpinner />}>
        <Component />
      </Suspense>
    );
  };

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-feelori-primary via-feelori-primary/80 to-feelori-secondary">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      
      <main className="flex-1 p-6 overflow-y-auto bg-white/5 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto">
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;