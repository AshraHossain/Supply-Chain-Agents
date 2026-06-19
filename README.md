# Supply Chain AI Agent System

A multi-agent supermarket replenishment system — **from demand prediction to a
human-controlled purchase order** — built as a **LangGraph** state graph and
**dockerized**. It implements the 7-step roadmap: map the workflow, split into
specialist agents, connect real tools, pass structured state, add human
approval, explain every decision, and evaluate the workflow.

```
Predict → Check Stock → Draft Order → Pick Supplier → Plan Delivery → Approve → Execute
```

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

```bash
LLM_PROVIDER=mock pytest -q
```

## Connecting real tools

`app/data/mock_data.py` simulates the POS, inventory DB, supplier catalog and
fleet schedule. Replace those functions with real API or MCP calls to go live —
the agents and graph don't change.

## Layout

```
app/
  config.py          env-driven settings & approval thresholds
  state.py           structured state + per-agent Pydantic schemas
  llm.py             anthropic / openai / mock client with structured output
  data/mock_data.py  simulated "real tools"
  agents/            the 7 specialist agents + evaluator
  graph.py           LangGraph wiring + human-approval interrupt
  main.py            FastAPI service
run_demo.py          end-to-end CLI demo
tests/test_graph.py  smoke tests
```
