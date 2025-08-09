// /frontend/tests/auth.spec.ts - FINAL VERSION
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start every test on the login page with a clean slate
    await page.goto('/login');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('should login successfully and display the dashboard', async ({ page }) => {
    // Wait for the form to be ready
    await expect(page.locator('input[type="password"]')).toBeVisible({ timeout: 10000 });
    
    // Use the test password
    await page.locator('input[type="password"]').fill('a_secure_test_password_123');
    
    // Click the login button
    await page.getByRole('button', { name: /login/i }).click();
    
    // The most reliable check: wait for the dashboard's main heading to appear.
    // Ensure your DashboardTab.tsx has data-testid="dashboard-heading" on the <h1>
    const dashboardHeading = page.getByTestId('dashboard-heading');
    await expect(dashboardHeading).toBeVisible({ timeout: 15000 });

    // As a final check, confirm the URL is correct.
    await expect(page).toHaveURL(/.*\/dashboard/);
  });
});

test.describe('Backend Connectivity', () => {
  test('should connect to the backend health endpoint', async ({ page }) => {
    // page.request automatically uses the baseURL, which is proxied by Vite.
    // This correctly tests the connection from the frontend's perspective.
    const response = await page.request.get('/api/health');
    expect(response.ok()).toBe(true);
  });
});