from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Case(BaseModel):
    id: str
    customer_id: str
    amount: float = Field(gt=0)
    currency: str = "INR"
    event_type: str
    payment_method: str | None = None
    failure_reason: str | None = None
    attempt_count: int = Field(default=0, ge=0)
    successful_payments: int = Field(default=0, ge=0)
    failed_payments: int = Field(default=0, ge=0)
    recovery_probability: float = Field(
        default=0.0,
        ge=0,
        le=1,
    )
    risk_score: float = Field(
        default=0.0,
        ge=0,
        le=1,
    )
    expected_recovery: float = Field(
        default=0.0,
        ge=0,
    )
    recovered_amount: float = Field(
        default=0.0,
        ge=0,
    )
    status: Literal[
        "at_risk",
        "investigating",
        "decision_ready",
        "recovery_pending",
        "ready_for_execution",
        "executed",
        "partially_recovered",
        "recovered",
        "stopped",
        "escalated",
        "human_review",
        "expired",
        "cancelled",
        "execution_failed",
    ] = "at_risk"
    recommended_action: str | None = None
    created_at: str | None = None


class Policy(BaseModel):

    auto_action_limit: float = Field(
        default=50000,
        ge=0,
    )

    max_attempts: int = Field(
        default=2,
        ge=0,
    )

    max_discount_percent: float = Field(
        default=5,
        ge=0,
    )

    max_contacts_24h: int = Field(
        default=2,
        ge=0,
    )

    human_review_limit: float = Field(
        default=75000,
        ge=0,
    )


class ActionRequest(BaseModel):
    action: str
    amount: float = Field(gt=0)
    attempt_count: int = Field(
        default=0,
        ge=0,
    )
    contacts_24h: int = Field(
        default=0,
        ge=0,
    )
    discount_percent: float = Field(
        default=0,
        ge=0,
    )


class EconomicsRequest(BaseModel):
    amount: float = Field(gt=0)
    recovery_probability: float = Field(
        ge=0,
        le=1,
    )
    event_type: str
    payment_method: str = "upi"
    failure_reason: str | None = None
    attempt_count: int = Field(
        default=0,
        ge=0,
    )
    contacts_24h: int = Field(
        default=0,
        ge=0,
    )
    customer_lifetime_value: float = Field(
        default=5000,
        ge=0,
    )
    hours_since_event: float = Field(
        default=1,
        ge=0,
    )


class RiskRequest(BaseModel):
    amount: float = Field(gt=0)
    event_type: str
    payment_method: str
    failure_reason: str | None = None
    attempt_count: int = Field(
        default=0,
        ge=0,
    )
    successful_payments: int = Field(
        default=0,
        ge=0,
    )
    failed_payments: int = Field(
        default=0,
        ge=0,
    )
    customer_age_days: int = Field(
        default=180,
        ge=0,
    )
    customer_lifetime_value: float = Field(
        default=5000,
        ge=0,
    )
    days_since_last_payment: float = Field(
        default=7,
        ge=0,
    )
    checkout_duration_seconds: float = Field(
        default=120,
        ge=0,
    )
    prior_recovery_rate: float = Field(
        default=0,
        ge=0,
        le=1,
    )
    contacts_24h: int = Field(
        default=0,
        ge=0,
    )


class AIRequest(BaseModel):
    task: Literal[
        "diagnosis",
        "strategy",
        "communication",
    ]
    case: dict
    complexity: int = Field(
        ge=0,
        le=100,
    )
    uncertainty: float = Field(
        ge=0,
        le=1,
    )
    high_value: bool = False
    force_provider: str | None = None


class RecoveryDecisionRequest(BaseModel):
    case_id: str
    customer_id: str
    amount: float = Field(gt=0)
    currency: str = "INR"

    event_type: str
    payment_method: str
    failure_reason: str | None = None

    attempts: int = Field(
        default=0,
        ge=0,
    )
    successes: int = Field(
        default=0,
        ge=0,
    )
    failures: int = Field(
        default=0,
        ge=0,
    )

    customer_age_days: int = Field(
        default=180,
        ge=0,
    )
    customer_lifetime_value: float = Field(
        default=5000,
        ge=0,
    )
    days_since_last_payment: float = Field(
        default=7,
        ge=0,
    )
    checkout_duration_seconds: float = Field(
        default=120,
        ge=0,
    )
    prior_recovery_rate: float = Field(
        default=0,
        ge=0,
        le=1,
    )

    contacts_24h: int = Field(
        default=0,
        ge=0,
    )
    hours_since_event: float = Field(
        default=1,
        ge=0,
    )


class RecoveryExecuteRequest(BaseModel):
    case_id: str
    customer_id: str
    amount: float = Field(gt=0)
    currency: str = "INR"
    action: str
    policy_status: str = "approved"

    customer_name: str | None = None
    customer_email: str | None = None
    customer_contact: str | None = None