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

  const sendMessage = useCallback((phoneNumber: string, message: string, apiKey: string) => {
    return execute({
      method: 'POST',
      url: '/send-message',
      data: { phone_number: phoneNumber, message },
      headers: { Authorization: `Bearer ${apiKey}` },
    });
  }, [execute]);

  return { sendMessage, ...rest };
}

export function useCustomer() {
  const { execute, ...rest } = useApi();

  const getCustomer = useCallback((phoneNumber: string, apiKey: string) => {
    return execute({
      method: 'GET',
      url: `/customers/${encodeURIComponent(phoneNumber)}`,
      headers: { Authorization: `Bearer ${apiKey}` },
    });
  }, [execute]);

  return { getCustomer, ...rest };
}

export function useOrders() {
  const { execute, ...rest } = useApi();

  const getOrders = useCallback((phoneNumber: string, apiKey: string) => {
    return execute({
      method: 'GET',
      url: `/orders/${encodeURIComponent(phoneNumber)}`,
      headers: { Authorization: `Bearer ${apiKey}` },
    });
  }, [execute]);

  return { getOrders, ...rest };
}