import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { LoginPage } from './Login';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';

// ✅ Mock react-router-dom useNavigate so it doesn't really navigate during tests
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => vi.fn(), // just a no-op mock
  };
});

// Mock the custom hooks
vi.mock('@/hooks/useAuth');
vi.mock('@/hooks/useToast');

describe('LoginPage', () => {
  const mockLogin = vi.fn();
  const mockSuccessToast = vi.fn();
  const mockErrorToast = vi.fn();

  beforeEach(() => {
    (useAuth as any).mockReturnValue({
      login: mockLogin,
      loading: false,
      isAuthenticated: false,
    });
    (useToast as any).mockReturnValue({
      success: mockSuccessToast,
      error: mockErrorToast,
    });
    vi.clearAllMocks();
  });

  it('should render the login form correctly', () => {
    render(<LoginPage />);
    expect(screen.getByText('Admin Login')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Login/i })).toBeInTheDocument();
  });

  it('should call the login function on form submit', async () => {
    render(<LoginPage />);
    const passwordInput = screen.getByPlaceholderText('Password');
    const loginButton = screen.getByRole('button', { name: /Login/i });

    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(loginButton);

    expect(mockLogin).toHaveBeenCalledWith('password123');
  });
});
