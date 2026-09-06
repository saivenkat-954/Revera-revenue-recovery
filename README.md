::: {align="center"}

REVERA

Intelligent Revenue Recovery System

Detect. Decide. Act. Prove.

AI-powered revenue recovery that doesn't stop at prediction --- it
chooses an action, enforces policy, executes through Razorpay, and
counts money only after it is verified.

<br>{=html}






:::

The Problem

A failed payment is not necessarily lost revenue.

But most recovery systems stop at:

"This payment is likely to fail."

REVERA asks the harder questions:

Why did it fail?
What should we do next?
Is that action economically worth taking?
Are we allowed to take it?
Did it actually recover money?

That turns revenue recovery from a notification problem into a
closed-loop decision system.

The REVERA Idea

        Revenue at Risk
              │
              ▼
          ┌────────┐
          │ DETECT │  ML risk scoring
          └───┬────┘
              ▼
        ┌───────────┐
        │ DIAGNOSE  │  AI investigates context
        └─────┬─────┘
              ▼
         ┌────────┐
         │ DECIDE │  AI proposes strategy
         └───┬────┘
             ▼
       ┌────────────┐
       │  OPTIMIZE  │  Economics ranks actions
       └─────┬──────┘
             ▼
        ┌────────┐
        │   ACT  │  Policy → Razorpay
        └───┬────┘
            ▼
       ┌──────────┐
       │  PROVE   │  Webhook verifies payment
       └────┬─────┘
            ▼
       Verified ₹ Recovered
            │
            └──────────────► Learn

The core principle

AI proposes. Policy authorizes. Razorpay executes. Webhooks prove.

The LLM is never the financial authority.

Why REVERA Is Different

01 --- From prediction to action

A risk model only tells us what might happen.

REVERA turns that prediction into an action plan:

PAYMENT_LINK

ALTERNATIVE_METHOD

RETRY

REMINDER

WAIT

INCENTIVE

STOP

02 --- From probability to economics

The highest-probability action is not always the best action.

REVERA compares expected recovery against intervention cost and
friction.

Expected Net Recovery
        =
Expected Recovery Value
        -
Intervention Cost

03 --- From AI autonomy to controlled autonomy

Gemini can reason about a case, but it cannot bypass policy.

Gemini
  ↓
Diagnosis + Strategy

Economics Engine
  ↓
Expected Outcome

Policy Guard
  ↓
Approve / Block / Stop / Human Review

Razorpay
  ↓
Execute

Webhook
  ↓
Verify

04 --- From "action taken" to "money recovered"

This is the most important distinction.

Payment Link Created
        ≠
Revenue Recovered

Payment Successful
        ↓
Razorpay Webhook
        ↓
Verified Revenue

REVERA only counts recovered revenue after external confirmation.

Architecture

┌─────────────────────────────────────────────────────────────┐
│                     REVERA CONTROL PLANE                    │
│                                                             │
│  Razorpay Event                                             │
│       │                                                     │
│       ▼                                                     │
│  Event Gateway                                              │
│       │                                                     │
│       ▼                                                     │
│  Customer + Payment Context                                 │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────┐                                    │
│  │ ML Risk Engine      │                                    │
│  │ recovery probability│                                    │
│  └──────────┬──────────┘                                    │
│             ▼                                               │
│  ┌─────────────────────┐                                    │
│  │ Gemini Investigator │                                    │
│  │ diagnose the case   │                                    │
│  └──────────┬──────────┘                                    │
│             ▼                                               │
│  ┌─────────────────────┐                                    │
│  │ Gemini Strategy     │                                    │
│  │ propose action      │                                    │
│  └──────────┬──────────┘                                    │
│             ▼                                               │
│  ┌─────────────────────┐                                    │
│  │ Economics Optimizer │                                    │
│  │ rank expected value │                                    │
│  └──────────┬──────────┘                                    │
│             ▼                                               │
│  ┌─────────────────────┐                                    │
│  │ Policy Guard        │                                    │
│  │ deterministic auth  │                                    │
│  └──────────┬──────────┘                                    │
│             ▼                                               │
│  ┌─────────────────────┐                                    │
│  │ Razorpay Executor   │                                    │
│  │ Test Mode actions   │                                    │
│  └──────────┬──────────┘                                    │
│             │                                               │
└─────────────┼───────────────────────────────────────────────┘
              ▼
       Razorpay Webhook
              │
              ▼
       HMAC Verification
              │
              ▼
       Idempotency Check
              │
              ▼
       Verified ₹ Recovery
              │
              ▼
         Audit Trail

