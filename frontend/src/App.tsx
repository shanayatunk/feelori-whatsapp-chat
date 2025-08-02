import React, { Suspense, lazy } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ToastProvider } from '@/components/ui/ToastProvider';
import '@/styles/globals.css';

// Lazy load components for code splitting
const Dashboard = lazy(() => import('@/pages/Dashboard'));

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

function App(): JSX.Element {
  return (
    <div className="min-h-screen bg-gradient-to-br from-feelori-primary via-feelori-primary/80 to-feelori-secondary">
      <div className="p-8">
        <h1 className="text-4xl font-bold text-white">Feelori AI Assistant</h1>
        <p className="text-white/80 mt-4">Dashboard loading...</p>
        <div className="mt-8 bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Quick Stats</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-feelori-primary/20 rounded-xl p-4">
              <p className="text-2xl font-bold text-white">1,247</p>
              <p className="text-white/70 text-sm">Total Messages</p>
            </div>
            <div className="bg-feelori-primary/20 rounded-xl p-4">
              <p className="text-2xl font-bold text-white">89</p>
              <p className="text-white/70 text-sm">Active Customers</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;