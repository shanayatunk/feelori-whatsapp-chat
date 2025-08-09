// frontend/src/test/Dashboard.test.tsx

import { render, screen, act, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Dashboard from '../pages/Dashboard';
import { useAuth } from '../hooks/useAuth';
// REMOVED: useRecentMessages from this import
import { useDashboardStats, useHealthCheck } from '../hooks/useApi';

// Mock the modules that these hooks come from
vi.mock('../hooks/useAuth');
vi.mock('../hooks/useApi', () => ({
  useDashboardStats: vi.fn(),
  useHealthCheck: vi.fn(),
  // REMOVED: useRecentMessages from this mock
}));

// Mock child components for simplicity
vi.mock('@/components/layout/Sidebar', () => ({
    Sidebar: ({ onTabChange }) => (
        <div>
            <button onClick={() => onTabChange('dashboard')}>Dashboard</button>
            <button onClick={() => onTabChange('products')}>Products</button>
        </div>
    ),
}));
vi.mock('@/components/tabs/DashboardTab', () => ({
    default: () => <div>Dashboard Tab Content</div>
}));
vi.mock('@/components/tabs/ProductsTab', () => ({
    default: () => <div>Products Tab Content</div>
}));


describe('Dashboard Component', () => {

  beforeEach(() => {
    vi.clearAllMocks();

    (useAuth as any).mockReturnValue({
      isAuthenticated: true,
      loading: false,
      logout: vi.fn(),
    });
    
    (useDashboardStats as any).mockReturnValue({
      getStats: vi.fn().mockResolvedValue({ data: {} }),
      loading: false,
      error: null,
    });
    
    (useHealthCheck as any).mockReturnValue({
      checkHealth: vi.fn(),
      loading: false,
    });
    
    // REMOVED: The mock setup for useRecentMessages
  });

  it('renders the dashboard tab by default', async () => {
    render(<Dashboard />);
    expect(await screen.findByText('Dashboard Tab Content')).toBeInTheDocument();
  });

  it('switches to the products tab when clicked', async () => {
    render(<Dashboard />);
    expect(await screen.findByText('Dashboard Tab Content')).toBeInTheDocument();

    await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /Products/i }));
    });
    
    expect(await screen.findByText('Products Tab Content')).toBeInTheDocument();
  });
});