import hmac
import hashlib
import json
from locust import HttpUser, task, between

from app.server import settings # Import settings to get secrets

class WebhookUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    @task
    def post_webhook_message(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "from": "15559876543", # Use a different number for each user if needed
                            "id": "wamid.LOCUST_ID",
                            "text": {"body": "Load test message"},
                            "timestamp": "1678886400",
                            "type": "text"
                        }]
                    }
                }]
            }]
        }
        payload_bytes = json.dumps(payload).encode('utf-8')

        # Generate the signature for each request
        signature = "sha256=" + hmac.new(
            settings.whatsapp_webhook_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json"
        }

        self.client.post(
            f"/api/{settings.api_version}/webhook",
            data=payload_bytes,
            headers=headers,
            name="/api/v1/webhook" # Group results under this name in the Locust UI
        )