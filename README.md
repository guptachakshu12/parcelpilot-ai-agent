# ParcelPilot AI Support Agent

AI-powered customer support agent for ParcelPilot, built as part of the **CalQuity AI Engineer First-Round AI Agent Assessment**.

ParcelPilot is a B2B logistics platform where support teams need to answer questions using a combination of customer agreements, support policies, operational data, orders, and historical support information.

This project demonstrates an end-to-end AI support system that combines:

* **React + Vite** frontend
* **FastAPI** backend
* **LangGraph** agent orchestration
* **Gemini** for LLM reasoning
* **FAISS** for retrieval-augmented generation
* Structured account, order, and ticket data
* Tool-based agent workflows
* Production deployment using **Vercel + Render**

---

## 1. Problem

ParcelPilot's support team needs to answer questions such as:

* What is the status of an order?
* Is a customer eligible for a service credit?
* What does the applicable support policy say?
* Does a customer-specific agreement override the general policy?
* What information is available about a support ticket?

The challenge is that the information is distributed across:

1. Policy documents
2. Customer agreements
3. SOPs
4. Product documentation
5. Account data
6. Order data
7. Support ticket data

The system therefore needs to retrieve the right information and reason across multiple sources instead of relying only on the LLM's internal knowledge.

---

# 2. Solution

ParcelPilot uses an agent-based architecture where the LLM can select the appropriate tool based on the user's question.

For example:

```text
User Question
      │
      ▼
React Frontend
      │
      ▼
FastAPI /chat
      │
      ▼
LangGraph Agent
      │
      ├───────────────┐
      ▼               ▼
Document Search   Structured Data
      │               │
      ▼               ▼
FAISS / RAG       Accounts / Orders / Tickets
      │               │
      └───────┬───────┘
              ▼
        Agent Reasoning
              │
              ▼
        Final Response
```

The system is designed so that operational questions can be answered using structured data while policy and agreement questions can be answered using retrieval.

---

# 3. Architecture

## Frontend

**React + Vite**

The frontend provides a simple support-chat interface with:

* Natural-language input
* Quick actions
* Conversation history
* Loading state
* Agent activity/tool visibility
* Error handling

The frontend sends requests to the FastAPI backend through:

```text
POST /chat
```

---

## Backend

**Python + FastAPI**

The backend exposes:

```text
GET  /
GET  /health
POST /chat
```

The `/chat` endpoint accepts:

```json
{
  "message": "Is LumenWorks eligible for a service credit for ORD-2002?"
}
```

and returns:

```json
{
  "answer": "...",
  "activity": [...]
}
```

The backend creates the ParcelPilot agent when the application starts and invokes it for each request.

---

# 4. Agent Design

The agent is implemented using **LangGraph**.

The LLM is responsible for deciding how to approach a request and which available tool or source is relevant.

The agent can combine:

* Structured operational data
* Retrieved policy information
* Customer-specific agreements
* Support information

This allows multi-step questions to be handled rather than hard-coding answers for individual order IDs.

For example, a service-credit question may require:

```text
User Question
      ↓
Identify Order
      ↓
Identify Customer
      ↓
Retrieve Relevant Agreement
      ↓
Retrieve Applicable Policy/SOP
      ↓
Compare Conditions
      ↓
Reason About Eligibility
      ↓
Return Answer
```

---

# 5. Agent Tools

The assessment requires distinct categories of tools.

The implemented system focuses on the following capabilities:

### 1. Document Retrieval

Searches the supplied policy, agreement, SOP, and product documentation.

Used for questions such as:

```text
What is the service credit policy?
```

or:

```text
What does the LumenWorks agreement say about service credits?
```

### 2. Structured Data Lookup

The agent can work with the supplied ParcelPilot operational data, including:

* Accounts
* Orders
* Tickets

This supports questions such as:

```text
What is the status of ORD-2002?
```

### 3. Combined Reasoning

The agent can combine structured data and retrieved documents.

For example:

```text
Order data
    +
Customer agreement
    +
Current policy
    ↓
Eligibility decision
```

This is important because business decisions should not be made from a single source.

