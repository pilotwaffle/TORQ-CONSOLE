import json
import os
import time
import unittest
from urllib.request import Request, urlopen

BASE_URL = os.getenv("TORQ_BASE_URL", "https://torq-console.vercel.app")

def http_json(method: str, path: str, payload: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        method=method.upper(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)

class TestTelemetrySchemaContract(unittest.TestCase):
    def test_telemetry_health(self):
        data = http_json("GET", "/api/telemetry/health")
        self.assertTrue(data.get("configured"), data)
        self.assertEqual(data.get("backend"), "supabase", data)

    def test_learning_status(self):
        data = http_json("GET", "/api/learning/status")
        self.assertTrue(data.get("configured"), data)

    def test_telemetry_ingest_minimal(self):
        now = int(time.time())
        now_ms = now * 1000
        payload = {
            "trace": {
                "trace_id": f"contract-{now}",
                "session_id": "contract-session",
                "agent_name": "contract_test",
            },
            "spans": [
                {
                    "span_id": f"span-{now}",
                    "trace_id": f"contract-{now}",
                    "kind": "agent",
                    "name": "contract_span",
                    "start_ms": now_ms,
                }
            ],
        }
        data = http_json("POST", "/api/telemetry", payload)
        self.assertTrue(data.get("ok"), data)
        self.assertEqual(data.get("trace_id"), f"contract-{now}", data)
        self.assertGreaterEqual(int(data.get("spans_ingested", 0)), 1, data)

if __name__ == "__main__":
    unittest.main(verbosity=2)
