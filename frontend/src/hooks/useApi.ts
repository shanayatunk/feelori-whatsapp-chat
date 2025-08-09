// frontend/src/hooks/useApi.ts - IMPROVED VERSION
import { useState, useCallback } from 'react';
import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { ApiResponse } from '@/types';

// Configure axios defaults
axios.defaults.timeout = 15000;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Add request/response interceptors for debugging
axios.interceptors.request.use(
  (config) => {
    console.log('🚀 API Request:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      timeout: config.timeout
    });
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', {
      status: response.status,
      url: response.config.url,
      data: response.data ? Object.keys(response.data) : 'no data'
    });
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', {
      status: error.response?.status,
      url: error.config?.url,
      message: error.message,
      data: error.response?.data
    });
    return Promise.reject(error);
  }
);

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
    setLoading(true);
    setError(null);
    
    const token = localStorage.getItem('admin_token');

    try {
      const response = await axios({
        // Use environment variable or fallback to proxy
        baseURL: import.meta.env.VITE_BACKEND_URL || '',
        timeout: config.timeout || 15000,
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
          ...config.headers,
        },
        ...config,
      });

      const result = response.data;
      
      // Handle different response formats
      let normalizedResult: ApiResponse<T>;
      
      if (result && typeof result === 'object' && 'success' in result) {
        // Backend already returns ApiResponse format
        normalizedResult = result;
      } else {
        // Wrap raw data in ApiResponse format
        normalizedResult = {
          success: true,
          data: result,
          message: 'Request successful',
          timestamp: new Date().toISOString(),
        };
      }

      setData(normalizedResult.data || null);
      return normalizedResult;
      
    } catch (err) {
      const axiosError = err as AxiosError;
      let errorMessage = 'An unexpected error occurred';

      if (axiosError.response) {
        // Server responded with error
        const status = axiosError.response.status;
        const errorData = axiosError.response.data as any;
        
        if (status === 401) {
          errorMessage = 'Authentication failed - please login again';
          // Clear invalid token
          localStorage.removeItem('admin_token');
        } else if (status === 403) {
          errorMessage = 'Access denied - insufficient permissions';
        } else if (status === 404) {
          errorMessage = 'Endpoint not found - check your configuration';
        } else if (status >= 500) {
          errorMessage = 'Server error - please try again later';
        } else if (errorData?.message) {
          errorMessage = errorData.message;
        } else if (errorData?.detail) {
          errorMessage = Array.isArray(errorData.detail) 
            ? errorData.detail[0]?.msg || 'Validation error'
            : errorData.detail;
        } else {
          errorMessage = `HTTP ${status}: ${axiosError.response.statusText}`;
        }
      } else if (axiosError.request) {
        // Network error
        if (axiosError.code === 'ECONNABORTED') {
          errorMessage = 'Request timeout - server is not responding';
        } else {
          errorMessage = 'Network error - cannot reach server. Check if the backend is running.';
        }
      } else {
        errorMessage = axiosError.message || 'Request setup error';
      }

      console.error('💥 API Error Details:', {
        url: config.url,
        method: config.method,
        status: axiosError.response?.status,
        message: errorMessage,
        originalError: axiosError.message
      });

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

export function useHealthCheck() {
  const { execute, ...rest } = useApi();

  const checkHealth = useCallback(() => {
    return execute({ method: 'GET', url: '/api/health' });
  }, [execute]);

  return { checkHealth, ...rest };
}

export function useDashboardStats() {
  const { execute, ...rest } = useApi();

  const getStats = useCallback(() => {
    return execute({
      method: 'GET',
      url: '/api/v1/admin/stats',
    });
  }, [execute]);

  return { getStats, ...rest };
}

export function useAdminCustomers() {
  const { execute, ...rest } = useApi();

  const getCustomers = useCallback((page = 1, limit = 20) => {
    return execute({
      method: 'GET',
      url: '/api/v1/admin/customers',
      params: { page, limit },
    });
  }, [execute]);

  return { getCustomers, ...rest };
}

export function useSecurityEvents() {
  const { execute, ...rest } = useApi();

  const getEvents = useCallback((limit = 50) => {
    return execute({
      method: 'GET',
      url: '/api/v1/admin/security/events',
      params: { limit },
    });
  }, [execute]);

  return { getEvents, ...rest };
}

export function useProducts() {
  const { execute, ...rest } = useApi();

  const getProducts = useCallback((query = '', limit = 50) => {
    return execute({
      method: 'GET',
      url: '/api/v1/admin/products',
      params: { query, limit },
    });
  }, [execute]);

  return { getProducts, ...rest };
}

export function useBroadcastMessage() {
  const { execute, ...rest } = useApi();

  const broadcast = useCallback((message: string, target_type: 'all' | 'active' | 'recent' = 'all') => {
    return execute({
      method: 'POST',
      url: '/api/v1/admin/broadcast',
      data: { message, target_type },
    });
  }, [execute]);

  return { broadcast, ...rest };
}