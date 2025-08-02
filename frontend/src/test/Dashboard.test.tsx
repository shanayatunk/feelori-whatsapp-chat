import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from 'react-query';
import Dashboard from '@/pages/Dashboard';
import { ToastProvider } from '@/components/ui/ToastProvider';

// Mock the API hooks
vi.mock('@/hooks/useApi', () => ({
  useHealthCheck: () => ({
    checkHealth: vi.fn().mockResolvedValue({
      success: true,
      data: {
        status: 'healthy',
        services: {
          database: 'connected',
          shopify: 'connected',
          whatsapp: 'configured',
          ai_models: {
            gemini: 'available',
            openai: 'available',
          },
        },
      },
    }),
    loading: false,
    error: null,
  }),
  useProducts: () => ({
    getProducts: vi.fn().mockResolvedValue({
      success: true,
      data: {
        products: [
          {
            id: '1',
            title: 'Test Product',
            handle: 'test-product',
            description: 'A test product',
            price: '29.99',
            images: ['https://example.com/image.jpg'],
            variants: [],
            tags: ['test'],
            available: true,
          },
        ],
      },
    }),
    loading: false,
    error: null,
  }),
  useSendMessage: () => ({
    sendMessage: vi.fn().mockResolvedValue({
      success: true,
      message: 'Message sent successfully',
    }),
    loading: false,
    error: null,
  }),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        {children}
      </ToastProvider>
    </QueryClientProvider>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard with all tabs', async () => {
    render(<Dashboard />, { wrapper: createWrapper() });
    
    // Check if navigation items are present
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Products')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('displays the correct brand name and version', async () => {
    render(<Dashboard />, { wrapper: createWrapper() });
    
    expect(screen.getByText('Feelori AI')).toBeInTheDocument();
    expect(screen.getByText('v2.0')).toBeInTheDocument();
  });

  it('allows navigation between tabs', async () => {
    const user = userEvent.setup();
    render(<Dashboard />, { wrapper: createWrapper() });
    
    // Click on Products tab
    await user.click(screen.getByText('Products'));
    
    // Should show products content
    await waitFor(() => {
      expect(screen.getByText('Shopify Products')).toBeInTheDocument();
    });

    // Click on Analytics tab
    await user.click(screen.getByText('Analytics'));
    
    await waitFor(() => {
      expect(screen.getByText('Analytics & Insights')).toBeInTheDocument();
    });
  });

  it('shows loading state correctly', async () => {
    render(<Dashboard />, { wrapper: createWrapper() });
    
    // The dashboard should render without showing loading indefinitely
    await waitFor(() => {
      expect(screen.getByText('Feelori AI Assistant Dashboard')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('handles tab switching with keyboard navigation', async () => {
    const user = userEvent.setup();
    render(<Dashboard />, { wrapper: createWrapper() });
    
    const dashboardTab = screen.getByText('Dashboard');
    const productsTab = screen.getByText('Products');
    
    // Focus and use keyboard to navigate
    dashboardTab.focus();
    await user.keyboard('{Tab}');
    
    expect(productsTab).toHaveFocus();
  });
});