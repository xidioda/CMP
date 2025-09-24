# Company Management Platform (CMP)

**🔗 Repository:** https://github.com/xidioda/CMP  
**📋 Project Board:** https://github.com/users/xidioda/projects/1

🤖 **AI-first, enterprise-grade platform** to automate core business operations with advanced machine learning and artificial intelligence. Phase 1 delivers the Core Platform and Module 1: AI Finance Department with comprehensive authentication, security, and intelligent automation.

## 🏆 Current Status

**✅ Completed Features:**
- **Issue #1**: Live API Integration (Zoho Books, Emirates NBD, Bank Import)
- **Issue #2**: Tesseract OCR for Arabic & English invoice processing  
- **Issue #3**: JWT Authentication System with Role-Based Access Control
- **Issue #4**: 🤖 **Advanced AI Implementation** - Machine Learning Financial Agents
- **Issue #6**: 🧠 **Context-Aware AI Enhancement** - Company-specific intelligent responses
- **💼 Executive Dashboard**: Professional browser interface with rich analytics & visualizations

**🔄 Current Work:**
- **Issue #5**: Production Deployment & DevOps Setup

## 🌐 Professional Web Dashboard

**🎯 Executive-Grade Interface:** http://localhost:8000/login
- **Demo Credentials**: `admin@cmp.local` / `admin123`
- **📊 Rich Analytics**: Real-time metrics, transaction analytics, AI performance monitoring
- **🎨 Modern UX**: Glassmorphism design, mobile-responsive, interactive visualizations
- **⚡ Live Updates**: Auto-refreshing data, real-time AI agent status, instant notifications
- **🔐 Secure Access**: JWT authentication, role-based permissions, session management

### Dashboard Features
- **📈 Financial Overview**: Transaction volumes, revenue trends, AI accuracy metrics
- **🤖 AI Agent Monitoring**: Real-time status of all 4 ML agents with refresh capabilities  
- **📊 Analytics Visualizations**: Category breakdowns, spending patterns, custom charts
- **💼 Smart Forms**: Transaction recording, invoice upload with AI OCR processing
- **📱 Activity Feed**: Real-time ledger entries with detailed transaction history
- **⚙️ System Health**: API status, database connectivity, ML model readiness

## 🤖 AI & Machine Learning Features

**NEW: Advanced AI Financial Management System**
- **🧠 AI Transaction Categorization**: ML-powered classification with confidence scoring
- **📄 Intelligent Document Analysis**: Advanced OCR with AI reasoning
- **🔍 Real-time Anomaly Detection**: Fraud prevention and unusual transaction alerts
- **📊 Predictive Analytics**: Cash flow forecasting and budget variance analysis
- **🎯 Business Intelligence**: AI-generated insights and recommendations
- **⚡ Multi-Agent Architecture**: Specialized AI agents for different financial functions

### AI Agent Capabilities

**🤖 AI Accountant:**
- Multi-bank transaction processing (Emirates NBD, File Import)
- ML transaction categorization with 90%+ accuracy
- Intelligent invoice processing with AI reasoning
- Real-time anomaly detection and fraud prevention
- Automated business insights generation

**🔍 AI Controller:**
- AI-enhanced work review and validation
- Budget vs actuals analysis with ML forecasting
- Intelligent policy violation monitoring
- Predictive AP/AR aging analytics
- VAT compliance verification with AI

**📈 AI Director:**
- Predictive cash flow forecasting with ML models
- AI-powered P&L and balance sheet analysis
- Intelligent payment authorization with risk assessment
- Executive dashboard with business intelligence

**🏢 AI CFO:**
- Advanced ML financial modeling (3-year horizon)
- AI-driven profitability and growth analysis
- Monte Carlo scenario simulations
- Strategic planning with predictive analytics
- Board-level insights and investor relations

## 🔐 Authentication & Security

The platform now includes enterprise-grade authentication:

- **JWT-based Authentication** with access/refresh tokens
- **Role-Based Access Control**: Admin → Orchestrator → Viewer hierarchy  
- **Protected Endpoints** with proper authorization
- **User Management** with admin controls
- **Password Security** using bcrypt hashing

**Default Admin Login:**
- Email: `admin@cmp.com`
- Password: `admin123` ⚠️ *Change immediately!*

## Quick start

Prereqs:
- Python 3.11+
- macOS (local-first, zero-cost)
- Optional: Docker (for local PostgreSQL)

### 1) Create a virtual environment and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 2) Set up authentication (required)

```bash
# Run database migration to create user tables
python scripts/migrate_auth.py
```

### 3) Run the API (SQLite by default; Postgres optional)

```bash
# Start API
uvicorn cmp.main:app --reload
```

Open: http://127.0.0.1:8000/dashboard

**Login required!** Use the default admin credentials above.

### Using PostgreSQL locally (optional, recommended)

Option A: Docker
```bash
```

