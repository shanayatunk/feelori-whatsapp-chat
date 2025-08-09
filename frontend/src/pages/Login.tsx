// frontend/src/pages/Login.tsx
import React, { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/useToast';

export function LoginPage() {
  const { login, loading } = useAuth();
  const { error: showError, success: showSuccess } = useToast();
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      console.log('Submitting login form');
      const response = await login(password);
      console.log('Login response:', response);
      showSuccess('Login successful!');
    } catch (err: any) {
      console.error('Login error:', err);
      showError(err.message || 'Login failed. Please try again.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-feelori-primary to-feelori-secondary">
      <form
        onSubmit={handleSubmit}
        className="bg-white/10 p-8 rounded-xl shadow-lg backdrop-blur-lg w-full max-w-sm space-y-6"
      >
        <h1 className="text-2xl font-bold text-center text-white">Admin Login</h1>

        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          data-testid="password-input"
        />

        <Button
          type="submit"
          disabled={loading}
          className="w-full"
        >
          {loading ? 'Logging in...' : 'Login'}
        </Button>
      </form>
    </div>
  );
}

export default LoginPage;