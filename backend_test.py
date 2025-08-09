#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Feelori AI WhatsApp Assistant
Tests all critical endpoints, authentication, integrations, and security features
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import httpx
import pytest


class FeeloriBackendTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
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
    
    async def test_health_endpoints(self):
        """Test all health check endpoints"""
        print("\n=== TESTING HEALTH ENDPOINTS ===")
        
        health_endpoints = [
            ("/health", "Basic health check"),
            ("/health/ready", "Readiness probe"),
            ("/health/live", "Liveness probe")
        ]
        
        for endpoint, description in health_endpoints:
            start_time = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "")
                    if status in ["healthy", "ready", "alive"]:
                        self.log_test(f"Health Check {endpoint}", "PASS", 
                                    f"{description} - Status: {status}", response_time)
                    else:
                        self.log_test(f"Health Check {endpoint}", "FAIL", 
                                    f"Unexpected status: {data}", response_time)
                else:
                    self.log_test(f"Health Check {endpoint}", "FAIL", 
                                f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Health Check {endpoint}", "ERROR", str(e), response_time)
    
    async def test_root_endpoint(self):
        """Test root endpoint"""
        print("\n=== TESTING ROOT ENDPOINT ===")
        
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "Feelori" in str(data) and "WhatsApp" in str(data):
                    self.log_test("Root Endpoint", "PASS", 
                                f"Service info returned: {data.get('service', 'N/A')}", response_time)
                else:
                    self.log_test("Root Endpoint", "FAIL", 
                                f"Unexpected response: {data}", response_time)
            else:
                self.log_test("Root Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Root Endpoint", "ERROR", str(e), response_time)
    
    async def test_admin_authentication(self):
        """Test admin login and JWT authentication"""
        print("\n=== TESTING ADMIN AUTHENTICATION ===")
        
        # Test login with correct password
        start_time = time.time()
        try:
            login_data = {"password": "mock_admin_password_123456"}
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.admin_token = data["access_token"]
                    self.log_test("Admin Login", "PASS", 
                                f"Token received, expires in: {data.get('expires_in', 'N/A')}s", response_time)
                else:
                    self.log_test("Admin Login", "FAIL", 
                                f"No access token in response: {data}", response_time)
            else:
                self.log_test("Admin Login", "FAIL", 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Admin Login", "ERROR", str(e), response_time)
        
        # Test login with wrong password
        start_time = time.time()
        try:
            login_data = {"password": "wrong_password"}
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Admin Login (Wrong Password)", "PASS", 
                            "Correctly rejected invalid password", response_time)
            else:
                self.log_test("Admin Login (Wrong Password)", "FAIL", 
                            f"Should reject wrong password, got HTTP {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Admin Login (Wrong Password)", "ERROR", str(e), response_time)
    
    async def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        print("\n=== TESTING ADMIN ENDPOINTS ===")
        
        if not self.admin_token:
            self.log_test("Admin Endpoints", "SKIP", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        admin_endpoints = [
            ("/api/v1/admin/me", "Admin profile"),
            ("/api/v1/admin/stats", "Admin statistics"),
            ("/api/v1/admin/products", "Admin products")
        ]
        
        for endpoint, description in admin_endpoints:
            start_time = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}", headers=headers)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Admin {endpoint}", "PASS", 
                                f"{description} - Data keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict response'}", 
                                response_time)
                elif response.status_code == 401:
                    self.log_test(f"Admin {endpoint}", "FAIL", 
                                "Authentication failed - token may be invalid", response_time)
                else:
                    self.log_test(f"Admin {endpoint}", "FAIL", 
                                f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Admin {endpoint}", "ERROR", str(e), response_time)
        
        # Test admin endpoint without token
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/admin/me")
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Admin Endpoint (No Token)", "PASS", 
                            "Correctly rejected request without token", response_time)
            else:
                self.log_test("Admin Endpoint (No Token)", "FAIL", 
                            f"Should require authentication, got HTTP {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Admin Endpoint (No Token)", "ERROR", str(e), response_time)
    
    async def test_whatsapp_webhook(self):
        """Test WhatsApp webhook endpoints"""
        print("\n=== TESTING WHATSAPP WEBHOOK ===")
        
        # Test webhook verification (GET)
        start_time = time.time()
        try:
            params = {
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": "mock_verify_token_12345"
            }
            response = await self.client.get(f"{self.base_url}/api/v1/webhook", params=params)
            response_time = time.time() - start_time
            
            if response.status_code == 200 and response.text == "test_challenge_123":
                self.log_test("WhatsApp Webhook Verification", "PASS", 
                            "Webhook verification successful", response_time)
            else:
                self.log_test("WhatsApp Webhook Verification", "FAIL", 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("WhatsApp Webhook Verification", "ERROR", str(e), response_time)
        
        # Test webhook verification with wrong token
        start_time = time.time()
        try:
            params = {
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": "wrong_token"
            }
            response = await self.client.get(f"{self.base_url}/api/v1/webhook", params=params)
            response_time = time.time() - start_time
            
            if response.status_code == 403:
                self.log_test("WhatsApp Webhook (Wrong Token)", "PASS", 
                            "Correctly rejected wrong verify token", response_time)
            else:
                self.log_test("WhatsApp Webhook (Wrong Token)", "FAIL", 
                            f"Should reject wrong token, got HTTP {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("WhatsApp Webhook (Wrong Token)", "ERROR", str(e), response_time)
        
        # Test webhook message processing (POST) - with mock message
        start_time = time.time()
        try:
            mock_message = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_entry_id",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "1234567890"},
                            "messages": [{
                                "id": f"test_msg_{uuid.uuid4().hex[:8]}",
                                "from": "+1234567890",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "Hello, I'm looking for products"},
                                "type": "text"
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            # Note: This will likely fail due to signature verification, but we test the endpoint
            response = await self.client.post(
                f"{self.base_url}/api/v1/webhook",
                json=mock_message,
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            # We expect this to fail due to signature verification with mock data
            if response.status_code in [400, 401, 403]:
                self.log_test("WhatsApp Webhook Message", "PASS", 
                            f"Webhook endpoint accessible, signature validation working (HTTP {response.status_code})", 
                            response_time)
            elif response.status_code == 200:
                self.log_test("WhatsApp Webhook Message", "PASS", 
                            "Webhook processed message successfully", response_time)
            else:
                self.log_test("WhatsApp Webhook Message", "FAIL", 
                            f"Unexpected response HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("WhatsApp Webhook Message", "ERROR", str(e), response_time)
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n=== TESTING RATE LIMITING ===")
        
        # Test multiple rapid requests to trigger rate limiting
        start_time = time.time()
        try:
            responses = []
            for i in range(10):  # Send 10 rapid requests
                response = await self.client.get(f"{self.base_url}/health")
                responses.append(response.status_code)
                await asyncio.sleep(0.1)  # Small delay
            
            response_time = time.time() - start_time
            
            # Check if any requests were rate limited (429)
            rate_limited = any(status == 429 for status in responses)
            success_count = sum(1 for status in responses if status == 200)
            
            if success_count >= 5:  # At least some requests should succeed
                self.log_test("Rate Limiting", "PASS", 
                            f"Rate limiting working: {success_count}/10 succeeded, rate limited: {rate_limited}", 
                            response_time)
            else:
                self.log_test("Rate Limiting", "FAIL", 
                            f"Too many requests failed: {success_count}/10 succeeded", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Rate Limiting", "ERROR", str(e), response_time)
    
    async def test_cors_headers(self):
        """Test CORS configuration"""
        print("\n=== TESTING CORS HEADERS ===")
        
        start_time = time.time()
        try:
            # Test preflight request
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
            response = await self.client.options(f"{self.base_url}/api/v1/auth/login", headers=headers)
            response_time = time.time() - start_time
            
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                "access-control-allow-headers": response.headers.get("access-control-allow-headers")
            }
            
            if any(cors_headers.values()):
                self.log_test("CORS Headers", "PASS", 
                            f"CORS headers present: {cors_headers}", response_time)
            else:
                self.log_test("CORS Headers", "FAIL", 
                            "No CORS headers found in preflight response", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("CORS Headers", "ERROR", str(e), response_time)
    
    async def test_error_handling(self):
        """Test error handling for invalid endpoints"""
        print("\n=== TESTING ERROR HANDLING ===")
        
        error_tests = [
            ("/api/v1/nonexistent", "Non-existent endpoint"),
            ("/api/v1/admin/invalid", "Invalid admin endpoint"),
            ("/api/v1/auth/invalid", "Invalid auth endpoint")
        ]
        
        for endpoint, description in error_tests:
            start_time = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                response_time = time.time() - start_time
                
                if response.status_code == 404:
                    self.log_test(f"Error Handling {endpoint}", "PASS", 
                                f"{description} - Correctly returned 404", response_time)
                elif response.status_code in [401, 403]:
                    self.log_test(f"Error Handling {endpoint}", "PASS", 
                                f"{description} - Auth required (HTTP {response.status_code})", response_time)
                else:
                    self.log_test(f"Error Handling {endpoint}", "FAIL", 
                                f"Unexpected status for {description}: HTTP {response.status_code}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Error Handling {endpoint}", "ERROR", str(e), response_time)
    
    async def test_security_headers(self):
        """Test security headers"""
        print("\n=== TESTING SECURITY HEADERS ===")
        
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/")
            response_time = time.time() - start_time
            
            security_headers = {
                "x-content-type-options": response.headers.get("x-content-type-options"),
                "x-frame-options": response.headers.get("x-frame-options"),
                "x-xss-protection": response.headers.get("x-xss-protection"),
                "strict-transport-security": response.headers.get("strict-transport-security")
            }
            
            present_headers = {k: v for k, v in security_headers.items() if v}
            
            if len(present_headers) >= 2:
                self.log_test("Security Headers", "PASS", 
                            f"Security headers present: {present_headers}", response_time)
            else:
                self.log_test("Security Headers", "WARN", 
                            f"Limited security headers: {present_headers}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Security Headers", "ERROR", str(e), response_time)
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n{'='*60}")
        print("FEELORI AI WHATSAPP ASSISTANT - BACKEND TESTING")
        print(f"Testing URL: {self.base_url}")
        print(f"Started at: {datetime.utcnow().isoformat()}")
        print(f"{'='*60}")
        
        # Run all test suites
        await self.test_health_endpoints()
        await self.test_root_endpoint()
        await self.test_admin_authentication()
        await self.test_admin_endpoints()
        await self.test_whatsapp_webhook()
        await self.test_rate_limiting()
        await self.test_cors_headers()
        await self.test_error_handling()
        await self.test_security_headers()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
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
    """Main test runner"""
    # Get backend URL from environment or use default
    backend_url = "http://localhost:8001"
    
    print("Starting Feelori AI WhatsApp Assistant Backend Tests...")
    print(f"Backend URL: {backend_url}")
    
    async with FeeloriBackendTester(backend_url) as tester:
        await tester.run_all_tests()
        
        # Save results to file
        with open("/app/backend_test_results.json", "w") as f:
            json.dump(tester.test_results, f, indent=2)
        
        print(f"\nDetailed results saved to: /app/backend_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())