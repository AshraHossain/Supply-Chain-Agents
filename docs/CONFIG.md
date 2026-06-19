# Configuration Guide

All configuration is managed via environment variables in `.env`. This document explains each setting.

## Quick Start

Copy the template and customize:

```bash
cp .env.example .env
# Edit .env with your values
```

---

## LLM Configuration

### `LLM_PROVIDER`
Which LLM service to use.

**Options:**
- `openrouter` (default) — Use any model via OpenRouter
- `anthropic` — Use Anthropic's Claude directly
- `openai` — Use OpenAI's GPT models directly
- `mock` — Deterministic mock LLM (no API key needed, testing only)

**Example:**
```bash
LLM_PROVIDER=openrouter
```

---

### `LLM_MODEL`
The specific model to use. Format depends on provider.

**OpenRouter models** (use `vendor/model` format):
```bash
LLM_MODEL=openai/gpt-4o-mini              # GPT-4o mini via OpenRouter
LLM_MODEL=anthropic/claude-sonnet-4.5     # Claude Sonnet via OpenRouter
LLM_MODEL=google/gemini-2.0-flash-001     # Gemini 2.0 Flash via OpenRouter
```

**Anthropic (direct):**
```bash
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_MODEL=claude-opus-4-1
```

**OpenAI (direct):**
```bash
LLM_MODEL=gpt-4o-mini
LLM_MODEL=gpt-4
```

**Mock:**
```bash
LLM_MODEL=mock  # Not used with mock provider
```

**Default:** `openai/gpt-4o-mini`

---

## API Keys

Use only the key matching your `LLM_PROVIDER`.

### `OPENROUTER_API_KEY`
Your OpenRouter API key. Get it at https://openrouter.ai/keys

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

### `ANTHROPIC_API_KEY`
Your Anthropic API key (only if `LLM_PROVIDER=anthropic`). Get it at https://console.anthropic.com

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### `OPENAI_API_KEY`
Your OpenAI API key (only if `LLM_PROVIDER=openai`). Get it at https://platform.openai.com/api-keys

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

### `OPENROUTER_BASE_URL`
The OpenRouter API endpoint. Usually doesn't need to change.

```bash
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

**Default:** `https://openrouter.ai/api/v1`

---

## Business Policy

These thresholds determine when an order requires human approval.

### `APPROVAL_QTY_THRESHOLD`
If the order quantity exceeds this, require human approval.

```bash
APPROVAL_QTY_THRESHOLD=500  # Require approval for orders > 500 units
```

**Default:** `500` units

**Impact:**
- Orders of ≤500 units auto-approve
- Orders of >500 units pause and request human review
- Can be overridden by approver at review time

### `APPROVAL_COST_THRESHOLD`
If the order cost (quantity × unit_cost) exceeds this, require human approval.

```bash
APPROVAL_COST_THRESHOLD=10000  # Require approval for orders > $10,000
```

**Default:** `10000` USD

**Impact:**
- Orders costing ≤$10,000 auto-approve
- Orders costing >$10,000 pause and request human review
- Independent of quantity threshold (either one triggers approval)

---

## Example Configurations

### Development (mock LLM, fastest)
```bash
LLM_PROVIDER=mock
LLM_MODEL=mock

APPROVAL_QTY_THRESHOLD=1000
APPROVAL_COST_THRESHOLD=50000
```

### Local Testing (OpenRouter + Claude Sonnet)
```bash
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-sonnet-4.5
OPENROUTER_API_KEY=sk-or-v1-...

APPROVAL_QTY_THRESHOLD=500
APPROVAL_COST_THRESHOLD=10000
```

### Production (OpenAI GPT-4o via OpenRouter)
```bash
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4o
OPENROUTER_API_KEY=sk-or-v1-...

APPROVAL_QTY_THRESHOLD=250   # More conservative
APPROVAL_COST_THRESHOLD=5000  # Lower cost threshold
```

### Production (Anthropic Claude, native)
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-opus-4-1
ANTHROPIC_API_KEY=sk-ant-...

APPROVAL_QTY_THRESHOLD=250
APPROVAL_COST_THRESHOLD=5000
```

---

## Environment Variables in Code

Configuration is loaded at startup via `app/config.py`:

```python
from app.config import settings

settings.llm_provider      # e.g., 'openrouter'
settings.llm_model         # e.g., 'anthropic/claude-sonnet-4.5'
settings.openrouter_api_key
settings.anthropic_api_key
settings.openai_api_key
settings.openrouter_base_url
settings.approval_qty_threshold    # 500
settings.approval_cost_threshold   # 10000.0
```

---

## Docker Compose

Pass environment variables to `docker compose`:

```bash
# With mock LLM (no API key)
docker compose up --build

# With OpenRouter
LLM_PROVIDER=openrouter \
OPENROUTER_API_KEY=sk-or-v1-... \
LLM_MODEL=anthropic/claude-sonnet-4.5 \
docker compose up --build

# With custom approval thresholds
APPROVAL_QTY_THRESHOLD=1000 \
APPROVAL_COST_THRESHOLD=50000 \
docker compose up --build
```

Or edit `docker-compose.yml` directly:

```yaml
services:
  api:
    environment:
      LLM_PROVIDER: openrouter
      LLM_MODEL: anthropic/claude-sonnet-4.5
      OPENROUTER_API_KEY: sk-or-v1-...
      APPROVAL_QTY_THRESHOLD: "500"
      APPROVAL_COST_THRESHOLD: "10000"
```

---

## Validation

Configuration is validated at runtime. Common errors:

**Missing API key for non-mock provider:**
```
ValueError: OPENROUTER_API_KEY not set but LLM_PROVIDER=openrouter
```
→ Add your API key to `.env` or environment

**Invalid model name:**
```
ValueError: Model 'google/gemini-3.5-flash' not available on openrouter
```
→ Check model slug at https://openrouter.ai/models or use a valid model

**Invalid threshold (not a number):**
```
ValueError: APPROVAL_QTY_THRESHOLD must be numeric, got 'abc'
```
→ Use integers for qty, floats for cost

---

## Best Practices

1. **Use `.env.example` as reference** — Don't commit `.env` to git
2. **Separate configs per environment** — dev, staging, prod
3. **Rotate API keys regularly** — Revoke old keys from your provider
4. **Use less permissive models in production** — GPT-4o or Claude Opus for quality
5. **Set conservative approval thresholds** — Lower values = more human review
6. **Monitor API costs** — Track usage on your provider's dashboard
