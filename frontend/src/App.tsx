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
        <h1 className="text-4xl font-bold text-white">Feelori AI Assistant - Test</h1>
        <p className="text-white/80 mt-4">If you can see this text, React is working!</p>
      </div>
    </div>
  );
}

export default App;