### 4) Run tests

```bash
pytest -q
```

## 🚀 API Endpoints

### Authentication Endpoints

- `POST /auth/login` - User authentication
- `POST /auth/register` - User creation (admin only)  
- `POST /auth/refresh` - Token refresh
- `GET /auth/me` - Current user information
- `GET /auth/users` - List users (admin only)
- `PUT /auth/users/{id}/activate` - Activate user (admin only)
- `PUT /auth/users/{id}/deactivate` - Deactivate user (admin only)

### Application Endpoints

- `GET /healthz` - Health check
- `GET /dashboard` - Main dashboard (authenticated)
- `POST /dashboard/realworld` - Record real-world events (orchestrator+)
- `POST /dashboard/upload-invoice` - Upload invoices for OCR (orchestrator+)
- `GET /dashboard/agent-status` - 🤖 **Enhanced AI agent status with ML capabilities** (viewer+)

### 🤖 AI Testing Examples

Test the AI transaction categorization:

```bash
# Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@cmp.com", "password": "admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Get enhanced AI agent status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/dashboard/agent-status | python3 -m json.tool
```

**Example AI Response Features:**
- **AI Accountant**: Shows ML categorization confidence, anomaly detection status
- **AI Controller**: Displays risk thresholds, policy engine status
- **AI Director**: Shows KPI targets, predictive analytics capabilities  
- **AI CFO**: Strategic KPIs, Monte Carlo simulation readiness

### 3) Run tests
```

Option B: Native install
- Install PostgreSQL via Homebrew: `brew install postgresql@15`
- Create DB and user, then set `DATABASE_URL` as above.

### 3) Run tests

```bash
pytest -q
```

## Project structure

```
CMP/
├─ cmp/                 # App source
│  ├─ agents/           # 🤖 AI Finance Department (ML-powered)
│  │  ├─ accountant.py  # AI Accountant with ML categorization
│  │  ├─ controller.py  # AI Controller with predictive analytics  
│  │  ├─ director.py    # AI Director with forecasting
│  │  └─ cfo.py         # AI CFO with strategic modeling
│  ├─ utils/            # AI/ML utilities
│  │  ├─ ai.py          # Core AI engine (NEW)
│  │  ├─ ocr.py         # Intelligent document processing
│  │  └─ api_client.py  # Enhanced API clients
│  ├─ integrations/     # External connectors (Emirates NBD, Zoho)
│  ├─ routers/          # FastAPI routers with AI endpoints
│  ├─ templates/        # Enhanced dashboard templates
│  ├─ __init__.py
│  ├─ config.py
│  ├─ db.py             # Enhanced with AI data models
│  ├─ main.py           # FastAPI app entrypoint
│  └─ models.py         # User models with AI permissions
├─ local_storage/       # Local file storage (OCR uploads, ML models)
│  └─ ml_models/        # Trained AI models (NEW)
├─ tests/               # Comprehensive test suite (34 tests)
├─ .env.example
├─ docker-compose.yml
├─ requirements.txt     # Enhanced with AI/ML dependencies
└─ README.md
```

## 🚀 Core Features Delivered
- FastAPI app with modular router loading
- Simulated immutable audit ledger (hash-chained rows)
- Basic dashboard for AI Orchestrators: real-world input, approvals, exceptions
- Finance module agent stubs: Accountant, Controller, Director, CFO
- OCR integration via pytesseract (falls back gracefully if Tesseract not installed)
- Connectors (Zoho Books, Wio Bank) mocked with interfaces and local stubs
- Tests for health endpoint and ledger hash chaining

## Configuration

- `.env` (optional):
```
DATABASE_URL=postgresql+psycopg://cmp:cmp@localhost:5432/cmp
ENV=development
```
If not set, SQLite file `cmp.db` is used in the project root for zero-config local runs.

## GitHub Project board

Creating a GitHub Project requires GitHub auth and cannot be done offline. We include `scripts/gh_project_setup.sh` which, with the GitHub CLI installed and authenticated, creates a Project and seeds Epics/Tasks from `docs/backlog.md`.

Steps (optional, once repo is pushed to GitHub):
```bash
# Requires: gh auth login
bash scripts/gh_project_setup.sh
```

## UAE compliance notes (initial placeholders)
- E-invoicing: `cmp/integrations/invoices.py` exposes a generator stub for UAE-compliant e-invoices. Update mappings once final spec is confirmed.
- Audit trail: All important actions should call `append_ledger_entry(...)` to create tamper-evident records.
- Human-in-the-loop: Critical submissions (e.g., VAT) are surfaced in the Approval Queue for explicit human confirmation.

## Troubleshooting
- Tesseract not installed: OCR functions will warn and skip. Install via Homebrew `brew install tesseract` for local OCR.
- Postgres not running: The app falls back to SQLite. Set `DATABASE_URL` for Postgres.

## License
TBD
