# SPYDRWEB

**SPYDRWEB** is a real-time fraud detection and investigation platform for financial transactions. It combines rule-based engines, behavioral profiling, graph analytics, and LLM-powered synthesis to detect elder exploitation, romance scams, account takeover, mule networks, and other fraud patterns—with full explainability for analysts.

---

## Features

- **Multi-layer detection pipeline**: Rules (Layer 1), behavioral profiling (Layer 2), graph topology (Layer 3), communication comprehension (Layer 4), and cross-signal synthesis (Layer 5)
- **Fast-path optimization**: Low-risk transactions are cleared instantly without invoking AI
- **Real-time streaming**: Live transaction and alert feed via WebSocket
- **Monitor interface**: Real-time transaction stream with configurable feed and scenario injection for monitoring and testing
- **Explainable reasoning**: Per-transaction pipeline trace with verdict summary, pipeline journey, key evidence, and full layer-by-layer breakdown
- **Ego-network graph**: Per-transaction relationship graph showing sender/receiver neighborhood
- **SAR report generation**: System-generated Suspicious Activity Report preview with executive summary
- **Markdown rendering**: LLM-generated narratives, tables, and formatted text displayed correctly in the UI
- **Agent loop workflow**: Built with [Railtracks] for agentic orchestration

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + Vite)                        │
│  Dashboard │ Analytics │ Graph │ Config │ Report Modal │ Investigation   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                         REST API + WebSocket
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI)                              │
│  Stream API │ Transactions │ Reports │ Graph │ WebSocket Broadcast        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                     PIPELINE ORCHESTRATOR                                │
│  Event Stream │ Brain Graph │ Account Store │ Profile Builder             │
│  Fast Path Filter │ Score Computer │ Alert Manager                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│  L1: Rules  │ L2: Profiling  │ L3: Graph  │ L4: Comms  │ L5: Synthesis  │
│  (8 rules)  │ (baseline)     │ (hub/fan)   │ (LLM)      │ (LLM)          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **LLM endpoint** (e.g., HuggingFace-hosted GPT-OSS or compatible OpenAI API)

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repository-url>
cd SpydrWeb
cp .env.example .env
```

Edit `.env` and set your LLM credentials:

```env
LLM_BASE_URL=https://your-llm-endpoint/v1
LLM_API_KEY=your-api-key
LLM_MODEL=your-model-name
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will:
- Load or build the world state (personas, transaction history, pre-processed reports)
- On first run, pre-process an initial batch and cache to `.state_cache/startup_state.pkl`
- Subsequent restarts restore from cache for faster startup

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

---

## Data Sources

| Mode        | Description |
|-------------|-------------|
| `synthetic` | Generated personas and transactions (default) |
| `paysim`    | PaySim1 dataset (place CSV in `backend/app/datasets/paysim/`) |
| `both`      | Synthetic + PaySim combined |

PaySim CSV: [Kaggle PaySim1](https://www.kaggle.com/datasets/ealaxi/paysim1). Expected path: `backend/app/datasets/paysim/PS_20174392719_1491204439457_log.csv`.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | — | LLM API base URL |
| `LLM_API_KEY` | — | API key |
| `LLM_MODEL` | — | Model name |
| `DATA_MODE` | synthetic | `synthetic` \| `paysim` \| `both` |
| `CACHE_LLM_RESPONSES` | true | Cache LLM calls |
| `SCORE_THRESHOLD_HOLD` | 0.7 | Score above which to HOLD |
| `SCORE_THRESHOLD_REFER` | 0.85 | Score above which to REFER |

---

## Cache Management

To force a full rebuild (e.g., after changing personas or data):

```bash
# Delete the startup cache
rm -rf backend/app/.state_cache

# Or use the API (with backend running)
curl -X POST http://localhost:8000/demo/clear-cache
```

Then restart the backend.

---

## Project Structure

```
SpydrWeb/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes, WebSocket
│   │   ├── accounts/     # Profiles, baselines, vulnerability, recipient risk
│   │   ├── ai/           # LLM provider, prompts, cache
│   │   ├── brain/        # Graph, overlay, velocity, analysis
│   │   ├── core/         # Orchestrator, event stream, fast path, scoring
│   │   ├── data/         # Generator, scenarios, PaySim loader, profiles
│   │   ├── layers/       # Rules, profiling, graph, comprehension, synthesis
│   │   └── models/       # Transaction, report, account, layers
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Dashboard, TransactionTable, InvestigationPanel, etc.
│   │   ├── hooks/        # useTransactionFeed, useGraph
│   │   ├── pages/        # Dashboard, Analytics, Graph, Config
│   │   ├── services/     # API client, WebSocket
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── .env
├── .env.example
└── README.md
```

---

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/demo/*` | POST | Stream / monitor control |
| `/reports/{id}` | GET | Get case report by ID |
| `/reports/by-transaction/{txId}` | GET | Get report by transaction ID |
| `/graph/data` | GET | Full graph data |
| `/graph/neighbors/{nodeId}` | GET | Ego-network subgraph |

WebSocket: `ws://localhost:8000/ws` — streams `transaction` and `alert` messages.

---

## License

See repository for license details.
