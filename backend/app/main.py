from __future__ import annotations

import csv
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    ActionRequest,
    AIRequest,
    Case,
    EconomicsRequest,
    Policy,
    RecoveryDecisionRequest,
    RecoveryExecuteRequest,
    RiskRequest,
)

from app.services.policy import evaluate_action

from app.services.model_router import (
    route,
    run_ai,
    router_status,
)

from app.services.quota_manager import quota_manager

from app.services.benchmark import benchmark

from app.services.risk_engine import risk_engine

from app.services.economics import evaluate_opportunities

from app.services.recovery_pipeline import decide_recovery

from app.services.razorpay_executor import (
    create_payment_link,
    RazorpayExecutionError,
)

from app.services.razorpay_webhooks import (
    process_webhook,
    verify_signature,
)

from app.db import (
    init_db,
    upsert_case,
    get_cases,
    get_case,
    get_audit_events,
    get_case_audit_events,
    get_recovery_actions,
    get_recovery_analytics,
    get_active_recovery_action,
)


app = FastAPI(
    title="REVERA API",
    description="Intelligent Revenue Recovery System",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://gerald-meaning-hotel-rock.trycloudflare.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    ROOT
    / "data"
    / "revenue_events.csv"
)


CASES = [
    Case(
        id="RCP-1042",
        customer_id="CUS-204",
        amount=8499,
        event_type="payment.failed",
        payment_method="upi",
        failure_reason="transient_failure",
        attempt_count=1,
        successful_payments=7,
        failed_payments=1,
        recovery_probability=0.78,
        risk_score=0.84,
        recommended_action="PAYMENT_LINK",
    ),
    Case(
        id="RCP-1043",
        customer_id="CUS-205",
        amount=12500,
        event_type="checkout.abandoned",
        payment_method="card",
        failure_reason=None,
        attempt_count=0,
        successful_payments=3,
        failed_payments=0,
        recovery_probability=0.61,
        risk_score=0.73,
        recommended_action="REMINDER",
    ),
    Case(
        id="RCP-1044",
        customer_id="CUS-206",
        amount=499,
        event_type="payment.failed",
        payment_method="upi",
        failure_reason="repeated_failure",
        attempt_count=2,
        successful_payments=1,
        failed_payments=6,
        recovery_probability=0.09,
        risk_score=0.41,
        recommended_action="STOP",
    ),
]


@app.on_event("startup")
def startup() -> None:
    init_db()

    if not DATA_PATH.exists():
        from scripts.generate_dataset import main as generate_dataset

        generate_dataset()

    for case in CASES:
        upsert_case(case.model_dump())

    risk_engine.initialize()


@app.get("/")
def root():
    return {
        "service": "REVERA",
        "description": "Intelligent Revenue Recovery System",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "revera-api",
        "version": "1.0.0",
        "risk_engine": risk_engine.ready,
    }


@app.get(
    "/api/cases",
    response_model=list[Case],
)
def list_cases():
    cases = get_cases()

    if not cases:
        return [
            case.model_dump()
            for case in CASES
        ]

    return cases


@app.get(
    "/api/cases/{case_id}",
    response_model=Case,
)
def get_case_endpoint(
    case_id: str,
):
    case = get_case(case_id)

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return case


@app.post("/api/policy/evaluate")
def policy(
    req: ActionRequest,
    policy: Policy = Policy(),
):
    return evaluate_action(
        req,
        policy,
    )


@app.get("/api/router/preview")
def router_preview(
    task: str = "diagnosis",
    complexity: int = 40,
    uncertainty: float = 0.3,
    high_value: bool = False,
):
    return route(
        task,
        complexity,
        uncertainty,
        high_value,
    ).__dict__


@app.get("/api/ai/status")
def ai_status():
    return router_status()


@app.get("/api/ai/quota")
def ai_quota():
    return quota_manager.snapshot()


@app.get("/api/ai/benchmark")
async def ai_benchmark(
    limit: int = 100,
    live: bool = False,
):
    limit = max(
        1,
        min(limit, 1000),
    )

    return benchmark(
        limit=limit,
        live=live,
    )


@app.get("/api/benchmark")
async def benchmark_endpoint(
    limit: int = 100,
    live: bool = False,
):
    limit = max(
        1,
        min(limit, 1000),
    )

    return benchmark(
        limit=limit,
        live=live,
    )


