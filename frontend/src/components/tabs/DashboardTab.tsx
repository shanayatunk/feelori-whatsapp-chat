// /frontend/src/components/tabs/DashboardTab.tsx - CORRECTED

import React from 'react';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { RecentConversations } from '@/components/dashboard/RecentConversations';
import { StatsGrid } from '@/components/dashboard/StatsGrid';

const DashboardTab: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        {/*
          THIS IS THE FIX: The data-testid is added directly to the H1 element
          that the Playwright test is waiting for.
        */}
        <h1 
          className="text-2xl font-bold tracking-tight text-white sm:text-3xl" 
          data-testid="dashboard-heading"
        >
          Dashboard
        </h1>
        <p className="mt-2 text-lg text-gray-300">
          Welcome back! Here's a quick overview of your assistant's activity.
        </p>
      </div>

      <StatsGrid />
      <QuickActions />
      <RecentConversations />
    </div>
  );
};

export default DashboardTab;