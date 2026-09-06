REVERA --- Intelligent Revenue Recovery System

Detect. Decide. Act. Prove.

REVERA is an AI-powered revenue recovery control plane built for the
Razorpay AI Buildathon 2026 --- Track 03: AI Revenue Recovery.

It detects revenue leakage, diagnoses why a payment is at risk, selects
the recovery action with the strongest expected economic outcome,
enforces deterministic safety policies, executes recovery through
Razorpay Test Mode, and verifies actual money recovered through webhook
events.

Why REVERA?

Payment failures are not all the same.

A failed UPI payment, an abandoned checkout, an insufficient-funds
failure, and a repeatedly failing customer may require completely
different recovery strategies.

REVERA combines:

Customer and payment context

A machine-learning recovery risk model

Gemini-powered diagnosis and strategy reasoning

Deterministic recovery economics

Deterministic policy enforcement

Razorpay payment execution

Webhook-based recovery verification

A complete audit trail

The key principle is:

AI proposes. Policy authorizes. Razorpay executes. Webhooks prove.

Core Flow

Razorpay Event
      ↓
Event Gateway
      ↓
Revenue / Customer Context
      ↓
Risk Engine
      ↓
Gemini Investigator
      ↓
Gemini Strategy
      ↓
Recovery Economics Optimizer
      ↓
Evidence / Schema Validation
      ↓
Deterministic Policy Guard
      ↓
Razorpay Action Executor
      ↓
Razorpay Webhook
      ↓
Verified ₹ Recovered
      ↓
Audit + Learning Loop

REVERA Recovery Loop

DETECT
   ↓
DIAGNOSE
   ↓
DECIDE
   ↓
OPTIMIZE
   ↓
EXECUTE
   ↓
VERIFY
   ↓
LEARN

What Makes REVERA Different?

1. It does not stop at risk detection

A risk score alone does not recover money.

REVERA turns the risk assessment into an executable recovery decision.

2. AI does not control money movement

Gemini is used for reasoning, diagnosis, and strategy generation.

It does not directly execute or authorize financial actions.

Gemini
  → Diagnosis
  → Strategy proposal

Deterministic Economics
  → Expected recovery calculation

Deterministic Policy
  → Authorization

Razorpay
  → Execution

Webhook
  → Verification

3. Recovery is based on economics

REVERA evaluates expected recovery value rather than blindly sending
reminders or retries.

It considers:

Probability of recovery

Expected recovery amount

Action-specific probability uplift

Intervention cost

Friction

Customer contact limits

Attempt limits

Discount limits

Transaction amount

4. Money is counted only after verification

Creating a payment link does not mean revenue has been recovered.

REVERA marks revenue as recovered only after the Razorpay webhook
confirms the payment.

Features

AI-Powered Diagnosis

Understands the payment situation using event and customer context.

Example context:

Payment method

Failure reason

Number of attempts

Previous successes/failures

Customer age

Customer lifetime value

Days since last payment

Checkout duration

Previous recovery rate

Recent customer contacts

Smart Recovery Decisions

REVERA can evaluate recovery actions including:

PAYMENT_LINK

RETRY

ALTERNATIVE_METHOD

REMINDER

WAIT

INCENTIVE

STOP

The selected action is based on expected economic outcome and policy
constraints.

Policy-Aware Automation

Current benchmark policy:

Policy                          Limit

Automated recovery limit      ₹50,000
Human review limit            ₹75,000
Maximum recovery attempts           2
Maximum contacts / 24h              2
Maximum discount                   5%

Actions can be:

APPROVED

BLOCK

STOP

HUMAN_REVIEW

Verified Revenue

Recovery status is updated from Razorpay webhook events.

The system supports webhook-driven reconciliation for payment-link
events and prevents duplicate webhook processing.

Complete Audit Trail

REVERA records:

Recovery cases

AI diagnosis

Strategy decisions

Economics calculations

Policy decisions

Recovery actions

