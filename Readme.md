# Ecommerce AI Support Agent (CLI)

A rule-based + LLM-assisted customer support AI agent for ecommerce use cases.

## Features
- Deterministic order status handling
- Natural language order ID extraction
- Strict business rule enforcement
- Escalation-only refunds & cancellations
- LLM used only for FAQs and general queries

## Design Philosophy
- Deterministic logic over AI guessing
- No LLM for critical operations
- Production-style agent behavior

## Current Status
✅ Stateless version (Day 4 baseline)  
⏭ Context memory to be added next

## How to Run
```bash
python main.py
