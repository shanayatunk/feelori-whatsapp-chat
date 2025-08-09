// frontend/tests/global-setup.ts
import { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global test setup...');
  
  // Wait a bit for servers to fully start
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  // Verify backend is responding
  try {
    const response = await fetch('http://127.0.0.1:8000/health');
    if (!response.ok) {
      throw new Error(`Backend health check failed: ${response.status}`);
    }
    console.log('✅ Backend health check passed');
  } catch (error) {
    console.error('❌ Backend health check failed:', error);
    throw error;
  }

  // Verify frontend is responding
  try {
    const response = await fetch('http://127.0.0.1:3000');
    if (!response.ok) {
      throw new Error(`Frontend health check failed: ${response.status}`);
    }
    console.log('✅ Frontend health check passed');
  } catch (error) {
    console.error('❌ Frontend health check failed:', error);
    throw error;
  }

  console.log('🎉 Global test setup completed');
}

export default globalSetup;