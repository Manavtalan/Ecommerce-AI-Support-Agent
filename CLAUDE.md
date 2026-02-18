# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
Read this file fully before making any changes. Every section exists to prevent
a known mistake or encode a hard-won decision.

> **Scope:** This file covers project-wide rules only. For workflow-specific
> knowledge (e.g. how to write a new brand config, how to add a tool), see the
> skill files in `.claude/skills/`.

---

## Project Overview

Production-grade multi-brand AI customer support agent for D2C e-commerce.
Single codebase, multi-instance deployment — different brands share core
intelligence but have **completely isolated data, voice, and policies**.

The agent handles inbound customer messages end-to-end: classifying intent,
detecting emotion, querying order/product/shipping/policy data, and generating
brand-voiced responses — with smart escalation to human agents when needed.

**This is not a chatbot prototype. It is production software.**
Every change must preserve: brand isolation, escalation precision, and
LLM-based intent classification. See Key Constraints before touching any
of these systems.

---

## Quick Commands

All commands run from `ai-cx-agent/` with the virtual environment activated.

```bash
# --- Environment Setup ---
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
.venv\Scripts\activate             # Windows
pip install -r requirements.txt

# --- Running the Agent ---
python main.py                     # Interactive CLI session

# --- Testing ---
pytest tests/automated/                                      # Full test suite
pytest tests/automated/test_emotion_handling.py -v          # Single file, verbose
pytest tests/automated/ -k "escalation" -v                  # Tests matching keyword
pytest tests/automated/ --tb=short                          # Shorter tracebacks

# --- Diagnostics & Validation ---
python scripts/diagnose_agent.py                # Health check all systems
python scripts/validate_production_ready.py    # Pre-deploy checklist

# --- Useful Dev One-Liners ---
python -c "from core.orchestrator import ConversationOrchestrator; print('Import OK')"
python -m pytest tests/ --collect-only          # See what tests exist without running
```

**IMPORTANT:** Always run `python scripts/validate_production_ready.py` before
marking any feature as complete. It catches env issues, brand config errors,
and broken tool connections.

---

## Architecture

### Request Flow (Step-by-Step)

Every inbound message travels this exact pipeline. Do not reorder steps.

```
User Message
  │
  ▼
1. Order ID Extraction
   └─ Regex scan of raw message for order number patterns
  │
  ▼
2. Intent Classification  [LLM call: GPT-4o-mini]
   └─ Returns UserIntent enum + confidence float (0–1)
   └─ DO NOT replace with keyword matching — see Key Constraints
  │
  ▼
3. Emotion Detection  [rule-based, no LLM]
   └─ Keyword scan + emoji + caps ratio + punctuation + sarcasm heuristics
   └─ Returns emotion label + intensity float (0–10)
  │
  ▼
4. Immediate Escalation Check  [pre-LLM gate]
   └─ Hard triggers: legal threats, abuse, self-harm keywords
   └─ Short-circuits pipeline — skips all LLM calls if triggered
  │
  ▼
5. Tool Execution  [parallel where possible]
   └─ get_order_status, search_knowledge, get_product_info,
      check_shipping_eligibility
   └─ Each tool has retry logic (3 attempts, exponential backoff)
  │
  ▼
6. Smart Context Management
   └─ Prunes conversation history to 20 messages / 4000 tokens
   └─ Tracks active order IDs and recent topics
  │
  ▼
7. Smart Escalation Check  [emotion-threshold gate]
   └─ Evaluates emotion intensity + retry count + unresolved issues
   └─ Thresholds: warn at 6, escalate at 8+ (see smart_escalation.py)
  │
  ▼
8. Response Generation  [LLM call: GPT-4o-mini]
   └─ Prompt = system_prompt + brand_voice + context + tool_results + history
   └─ Brand voice injected here — forbidden phrases enforced post-generation
  │
  ▼
Agent Response
```

---

## Core Modules

