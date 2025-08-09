// frontend/src/hooks/useAuth.ts - FIXED VERSION
import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from './useApi';
import { ApiResponse } from '@/types';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const { execute } = useApi();
  const navigate = useNavigate();

  const checkSession = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem('admin_token');
    console.log('🔍 Checking session, token exists:', !!token);

    if (!token) {
      console.log('❌ No token, setting unauthenticated');
      setIsAuthenticated(false);
      setLoading(false);
      return false;
    }

    try {
      console.log('🌐 Requesting /api/v1/admin/me');
      await execute({
        method: 'GET',
        url: '/api/v1/admin/me',
        timeout: 10000,
      });
      console.log('✅ Session valid');
      setIsAuthenticated(true);
      return true;
    } catch (error) {
      console.error('❌ Session check failed:', error);
      localStorage.removeItem('admin_token');
      setIsAuthenticated(false);
      return false;
    } finally {
      console.log('🏁 Session check complete');
      setLoading(false);
    }
  }, [execute]);

  useEffect(() => {
    console.log('🚀 Initializing auth check');
    
    // Set a timeout to prevent infinite loading
    const timeoutId = setTimeout(() => {
      console.error('⏰ Auth initialization timed out');
      setLoading(false);
      setIsAuthenticated(false);
    }, 15000);

    checkSession()
      .catch(error => {
        console.error('💥 checkSession error:', error);
        setLoading(false);
        setIsAuthenticated(false);
      })
      .finally(() => {
        clearTimeout(timeoutId);
      });
  }, [checkSession]);

  const login = useCallback(async (password: string): Promise<ApiResponse> => {
    if (!password || password.trim() === '') {
      throw new Error('Password is required');
    }

    try {
      console.log('🔐 Attempting login');
      const response = await execute({
        method: 'POST',
        url: '/api/v1/auth/login',
        data: { password: password.trim() },
        timeout: 10000,
      });

      console.log('📡 Login response:', { 
        success: response.success, 
        hasToken: !!response.data?.access_token 
      });

      if (response.success && response.data?.access_token) {
        console.log('✅ Login successful, storing token');
        localStorage.setItem('admin_token', response.data.access_token);
        
        // FIXED: Update state synchronously and navigate in useEffect
        setIsAuthenticated(true);
        console.log('🚀 Authentication state updated, navigation will happen via route change');
        
        return response;
      } else {
        console.error('❌ Login failed: Invalid response format', response);
        throw new Error('Invalid login response - no access token');
      }
    } catch (error: any) {
      console.error('💥 Login failed:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data
      });
      
      // Clear any existing token
      localStorage.removeItem('admin_token');
      setIsAuthenticated(false);
      
      throw error;
    }
  }, [execute]);

  // FIXED: Handle navigation when authentication state changes
  useEffect(() => {
    if (isAuthenticated && !loading) {
      console.log('🚀 User authenticated, navigating to dashboard');
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);

  const logout = useCallback(async () => {
    console.log('🚪 Logging out');
    
    try {
      // Try to notify backend, but don't wait for it
      execute({
        method: 'POST',
        url: '/api/v1/auth/logout',
        timeout: 5000,
      }).catch(err => console.warn('Logout API call failed:', err));
    } finally {
      // Always clear local state regardless of API response
      localStorage.removeItem('admin_token');
      setIsAuthenticated(false);
      navigate('/login', { replace: true });
    }
  }, [execute, navigate]);

  return { 
    isAuthenticated, 
    loading, 
    login, 
    logout, 
    checkSession 
  };
}