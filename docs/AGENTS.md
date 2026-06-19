# Agent Details

Each agent is a specialized decision-maker in the supply chain workflow. This document explains what each agent does and how it makes decisions.

## Demand Agent

**Job:** Forecast unit demand for the next 7 days

**Input:**
- SKU identifier
- Last 14 days of POS sales data

**Process:**
1. Calculate mean daily sales from last 14 days
2. Account for weekly patterns (weekends vs weekdays)
3. Multiply by 7-day horizon
4. Assign confidence (0.0-1.0) based on data availability

**Output:**
```python
{
  "sku": "SKU-MILK-1L",
  "forecast_units": 604,
  "horizon_days": 7,
  "confidence": 0.8,
  "rationale": "Mean of last 14 days (86.3 units/day) x 7 = 604"
}
```

**Rationale Examples:**
- High confidence (0.8+): Strong recent sales data, stable demand pattern
- Medium confidence (0.5-0.8): Some variability or recent stockouts
- Low confidence (<0.5): Sparse or inconsistent sales history

---

## Inventory Agent

**Job:** Determine if reorder is needed and suggest quantity

**Input:**
- SKU + current on-hand quantity
- Demand forecast (from Demand agent)
- Reorder point threshold
- Safety stock percentage (14%)

**Process:**
1. Check: `on_hand < reorder_point` OR `on_hand < forecast`?
2. If yes: Calculate reorder quantity to reach target (forecast + safety buffer)
3. If no: `needs_reorder = false`, `suggested_quantity = 0`

**Output:**
```python
{
  "sku": "SKU-MILK-1L",
  "on_hand": 95,
  "reorder_point": 250,
  "needs_reorder": true,
  "suggested_quantity": 600,
  "rationale": "On-hand 95 vs reorder point 250. Below threshold → order 600..."
}
```

**Decision Logic:**
- **Reorder if:** `on_hand ≤ reorder_point` OR `on_hand ≤ forecast`
- **Target stock:** `forecast + (forecast × 0.14)` to include safety margin
- **Quantity:** Enough to reach target without overshooting

---

## Procurement Agent

**Job:** Draft a purchase order with urgency level

**Input:**
- Suggested quantity from Inventory agent
- On-hand quantity (for urgency scoring)

**Process:**
1. Assign urgency based on stock depletion rate:
   - **High:** On-hand < 40% of reorder point
   - **Normal:** On-hand 40-70% of reorder point
   - **Low:** On-hand > 70% of reorder point
2. LLM reviews the draft and may adjust quantity/urgency with rationale

**Output:**
```python
{
  "sku": "SKU-MILK-1L",
  "quantity": 600,
  "urgency": "high",
  "rationale": "On-hand is 38% of reorder point, so urgency = high..."
}
```

**Urgency Impact:**
- **High urgency** → Triggers faster shipping (premium cost)
- **Normal** → Standard shipping
- **Low** → Can wait; may batch with other orders

---

## Supplier Agent

**Job:** Select the best supplier by cost, lead time, and reliability

**Input:**
- SKU
- Order quantity
- Urgency level

**Process:**
1. Query supplier catalog for all suppliers who stock the SKU
2. Score each supplier:
   - Cost per unit (lower is better)
   - Lead time (lower is better, weighted by urgency)
   - Reliability (98-99% on-time delivery)
3. Pick supplier with best blended score

**Output:**
```python
{
  "supplier_id": "SUP-BAKEWELL",
  "supplier_name": "BakeWell",
  "unit_cost": 1.1,
  "lead_time_days": 1,
  "rationale": "BakeWell: cost $1.10/unit, 1d lead, 99% reliability—best score for high urgency"
}
```

**Scoring:** Cost weighted 40%, lead time 40%, reliability 20%

---

## Delivery Agent

**Job:** Plan the shipment (DC, carrier, dates)

**Input:**
- Supplier choice
- Order quantity
- Urgency

**Process:**
1. Select destination DC (closest to store, or load-balanced)
2. Pick carrier based on urgency:
   - **High:** FleetA (premium, 1-day)
   - **Normal:** FleetB (standard, 2-day)
   - **Low:** FleetC (slow, 3-day+)
3. Calculate dates:
   - Ship date = next outbound + lead time offset
   - ETA = ship date + lead time + carrier transit

**Output:**
```python
{
  "dc_id": "DC-WEST",
  "ship_date": "2026-06-21",
  "eta_date": "2026-06-22",
  "carrier": "FleetB",
  "rationale": "Ship from DC-WEST on next outbound 2026-06-21 via FleetB..."
}
```