### `core/` — The Engine

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `orchestrator.py` | Central entry point. Runs the full request pipeline. All external callers talk to this. | `ConversationOrchestrator` |
| `intelligence/intent_classifier.py` | LLM-powered intent classification. Returns structured intent with confidence. | `UserIntent`, `IntentResult` |
| `emotion/detector.py` | Multi-signal emotion analysis. No LLM — pure heuristics for latency. | `EmotionResult`, `EmotionType` |
| `conversation/context.py` | Multi-turn memory. Sliding window of 20 messages / 4000 tokens. | `ConversationContext`, `Message` |
| `conversation/smart_escalation.py` | Human handoff decision engine. Checks emotion thresholds + retry failures. | `EscalationDecision`, `EscalationTrigger` |
| `tools/registry.py` | Tool executor with retry logic. Wraps all 4 data tools. | `ToolRegistry`, `ToolResult` |
| `brands/voice.py` | Per-brand tone, formality, emoji prefs, signature phrases, forbidden phrases. | `BrandVoice` |
| `brands/registry.py` | Multi-brand config loader. Handles session isolation between brands. | `BrandRegistry`, `BrandSession` |
| `llm/response_composer.py` | Prompt assembly + OpenAI call. Injects brand voice and context. | `ResponseComposer`, `LLMPrompt` |
| `rag/retriever.py` | Policy retrieval via Qdrant. **Currently disabled** — falls back to JSON search. | `RAGRetriever` |
| `utils/brand_loader.py` | Loads brand YAML configs. **All accessors must be null-safe** — missing keys are common in new brand configs. | `BrandLoader` |

### Tools (the 4 core data tools)

All tools live in `core/tools/` and are registered in `tools/registry.py`.

| Tool | What It Does | Input | Output |
|------|-------------|-------|--------|
| `get_order_status` | Fetches order from test_data or live OMS | `order_id: str`, `brand_id: str` | `OrderStatus` |
| `search_knowledge` | Searches policy docs + FAQs | `query: str`, `brand_id: str` | `List[KnowledgeChunk]` |
| `get_product_info` | Product details + availability | `product_id: str`, `brand_id: str` | `ProductInfo` |
| `check_shipping_eligibility` | Checks if order qualifies for free reshipping | `order_id: str`, `brand_id: str` | `ShippingEligibility` |

**All tools are brand-scoped.** Always pass `brand_id` — never query without it.
Tool results are never shared across brand sessions. See Key Constraints.

---

## Brand System

### Brand Configuration Files

Each brand lives in `test_data/brands/<brand_id>/` with three YAML files:

```
test_data/brands/
  fashionhub/
    brand_config.yaml       # voice personality, policies, escalation rules, hours
    voice_guidelines.yaml   # tone descriptors, sample phrases, forbidden words
    integrations.yaml       # channel config (email, chat, SMS settings)
```

### Adding a New Brand

1. Copy `test_data/brands/fashionhub/` as a template
2. Edit all three YAML files — especially `brand_config.yaml`
3. Run `python scripts/validate_production_ready.py` to check for missing keys
4. Add at least 3 test orders in `test_data/orders/<brand_id>/`
5. Write at minimum one escalation test and one voice test

### Brand Isolation Rules

- **Never** pass data from one brand session to another
- **Never** use a brand's policies to answer a query from a different brand
- `BrandRegistry.get_session(brand_id)` creates fully isolated session objects
- If you see any code sharing a context or registry object across two different
  brand IDs, that is a critical bug

---

## Test Data Reference

Located in `test_data/`. All test data is fictional.

### Key Test Orders

| Order ID | Status | Scenario |
|----------|--------|----------|
| `12345` | Delivered | Happy path, normal resolution |
| `12348` | Delayed | Frustrated customer scenario |
| `12350` | Wrong Item | Wrong size delivered |
| `12353` | Damaged | Item arrived damaged |

Use these order IDs in tests. Don't hardcode other IDs in test assertions
without first confirming they exist in `test_data/orders/`.

### Test Data Counts
- **Orders:** 11 (varied statuses)
- **Products:** 15
- **Policy docs:** 5
- **FAQs:** 35+

---

## Environment & Configuration

### Environment Files

```
.env                        # Local dev overrides (not committed)
config/development.env      # Dev defaults (committed)
config/production.env       # Prod defaults (committed, no secrets)
```

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | All LLM calls use this |
| `QDRANT_URL` | RAG only | Not needed while RAG is disabled |
| `QDRANT_API_KEY` | RAG only | Not needed while RAG is disabled |
| `LOG_LEVEL` | Optional | Defaults to `INFO` |
| `BRAND_DATA_PATH` | Optional | Defaults to `test_data/brands/` |

### Model Configuration

The agent uses **GPT-4o-mini for all LLM calls** (cost-optimized).
Do not upgrade to GPT-4o without first running a cost impact analysis.
If you add a new LLM call, use `gpt-4o-mini` unless there is a documented
reason otherwise.

---

## RAG System (Disabled — Day 2)

