import hmac
import hashlib
import json
from unittest.mock import AsyncMock

# Assuming your settings are accessible for testing
from app.server import settings, services 

def test_webhook_verification_success(test_client):
    """Test the webhook verification GET request."""
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": "12345",
        "hub.verify_token": settings.whatsapp_verify_token
    }
    response = test_client.get(f"/api/{settings.api_version}/webhook", params=params)
    assert response.status_code == 200
    assert response.text == "12345"

def test_webhook_verification_failure(test_client):
    """Test a failed webhook verification."""
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": "12345",
        "hub.verify_token": "wrong_token"
    }
    response = test_client.get(f"/api/{settings.api_version}/webhook", params=params)
    assert response.status_code == 403

def test_handle_webhook_success(test_client, mocker):
    """Test a valid POST to the webhook, mocking the message queue."""
    # Mock the RedisMessageQueue's add_message method
    mock_add_message = mocker.patch.object(services.message_queue, 'add_message', new_callable=AsyncMock)

    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "field": "messages",
                "value": {
                    "messages": [{
                        "from": "15551234567",
                        "id": "wamid.ID",
                        "text": {"body": "Hello"},
                        "timestamp": "1678886400",
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    payload_bytes = json.dumps(payload).encode('utf-8')
    
    # Generate a valid signature for the test
    signature = "sha256=" + hmac.new(
        settings.whatsapp_webhook_secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }

    response = test_client.post(f"/api/{settings.api_version}/webhook", content=payload_bytes, headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify that our mocked queue function was called once
    mock_add_message.assert_awaited_once()

def test_admin_stats_unauthorized(test_client):
    """Test that the admin stats endpoint is protected."""
    response = test_client.get(f"/api/{settings.api_version}/admin/stats")
    assert response.status_code == 401 # Or 403 depending on your setup