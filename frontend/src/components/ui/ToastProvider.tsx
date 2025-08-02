import React, { createContext, useContext } from 'react';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { Toast } from '@/types';
import { cn } from '@/lib/utils';

const ToastContext = createContext<ReturnType<typeof useToast> | null>(null);

export const useToastContext = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within ToastProvider');
  }
  return context;
};

interface ToastProviderProps {
  children: React.ReactNode;
}

const getToastIcon = (type: Toast['type']) => {
  const iconMap = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
    info: Info,
  };
  return iconMap[type];
};

const getToastClasses = (type: Toast['type']) => {
  const classMap = {
    success: 'border-green-500/30 bg-green-500/10 text-green-400',
    error: 'border-red-500/30 bg-red-500/10 text-red-400',
    warning: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-400',
    info: 'border-blue-500/30 bg-blue-500/10 text-blue-400',
  };
  return classMap[type];
};

const ToastItem: React.FC<{ toast: Toast; onRemove: (id: number) => void }> = ({ toast, onRemove }) => {
  const Icon = getToastIcon(toast.type);
  
  return (
    <div
      className={cn(
        'flex items-center gap-3 p-4 rounded-xl border backdrop-blur-lg shadow-lg min-w-[300px] max-w-[400px]',
        'animate-slide-in transition-all duration-300',
        getToastClasses(toast.type)
      )}
    >
      <Icon className="w-5 h-5 flex-shrink-0" />
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => onRemove(toast.id)}
        className="flex-shrink-0 p-1 hover:bg-white/10 rounded-md transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const toastContext = useToast();

  return (
    <ToastContext.Provider value={toastContext}>
      {children}
      
      {/* Toast Container */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toastContext.toasts.map((toast) => (
          <ToastItem
            key={toast.id}
            toast={toast}
            onRemove={toastContext.removeToast}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};