Razorpay execution

Webhook events

Verified recovery

Machine Learning Risk Engine

REVERA uses a customer-group holdout evaluation strategy to reduce
customer-level leakage between training and testing data.

Current evaluation results:

Metric          Result

ROC-AUC         0.7829
Precision       0.5566
Recall          0.7047
F1              0.6220
Accuracy        0.7129
Brier Score     0.1901

Evaluation split:

Train events: 9,544
Test events: 2,456
Test customers: 586
Split strategy: Customer-group holdout

The dataset used for the benchmark is synthetic.

Recovery Economics

REVERA does not simply select the action with the highest raw recovery
probability.

It estimates the economic value of each action.

Conceptually:

Expected Recovery Value
    =
Expected Recovery Amount
    -
Intervention Cost

The engine considers action-specific recovery probability changes and
operational costs.

This allows REVERA to answer:

"Which action is most likely to recover money while creating the
strongest net economic outcome?"

Controlled Benchmark

REVERA was evaluated on 1,000 controlled synthetic cases.

Results

Metric                        REVERA      Baseline   Fixed Reminder

Gross recovered          ₹61.34 lakh   ₹56.43 lakh      ₹59.32 lakh
Net recovered        ₹60.43 lakh   ₹56.43 lakh      ₹59.08 lakh
Recovery rate              55.8%         51.9%            53.9%
Successful cases      558 / 1000    519 / 1000       539 / 1000

REVERA improvement

Net recovered:
₹60.43 lakh

Baseline:
₹56.43 lakh

Incremental net recovery:
₹3.99 lakh

Relative uplift:
+7.09%

Above fixed reminder:
₹1.35 lakh

Policy violations:
0
Stopping violations:
0

REVERA action distribution

PAYMENT_LINK        365
ALTERNATIVE_METHOD  364
INCENTIVE           121
STOP                150
RETRY                 0
REMINDER              0
WAIT                  0

Important: These benchmark numbers are from controlled synthetic
data and are not production merchant performance claims.

Razorpay Integration

REVERA integrates with Razorpay Test Mode for the recovery execution
path.

Example flow:

Recovery Decision
      ↓
Policy APPROVED
      ↓
PAYMENT_LINK selected
      ↓
Razorpay Test Mode Payment Link
      ↓
Customer completes payment
      ↓
Razorpay webhook
      ↓
HMAC verification
      ↓
Idempotency check
      ↓
Recovery action updated
      ↓
Case marked recovered
      ↓
Audit event created

A successful payment is therefore reflected as verified recovered
revenue, rather than merely an attempted recovery.

Gemini Integration

Gemini is used for:

Investigator reasoning

Recovery strategy generation

Structured decision output

REVERA keeps the model behind a provider abstraction so the application
can support multiple model providers.

When live Gemini quota is unavailable, the application has a
deterministic fallback for demo continuity.

Fallback decisions are explicitly marked with:

provider: revera-deterministic
model: revera-fallback-v1
live: false

This prevents the system from falsely representing a deterministic
fallback as a live Gemini response.

Project Structure

recoveros/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── db.py
│   │   ├── policy.py
│   │   ├── economics.py
│   │   ├── recovery_pipeline.py
│   │   ├── model_router.py
│   │   └── ...
│   │
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── style.css
│   │   └── ...
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md

Local Setup

Prerequisites

Python 3.12.x

Node.js

npm

Razorpay Test Mode credentials

Gemini API key

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY>
cd recoveros

2. Backend setup

cd backend
python -m venv .venv

Windows

.venv\Scripts\activate

macOS / Linux

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Start the API:

uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

Swagger API documentation:

http://127.0.0.1:8000/docs

Backend Environment Variables

Create:

backend/.env

Example:

GEMINI_API_KEY=your_gemini_api_key

RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_test_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

Never commit real secrets to GitHub.

Frontend Setup

Open another terminal:

cd frontend
npm install

Create:

frontend/.env

