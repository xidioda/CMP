# Company Management Platform (CMP)

**🔗 Repository:** https://github.com/xidioda/CMP  
**📋 Project Board:** https://github.com/users/xidioda/projects/1

AI-first, modular platform to automate core business operations. Phase 1 delivers the Core Platform and Module 1: AI Finance Department with comprehensive authentication and security.

## 🏆 Current Status

**✅ Completed Features:**
- **Issue #2**: Tesseract OCR for Arabic & English invoice processing
- **Issue #1**: Live API Integration (Zoho Books, Emirates NBD, Bank Import)
- **Issue #3**: JWT Authentication System with Role-Based Access Control

**🔄 Next Priority:**
- **Issue #4**: Phase 2B: Advanced AI Implementation
- **Issue #5**: Production Deployment Setup

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
- `GET /dashboard/agent-status` - AI agent status (viewer+)

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
│  ├─ agents/           # AI Finance Department (stubs)
│  ├─ integrations/     # External connectors (stubs)
│  ├─ routers/          # FastAPI routers
│  ├─ templates/        # Jinja2 templates for dashboard
│  ├─ __init__.py
│  ├─ config.py
│  ├─ db.py
│  ├─ main.py           # FastAPI app entrypoint
│  └─ models.py
├─ local_storage/       # Local file storage (OCR uploads, etc.)
├─ tests/
├─ .env.example
├─ docker-compose.yml
├─ requirements.txt
└─ README.md
```

## Core pieces delivered in Phase 1 scaffolding
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
