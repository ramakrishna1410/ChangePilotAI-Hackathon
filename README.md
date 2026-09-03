# ChangePilot AI — Hackathon MVP

An agentic GenAI assistant that turns a change request into an evidence-backed
change-impact analysis (impacted components, dependencies, risk, effort
estimate, regression scenarios) for an enterprise .NET application. This is
the hackathon MVP vertical slice described in the ChangePilot AI technical
blueprint (Sections 3–11): CR intake → RAG over the target codebase →
orchestrator with specialist agents → structured, evidence-backed output →
Tech Lead approve/edit/reject.

## Why this stack (and not Azure yet)

The blueprint's target production stack is ASP.NET Core + Azure OpenAI +
Azure AI Search on Azure. This MVP implements the same architecture shape
(orchestrator + tool-calling agents + hybrid RAG + evidence-backed structured
output + human-in-the-loop) on a stack that runs anywhere without Azure
credentials:

| Blueprint (production)   | This MVP                         |
|---------------------------|-----------------------------------|
| ASP.NET Core Web API      | FastAPI (Python)                  |
| Azure OpenAI               | OpenAI API                        |
| Azure AI Search (RAG)      | Chroma (embedded vector store)    |
| SQL Server                 | SQLite                            |
| Semantic Kernel orchestration | Plain Python orchestrator (`app/agents/orchestrator.py`) |
| React/Blazor dashboard     | React + Vite dashboard            |
| Microsoft Entra ID, Key Vault | Not implemented (see "Path to production" below) |

Swapping to the production stack later means changing the client layer
(`backend/app/agents/llm.py` for `AzureOpenAI`, `backend/app/ingestion/indexer.py`
+ `backend/app/rag/retriever.py` for Azure AI Search SDK calls, `DB_PATH` for a
SQL Server connection string) — the agent logic, data model and API contracts
stay the same.

## Repository layout

```
sample-app/     Small representative ASP.NET Core app (order-approval workflow) —
                the RAG target. Not built/run; it's indexed as source content.
backend/        FastAPI service: ingestion, RAG, agents/orchestrator, API.
frontend/       React/Vite dashboard: CR intake, analysis tabs, evidence, approval.
```

See the design doc's Section 5 (architecture) and Section 7 (data model) for
the full mapping; `backend/app/models.py` implements the same entities
(`ChangeRequest`, `AnalysisRun`, `ImpactItem`, `Dependency`, `RiskItem`,
`EffortEstimate`, `TestScenario`, `Feedback`).

## Running it

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set OPENAI_API_KEY

python seed_index.py        # chunks + embeds sample-app/ into Chroma
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

### 3. Demo flow (mirrors Section 21 of the doc)

1. Open the dashboard, click **New Change Request**. A representative CR is
   pre-filled: *"Add order-approval threshold business rule"* — matching the
   sample app's `OrderApprovalService`, which today has no auto-approval path.
2. Submit — this creates the CR and immediately starts an analysis run.
3. The orchestrator runs Requirement → Impact (RAG) → Dependency →
   Risk/Effort → Regression → Validation, and the Analysis view shows each
   as a tab, with evidence (source file + class/method/SQL object) attached
   to every finding.
4. The **Needs Validation** tab surfaces anything the Validation stage
   flagged as unsupported by evidence or low-confidence.
5. Check the **Effort** tab: a full SDLC effort breakdown in days (8h = 1
   day) — Analysis & Design, Build (Dev & Unit Testing), Testing (SIT), UAT
   Support are AI-estimated; Change Management (SNOW) defaults to a fixed
   0.50 days; Enhancement/Project Coordination defaults to 10% of the
   Analysis+Build+Testing+UAT subtotal (not a flat day count) — both
   configurable on the Settings page — plus the total days and the
   resulting EUR cost from the configured cost bands.
6. Use **Accept / Accept with edits / Reject**:
   - **Accept** locks the run and marks the CR "Approved" — read-only from
     then on.
   - **Accept with edits** opens an inline form to adjust the effort days
     per phase (cost recalculates live) and each impacted component's
     impact level, then saves your edited version as the run's result
     (the original AI output is preserved for audit) and locks the run as
     "Approved (Edited)".
   - **Reject** marks the run/CR "Rejected" and — unlike Accept — leaves
     "Re-run Analysis" available so you can try again.
   - Once a run is decided, it's locked: submitting feedback on it again
     returns an error; start a new analysis run instead.

### 4. Settings page

Click **Settings** from the dashboard to edit the cost bands (label, upper
bound in days, EUR cost — first band where `total_days < upper_bound` wins;
totals at or beyond the largest band show "Manual costing required"), the
Change Management default (flat days), and the Enhancement/Project
Coordination percentage (of the Analysis+Build+Testing+UAT subtotal).
Changes apply to analysis runs started after the save — update these
periodically as rates change.

## Architecture mapping

| MVP component | Blueprint section | Implementation |
|---|---|---|
| CR intake | §3.1 | `POST /change-requests`, `frontend/src/pages/Intake.tsx` |
| Application understanding / RAG | §3.2, §6 | `backend/app/ingestion/`, `backend/app/rag/retriever.py` |
| Impact analysis | §3.3 | `backend/app/agents/impact_agent.py` |
| Dependency/risk analysis | §3.4 | `dependency_agent.py`, `risk_effort_agent.py` |
| Effort estimation (AI days) | §3.5 | `risk_effort_agent.py` (`EffortEstimateDraft`) |
| Effort/cost roll-up (overhead + EUR) | §3.5, §13 | `agents/effort_calculator.py` (deterministic, not LLM) |
| Configurable cost settings | — | `api/routes_settings.py`, `frontend/src/pages/Settings.tsx` |
| Regression recommendation | §3.6 | `test_agent.py` |
| Explainability/evidence | §3.7 | `EvidenceRef` on every finding; `validation_agent.py` |
| Orchestrator + specialist agents | §4, §5.1 | `orchestrator.py` |
| Data model | §7 | `backend/app/models.py`, `backend/app/db.py` |
| MVP UX screens + review workflow | §9 | `frontend/src/pages/*`, `components/ReviewPanel.tsx`, `api/routes_feedback.py` |

## Path to production (out of scope for this MVP)

Per §8 and §16 of the design doc, before any enterprise rollout:

- Replace OpenAI/Chroma with Azure OpenAI + Azure AI Search.
- Replace SQLite with SQL Server; add proper migrations.
- Add Microsoft Entra ID authentication and repo/application-level
  authorization before retrieval.
- Move secrets to Azure Key Vault (currently `.env`-only, gitignored).
- Add audit logging for analysis runs, model/prompt versions, retrieved
  evidence and approvals.
- Integrate ServiceNow (CR ingestion, write-back) and Azure DevOps
  (traceability) through approved enterprise APIs, instead of manual CR
  paste.
- Security/data-classification/AI-governance review before indexing any
  real Sanofi/Cognizant source code or documents.

## Known limitations (MVP)

- Analysis runs synchronously in the request (no background job queue) —
  fine for a demo, not for production load.
- C#/SQL chunking uses regex-based parsing, not a real Roslyn/T-SQL parser —
  good enough for semantic-unit chunking on a small sample app, not robust
  against arbitrary production codebases.
- No authentication on the API or dashboard.
- The EUR cost bands and overhead-day defaults are illustrative starting
  values (per §13 of the doc, "should be replaced with measured project
  data where available") — update them on the Settings page to match real
  rates before relying on the cost figure for anything.
- "Accept with edits" lets the Tech Lead override effort days and impact
  levels; it does not yet support editing risks, dependencies, or test
  scenarios inline — those still go through the free-text review comment.
