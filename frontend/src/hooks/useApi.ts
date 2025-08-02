import { useState, useCallback } from 'react';
import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { ApiResponse } from '@/types';

interface UseApiReturn<T = any> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (config: AxiosRequestConfig) => Promise<ApiResponse<T>>;
  reset: () => void;
}

/**
 * A generic hook for making API calls using axios.
 * It handles loading, error, and data states.
 * @returns An object with the current data, loading state, error state, and an execute function to make API calls.
 */
export function useApi<T = any>(): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (config: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios({
        baseURL: '/api',
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
          ...config.headers,
        },
        ...config,
      });

      const result = response.data as ApiResponse<T>;
      setData(result.data || null);
      return result;
    } catch (err) {
      const axiosError = err as AxiosError;
      let errorMessage = 'An unexpected error occurred';

      if (axiosError.response) {
        // Server responded with error status
        errorMessage = `HTTP ${axiosError.response.status}: ${axiosError.response.statusText}`;
        if (axiosError.response.data && typeof axiosError.response.data === 'object') {
          const errorData = axiosError.response.data as any;
          if (errorData.message) {
            errorMessage = errorData.message;
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        }
      } else if (axiosError.request) {
        // Request was made but no response received
        errorMessage = 'Network error - please check your connection';
      } else {
        // Something else happened
        errorMessage = axiosError.message || 'Unknown error occurred';
      }

      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  return { data, loading, error, execute, reset };
}

// Specific API hooks
export function useHealthCheck() {
  const { execute, ...rest } = useApi();

  const checkHealth = useCallback(() => {
    return execute({ method: 'GET', url: '/health' });
  }, [execute]);

  return { checkHealth, ...rest };
}

export function useProducts() {
  const { execute, ...rest } = useApi();

  const getProducts = useCallback((query = '', limit = 10) => {
    return execute({
      method: 'GET',
      url: '/products',
      params: { query, limit },
    });
  }, [execute]);

  return { getProducts, ...rest };
}

export function useSendMessage() {
  const { execute, ...rest } = useApi();

  const sendMessage = useCallback((phoneNumber: string, message: string) => {
    return execute({
      method: 'POST',
      url: '/send-message',
      data: { phone_number: phoneNumber, message },
    });
  }, [execute]);

  return { sendMessage, ...rest };
}

export function useCustomer() {
  const { execute, ...rest } = useApi();

  const getCustomer = useCallback((phoneNumber: string) => {
    return execute({
      method: 'GET',
      url: `/customers/${encodeURIComponent(phoneNumber)}`,
    });
  }, [execute]);

  return { getCustomer, ...rest };
}

export function useOrders() {
  const { execute, ...rest } = useApi();

  const getOrders = useCallback((phoneNumber: string) => {
    return execute({
      method: 'GET',
      url: `/orders/${encodeURIComponent(phoneNumber)}`,
    });
  }, [execute]);

  return { getOrders, ...rest };
}

export function useDashboardStats() {
  const { execute, ...rest } = useApi();

  const getStats = useCallback(() => {
    return execute({
      method: 'GET',
      url: '/dashboard/stats',
    });
  }, [execute]);

  return { getStats, ...rest };
}

export function useRecentMessages() {
  const { execute, ...rest } = useApi();

  const getMessages = useCallback(() => {
    return execute({
      method: 'GET',
      url: '/dashboard/recent-messages',
    });
  }, [execute]);

  return { getMessages, ...rest };
}