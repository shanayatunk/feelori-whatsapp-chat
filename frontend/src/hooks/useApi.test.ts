// frontend/src/hooks/useApi.test.ts
import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import axios from 'axios';
import { useApi } from './useApi';

vi.mock('axios');

describe('useApi Hook', () => {
  it('should handle a successful API call', async () => {
    const mockData = { access_token: 'test-token', token_type: 'bearer', expires_in: 86400 };
    const mockApiResponse = { success: true, message: 'Request successful', data: mockData };

    (axios as any).mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useApi());

    let apiResponse;
    await act(async () => {
      apiResponse = await result.current.execute({ url: '/api/v1/auth/login', method: 'POST' });
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
    expect(apiResponse).toEqual(mockApiResponse);
  });

  it('should handle a failed API call', async () => {
    const errorMessage = 'Request failed';
    (axios as any).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useApi());

    await act(async () => {
      try {
        await result.current.execute({ url: '/fail' });
      } catch (e) {
        // Expected to throw
      }
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe(errorMessage);
  });
});