### State-changing actions

State-changing actions and confirmation workflows were intentionally kept outside the current minimal implementation.

If continuing development, I would add an explicit action layer for:

* Creating escalations
* Updating tickets
* Creating follow-up tasks

These actions would require explicit user confirmation before execution.

---

# 6. RAG Architecture

The project includes a FAISS vector index for production retrieval.

The retrieval pipeline is approximately:

```text
Source Documents
      ↓
Document Processing
      ↓
Chunking
      ↓
Embeddings
      ↓
FAISS Index
      ↓
Query Embedding
      ↓
Similarity Search
      ↓
Relevant Context
      ↓
LLM / Agent
```

The repository contains the generated FAISS index:

```text
backend/rag/parcelpilot.index
```

The retrieval implementation is separated from the agent logic so that the knowledge layer can be updated independently.

---

# 7. Source Reliability and Conflict Handling

One of the important aspects of the assessment is that not every source should be treated equally.

The source base can contain:

* Current policies
* Deprecated policies
* Customer-specific agreements
* SOPs
* Product documentation
* Historical ticket resolutions

I treat customer-specific agreements and current authoritative policies as more reliable than historical ticket responses.

In particular:

```text
Customer-specific agreement
        ↓
Applicable current policy / SOP
        ↓
Current product documentation
        ↓
Historical ticket context
```

Historical support resolutions are treated as contextual evidence rather than authoritative policy.

If sources conflict, the system should prefer the more authoritative and current source rather than blindly combining contradictory information.

For production, I would make this source hierarchy explicit in metadata and retrieval filtering rather than relying only on the LLM's judgment.

---

# 8. Structured Data Handling

The supplied Excel workbook contains operational datasets.

The backend loads:

* `accounts`
* `orders`
* `tickets`

The workbook README provides the dataset snapshot context.

Time-sensitive questions should use the **dataset snapshot time** rather than the machine's current time.

This avoids incorrect answers caused by treating today's date as the reference point for historical assessment data.

---

# 9. Data Privacy and Access Control

The assessment requires customer data to be scoped appropriately.

The current implementation is primarily designed as a support-agent prototype using the supplied assessment dataset.

For a production customer-facing implementation, I would enforce account-level authorization in the **tool/data-access layer**, rather than relying on the LLM prompt.

The intended architecture would be:

```text
Authenticated User
       ↓
Account Context
       ↓
Authorization Layer
       ↓
Data Tool
       ↓
Only Authorized Records
```

This prevents the model from accessing another customer's orders or agreements even if a malicious prompt attempts to request them.

---

# 10. Multi-Step Requests

A key design goal is supporting questions that require multiple sources.

For example:

> Is LumenWorks eligible for a service credit for ORD-2002?

A robust workflow may require:

```text
1. Find ORD-2002
2. Identify the associated customer
3. Retrieve customer-specific agreement
4. Retrieve applicable service-credit policy
5. Compare order facts with policy conditions
6. Determine eligibility
7. Explain the reasoning
```

This is preferable to hard-coding a response for `ORD-2002`.

---

# 11. Additional Client Problem

## Problem Chosen: Trust and Reliability

I focused on the **Trust and Reliability** problem because incorrect answers are particularly risky in a support system.

The system therefore separates:

* Structured operational facts
* Retrieved policy information
* Customer agreements
* Historical support context

The intended behavior is to prioritize authoritative sources and avoid treating historical ticket responses as ground truth.

### Future improvement

I would introduce explicit source metadata:

```text
source
document_type
authority
effective_date
customer_scope
status
```

The retrieval layer could then filter and rank documents using these attributes before sending context to the LLM.

This would make conflict resolution more deterministic and auditable.

---

# 12. Technical Trade-offs

### FAISS vs hosted vector database

I chose FAISS because the assessment dataset is relatively small and a local vector index keeps the architecture simple.

For a larger production deployment, I would evaluate a managed vector database or PostgreSQL/pgvector depending on scale and operational requirements.

### FastAPI

FastAPI provides a lightweight API layer with strong Python ecosystem compatibility and straightforward integration with the agent.

