import { useState, useCallback } from 'react';
import { Toast } from '@/types';
import { generateId } from '@/lib/utils';

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
    const toast: Toast = {
      id: parseInt(generateId(), 36),
      message,
      type,
    };

    setToasts(prev => [...prev, toast]);

    // Auto-remove toast after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== toast.id));
    }, 5000);

    return toast.id;
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toasts,
    addToast,
    removeToast,
    clearToasts,
    success: (message: string) => addToast(message, 'success'),
    error: (message: string) => addToast(message, 'error'),
    info: (message: string) => addToast(message, 'info'),
    warning: (message: string) => addToast(message, 'warning'),
  };
}