The `rag/` module exists but is not active.

**Current state:**
- `rag/retriever.py` is written but all Qdrant client calls are commented out
- Knowledge lookups fall back to direct JSON search via `tools/knowledge_tool.py`
- `sentence-transformers` and `qdrant-client` are in requirements but not called

**When re-enabling RAG:**
1. Spin up a Qdrant instance (local Docker or Qdrant Cloud)
2. Set `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
3. Run `python scripts/seed_qdrant.py` to index the policy docs
4. Uncomment the client calls in `rag/retriever.py`
5. Run `pytest tests/automated/test_rag.py -v` to validate

Do not partially enable RAG — it's either fully on or fully off per brand.

---

## Key Constraints

These encode architectural decisions that, if violated, will cause incorrect
behavior in production.

### 1. Brand Data Isolation Is Absolute

Never mix order, policy, or product data across brands. Every tool call must
include `brand_id`. Every session object is brand-scoped. There is no legitimate
reason to share data across brand sessions.

### 2. LLM for Intent, Not Regex

The intent classifier uses LLM calls intentionally. Customer messages are
ambiguous — "It's broken" could mean a damaged product, a website bug, or
emotional frustration. Keyword matching fails at scale. Do not replace
`intelligence/intent_classifier.py` with regex or keyword logic.

### 3. Escalation Thresholds Are Calibrated

The escalation logic in `conversation/smart_escalation.py` was tuned to
achieve <5% false positive escalations. The thresholds (warn at 6, escalate
at 8+) are not arbitrary. Before changing any threshold, run the full test
suite and confirm escalation test pass rates don't drop.

### 4. Emotion Intensity Is a Float (0–10), Not a Category

The detector returns a float, not a string label. Downstream code checks
specific numeric thresholds (3.0, 6.0, 8.0). Use numeric comparisons —
not string matching on the label.

### 5. Null-Safe Brand Config Access Is Non-Optional

Brand YAML files are authored by non-engineers — keys will be missing.
Always use the null-safe accessors in `utils/brand_loader.py`. Never do
`config["key"]` directly on a brand config dict.

### 6. Tool Retries Are Baked In — Don't Add Your Own

`tools/registry.py` handles retry logic (3 attempts, exponential backoff)
for all tools. Do not add manual retry loops around tool calls elsewhere —
double-retrying creates unpredictable latency spikes.

---

## Testing

- **`tests/automated/`** — fast, no external calls (all LLM calls are mocked); run on every change
- **`tests/integration/`** — require live `OPENAI_API_KEY`; run before releases
- Test data is deterministic — use the order IDs from the table above

When writing new tests:
1. Mock all LLM calls using fixtures in `tests/fixtures/llm_mocks.py`
2. Use `brand_id="fashionhub"` as the default test brand
3. Assert on `ConversationResponse` fields — not on raw string content
4. Cover at least: happy path, emotion edge case, escalation trigger

---

## Common Gotchas

- **`brand_loader.py` null safety** — missing YAML keys are the #1 cause of `KeyError` crashes in new brand setups
- **RAG is disabled** — if you see `qdrant` connection errors, you're accidentally hitting the un-commented RAG path
- **GPT-4o-mini only** — the response composer accepts any model string without error; wrong model = unexpected costs
- **Emotion scale is 0–10 float** — not 0–1; if something looks 10x too sensitive, check for incorrect normalization
- **Tests mock LLM** — integration failures that pass in unit tests almost always mean the mock fixture doesn't match the real API response shape; check `tests/fixtures/llm_mocks.py`
- **Brand session isolation in tests** — if data bleeds between brands, check whether `BrandRegistry` is being reused across test cases without reset; use `registry.reset()` between brand-switching tests

---

## Workflow Rules

- Run `pytest tests/automated/` before committing any change
- Run `python scripts/validate_production_ready.py` before marking a task done
- When modifying escalation logic, run `pytest tests/automated/test_escalation.py -v` specifically and confirm all threshold tests pass
- When adding a new brand, validate with `python scripts/diagnose_agent.py` before writing tests

---

## Skills Reference

For detailed guidance on specific workflows, see `.claude/skills/`:

| Skill | When to use |
|-------|------------|
| `add-new-brand` | Step-by-step guide to onboarding a new brand config |
| `add-new-tool` | How to create and register a new data tool |
| `debug-escalation` | Diagnosing false-positive or missed escalation cases |
| `write-cx-test` | Template and rules for writing new automated CX tests |