### LangGraph

LangGraph provides explicit orchestration and makes multi-step agent workflows easier to extend than a single LLM call.

### React/Vite

React provides a simple way to build the support interface while keeping the frontend independent from the Python backend.

---

# 13. What I Would Build Next

If continuing development, I would prioritize:

### 1. Authorization and user context

Add authentication and account/role-based access control.

**Priority: Very High**

This is necessary before exposing customer-specific data in production.

### 2. Confirmed action workflows

Add tools for:

* Escalating tickets
* Updating tickets
* Creating follow-up tasks

The agent would first prepare an action and ask:

```text
I can escalate this ticket to the operations team.

Do you want me to proceed?
```

Only explicit confirmation would execute the action.

**Priority: Very High**

### 3. Proactive issue detection

Build an internal operations dashboard that identifies:

* SLA breaches
* Repeated product issues
* High-severity tickets
* Sudden complaint increases
* Cross-customer incidents

**Priority: High**

This moves the system from reactive support toward proactive operations.

### 4. Better source governance

Add document metadata and effective dates to make policy conflicts deterministic.

**Priority: High**

### 5. Evaluation framework

Create a test set containing:

* Straightforward questions
* Multi-step questions
* Conflicting documents
* Customer-specific overrides
* Unsupported requests
* Privacy/access-control cases

Measure:

* Answer correctness
* Retrieval precision
* Tool-selection accuracy
* Escalation accuracy
* Unauthorized data access

---

# 14. What I Intentionally Left Out

To keep the assessment implementation focused, I did not build a full production identity and authorization system, enterprise ticketing integration, or comprehensive operations dashboard.

I also kept state-changing workflows outside the core prototype rather than implementing actions without a robust confirmation and authorization layer.

These are the areas I would prioritize before production deployment.

---

# 15. Success Metric

The primary product metric I would use is:

## Support Resolution Rate

**Percentage of support requests correctly resolved by the agent without human intervention.**

I would combine this with:

* Answer correctness
* Escalation precision
* Unauthorized-access rate
* Average resolution time

Correctness would be more important than simply maximizing automation.

---

# 16. Project Structure

```text
parcelpilot-ai-agent/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── agent/
│   │   └── graph.py
│   │
│   ├── rag/
│   │   ├── ingest.py
│   │   ├── retriever.py
│   │   └── parcelpilot.index
│   │
│   ├── data/
│   │   └── ParcelPilot_Assessment_Data.xlsx
│   │
│   └── main.py
│
├── requirements.txt
└── README.md
```

---

# 17. Running Locally

## Backend

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

The Vite development server will provide the frontend URL.

---

# 18. Deployment

The application is deployed as two services:

```text
Frontend
Vercel
   │
   │ HTTPS
   ▼
Backend
Render
   │
   ▼
LangGraph + Gemini + FAISS + Dataset
```

The frontend communicates with the deployed FastAPI `/chat` endpoint.

---

# 19. Demo

A walkthrough video covering the architecture, implementation, technical decisions, and product decisions is included with the assessment submission.

Hosted application:

**Frontend:** https://parcelpilot-ai-agent.vercel.app/

**Backend:** https://parcelpilot-ai-agent-0u4s.onrender.com/

---

# 20. AI Coding Tool Usage

AI coding assistants were used during development for:

* Debugging implementation issues
* Reviewing and improving code structure
* Generating initial implementation ideas
* Troubleshooting deployment and integration issues
* Iterating on the React UI
* Debugging FastAPI/frontend integration

I remained responsible for the architecture, implementation decisions, testing, debugging, and final integration.

---

# 21. Key Takeaway

ParcelPilot is designed as an AI support system rather than a simple LLM chatbot.

The core design combines:

```text
LLM Reasoning
      +
Agent Orchestration
      +
Tool Calling
      +
RAG
      +
Structured Operational Data
      +
Source Reliability
      +
API Backend
      +
Web Interface
```

The next step toward production would be strengthening authorization, confirmed state-changing actions, evaluation, observability, and proactive issue detection.

```
```
