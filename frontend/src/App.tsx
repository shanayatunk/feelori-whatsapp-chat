import React from 'react';
import { useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { LoadingSpinner } from './components/ui/LoadingSpinner';
import { ToastProvider } from './components/ui/ToastProvider';

function App(): JSX.Element {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-feelori-primary to-feelori-secondary">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <ToastProvider>
      {isAuthenticated ? <Dashboard /> : <LoginPage />}
    </ToastProvider>
  );
}

export default App;