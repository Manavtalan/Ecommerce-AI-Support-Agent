# AI Customer Experience Agent

Multi-brand AI agent for D2C e-commerce customer support automation.

## 🎯 Project Overview

**Goal:** Scale Module Labs AI from ₹5L to ₹10L monthly revenue through productized AI customer support services.

**What it does:**
- Provides human-like customer support via WhatsApp, Instagram, Email
- Maintains conversation context across 15+ message exchanges
- Detects customer emotions and adapts tone accordingly
- Retrieves accurate policy information from knowledge base (RAG)
- Supports multiple brands with complete data isolation

**Business Model:**
- Setup fees: ₹1.5L - ₹2.5L per brand
- Recurring: ₹23K+ profit per client monthly
- 3-4 hour onboarding time per new brand

## 🏗️ Architecture

**Deployment Model:** Single codebase, multi-instance deployment
- Each brand gets separate deployment with isolated data
- 95% customization via config files
- Complete brand voice and policy customization

**Tech Stack:**
- Python 3.11+
- OpenAI GPT-4o-mini (cost-optimized)
- Qdrant (vector database for RAG)
- Railway (deployment hosting)
- WhatsApp Business API

## 📊 Current Status

**Day 0: Complete ✅**
- Project structure organized
- FashionHub brand fully configured
- 11 realistic test orders
- 15 product catalog
- 5 policy documents (2000+ lines)
- 35 FAQs
- 10 test scenarios
- Success criteria defined

**Day 1: In Progress 🚧**
- Conversation memory system
- Emotion-aware response generation
- Context retention (15+ turns)

**Days 2-5: Planned 📅**
- Day 2: RAG knowledge base + Tool integration
- Day 3: Multi-brand architecture
- Day 4: Edge cases & quality monitoring
- Day 5: Production deployment

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11+
pip (Python package manager)
Git
```

### Installation

1. **Clone repository:**
```bash
git clone https://github.com/YOUR_USERNAME/ai-customer-experience-agent.git
cd ai-customer-experience-agent
```

2. **Create virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Usage

**Coming after Day 1 - Memory system implementation**

## 📁 Project Structure
```
ai-cx-agent/
├── core/                    # Core agent engine
│   ├── conversation/        # Memory & state management
│   ├── llm/                # LLM composition
│   ├── emotion/            # Emotion detection
│   └── utils/              # Config & utilities
├── test_data/              # Complete test ecosystem
│   ├── brands/             # Brand configurations
│   ├── orders/             # Order database
│   ├── products/           # Product catalog
│   ├── policies/           # Policy documents
│   ├── faqs/              # FAQ database
│   └── test_conversations/ # Test scenarios
├── legacy/                 # Reference implementations
└── scripts/                # Management scripts
```

## 🎯 Key Features

### Context Retention (Day 1)
- Remembers order numbers for 15+ turns
- No "which order?" loops
- Maintains conversation flow

### Emotion Detection (Day 1)
- Detects: frustrated, confused, urgent, happy, neutral
- Adapts response tone accordingly
- Empathy-first approach for negative emotions

### RAG Knowledge Base (Day 2)
- Accurate policy retrieval
- No hallucinated information
- Proper source citation

### Multi-Brand Support (Day 3)
- Complete data isolation
- Distinct brand voices
- 3-4 hour onboarding

### Production Ready (Day 5)
- WhatsApp integration
- Email support
- Monitoring & analytics
- Deployment automation

## 📈 Success Metrics

**Target (End of Day 5):**
- ✅ Context retention: 15+ turns
- ✅ Emotion detection: 80%+ accuracy
- ✅ RAG accuracy: 90%+
- ✅ Response time: <3s (P95)
- ✅ Brand voice: Passes blind A/B test
- ✅ Escalation precision: <5% false positives

## 🗓️ Development Timeline

**5-Day Sprint:**
- **Day 0:** ✅ Foundation & test data
- **Day 1:** 🚧 Memory & emotion
- **Day 2:** RAG & tools
- **Day 3:** Multi-brand
- **Day 4:** Quality & edge cases
- **Day 5:** Production deployment

**Target:** 9/10 production-ready agent

## 🧪 Testing

**Test Scenarios:** 10 comprehensive scenarios
- Happy path (order status)
- Frustrated customer handling
- Context retention (15 turns)
- Policy questions
- Multi-issue handling
- Brand voice consistency

**Run tests:**
```bash
# Coming after Day 1
pytest tests/
```

## 📝 Configuration

**Brand Setup Example:**
```yaml
# test_data/brands/fashionhub/brand_config.yaml
brand_id: brand_fashionhub_001
name: FashionHub
tone: friendly_professional
return_window: 30
free_shipping_threshold: 999
```

## 🤝 Contributing

This is a private business project. Contributions limited to Module Labs AI team.

## 📄 License

Proprietary - Module Labs AI © 2026

## 📞 Contact

**Module Labs AI**
- Website: [Coming Soon]
- Email: contact@modulelabs.ai
- Business Inquiries: manav@modulelabs.ai

## 🎯 Business Goals

**150-Day Plan:**
- Scale from ₹5L to ₹10L MRR
- Onboard 5-8 D2C brands
- Maintain strong unit economics (₹1.67L+ Month 1 profit per client)
- Build productized, scalable solution

---

**Status:** Day 0 Complete | Day 1 In Progress  
**Last Updated:** January 28, 2026  
**Version:** 0.1.0-dev
