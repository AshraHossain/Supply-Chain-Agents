"""Mock 'real tools' — POS sales, inventory DB, supplier catalog, fleet schedule.

Roadmap step 3 says connect real tools (POS, inventory DB, supplier catalog,
fleet schedule). Here those tools are simulated with deterministic in-memory
data so the system runs end-to-end without external dependencies. Swap these
functions for MCP / real API calls in production.
"""
from __future__ import annotations

# SKU master + 28 days of POS sales (units/day, most recent last)
_POS_SALES: dict[str, list[int]] = {
    "SKU-MILK-1L": [120, 140, 135, 150, 160, 210, 230, 125, 138, 142, 155,
                    158, 205, 240, 130, 145, 150, 162, 170, 215, 250, 135,
                    148, 152, 168, 175, 220, 260],
    "SKU-EGGS-12": [80, 75, 82, 90, 95, 130, 140, 78, 80, 85, 92, 96, 135,
                    150, 82, 84, 88, 95, 100, 140, 160, 85, 88, 90, 98, 105,
                    145, 165],
    "SKU-BREAD-WG": [60, 65, 70, 68, 72, 110, 120, 62, 66, 71, 69, 74, 112,
                     125, 64, 68, 72, 70, 76, 115, 130, 66, 70, 74, 72, 78,
                     118, 135],
    # Slow, stable mover that stays well above its reorder point (no-reorder path)
    "SKU-RICE-5KG": [18, 20, 19, 21, 22, 25, 24, 19, 20, 21, 20, 22, 26, 23,
                     18, 21, 20, 22, 21, 24, 25, 19, 20, 22, 21, 23, 25, 24],
}

# Inventory DB: on-hand units + reorder point per SKU
_INVENTORY: dict[str, dict[str, int]] = {
    "SKU-MILK-1L": {"on_hand": 210, "reorder_point": 400, "dc_id": "DC-NORTH"},
    "SKU-EGGS-12": {"on_hand": 520, "reorder_point": 300, "dc_id": "DC-NORTH"},
    "SKU-BREAD-WG": {"on_hand": 95, "reorder_point": 250, "dc_id": "DC-WEST"},
    "SKU-RICE-5KG": {"on_hand": 800, "reorder_point": 200, "dc_id": "DC-WEST"},
}

# Supplier catalog: who can supply each SKU, at what cost / lead time / reliability
_SUPPLIERS: dict[str, list[dict]] = {
    "SKU-MILK-1L": [
        {"supplier_id": "SUP-DAIRYCO", "supplier_name": "DairyCo",
         "unit_cost": 0.82, "lead_time_days": 2, "reliability": 0.97},
        {"supplier_id": "SUP-FARMFRESH", "supplier_name": "FarmFresh",
         "unit_cost": 0.78, "lead_time_days": 4, "reliability": 0.88},
    ],
    "SKU-EGGS-12": [
        {"supplier_id": "SUP-HENHOUSE", "supplier_name": "HenHouse",
         "unit_cost": 1.95, "lead_time_days": 3, "reliability": 0.94},
    ],
    "SKU-BREAD-WG": [
        {"supplier_id": "SUP-BAKEWELL", "supplier_name": "BakeWell",
         "unit_cost": 1.10, "lead_time_days": 1, "reliability": 0.99},
        {"supplier_id": "SUP-GRAINCO", "supplier_name": "GrainCo",
         "unit_cost": 0.95, "lead_time_days": 3, "reliability": 0.91},
    ],
    "SKU-RICE-5KG": [
        {"supplier_id": "SUP-GRAINCO", "supplier_name": "GrainCo",
         "unit_cost": 4.20, "lead_time_days": 5, "reliability": 0.93},
    ],
}

# Known supplier disruptions (drives the Exception agent)
_DISRUPTIONS: dict[str, str] = {
    "SUP-FARMFRESH": "Carrier strike — lead times +3 days this week.",
}

# Fleet / carrier schedule per DC
_FLEET: dict[str, dict] = {
    "DC-NORTH": {"carrier": "FleetA", "next_outbound": "2026-06-20"},
    "DC-WEST": {"carrier": "FleetB", "next_outbound": "2026-06-21"},
}


def get_pos_sales(sku: str) -> list[int]:
    return _POS_SALES.get(sku, [])


def get_inventory(sku: str) -> dict:
    return dict(_INVENTORY.get(sku, {"on_hand": 0, "reorder_point": 0, "dc_id": "DC-UNKNOWN"}))


def get_suppliers(sku: str) -> list[dict]:
    return [dict(s) for s in _SUPPLIERS.get(sku, [])]


def get_disruption(supplier_id: str) -> str | None:
    return _DISRUPTIONS.get(supplier_id)


def get_fleet(dc_id: str) -> dict:
    return dict(_FLEET.get(dc_id, {"carrier": "FleetX", "next_outbound": "2026-06-22"}))


def known_skus() -> list[str]:
    return list(_POS_SALES.keys())
