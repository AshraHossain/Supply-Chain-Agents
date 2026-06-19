# Graph Report - .  (2026-06-19)

## Corpus Check
- Corpus is ~6,567 words - fits in a single context window. You may not need a graph.

## Summary
- 217 nodes · 403 edges · 30 communities (14 shown, 16 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Core Agent Architecture|Core Agent Architecture]]
- [[_COMMUNITY_Agent Implementations|Agent Implementations]]
- [[_COMMUNITY_Data Structures & State|Data Structures & State]]
- [[_COMMUNITY_LLM Provider Integration|LLM Provider Integration]]
- [[_COMMUNITY_API & Deployment|API & Deployment]]
- [[_COMMUNITY_Testing Framework|Testing Framework]]
- [[_COMMUNITY_Approval Workflow|Approval Workflow]]
- [[_COMMUNITY_Configuration & Setup|Configuration & Setup]]
- [[_COMMUNITY_Mock Data Ecosystem|Mock Data Ecosystem]]
- [[_COMMUNITY_Delivery Scheduling|Delivery Scheduling]]
- [[_COMMUNITY_Exception Handling|Exception Handling]]
- [[_COMMUNITY_Utility Modules|Utility Modules]]
- [[_COMMUNITY_Demand Forecasting|Demand Forecasting]]
- [[_COMMUNITY_Inventory Checking|Inventory Checking]]
- [[_COMMUNITY_Procurement|Procurement]]
- [[_COMMUNITY_Supplier Selection|Supplier Selection]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 29|Community 29]]

## God Nodes (most connected - your core abstractions)
1. `_run()` - 25 edges
2. `Decision` - 21 edges
3. `LangGraph State Graph Orchestration` - 17 edges
4. `get_client()` - 12 edges
5. `Inventory Agent` - 12 edges
6. `Supplier Agent` - 12 edges
7. `Delivery Agent` - 12 edges
8. `SupplyChainState` - 11 edges
9. `Demand Agent` - 11 edges
10. `Exception Agent` - 10 edges

## Surprising Connections (you probably didn't know these)
- `4-Step Agent Design Pattern` --guides--> `LLMClient Multi-Provider Abstraction`  [INFERRED]
  CLAUDE.md → app/llm.py
- `Human-in-the-Loop Interrupt Pattern` --exemplifies--> `Human Approval Node with Interrupt`  [INFERRED]
  CLAUDE.md → app/graph.py
- `Audit Trail via Decisions List` --rationale_for--> `SupplyChainState TypedDict`  [EXTRACTED]
  CLAUDE.md → app/state.py
- `Structured Outputs Architecture Pattern` --exemplifies--> `Decision Pydantic Model`  [INFERRED]
  CLAUDE.md → app/state.py
- `Structured Outputs Architecture Pattern` --exemplifies--> `DemandForecast Pydantic Model`  [INFERRED]
  CLAUDE.md → app/state.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Specialized Agents Workflow** — demand_agent, inventory_agent, procurement_agent, supplier_agent, delivery_agent, exception_agent, human_approval, execute_node, evaluator_agent [EXTRACTED 1.00]
- **Structured Pydantic Output Pipeline** — demandforecast_class, stocksignal_class, draftorder_class, supplierchoice_class, deliveryplan_class, exceptionflag_class, approval_class, evaluation_class, decision_class [EXTRACTED 1.00]
- **Multi-Provider LLM Abstraction Layer** — anthropic_provider, openai_provider, openrouter_provider, mock_provider [EXTRACTED 1.00]
- **Mock Data Simulation Ecosystem** — pos_sales_data, inventory_db_data, suppliers_catalog_data, disruptions_data, fleet_schedule_data [EXTRACTED 1.00]

## Communities (30 total, 16 thin omitted)

### Community 0 - "Core Agent Architecture"
Cohesion: 0.09
Nodes (42): _add_days(), delivery_agent(), Delivery / DC-planning agent — Plan Delivery. One job: schedule the inbound deli, demand_agent(), Demand agent — Predict. One job: forecast demand from POS sales., evaluator_agent(), Evaluator agent — Evaluate the Workflow (roadmap step 7).  Checks the run for co, Specialist agents (roadmap step 2: split into specialist agents — one job each). (+34 more)

### Community 1 - "Agent Implementations"
Cohesion: 0.16
Nodes (15): exception_agent(), Exception agent — catch supplier delays / issues early. One job: flag exceptions, Rule-based monitor — fast, deterministic, no LLM needed for alerting triggers., Any, SupplyChainState, ApprovalRequest, approve(), _config() (+7 more)

### Community 2 - "Data Structures & State"
Cohesion: 0.20
Nodes (19): SupplyChainState, Delivery Agent, DeliveryPlan, Demand Agent, Disruption Monitor, DraftOrder, Exception Agent, ExceptionFlag Pydantic Model (+11 more)