@app.get("/api/ai/route")
def ai_route(
    task: str = "diagnosis",
    complexity: int = 40,
    uncertainty: float = 0.3,
    high_value: bool = False,
):
    return route(
        task,
        complexity,
        uncertainty,
        high_value,
    ).__dict__


@app.post("/api/ai/run")
async def ai_run(
    req: AIRequest,
):
    result = await run_ai(
        req.task,
        req.case,
        req.complexity,
        req.uncertainty,
        req.high_value,
        req.force_provider,
    )

    return result.__dict__


@app.get("/api/risk/metrics")
def risk_metrics():
    return risk_engine.metrics


@app.post("/api/risk/score")
def risk_score(
    req: RiskRequest,
):
    return risk_engine.predict(
        req.model_dump()
    )


@app.post("/api/economics/evaluate")
def economics(
    req: EconomicsRequest,
):
    return evaluate_opportunities(
        req.model_dump()
    )


@app.post("/api/recovery/decide")
async def recovery_decide(
    req: RecoveryDecisionRequest,
):
    case = req.model_dump()

    existing_case = get_case(
        case["case_id"]
    )

    if existing_case is None:
        case_data = {
            "id": case["case_id"],
            "customer_id": case["customer_id"],
            "amount": case["amount"],
            "currency": case.get(
                "currency",
                "INR",
            ),
            "event_type": case.get(
                "event_type",
                "payment.failed",
            ),
            "payment_method": case.get(
                "payment_method",
                "upi",
            ),
            "failure_reason": case.get(
                "failure_reason"
            ),
            "attempt_count": case.get(
                "attempts",
                0,
            ),
            "successful_payments": case.get(
                "successes",
                0,
            ),
            "failed_payments": case.get(
                "failures",
                0,
            ),
            "customer_age_days": case.get(
                "customer_age_days",
                180,
            ),
            "customer_lifetime_value": case.get(
                "customer_lifetime_value",
                5000,
            ),
            "days_since_last_payment": case.get(
                "days_since_last_payment",
                7,
            ),
            "checkout_duration_seconds": case.get(
                "checkout_duration_seconds",
                120,
            ),
            "prior_recovery_rate": case.get(
                "prior_recovery_rate",
                0,
            ),
            "contacts_24h": case.get(
                "contacts_24h",
                0,
            ),
            "hours_since_event": case.get(
                "hours_since_event",
                1,
            ),
            "status": "at_risk",
        }

        existing_case = upsert_case(
            case_data
        )

    else:
        case_data = {
            **existing_case,
            **case,
            "id": case["case_id"],
            "attempt_count": case.get(
                "attempts",
                existing_case.get(
                    "attempt_count",
                    0,
                ),
            ),
            "successful_payments": case.get(
                "successes",
                existing_case.get(
                    "successful_payments",
                    0,
                ),
            ),
            "failed_payments": case.get(
                "failures",
                existing_case.get(
                    "failed_payments",
                    0,
                ),
            ),
        }

    decision = await decide_recovery(
        case_data
    )

    return decision


