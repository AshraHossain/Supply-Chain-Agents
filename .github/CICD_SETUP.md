# CI/CD Setup Guide

This project uses GitHub Actions for continuous integration and deployment. All workflows run automatically on push and pull requests.

## Workflows

### 1. **Tests** (`tests.yml`)
**Trigger:** Push to `main`/`develop` or any PR

Runs comprehensive test suite with mock LLM provider:
- Python 3.11 and 3.12
- All 29 unit tests
- Code coverage reporting
- No API keys required (uses mock LLM)

**View results:** Actions tab → Tests

### 2. **Lint & Format** (`lint.yml`)
**Trigger:** Push to `main`/`develop` or any PR

Code quality checks:
- Black (code formatting)
- isort (import sorting)
- flake8 (linting)

**View results:** Actions tab → Lint & Format

### 3. **Integration Tests** (`integration-tests.yml`)
**Trigger:** Manual workflow dispatch only

Runs tests with real LLM providers:
- Supports OpenRouter, Anthropic, OpenAI
- Requires API keys in GitHub Secrets
- Useful for validating real LLM integrations

**To run manually:**
1. Go to Actions tab
2. Select "Integration Tests (with real LLM)"
3. Click "Run workflow"
4. Choose LLM provider

## Setting Up Secrets

For integration tests, add API keys to GitHub Secrets:

1. Go to Settings → Secrets and variables → Actions
2. Add these secrets:
   - `OPENROUTER_API_KEY` — Your OpenRouter API key
   - `ANTHROPIC_API_KEY` — Anthropic API key (optional)
   - `OPENAI_API_KEY` — OpenAI API key (optional)

**Note:** Secrets are never logged or exposed in workflows.

## Status Badge

Add this to your README to show CI status:

```markdown
[![Tests](https://github.com/AshraHossain/Supply-Chain-Agents/actions/workflows/tests.yml/badge.svg)](https://github.com/AshraHossain/Supply-Chain-Agents/actions/workflows/tests.yml)
[![Lint](https://github.com/AshraHossain/Supply-Chain-Agents/actions/workflows/lint.yml/badge.svg)](https://github.com/AshraHossain/Supply-Chain-Agents/actions/workflows/lint.yml)
```

## Local Testing

Run tests locally before pushing:

```bash
# Mock LLM (no API key needed)
LLM_PROVIDER=mock pytest tests/ -v

# Real LLM (requires API key)
pytest tests/ -v
```

## Coverage Reports

Coverage reports are generated and uploaded to Codecov:
- View at https://codecov.io/github/AshraHossain/Supply-Chain-Agents
- Requires Codecov account (free for public repos)

## Troubleshooting

**Tests failing in CI but passing locally?**
- Check Python version (CI runs 3.11 & 3.12)
- Ensure all dependencies are in `requirements.txt`
- Mock LLM should have zero external dependencies

**Integration tests not running?**
- Verify API key secrets are added
- Only runs on manual trigger (workflow_dispatch)
- Check Actions tab for workflow status

**Coverage not uploading?**
- Codecov integration is optional (continue-on-error: true)
- Coverage still generated locally
