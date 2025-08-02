import React, { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/useToast';

export function LoginPage() {
  const [password, setPassword] = useState('');
  const { login, loading } = useAuth();
  const { showToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(password);
      showToast('Logged in successfully', { type: 'success' });
    } catch (error: any) {
      showToast(error.message || 'Login failed', { type: 'error' });
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-feelori-primary to-feelori-secondary">
      <div className="w-full max-w-md p-8 space-y-8 bg-white/10 backdrop-blur-lg rounded-2xl shadow-lg">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white">Feelori AI</h1>
          <p className="text-white/80">Admin Login</p>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="bg-white/10 border-white/20 text-white placeholder-white/50"
            disabled={loading}
          />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </Button>
        </form>
      </div>
    </div>
  );
}
