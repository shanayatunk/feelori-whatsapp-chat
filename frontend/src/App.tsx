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
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <div className="min-h-screen bg-gradient-to-br from-feelori-primary via-feelori-primary/80 to-feelori-secondary">
            <Suspense fallback={<LoadingSpinner />}>
              <Dashboard />
            </Suspense>
          </div>
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;