@app.post("/api/recovery/execute")
async def recovery_execute(
    req: RecoveryExecuteRequest,
):
    request_data = req.model_dump()

    case_id = str(
        request_data["case_id"]
    )

    existing_case = get_case(
        case_id
    )

    if not existing_case:
        raise HTTPException(
            status_code=404,
            detail="Recovery case not found.",
        )

    case_status = str(
        existing_case.get(
            "status",
            "at_risk",
        )
    ).lower()

    if case_status in {
        "recovered",
        "stopped",
        "expired",
        "cancelled",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Case is already in terminal "
                f"state: {case_status}."
            ),
        )

    if request_data["action"] != "PAYMENT_LINK":
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PAYMENT_LINK execution "
                "is enabled in Test Mode."
            ),
        )

    active_action = get_active_recovery_action(
        case_id
    )

    if active_action:
        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Recovery action already exists "
                    "for this case."
                ),
                "case_id": case_id,
                "action_id": active_action["id"],
                "action": active_action["action"],
                "status": active_action["status"],
                "provider_id": active_action.get(
                    "provider_id"
                ),
                "payment_link": active_action.get(
                    "payment_link"
                ),
            },
        )

    server_amount = float(
        existing_case.get(
            "amount",
            0,
        ) or 0
    )

    server_currency = str(
        existing_case.get(
            "currency",
            "INR",
        )
    ).upper()

    server_customer_id = str(
        existing_case.get(
            "customer_id",
            request_data["customer_id"],
        )
    )

    server_attempts = int(
        existing_case.get(
            "attempt_count",
            0,
        ) or 0
    )

    server_contacts = int(
        existing_case.get(
            "contacts_24h",
            0,
        ) or 0
    )

    authorization = evaluate_action(
        ActionRequest(
            action="PAYMENT_LINK",
            amount=server_amount,
            attempt_count=server_attempts,
            contacts_24h=server_contacts,
            discount_percent=0,
        ),
        Policy(),
    )

    if authorization["decision"] != "APPROVED":
        raise HTTPException(
            status_code=403,
            detail={
                "message": (
                    "Recovery action was rejected "
                    "by the server-side policy guard."
                ),
                "authorization": authorization,
            },
        )

    execution_case = {
        "case_id": case_id,
        "customer_id": server_customer_id,
        "amount": server_amount,
        "currency": server_currency,
        "action": "PAYMENT_LINK",
        "customer_name": request_data.get(
            "customer_name"
        ),
        "customer_email": request_data.get(
            "customer_email"
        ),
        "customer_contact": request_data.get(
            "customer_contact"
        ),
    }

    try:
        result = await create_payment_link(
            execution_case
        )

        return {
            **result,
            "authorization": {
                "source": "server",
                "decision": authorization[
                    "decision"
                ],
                "policy": authorization,
            },
        }

    except RazorpayExecutionError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post("/api/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
):
    body = await request.body()

    signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    event_id = request.headers.get(
        "x-razorpay-event-id"
    )

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Razorpay-Signature.",
        )

    if not event_id:
        raise HTTPException(
            status_code=400,
            detail="Missing x-razorpay-event-id.",
        )

    if not verify_signature(
        body,
        signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature.",
        )

    try:
        return process_webhook(
            body,
            event_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.get("/api/audit")
def audit_events(
    limit: int = 100,
):
    limit = max(
        1,
        min(limit, 500),
    )

    return {
        "success": True,
        "events": get_audit_events(
            limit
        ),
    }


@app.get("/api/audit/{case_id}")
def case_audit(
    case_id: str,
):
    return {
        "success": True,
        "case_id": case_id,
        "events": get_case_audit_events(
            case_id
        ),
    }


@app.get("/api/recovery/actions")
def recovery_actions(
    limit: int = 100,
):
    limit = max(
        1,
        min(limit, 500),
    )

    return {
        "success": True,
        "actions": get_recovery_actions(
            limit
        ),
    }


@app.get("/api/analytics")
def analytics():
    events = 0
    customers = 0
    revenue_at_risk = 0.0
    average_event_value = 0.0

    if DATA_PATH.exists():
        with DATA_PATH.open(
            encoding="utf-8"
        ) as f:
            rows = list(
                csv.DictReader(f)
            )

        events = len(rows)

        customers = len(
            {
                r["customer_id"]
                for r in rows
            }
        )

        if rows:
            revenue_at_risk = sum(
                float(r["amount"])
                for r in rows
                if r["recovered"] == "0"
            )

            average_event_value = (
                sum(
                    float(r["amount"])
                    for r in rows
                )
                / len(rows)
            )

    recovery = get_recovery_analytics()

    verified_recovered = float(
        recovery.get(
            "verified_recovered",
            0,
        )
        or 0
    )

    recovery_attempts = int(
        recovery.get(
            "recovery_attempts",
            0,
        )
        or 0
    )

    active_recovery_value = float(
        recovery.get(
            "active_recovery_value",
            0,
        )
        or 0
    )

    partial_verified_recovered = float(
        recovery.get(
            "partial_verified_recovered",
            0,
        )
        or 0
    )

    recovery_rate = (
        verified_recovered / revenue_at_risk
        if revenue_at_risk > 0
        else 0
    )

    return {
        "events": events,
        "customers": customers,
        "revenue_at_risk": round(
            revenue_at_risk,
            2,
        ),
        "recovered": round(
            verified_recovered,
            2,
        ),
        "verified_recovered": round(
            verified_recovered,
            2,
        ),
        "partial_verified_recovered": round(
            partial_verified_recovered,
            2,
        ),
        "recovery_attempts": recovery_attempts,
        "active_recovery_value": round(
            active_recovery_value,
            2,
        ),
        "recovery_rate": round(
            recovery_rate,
            4,
        ),
        "average_event_value": round(
            average_event_value,
            2,
        ),
        "risk_model": risk_engine.metrics,
    }