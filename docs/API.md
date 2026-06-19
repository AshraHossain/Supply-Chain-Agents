# API Reference

The FastAPI server exposes endpoints for running the supply chain graph and managing approvals.

## Endpoints

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "llm_provider": "openrouter",
  "llm_model": "openai/gpt-4o-mini"
}
```

---

### GET `/skus`
List all known SKUs in the system.

**Response:**
```json
{
  "skus": [
    "SKU-MILK-1L",
    "SKU-BREAD-WG",
    "SKU-RICE-5KG",
    "SKU-EGGS-12CT",
    "SKU-CHEESE-500G"
  ]
}
```

---

### POST `/run`
Start a new supply chain workflow for a SKU.

**Request:**
```json
{
  "sku": "SKU-MILK-1L",
  "store_id": "STORE-001",
  "request": "Routine replenishment check"
}
```

**Response (Auto-approved order):**
```json
{
  "sku": "SKU-MILK-1L",
  "status": "completed",
  "purchase_order": {
    "status": "issued",
    "sku": "SKU-MILK-1L",
    "quantity": 600,
    "supplier_id": "SUP-BAKEWELL",
    "supplier_name": "BakeWell",
    "unit_cost": 1.1,
    "total_cost": 660.0,
    "eta_date": "2026-06-22"
  },
  "decisions": [
    {
      "agent": "demand",
      "summary": "Forecast 604 units over 7d",
      "rationale": "Mean of last 14 days..."
    },
    ...
  ],
  "evaluation": {
    "completeness_score": 1.0,
    "handoff_quality": 1.0,
    "notes": "6/6 artifacts present..."
  }
}
```

**Response (Awaiting approval):**
```json
{
  "sku": "SKU-MILK-1L",
  "status": "awaiting_approval",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "approval_request": {
    "quantity": 1200,
    "sku": "SKU-MILK-1L",
    "supplier": "BakeWell",
    "estimated_cost": 1320.0,
    "exceptions": [
      {
        "severity": "warning",
        "message": "Order exceeds cost threshold"
      }
    ]
  }
}
```

**Status Codes:**
- `200` — Success (check `status` field for awaiting_approval or completed)
- `400` — Invalid SKU or missing fields
- `500` — Server error

---

### POST `/approve`
Resume a paused workflow by approving or rejecting the order.

**Request:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved": true,
  "approver": "manager@store.com",
  "reason": "Order within policy"
}
```

**Response:**
```json
{
  "status": "completed",
  "purchase_order": {
    "status": "issued",
    "sku": "SKU-MILK-1L",
    "quantity": 1200,
    "total_cost": 1320.0,
    "eta_date": "2026-06-23"
  }
}
```

**or (if rejected):**
```json
{
  "status": "completed",
  "purchase_order": {
    "status": "cancelled",
    "sku": "SKU-MILK-1L"
  }
}
```

---

## Examples

### Using cURL

**Start a run:**
```bash
curl -s http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"sku":"SKU-MILK-1L","store_id":"S1","request":"replenish"}'
```

**Get SKUs:**
```bash
curl -s http://localhost:8000/skus
```

**Approve an order:**
```bash
curl -s http://localhost:8000/approve \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id":"550e8400-e29b-41d4-a716-446655440000",
    "approved":true,
    "approver":"ash",
    "reason":"ok"
  }'
```

### Using Python

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Start a run
response = client.post("/run", json={
    "sku": "SKU-MILK-1L",
    "store_id": "S1",
    "request": "replenish"
})
data = response.json()

if data["status"] == "awaiting_approval":
    thread_id = data["thread_id"]
    # Later: approve it
    response = client.post("/approve", json={
        "thread_id": thread_id,
        "approved": True,
        "approver": "ash",
        "reason": "approved"
    })
    print(response.json())
else:
    print(data["purchase_order"])
```

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "SKU-UNKNOWN-999 not found in catalog"
}
```

**Common errors:**
- `400 Bad Request` — Missing required field or invalid SKU
- `404 Not Found` — Thread ID doesn't exist
- `500 Internal Server Error` — LLM or database error

---

## Rate Limiting

No rate limiting currently enabled. For production, consider:
- API key authentication
- Per-user rate limits (e.g., 100 requests/minute)
- Request queuing for high throughput