Example:

VITE_API_BASE_URL=http://127.0.0.1:8000

Start the frontend:

npm run dev

The Vite development server will display the local frontend URL.

Main API Endpoints

Endpoint                            Purpose

GET /api/cases                    List recovery cases

GET /api/cases/{case_id}          Get a recovery case

POST /api/risk/score              Calculate recovery risk

POST /api/recovery/decide         Run the complete recovery decision
pipeline

POST /api/recovery/execute        Execute an approved recovery action

GET /api/recovery/actions         View recovery actions

GET /api/analytics                Revenue recovery analytics

GET /api/benchmark                Controlled benchmark

GET /api/ai/status                AI provider status

POST /api/webhooks/razorpay       Razorpay webhook receiver

Example Decision Pipeline

A recovery case enters the system:

Case:
RCP-1042

Amount:
₹8,499

Event:
payment.failed

Payment method:
UPI

Failure reason:
transient_failure

REVERA then performs:

1. Risk scoring
2. Customer/payment diagnosis
3. Recovery strategy proposal
4. Economic comparison
5. Policy authorization
6. Final action selection

The final decision can look conceptually like:

Action:
PAYMENT_LINK

Policy:
APPROVED

Execution:
READY_FOR_EXECUTION

Expected recovery:
₹8,278.53

The final recovered amount is not considered verified until Razorpay
confirms the payment through the webhook.

Safety Architecture

REVERA follows a layered authorization model.

                 ┌────────────────────┐
                 │      Gemini        │
                 │ Reason / Propose   │
                 └─────────┬──────────┘
                           ↓
                 ┌────────────────────┐
                 │ Economics Engine   │
                 │ Optimize outcome   │
                 └─────────┬──────────┘
                           ↓
                 ┌────────────────────┐
                 │ Policy Guard       │
                 │ Authorize / Block  │
                 └─────────┬──────────┘
                           ↓
                 ┌────────────────────┐
                 │ Razorpay Executor  │
                 │ Execute action     │
                 └─────────┬──────────┘
                           ↓
                 ┌────────────────────┐
                 │ Webhook Verification│
                 │ Prove recovery     │
                 └────────────────────┘

This separation prevents the LLM from becoming the financial authority.

Stopping Rules

Automation must know when not to act.

REVERA stops recovery when:

Maximum attempts are reached

Customer contact limit is reached

Policy blocks the requested action

Transaction requires human review

The recovery strategy determines that further intervention is not
economically justified

The objective is not maximum automation.

The objective is:

Maximum verified recovery within controlled risk.

Auditability

Every important transition can be traced through the recovery lifecycle.

Case Created
     ↓
Risk Scored
     ↓
AI Diagnosed
     ↓
Strategy Proposed
     ↓
Economics Evaluated
     ↓
Policy Checked
     ↓
Action Executed
     ↓
Webhook Received
     ↓
Payment Verified
     ↓
Revenue Recovered

This makes the system suitable for explaining not only what
happened, but also why an action was selected.

Testing Strategy

REVERA should be tested across:

Risk

Low-risk case

High-risk case

Failed payment

Checkout abandonment

Repeated failures

Economics

PAYMENT_LINK

ALTERNATIVE_METHOD

RETRY

REMINDER

WAIT

INCENTIVE

STOP

Policy

Amount below automation limit

Amount above automation limit

Amount above human-review limit

Maximum attempts

Maximum contacts

Excessive discount

Razorpay

Payment-link creation

Successful payment

Partial payment

Cancellation

Expiration

Invalid webhook signature

Duplicate webhook event

Recovery Verification

Attempted ≠ Recovered

Created Payment Link ≠ Recovered

Successful Razorpay Webhook = Verified Recovery

Dashboard

The REVERA dashboard provides visibility into:

Revenue at risk

Verified recovered revenue

Recovery attempts

Active recovery value

Recovery rate

Case status

AI decisions

Recovery pipeline

