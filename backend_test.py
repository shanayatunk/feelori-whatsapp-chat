import requests
import sys
import json
from datetime import datetime

class FeeloriAPITester:
    def __init__(self, base_url="https://496955ca-aa39-4399-9071-3dc797aacf6f.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_key = "feelori-admin-2024-secure-key-change-in-production"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, auth_required=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required
        if auth_required:
            headers['Authorization'] = f'Bearer {self.api_key}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if auth_required:
            print(f"   Auth: Required")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            result = {
                'test_name': name,
                'success': success,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'response_data': None,
                'error': None
            }

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result['response_data'] = response.json()
                    print(f"   Response: {json.dumps(result['response_data'], indent=2)[:200]}...")
                except:
                    result['response_data'] = response.text[:200]
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    result['response_data'] = response.json()
                    print(f"   Error Response: {json.dumps(result['response_data'], indent=2)}")
                except:
                    result['response_data'] = response.text
                    print(f"   Error Response: {response.text}")

            self.test_results.append(result)
            return success, result['response_data']

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            result = {
                'test_name': name,
                'success': False,
                'expected_status': expected_status,
                'actual_status': 'ERROR',
                'response_data': None,
                'error': str(e)
            }
            self.test_results.append(result)
            return False, {}

    def test_health_check(self):
        """Test health check endpoint"""
        return self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )

    def test_root_endpoint(self):
        """Test root endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )

    def test_products_endpoint(self):
        """Test products endpoint"""
        return self.run_test(
            "Get Products",
            "GET",
            "api/products",
            200,
            params={"limit": 5}
        )

    def test_webhook_verification(self):
        """Test webhook verification"""
        return self.run_test(
            "Webhook Verification",
            "GET",
            "api/webhook",
            200,
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "feelori-verify-token",
                "hub.challenge": "12345"
            }
        )

    def test_webhook_verification_fail(self):
        """Test webhook verification with wrong token"""
        return self.run_test(
            "Webhook Verification (Wrong Token)",
            "GET",
            "api/webhook",
            403,
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "12345"
            }
        )

    def test_send_message(self):
        """Test send message endpoint"""
        return self.run_test(
            "Send Message",
            "POST",
            "api/send-message",
            200,
            data={
                "phone_number": "+1234567890",
                "message": "Test message from API test"
            },
            auth_required=True
        )

    def test_send_message_no_auth(self):
        """Test send message without authentication"""
        return self.run_test(
            "Send Message (No Auth)",
            "POST",
            "api/send-message",
            401,
            data={
                "phone_number": "+1234567890",
                "message": "Test message from API test"
            }
        )

    def test_send_message_invalid(self):
        """Test send message with invalid data"""
        return self.run_test(
            "Send Message (Invalid Data)",
            "POST",
            "api/send-message",
            422,
            data={
                "phone_number": "invalid-phone",
                "message": ""
            },
            auth_required=True
        )

    def test_get_customer(self):
        """Test get customer endpoint"""
        return self.run_test(
            "Get Customer",
            "GET",
            "api/customers/+1234567890",
            200,
            auth_required=True
        )

    def test_get_customer_no_auth(self):
        """Test get customer without authentication"""
        return self.run_test(
            "Get Customer (No Auth)",
            "GET",
            "api/customers/+1234567890",
            401
        )

    def test_get_orders(self):
        """Test get orders endpoint"""
        return self.run_test(
            "Get Orders",
            "GET",
            "api/orders/+1234567890",
            200,
            auth_required=True
        )

    def test_get_orders_no_auth(self):
        """Test get orders without authentication"""
        return self.run_test(
            "Get Orders (No Auth)",
            "GET",
            "api/orders/+1234567890",
            401
        )

    def test_get_metrics(self):
        """Test get metrics endpoint"""
        return self.run_test(
            "Get Metrics",
            "GET",
            "api/metrics",
            200,
            auth_required=True
        )

    def test_get_metrics_no_auth(self):
        """Test get metrics without authentication"""
        return self.run_test(
            "Get Metrics (No Auth)",
            "GET",
            "api/metrics",
            401
        )

    def test_webhook_post(self):
        """Test webhook POST endpoint"""
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "test_entry",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "test_message_id",
                                        "text": {
                                            "body": "Hello, this is a test message"
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        
        return self.run_test(
            "Webhook POST",
            "POST",
            "api/webhook",
            200,
            data=webhook_data
        )

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test_name']}")
            if not result['success']:
                if result['error']:
                    print(f"      Error: {result['error']}")
                else:
                    print(f"      Expected: {result['expected_status']}, Got: {result['actual_status']}")

def main():
    print("🚀 Starting Feelori AI WhatsApp Assistant API Tests")
    print("="*60)
    
    tester = FeeloriAPITester()
    
    # Run all tests
    print("\n🔧 Testing Core Endpoints...")
    tester.test_root_endpoint()
    tester.test_health_check()
    
    print("\n🛍️ Testing Shopify Integration...")
    tester.test_products_endpoint()
    
    print("\n📱 Testing WhatsApp Webhook...")
    tester.test_webhook_verification()
    tester.test_webhook_verification_fail()
    tester.test_webhook_post()
    
    print("\n💬 Testing Message Functionality...")
    tester.test_send_message()
    tester.test_send_message_no_auth()
    tester.test_send_message_invalid()
    
    print("\n👥 Testing Customer & Order Management...")
    tester.test_get_customer()
    tester.test_get_customer_no_auth()
    tester.test_get_orders()
    tester.test_get_orders_no_auth()
    
    print("\n📊 Testing Metrics & Analytics...")
    tester.test_get_metrics()
    tester.test_get_metrics_no_auth()
    
    # Print summary
    tester.print_summary()
    
    # Return exit code
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())