A Recovery Decision, End to End

Consider a case like:

Case                RCP-1042
Amount              ₹8,499
Event               payment.failed
Payment method      UPI
Failure reason      transient_failure
Attempts            0
Customer age        180 days

REVERA evaluates the case through multiple layers.

Risk Engine

Predicts the likelihood that the revenue can still be recovered.

AI Investigator

Uses payment + customer context to explain the likely reason and
recovery opportunity.

AI Strategy

Proposes the most suitable recovery action.

Economics Engine

Compares actions using expected recovery value, uplift, friction and
intervention cost.

Policy Guard

Checks whether the proposed action is permitted.

Executor

If authorized, creates the Razorpay Test Mode recovery action.

Webhook

When the customer actually pays, Razorpay confirms the outcome.

Result

The case moves from:

AT RISK
   ↓
RECOVERY ACTION
   ↓
PAYMENT CONFIRMED
   ↓
RECOVERED

The Intelligence Stack

REVERA deliberately separates different kinds of intelligence.

Layer                 Responsibility                Authority

ML Risk Engine        Predict recovery likelihood   No
Gemini Investigator   Understand the situation      No
Gemini Strategy       Propose an action             No
Economics Engine      Calculate expected value      No
Policy Guard          Authorize or stop action      Yes
Razorpay              Execute payment action        Yes
Webhook               Verify outcome                Yes

This separation is intentional.

The model can recommend. The system decides.

Recovery Economics

REVERA evaluates actions using an expected-value framework.

For an action a:

Expected Recovery(a)
    =
Amount at Risk × P(recovery | action, context)

Expected Net Recovery(a)
    =
Expected Recovery(a) − Intervention Cost(a)

The engine also accounts for action-specific behavior such as:

Recovery probability uplift

Payment friction

Attempt count

Customer contact frequency

Failure reason

Time since failure

Discount cost

Operational cost

The result is not:

"Which action sounds best?"

It is:

"Which permitted action has the strongest expected economic
outcome?"

Policy & Safety

Automation is useful only when it knows when to stop.

Current policy

Guardrail                       Limit

Automated recovery limit      ₹50,000
Human review limit            ₹75,000
Maximum recovery attempts           2
Maximum contacts / 24h              2
Maximum discount                   5%

Possible policy outcomes:

APPROVED
BLOCK
STOP
HUMAN_REVIEW

Stopping rules

REVERA stops intervention when:

Maximum attempts are reached

Customer contact limits are reached

A requested action violates merchant policy

Transaction value requires human review

Further intervention is not economically justified

The goal is not maximum automation.

The goal is maximum verified recovery within controlled risk.

Benchmark: 1,000 Controlled Synthetic Cases

REVERA was evaluated against two strategies:

Baseline

Fixed Reminder

REVERA

Results

Metric                        REVERA      Baseline   Fixed Reminder

Gross recovered      ₹61.34 lakh   ₹56.43 lakh      ₹59.32 lakh
Net recovered        ₹60.43 lakh   ₹56.43 lakh      ₹59.08 lakh
Recovery rate              55.8%         51.9%            53.9%
Successful cases      558 / 1000    519 / 1000       539 / 1000

REVERA outcome