Benchmark performance

Audit events

The interface is designed around the operational question:

Where is revenue leaking, what should we do, and how much money did
we actually recover?

Deployment

The recommended deployment architecture is:

                Internet
                   │
          ┌────────┴────────┐
          ↓                 ↓
     React Frontend      Razorpay
          │                 │
          ↓                 ↓
     FastAPI Backend ← Webhook
          │
     ┌────┴────┐
     ↓         ↓
  SQLite     Gemini

For the Buildathon demo:

Frontend can be deployed as a static site

FastAPI can be deployed as a web service

Razorpay Test Mode is used for the payment execution demo

Environment variables store secrets

SQLite is acceptable for the demonstration environment

For production deployment, the database should be replaced with a
durable managed database and additional operational controls should be
introduced.

Buildathon Demo Story

The recommended 5-minute story is:

0:00--0:25 --- Hook

"Every failed payment is not just a failed transaction. It is revenue
that may still be recoverable."

0:25--1:10 --- Problem

Show the revenue-at-risk dashboard and explain that generic retries or
reminders treat every failure the same.

1:10--2:00 --- AI Decision

Open a recovery case and show:

Risk
→ Diagnosis
→ Strategy
→ Economics
→ Policy
→ Final Action

2:00--3:00 --- Real Razorpay Flow

Execute an approved payment-link recovery in Razorpay Test Mode.

3:00--3:40 --- Governance

Show:

Policy decision

Audit trail

Attempt limits

Contact limits

Stopping rules

3:40--4:20 --- Benchmark

Show the 1,000-case controlled synthetic benchmark:

₹60.43 lakh net recovered
+7.09% vs baseline
₹1.35 lakh above fixed reminder
0 policy violations

4:20--5:00 --- Close

"REVERA doesn't just identify revenue leakage. It closes the loop from
detection to verified money recovered."

Key Design Principles

Detect

Find revenue that is at risk.

Diagnose

Understand the customer and payment context.

Decide

Choose a recovery strategy.

Optimize

Select the strongest expected economic outcome.

Act

Execute only an authorized action.

Prove

Count revenue only after external confirmation.

Learn

Use outcomes to improve future decisions.

Limitations

REVERA is a Buildathon prototype and should not be interpreted as a
production-ready financial automation platform.

Current limitations include:

Benchmark data is synthetic.

Razorpay execution is demonstrated in Test Mode.

SQLite is used for the prototype.

Model quality depends on available training data.

Live Gemini usage may be constrained by API quota.

Production deployment would require stronger observability,
authentication, durable storage, secret management, rate limiting,
and operational review workflows.

Future Roadmap

V1 --- Buildathon Prototype

Risk prediction

AI diagnosis

Strategy selection

Economics optimizer

Policy guard

Razorpay execution

Webhook verification

Audit trail

Benchmark lab

V2 --- Production Recovery Platform

Merchant-specific models

Online learning from verified outcomes

Durable event streaming

Multi-tenant architecture

Human approval workflows

Advanced customer segmentation

Experimentation / A-B testing

Recovery policy configuration UI

Production-grade observability

V3 --- Autonomous Revenue Recovery

Observe
   ↓
Predict
   ↓
Reason
   ↓
Optimize
   ↓
Act
   ↓
Verify
   ↓
Learn
   ↺

Security Notes

Never commit:

.env
API keys
Razorpay secrets
Webhook secrets
Database files containing sensitive data

Recommended .gitignore:

.env
.env.*
!.env.example

*.db
*.sqlite
*.sqlite3

__pycache__/
*.py[cod]

.venv/
venv/

node_modules/
dist/
.vite/

.DS_Store

Tech Stack

Frontend

React

Vite

JavaScript

CSS

Backend

Python

FastAPI

SQLite

AI / ML

Gemini

Scikit-learn

Structured model outputs

Provider abstraction

Payments

Razorpay Test Mode

Payment Links

Webhooks

HMAC verification