### Community 3 - "LLM Provider Integration"
Cohesion: 0.14
Nodes (7): Runtime configuration loaded from environment variables., Settings, Mock 'real tools' — POS sales, inventory DB, supplier catalog, fleet schedule., _line(), main(), End-to-end CLI demo of the supply chain agent graph.  Usage:     python run_demo, run_one()

### Community 4 - "API & Deployment"
Cohesion: 0.18
Nodes (11): Test that supplier choice has all required fields and valid types., Test that high-cost orders require approval., Test that multiple SKU runs don't interfere with each other., _run(), test_approval_required_for_high_cost(), test_every_decision_has_rationale(), test_low_stock_triggers_order(), test_multiple_skus_independent() (+3 more)

### Community 5 - "Testing Framework"
Cohesion: 0.24
Nodes (10): POST /approve API Endpoint, POST /run API Endpoint, Approval Policy Thresholds, Docker Compose Service Configuration, FastAPI Service, Human Approval Node with Interrupt, Human-in-the-Loop Interrupt Pattern, LangGraph State Graph Orchestration (+2 more)

### Community 6 - "Approval Workflow"
Cohesion: 0.24
Nodes (10): Approval Pydantic Model, Audit Trail via Decisions List, Decision Pydantic Model, DeliveryPlan Pydantic Model, DemandForecast Pydantic Model, DraftOrder Pydantic Model, Evaluation Pydantic Model, Purchase Order Execution Node (+2 more)

### Community 7 - "Configuration & Setup"
Cohesion: 0.22
Nodes (10): Conditional Routing After Inventory, Decision, DemandForecast, Evaluation, Evaluator Agent, ExceptionFlag, Inventory Agent, Inventory Data (+2 more)

### Community 8 - "Mock Data Ecosystem"
Cohesion: 0.20
Nodes (9): Smoke tests — run with `LLM_PROVIDER=mock pytest`., Test that delivery plan has valid date fields., Test that configuration loads correctly from environment variables., Test that approval thresholds are properly typed as numeric values., Test that demand forecast contains required fields., test_config_loads_from_env(), test_config_thresholds_are_numeric(), test_delivery_plan_dates_valid() (+1 more)

### Community 9 - "Delivery Scheduling"
Cohesion: 0.22
Nodes (9): build_graph(), Test that different threads don't share state., Test that empty SKU is handled gracefully., Test that unknown SKU is handled gracefully., Test that the supply chain graph initializes without errors., test_empty_sku_string_handling(), test_graph_initialization(), test_thread_isolation() (+1 more)

### Community 10 - "Exception Handling"
Cohesion: 0.29
Nodes (7): 4-Step Agent Design Pattern, Anthropic LLM Provider, Deterministic Proposal + LLM Review, LLMClient Multi-Provider Abstraction, Mock LLM Provider, OpenAI LLM Provider, OpenRouter LLM Provider

### Community 11 - "Utility Modules"
Cohesion: 0.40
Nodes (3): LLMClient, Return a validated `schema` instance.          `fallback` is a deterministic pro, T

### Community 12 - "Demand Forecasting"
Cohesion: 0.33
Nodes (6): Supplier Disruptions Mock Data, Fleet Schedule Mock Data, Inventory Database Mock Data, Mock Data Tools Simulation, POS Sales Mock Data, Supplier Catalog Mock Data

## Knowledge Gaps
- **30 isolated node(s):** `SupplyChainState`, `SupplyChainState`, `SupplyChainState`, `SupplyChainState`, `SupplyChainState` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LangGraph State Graph Orchestration` connect `Testing Framework` to `Data Structures & State`, `LLM Provider Integration`, `Approval Workflow`, `Configuration & Setup`?**
  _High betweenness centrality (0.249) - this node is a cross-community bridge._
- **Why does `delivery_agent()` connect `Core Agent Architecture` to `Data Structures & State`?**
  _High betweenness centrality (0.135) - this node is a cross-community bridge._
- **Why does `SupplyChainState` connect `Data Structures & State` to `Core Agent Architecture`, `Configuration & Setup`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Inventory Agent` (e.g. with `DemandForecast` and `Inventory Data`) actually correct?**
  _`Inventory Agent` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Supply Chain AI Agent System — replenishment to human-controlled.`, `Specialist agents (roadmap step 2: split into specialist agents — one job each).`, `Delivery / DC-planning agent — Plan Delivery. One job: schedule the inbound deli` to the rest of the system?**
  _77 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Core Agent Architecture` be split into smaller, more focused modules?**
  _Cohesion score 0.09200603318250378 - nodes in this community are weakly interconnected._
- **Should `LLM Provider Integration` be split into smaller, more focused modules?**
  _Cohesion score 0.14166666666666666 - nodes in this community are weakly interconnected._