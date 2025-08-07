import { useState, useCallback, useEffect } from 'react';
import { useApi } from './useApi';
import { ApiResponse } from '@/types';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const { execute } = useApi();

  const checkSession = useCallback(async () => {
    try {
      setLoading(true);
      // Assuming you have a session check endpoint, update if necessary
      const response = await execute({ method: 'GET', url: '/v1/auth/session' }); 
      if (response.success) {
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, [execute]);

  useEffect(() => {
    // You can uncomment this if you implement a session check endpoint
    // checkSession();
    setLoading(false); // For now, just set loading to false
  }, [checkSession]);

  const login = useCallback(async (password: string): Promise<ApiResponse> => {
    // --- FIX IS HERE ---
    // Provide the full path from the base /api URL
    const response = await execute({
      method: 'POST',
      url: '/v1/auth/login', // Corrected URL
      data: { password },
    });
    if (response.success && response.data?.access_token) {
      localStorage.setItem('admin_token', response.data.access_token);
      setIsAuthenticated(true);
    }
    return response;
  }, [execute]);

  const logout = useCallback(async () => {
    // --- FIX IS HERE ---
    await execute({ method: 'POST', url: '/v1/auth/logout' }); // Corrected URL
    localStorage.removeItem('admin_token');
    setIsAuthenticated(false);
  }, [execute]);

  return { isAuthenticated, loading, login, logout, checkSession };
}