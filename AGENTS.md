# AGENTS.md

> This file tells coding agents how to work in the TechWatch repository.
> It is read by tools like OpenAI Codex, GitHub Copilot Workspace, and similar.

## Setup

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify
techwatch --help
ruff check .
mypy src/
pytest tests/
```

## Architecture Invariants

These rules are **non-negotiable**. Do not violate them without explicit human approval.

1. **Adapters only fetch raw source data.** They must not normalize, score, or explain.
2. **Normalization is deterministic Python.** No LLM calls in `src/techwatch/normalization/`.
3. **Scoring is deterministic Python.** No LLM calls in `src/techwatch/scoring/`.
4. **LLMs may plan and explain, never mutate normalized facts.** Agent outputs go through strict Pydantic validation.
5. **Condition is always 3-axis:** `canonical_condition`, `functional_state`, `cosmetic_grade`. Never collapse to a single enum.
6. **Currency is lossless.** Always preserve original amount + currency alongside any converted values. Never fabricate precision.
7. **Times are UTC internally, IANA timezone for display.** Use `zoneinfo`, not `pytz`.

## Source Compliance Rules

1. **Prefer official APIs** (Best Buy Products/Categories/Open Box, eBay Browse/Taxonomy).
2. **Prefer structured data (JSON-LD) over DOM scraping** when APIs are unavailable.
3. **Do not add authenticated scraping** in v1 — no retailer account login.
4. **Respect per-source rate limits** — every adapter has `max_qps`, `burst`, `cache_ttl`.
5. **Check `robots.txt` and legal guidance** before adding any new scraping adapter.
6. **All HTTP fetches go through the domain allowlist** in `src/techwatch/adapters/base.py`.

## Testing Rules

1. **Every feature needs unit tests.** Put them in `tests/unit/`.
2. **Any ranking change needs golden fixture updates** in `tests/golden/`.
3. **Any LLM schema change needs contract tests** in `tests/contracts/`.
4. **Normalization changes need parametrized tests** covering all marketplace variants.
5. **Run the full suite before opening a PR:** `pytest tests/ -x`

## Code Style

- **Formatter/Linter:** Ruff (`ruff check .` and `ruff format .`)
- **Type checker:** mypy strict mode (`mypy src/`)
- **Imports:** sorted by isort (integrated in Ruff)
- **Line length:** 100 characters
- **Docstrings:** Google style

## Protected Files

Do **not** edit these without explicit approval from a code owner:

- `.github/workflows/*`
- `docs/architecture/*`
- `src/techwatch/normalization/*`
- `src/techwatch/scoring/*`
- `AGENTS.md`
- `CODEOWNERS`