---

## Exception Agent

**Job:** Flag anomalies and risks

**Input:**
- All prior agent outputs
- Current inventory state

**Process:**
1. Check for critical conditions:
   - Stock-out risk (forecast > on-hand + incoming)
   - Supplier disruptions (downtime, capacity limits)
   - Unusual demand spikes
   - Cost overruns
2. Flag each with severity: `info`, `warning`, or `critical`

**Output:**
```python
[
  {
    "code": "STOCK_OUT_RISK",
    "severity": "critical",
    "message": "Forecast 604 > on-hand 95 + incoming 500. Will be short 9 units"
  }
]
```

**Severity Levels:**
- **Info:** Non-blocking observation (e.g., "order above median cost")
- **Warning:** Should review (e.g., "supplier at capacity, may miss ETA")
- **Critical:** May require human override (e.g., stock-out risk, supplier down)

---

## Approval Agent

**Job:** Determine if order needs human approval

**Input:**
- Draft order (quantity, cost, exceptions)
- Policy thresholds (qty_threshold, cost_threshold)

**Process:**
1. Calculate total cost = quantity × supplier unit_cost
2. Check: `quantity > qty_threshold` OR `cost > cost_threshold` OR `critical exception`?
3. If yes: **Pause workflow** and request human approval
4. If no: **Auto-approve** and continue

**Output:**
```python
{
  "required": true,  # if thresholds exceeded or critical exception
  "status": "pending",
  "approver": null,
  "reason": null
}
```

**Policy Thresholds (configurable via .env):**
- `APPROVAL_QTY_THRESHOLD`: 500 units (default)
- `APPROVAL_COST_THRESHOLD`: 10000 USD (default)

---

## Execute Agent

**Job:** Issue or cancel the purchase order based on approval

**Input:**
- Approval decision (approved: true/false)
- All prior order details

**Process:**
1. If approved: **Issue** PO to supplier
   - Generate PO number
   - Send to supplier (or queue for dispatch)
   - Record in order history
2. If rejected: **Cancel** the order
   - Mark as cancelled
   - Notify stakeholders
   - No shipment scheduled

**Output:**
```python
{
  "status": "issued",  # or "cancelled"
  "sku": "SKU-MILK-1L",
  "quantity": 600,
  "supplier_id": "SUP-BAKEWELL",
  "supplier_name": "BakeWell",
  "unit_cost": 1.1,
  "total_cost": 660.0,
  "dc_id": "DC-WEST",
  "eta_date": "2026-06-22",
  "carrier": "FleetB"
}
```

---

## Evaluator Agent

**Job:** Score the workflow quality

**Input:**
- All agent outputs
- Final purchase order

**Process:**
1. **Completeness:** Check that all expected artifacts are present
   - ✓ Demand forecast
   - ✓ Stock signal
   - ✓ Draft order
   - ✓ Supplier choice
   - ✓ Delivery plan
   - ✓ PO issued
2. **Handoff Quality:** Verify each decision has a rationale
   - Each agent recorded a `rationale` (5+ words)
   - Decisions flow logically from upstream outputs
   - No missing links in the chain

**Output:**
```python
{
  "completeness_score": 1.0,  # 0.0-1.0 (6/6 artifacts)
  "handoff_quality": 1.0,     # 0.0-1.0 (all decisions rationale'd)
  "notes": "6/6 expected artifacts present; 8/8 decisions carry rationale; 0 critical exceptions"
}
```

**Perfect Score:** 1.0 = all artifacts present + all decisions rationale'd
**Notes:** Summarize completeness & any gaps for operator review

---

## Decision Trail Example

For a single run, the `decisions` list captures every agent's reasoning:

```python
{
  "decisions": [
    {
      "agent": "demand",
      "summary": "Forecast 604 units over 7d (confidence 80%)",
      "rationale": "Mean of last 14 days (86.3 units/day) x 7 days = 604 units"
    },
    {
      "agent": "inventory",
      "summary": "Reorder needed: 600 units",
      "rationale": "On-hand 95 vs reorder point 250 and forecast 604. Below threshold..."
    },
    {
      "agent": "procurement",
      "summary": "Draft order: 600 x SKU-MILK-1L (high urgency)",
      "rationale": "Draft order for 600 units. On-hand is 38% of reorder point..."
    },
    ...
  ]
}
```

This audit trail allows operators to trace every decision back to its reasoning.
