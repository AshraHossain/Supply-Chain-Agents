# Contributing Guide

Thank you for contributing to the Supply Chain AI Agent System! This guide explains how to set up your development environment and contribute code.

## Getting Started

### Fork & Clone

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/Supply-Chain-Agents.git
cd Supply-Chain-Agents
git remote add upstream https://github.com/AshraHossain/Supply-Chain-Agents.git
```

### Setup Development Environment

```bash
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Install Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-feature
# or for bug fixes:
git checkout -b fix/my-bug
```

Branch naming:
- `feature/` — New feature
- `fix/` — Bug fix
- `docs/` — Documentation
- `refactor/` — Code refactoring
- `test/` — Test improvements

### 2. Make Changes

Follow these conventions:

**Code Style:**
- Use Black for formatting: `black app tests`
- Use isort for imports: `isort app tests`
- Type hints on all functions: `def my_func(x: str) -> dict:`
- Docstrings on public functions (one-line is fine)

**Commit Messages:**
```
type(scope): description

Longer explanation if needed.

Fixes #123
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`

Example:
```
feat(demand): add seasonal adjustment factor

Incorporate weekly patterns into demand forecast.
Improves accuracy by ~8% on test set.

Fixes #45
```

### 3. Run Tests Locally

```bash
# Test with mock LLM (fast)
LLM_PROVIDER=mock pytest tests/ -v

# Test with coverage
LLM_PROVIDER=mock pytest tests/ --cov=app

# Lint & format
black --check app tests
isort --check-only app tests
flake8 app tests
```

### 4. Push & Create Pull Request

```bash
git push origin feature/my-feature
```

Then create a PR on GitHub with:
- Clear title
- Description of changes
- Link to related issues
- Any breaking changes noted

---

## Testing

### Running Tests

```bash
# Mock LLM (no API key needed)
LLM_PROVIDER=mock pytest

# Real LLM (requires API key in .env)
pytest

# Specific test
pytest tests/test_graph.py::test_low_stock_triggers_order

# With coverage
pytest --cov=app --cov-report=html
```

### Writing Tests

Add tests in `tests/test_graph.py` or create new test files:

```python
def test_my_feature():
    """Test that my feature works correctly."""
    from app.agents.my_agent import my_agent
    
    # Setup
    state = {"sku": "SKU-TEST", ...}
    
    # Execute
    result = my_agent(state)
    
    # Assert
    assert result["status"] == "success"
    assert len(result["rationale"]) > 0
```

**Test Guidelines:**
- Prefix functions with `test_`
- Use descriptive names: `test_demand_confidence_for_new_sku()`
- Test both success and edge cases
- Include assertions on rationale (agents must explain decisions)
- Use mock LLM by default

---

## Code Structure

### Adding a New Agent

1. Create file: `app/agents/my_agent.py`
2. Define agent function with type hints
3. Use Pydantic models for output (see `app/state.py`)
4. Include system prompt & fallback
5. Add to graph in `app/graph.py`
6. Write tests in `tests/test_graph.py`

Example:

```python
from ..state import Decision, SupplyChainState

SYSTEM = "You are the MyAgent..."

def my_agent(state: SupplyChainState) -> dict:
    sku = state["sku"]
    
    # Your logic here
    result = {"key": "value", "rationale": "because..."}
    
    decision = Decision(
        agent="my_agent",
        summary="What I decided",
        rationale="Why I decided it"
    )
    
    return {"my_output": result, "decisions": [decision]}
```

### Modifying State

The `SupplyChainState` is in `app/state.py`. If you add a new field:

1. Add to `SupplyChainState` TypedDict
2. Create corresponding Pydantic model if structured
3. Update agents that read/write it
4. Update tests that check the state
5. Update documentation

---

## Code Quality Standards

### Type Hints

All functions should have type hints:

```python
from typing import Optional, Dict, List
from app.state import SupplyChainState, Decision

def my_function(state: SupplyChainState, count: int = 5) -> Dict[str, str]:
    """Brief description."""
    return {"key": "value"}
```

### Docstrings

Public functions need docstrings. Keep them short:

```python
def my_function(state: SupplyChainState) -> dict:
    """Calculate something important."""
    ...
```

### No Dead Code

- Delete unused variables, functions, imports
- No commented-out code blocks
- No `# TODO` without a GitHub issue reference

### Error Handling

- Validate inputs at system boundaries
- Let exceptions propagate for agent errors
- Log errors with context

```python
try:
    result = some_operation()
except ValueError as e:
    logger.error(f"Invalid input for {sku}: {e}")
    raise
```

---

## Documentation

### README Updates

If your feature is user-facing, update the README with:
- What it does
- How to use it
- Any new configuration

### Agent Documentation

Add your agent to `docs/AGENTS.md` with:
- Input & output examples
- Decision logic
- Impact on overall workflow

### Code Comments

Don't comment *what* the code does (variable names should do that). Comment *why*:

```python
# BAD
x = y + 1  # Add one to y

# GOOD
safety_stock = demand * 1.14  # Add 14% safety margin per company policy
```

---

## Common Tasks

### Running the Demo

```bash
LLM_PROVIDER=mock python run_demo.py SKU-MILK-1L
```

### Checking Your Changes Against CI

Local CI checks (what GitHub Actions will run):

```bash
# Tests
LLM_PROVIDER=mock pytest tests/ -v

# Formatting
black app tests
isort app tests

# Linting
flake8 app tests

# Type checking (optional, future enhancement)
mypy app
```

### Running Docker Locally

```bash
docker compose up --build

# In another terminal
curl http://localhost:8000/health
```

---

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Tests pass: `LLM_PROVIDER=mock pytest`
- [ ] Code is formatted: `black app tests`
- [ ] Imports are sorted: `isort app tests`
- [ ] No linting errors: `flake8 app tests`
- [ ] New tests added for new features
- [ ] All agents have rationales in their output
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventions
- [ ] No API keys or secrets in the code

---

## Questions?

- Check existing issues & discussions
- Look at agent examples in `app/agents/`
- Review test examples in `tests/test_graph.py`
- Ask in a GitHub issue

Happy coding! 🚀
