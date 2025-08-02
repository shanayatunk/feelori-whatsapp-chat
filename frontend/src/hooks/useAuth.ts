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
      const response = await execute({ method: 'GET', url: '/session' });
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
    checkSession();
  }, [checkSession]);

  const login = useCallback(async (password: string): Promise<ApiResponse> => {
    const response = await execute({
      method: 'POST',
      url: '/login',
      data: { password },
    });
    if (response.success) {
      setIsAuthenticated(true);
    }
    return response;
  }, [execute]);

  const logout = useCallback(async () => {
    await execute({ method: 'POST', url: '/logout' });
    setIsAuthenticated(false);
  }, [execute]);

  return { isAuthenticated, loading, login, logout, checkSession };
}
