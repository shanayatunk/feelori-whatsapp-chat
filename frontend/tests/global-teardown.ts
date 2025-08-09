// frontend/tests/global-teardown.ts
import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global test teardown...');
  
  // You can add logic here to clean up test data from your database
  console.log('🎉 Global test teardown completed');
}

export default globalTeardown;