Net recovered                 ₹60.43 lakh
Baseline                      ₹56.43 lakh
Incremental net recovery      ₹3.99 lakh
Relative uplift               +7.09%
Above fixed reminder          ₹1.35 lakh

Policy violations             0
Stopping violations           0

Action distribution

PAYMENT_LINK        365
ALTERNATIVE_METHOD  364
INCENTIVE           121
STOP                150

The headline

Across 1,000 controlled synthetic cases, REVERA generated ₹60.43
lakh in net recovered revenue --- a +7.09% uplift over baseline and
₹1.35 lakh above a fixed-reminder strategy, with zero policy
violations.

Important: This is a controlled synthetic benchmark, not a
production merchant performance claim.

ML Risk Model

REVERA uses a customer-group holdout strategy to reduce customer-level
leakage between training and test data.

Evaluation

Metric               Score

ROC-AUC         0.7829
Precision           0.5566
Recall              0.7047
F1                  0.6220
Accuracy            0.7129
Brier Score         0.1901

Train events      9,544
Test events       2,456
Test customers      586
Split              Customer-group holdout

The benchmark dataset is synthetic.

Razorpay Integration

REVERA demonstrates an actual recovery execution loop using Razorpay
Test Mode.

Decision
   ↓
Policy APPROVED
   ↓
PAYMENT_LINK
   ↓
Razorpay Test Payment Link
   ↓
Customer Payment
   ↓
Razorpay Webhook
   ↓
HMAC Verification
   ↓
Idempotency Check
   ↓
Recovery Action = PAID
   ↓
Case = RECOVERED
   ↓
Verified ₹ Revenue

The system also handles webhook-driven reconciliation and protects
against duplicate event processing.

AI Integration

REVERA uses Gemini for structured reasoning in two major stages:

Investigator

Payment context
Customer context
Failure context
        ↓
Why is this revenue at risk?

Strategy

Diagnosis
Risk
Economics context
        ↓
What should we do next?

The application uses a provider abstraction so AI providers can be
swapped without changing the recovery control plane.

Demo resilience

If live Gemini quota is unavailable, REVERA can fall back to
deterministic reasoning for continuity.

Fallback responses are explicitly identified as:

provider = revera-deterministic
model    = revera-fallback-v1
live     = false

The system therefore does not present fallback output as live Gemini
output.

Dashboard

The REVERA interface is designed as an operational revenue control
center.

It exposes:

Revenue at risk

Verified recovered revenue

Recovery attempts

Active recovery value

Recovery rate

Recovery cases

AI decision traces

Recovery pipeline

Benchmark results

Audit events

System configuration

The key question behind the UI is:

Where is money slipping away, what should we do, and what did we
actually recover?

API

Endpoint                        Purpose

GET /api/cases                List recovery cases
GET /api/cases/{case_id}      Inspect a case
POST /api/risk/score          Generate recovery risk
POST /api/recovery/decide     Run the decision pipeline
POST /api/recovery/execute    Execute an approved recovery action
GET /api/recovery/actions     View recovery actions
GET /api/analytics            Recovery analytics
GET /api/benchmark            Benchmark results
GET /api/ai/status            AI provider status
POST /api/webhooks/razorpay   Receive Razorpay events

Interactive API documentation is available through FastAPI Swagger at:

http://127.0.0.1:8000/docs

Repository Structure

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
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── style.css
│   │   └── ...
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
├── README.md
└── ...

Run Locally

Prerequisites

Python 3.12.x

Node.js

npm

Razorpay Test Mode credentials

Gemini API key

Backend

cd backend
python -m venv .venv

Windows

.venv\Scripts\activate

macOS / Linux

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Start:

uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

Environment Variables

Create backend/.env:

GEMINI_API_KEY=your_gemini_api_key

RAZORPAY_KEY_ID=rzp_test_xxxxxxxxx
RAZORPAY_KEY_SECRET=your_test_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

Never commit secrets.

Frontend

Open another terminal:

cd frontend
npm install

Create frontend/.env:

VITE_API_BASE_URL=http://127.0.0.1:8000

Start:

npm run dev

Security

Never commit:

.env
.env.*
*.db
*.sqlite
*.sqlite3
API keys
Razorpay secrets
Webhook secrets

Recommended root .gitignore:

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

Testing

REVERA's critical paths should be tested at every layer.

Risk

High-risk payment

Low-risk payment

Repeated failures

Checkout abandonment

Different payment methods

Different failure reasons

Economics

Payment link

Alternative method

Retry

Reminder

Wait

Incentive

Stop

Policy

Amount within automation limit

Amount above automation limit

Amount above human-review limit

Maximum attempts

Maximum contacts

Excessive discount

Webhooks

Valid signature

Invalid signature

Duplicate event

Payment success

Partial payment

Cancellation

Expiration

Recovery truth

Attempted
   ≠
Recovered

Created
   ≠
Recovered

Paid + Verified Webhook
   =
Verified Recovery

Tech Stack

Area       Technology

Frontend   React + Vite
Backend    Python + FastAPI
Database   SQLite
ML         Scikit-learn
AI         Gemini + provider abstraction
Payments   Razorpay Test Mode
Webhooks   HMAC SHA-256 verification
Recovery   Deterministic economics + policy engine

Roadmap

V1 --- Buildathon

Revenue risk scoring

AI diagnosis

AI strategy

Recovery economics

Policy guard

Razorpay Test Mode execution

Webhook verification

Audit trail

Controlled benchmark

V2 --- Production Recovery Platform

Merchant-specific models

Durable event streaming

Multi-tenant architecture

Human approval workflows

Online learning from verified outcomes

A/B recovery experiments

Advanced customer segmentation

Production observability

V3 --- Closed-Loop Revenue Intelligence

OBSERVE
   ↓
PREDICT
   ↓
REASON
   ↓
OPTIMIZE
   ↓
ACT
   ↓
VERIFY
   ↓
LEARN
   ↺

What We Would Build Next

The most valuable next step is not simply "more AI."

It is better feedback.

Every verified outcome can become a learning signal:

Context
  +
Decision
  +
Action
  +
Policy
  +
Outcome
  =
Better Future Recovery

That creates a compounding recovery system instead of a one-shot
automation.

Buildathon Demo

A five-minute demonstration can follow this sequence:

00:00 --- The hook

"Every failed payment is a revenue opportunity until we prove it is
lost."

00:30 --- Show the problem

Open the REVERA dashboard and show revenue at risk.

01:10 --- Show intelligence

Open a case and walk through:

Risk
→ Diagnosis
→ Strategy
→ Economics
→ Policy
→ Action

02:00 --- Show real execution

Execute an approved Razorpay Test Mode payment-link recovery.

03:00 --- Show governance

Open the audit trail and demonstrate that AI cannot bypass deterministic
policy.

03:40 --- Show proof

Show the webhook-confirmed recovery.

04:10 --- Show the benchmark

₹60.43 lakh net recovered
+7.09% vs baseline
₹1.35 lakh above fixed reminder
0 policy violations

04:40 --- Close

"REVERA doesn't just identify revenue leakage. It closes the loop
from detection to verified money recovered."

The One-Sentence Pitch

REVERA is an AI revenue recovery control plane that predicts
recoverability, reasons about the right intervention, optimizes for
expected net recovery, enforces policy before execution, and verifies
the actual money recovered through Razorpay.

Project Status

Buildathon-ready prototype

ML Risk Engine          ✓
AI Reasoning            ✓
Recovery Economics      ✓
Policy Guard            ✓
Razorpay Execution      ✓
Webhook Verification    ✓
Audit Trail             ✓
Benchmark               ✓
Dashboard               ✓

::: {align="center"}

REVERA

Recover More. Grow Smarter.

Detect. Decide. Act. Prove.
:::
