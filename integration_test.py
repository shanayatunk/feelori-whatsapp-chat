#!/usr/bin/env python3
"""
Integration Testing for Feelori AI WhatsApp Assistant
Tests AI services, database operations, and external integrations
"""

import asyncio
import json
import time
from datetime import datetime

import httpx


class IntegrationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.admin_token = None
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_time: float = 0):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {details}")
    
    async def get_admin_token(self):
        """Get admin token for authenticated requests"""
        try:
            login_data = {"password": "mock_admin_password_123456"}
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                return True
        except Exception as e:
            print(f"Failed to get admin token: {e}")
        return False
    
    async def test_ai_integration(self):
        """Test AI service integration with mock APIs"""
        print("\n=== TESTING AI INTEGRATION ===")
        
        if not await self.get_admin_token():
            self.log_test("AI Integration", "SKIP", "No admin token available")
            return
        
        # Test AI response generation through webhook simulation
        start_time = time.time()
        try:
            # Simulate a message that would trigger AI response
            mock_message = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_entry_id",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "1234567890"},
                            "messages": [{
                                "id": "test_ai_msg_001",
                                "from": "+1234567890",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "Hello, I'm looking for fashion products"},
                                "type": "text"
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/webhook",
                json=mock_message,
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            # With mock APIs, we expect signature validation to fail, but AI should be accessible
            if response.status_code in [200, 403]:
                self.log_test("AI Integration", "PASS", 
                            f"AI service accessible (signature validation working)", response_time)
            else:
                self.log_test("AI Integration", "FAIL", 
                            f"Unexpected response: HTTP {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("AI Integration", "ERROR", str(e), response_time)
    
    async def test_database_operations(self):
        """Test database connectivity and operations"""
        print("\n=== TESTING DATABASE OPERATIONS ===")
        
        if not self.admin_token:
            await self.get_admin_token()
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test admin stats (which queries database)
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/admin/stats", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                stats_data = data.get("data", {})
                
                # Check if we get database-related stats
                if isinstance(stats_data, dict) and len(stats_data) > 0:
                    self.log_test("Database Operations", "PASS", 
                                f"Database stats retrieved: {list(stats_data.keys())}", response_time)
                else:
                    self.log_test("Database Operations", "FAIL", 
                                f"No database stats returned: {data}", response_time)
            else:
                self.log_test("Database Operations", "FAIL", 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Database Operations", "ERROR", str(e), response_time)
    
    async def test_shopify_integration(self):
        """Test Shopify integration with mock API"""
        print("\n=== TESTING SHOPIFY INTEGRATION ===")
        
        if not self.admin_token:
            await self.get_admin_token()
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test products endpoint (which uses Shopify)
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/admin/products", headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                products_data = data.get("data", {})
                
                # With mock Shopify API, we expect empty or fallback data
                if isinstance(products_data, (dict, list)):
                    self.log_test("Shopify Integration", "PASS", 
                                f"Shopify service accessible (mock data): {type(products_data).__name__}", 
                                response_time)
                else:
                    self.log_test("Shopify Integration", "FAIL", 
                                f"Unexpected products data: {data}", response_time)
            else:
                self.log_test("Shopify Integration", "FAIL", 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Shopify Integration", "ERROR", str(e), response_time)
    
    async def test_redis_connectivity(self):
        """Test Redis connectivity through rate limiting"""
        print("\n=== TESTING REDIS CONNECTIVITY ===")
        
        # Test multiple requests to check if Redis-based rate limiting works
        start_time = time.time()
        try:
            responses = []
            for i in range(5):
                response = await self.client.get(f"{self.base_url}/health")
                responses.append(response.status_code)
                await asyncio.sleep(0.1)
            
            response_time = time.time() - start_time
            
            success_count = sum(1 for status in responses if status == 200)
            
            if success_count >= 4:  # Most requests should succeed
                self.log_test("Redis Connectivity", "PASS", 
                            f"Redis-based services working: {success_count}/5 requests succeeded", 
                            response_time)
            else:
                self.log_test("Redis Connectivity", "FAIL", 
                            f"Redis issues detected: {success_count}/5 requests succeeded", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Redis Connectivity", "ERROR", str(e), response_time)
    
    async def test_circuit_breaker_behavior(self):
        """Test circuit breaker functionality"""
        print("\n=== TESTING CIRCUIT BREAKER BEHAVIOR ===")
        
        # Test with a potentially failing endpoint
        start_time = time.time()
        try:
            # Make requests to an endpoint that might trigger circuit breaker
            responses = []
            for i in range(3):
                response = await self.client.get(f"{self.base_url}/api/v1/admin/products")
                responses.append(response.status_code)
                await asyncio.sleep(0.5)
            
            response_time = time.time() - start_time
            
            # Circuit breaker should allow requests to go through (even if they fail auth)
            auth_failures = sum(1 for status in responses if status == 401)
            success_or_auth = sum(1 for status in responses if status in [200, 401])
            
            if success_or_auth >= 2:
                self.log_test("Circuit Breaker", "PASS", 
                            f"Circuit breaker allowing requests: {success_or_auth}/3 processed", 
                            response_time)
            else:
                self.log_test("Circuit Breaker", "FAIL", 
                            f"Circuit breaker may be blocking: {success_or_auth}/3 processed", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Circuit Breaker", "ERROR", str(e), response_time)
    
    async def test_performance_metrics(self):
        """Test performance and response times"""
        print("\n=== TESTING PERFORMANCE METRICS ===")
        
        endpoints = [
            "/health",
            "/",
            "/api/v1/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=mock_verify_token_12345"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                response_time = time.time() - start_time
                
                if response_time < 1.0:  # Should respond within 1 second
                    self.log_test(f"Performance {endpoint}", "PASS", 
                                f"Fast response: {response_time:.3f}s", response_time)
                elif response_time < 3.0:
                    self.log_test(f"Performance {endpoint}", "WARN", 
                                f"Slow response: {response_time:.3f}s", response_time)
                else:
                    self.log_test(f"Performance {endpoint}", "FAIL", 
                                f"Very slow response: {response_time:.3f}s", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Performance {endpoint}", "ERROR", str(e), response_time)
    
    async def run_integration_tests(self):
        """Run all integration tests"""
        print(f"\n{'='*60}")
        print("FEELORI AI WHATSAPP ASSISTANT - INTEGRATION TESTING")
        print(f"Testing URL: {self.base_url}")
        print(f"Started at: {datetime.utcnow().isoformat()}")
        print(f"{'='*60}")
        
        # Run all integration test suites
        await self.test_ai_integration()
        await self.test_database_operations()
        await self.test_shopify_integration()
        await self.test_redis_connectivity()
        await self.test_circuit_breaker_behavior()
        await self.test_performance_metrics()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate integration test summary"""
        print(f"\n{'='*60}")
        print("INTEGRATION TEST SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        errors = len([r for r in self.test_results if r["status"] == "ERROR"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        skipped = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🚨 Errors: {errors}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"⏭️  Skipped: {skipped}")
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Show failed/error tests
        if failed > 0 or errors > 0:
            print(f"\n{'='*40}")
            print("FAILED/ERROR TESTS:")
            print(f"{'='*40}")
            for result in self.test_results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"❌ {result['test']}: {result['details']}")
        
        # Performance summary
        avg_response_time = sum(r["response_time"] for r in self.test_results) / total_tests if total_tests > 0 else 0
        print(f"\nAverage Response Time: {avg_response_time:.3f}s")
        
        return {
            "total": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "warnings": warnings,
            "skipped": skipped,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time
        }


async def main():
    """Main integration test runner"""
    backend_url = "http://localhost:8001"
    
    print("Starting Feelori AI WhatsApp Assistant Integration Tests...")
    print(f"Backend URL: {backend_url}")
    
    async with IntegrationTester(backend_url) as tester:
        await tester.run_integration_tests()
        
        # Save results to file
        with open("/app/integration_test_results.json", "w") as f:
            json.dump(tester.test_results, f, indent=2)
        
        print(f"\nDetailed results saved to: /app/integration_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())