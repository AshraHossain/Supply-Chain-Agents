# Supply Chain AI Agent System

[![Tests](https://github.com/AshraHossain/Supply-Chain-Agents/actions/workflows/tests.yml/badge.svg)](https://github.com/AshraHossain/Supply-Chain-Agents/actions/workflows/tests.yml)
[![Lint](https://github.com/AshraHossain/Supply-Chain-Agents/actions/workflows/lint.yml/badge.svg)](https://github.com/AshraHossain/Supply-Chain-Agents/actions/workflows/lint.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A multi-agent supermarket replenishment system — **from demand prediction to a
human-controlled purchase order** — built as a **LangGraph** state graph and
**dockerized**. It implements the 7-step roadmap: map the workflow, split into
specialist agents, connect real tools, pass structured state, add human
approval, explain every decision, and evaluate the workflow.

```
Predict → Check Stock → Draft Order → Pick Supplier → Plan Delivery → Approve → Execute
```

**Features:**
- 🤖 9 AI agents with specialized roles (demand, inventory, procurement, supplier, delivery, exception handling, approval, execution, evaluation)
- 📊 Structured state machine with full audit trail
- 👤 Human-in-the-loop approval for risky orders
- 🔄 LangGraph-based orchestration with memory & checkpointing
- 🚀 Docker & FastAPI ready
- ✅ 29 comprehensive tests (all passing)
- 🔌 Support for OpenRouter, Anthropic, OpenAI, or mock LLM

## The agent graph

| Agent | Step | Job |
|-------|------|-----|
| **Demand** | Predict | Forecast demand from POS sales |
| **Inventory** | Check Stock | Compare on-hand/reorder point vs forecast |
| **Procurement** | Draft Order | Turn the stock signal into a draft order (SKU, qty, urgency) |
| **Supplier** | Pick Supplier | Choose supplier by cost / lead time / reliability |
| **Delivery** | Plan Delivery | Schedule DC, ship date, ETA, carrier |
| **Exception** | — | Flag supplier disruptions & stock-out risk early |
| **Human Approval** | Approve | Risky orders pause for a human; safe ones auto-approve |
| **Execute** | Execute | Issue or cancel the purchase order |
| **Evaluator** | Evaluate | Score completeness & handoff quality |

The bracketed order steps only run when a reorder is actually needed
(conditional edge after the Inventory agent). **Every agent attaches a
rationale** to its decision, producing a full audit trail.

## Human-in-the-loop

Approval is a real LangGraph [`interrupt`](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/).
An order needs a human when quantity **or** estimated cost exceeds the policy
thresholds, or when a critical exception is flagged. Otherwise it auto-approves.
A `MemorySaver` checkpointer lets a paused run be resumed by `thread_id`.

## Quick start

### Run with no API key (mock provider)

```bash
cp .env.example .env          # defaults are fine; or set LLM_PROVIDER=mock
echo "LLM_PROVIDER=mock" >> .env
pip install -r requirements.txt
python run_demo.py            # full end-to-end run over all SKUs
```

### Run with an LLM (OpenRouter — default)

```bash
cp .env.example .env
# in .env:
#   LLM_PROVIDER=openrouter
#   OPENROUTER_API_KEY=sk-or-...
#   LLM_MODEL=anthropic/claude-sonnet-4.5   # any OpenRouter "vendor/model" slug
pip install -r requirements.txt
python run_demo.py
```

`openrouter` is OpenAI-compatible — it points `ChatOpenAI` at
`https://openrouter.ai/api/v1`, so you can use any model OpenRouter serves
(`openai/gpt-4o-mini`, `google/gemini-2.0-flash-001`, etc.). `anthropic` and
`openai` providers are also supported with their own keys. Each agent computes a
deterministic proposal from its tools and the LLM reviews/finalizes it with
reasoning.

## Docker

```bash
# Defaults to the mock provider — runs with zero credentials
docker compose up --build

# With a real LLM (OpenRouter)
LLM_PROVIDER=openrouter OPENROUTER_API_KEY=sk-or-... \
  LLM_MODEL=anthropic/claude-sonnet-4.5 docker compose up --build
```

The API is then at `http://localhost:8000`.

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/health` | Liveness + active LLM provider |
| `GET`  | `/skus` | List known SKUs |
| `POST` | `/run` | Run the graph for a SKU; returns result or an approval request |
| `POST` | `/approve` | Resume a paused run by `thread_id` |

```bash
# Start a run (low stock → needs human approval)
curl -s localhost:8000/run -H 'content-type: application/json' \
  -d '{"sku":"SKU-MILK-1L"}'
# -> {"thread_id":"...","status":"awaiting_approval","approval_request":{...}}

# Approve it
curl -s localhost:8000/approve -H 'content-type: application/json' \
  -d '{"thread_id":"<id>","approved":true,"approver":"ash","reason":"ok"}'
```

## Tests

Run all tests with mock LLM (no API key needed):

```bash
LLM_PROVIDER=mock pytest tests/ -v
```

Run with coverage report:

```bash
LLM_PROVIDER=mock pytest tests/ --cov=app --cov-report=html
```

**Test Coverage:**
- ✅ 29 tests covering all agents and workflows
- ✅ Configuration & setup validation
- ✅ Agent-specific logic (demand, inventory, procurement, supplier, delivery)
- ✅ State management & validation
- ✅ Approval workflows
- ✅ Multi-SKU isolation & thread safety
- ✅ Edge cases & error handling
- ✅ End-to-end integration

**CI/CD:** Tests run automatically on push/PR. See [.github/CICD_SETUP.md](.github/CICD_SETUP.md) for details.

## Connecting real tools

`app/data/mock_data.py` simulates the POS, inventory DB, supplier catalog and
fleet schedule. Replace those functions with real API or MCP calls to go live —
the agents and graph don't change.

## Architecture

### Agent Workflow

Each agent is a specialized decision-maker:

1. **Demand Agent** — Forecasts unit demand from recent POS sales (7-day horizon)
2. **Inventory Agent** — Compares on-hand stock vs reorder point and forecast
3. **Procurement Agent** — Drafts the purchase order with urgency level
4. **Supplier Agent** — Selects best supplier by cost, lead time, reliability
5. **Delivery Agent** — Plans DC, ship date, ETA, and carrier
6. **Exception Agent** — Flags disruptions, stock-out risk, anomalies
7. **Approval Agent** — Pauses for human review if qty/cost exceeds thresholds
8. **Execute Agent** — Issues or cancels the final purchase order
9. **Evaluator Agent** — Scores completeness and handoff quality

### State Flow

```
Input (SKU, store, request)
  ↓
Demand Forecast
  ↓
Stock Signal (needs_reorder? Yes → continue; No → exit)
  ↓
Draft Order
  ↓
Supplier Choice
  ↓
Delivery Plan
  ↓
Exception Checks
  ↓
Approval Gate (high-risk? → human interrupt; else → auto-approve)
  ↓
Purchase Order (issued or cancelled)
  ↓
Evaluation (completeness & quality scores)
```

### Project Layout

```
.github/
  workflows/           GitHub Actions for CI/CD testing & linting
  CICD_SETUP.md        CI/CD documentation

app/
  config.py            Environment variables & approval thresholds
  state.py             TypedDict state + Pydantic schemas for each agent
  llm.py               LLM client wrapper (Anthropic/OpenAI/OpenRouter/mock)
  data/
    mock_data.py       Simulated POS, inventory, suppliers, fleet
  agents/
    demand.py          Demand forecasting agent
    inventory.py       Stock level & reorder point analysis
    procurement.py     Draft order creation
    supplier.py        Supplier selection
    delivery.py        Delivery planning
    exception.py       Exception detection
    evaluator.py       Workflow quality evaluation
  graph.py             LangGraph state machine + interrupts
  main.py              FastAPI endpoints

run_demo.py            End-to-end CLI demo (all SKUs or specific)
tests/
  test_graph.py        29 comprehensive unit & integration tests

docker-compose.yml     Docker orchestration (API + optional services)
Dockerfile             Multi-stage build for production
requirements.txt       Python dependencies
.env                   Runtime configuration (create from .env.example)
.env.example           Template with defaults
```

## Documentation

- [API Reference](docs/API.md) — Endpoint specs & examples
- [Agent Details](docs/AGENTS.md) — How each agent works internally
- [Configuration Guide](docs/CONFIG.md) — Environment variables & thresholds
- [Deployment Guide](docs/DEPLOYMENT.md) — Docker, cloud platforms, scaling
- [CI/CD Setup](docs/CICD.md) — GitHub Actions workflows & secrets
- [Contributing](CONTRIBUTING.md) — Development workflow & standards

## Performance

- **Latency:** ~1-2s per SKU (mock LLM) or ~3-5s (real LLM)
- **Memory:** ~150MB base + ~50MB per concurrent thread
- **Throughput:** 10+ concurrent orders with single instance
- **Reliability:** Full audit trail; all decisions are rationale'd & observable
