from __future__ import annotations

from typing import Any

from app.models import ActionRequest, Policy
from app.services.economics import evaluate_opportunities
from app.services.model_router import run_ai
from app.services.policy import evaluate_action
from app.services.risk_engine import risk_engine


ALLOWED_ACTIONS = {
    "PAYMENT_LINK",
    "RETRY",
    "ALTERNATIVE_METHOD",
    "REMINDER",
    "WAIT",
    "INCENTIVE",
    "STOP",
    "HUMAN_REVIEW",
}


TERMINAL_STATUSES = {
    "recovered",
    "stopped",
    "expired",
    "cancelled",
}


def _complexity(case: dict[str, Any]) -> int:
    score = 20

    amount = float(case.get("amount", 0) or 0)

    attempts = int(
        case.get(
            "attempt_count",
            case.get("attempts", 0),
        )
        or 0
    )

    failures = int(
        case.get(
            "failed_payments",
            case.get("failures", 0),
        )
        or 0
    )

    if amount >= 10000:
        score += 20

    if amount >= 25000:
        score += 20

    if attempts >= 1:
        score += 10

    if attempts >= 2:
        score += 15

    if failures >= 3:
        score += 15

    if case.get("failure_reason"):
        score += 5

    return min(score, 100)


def _uncertainty(
    risk_probability: float,
    diagnosis_confidence: float,
) -> float:
    risk_probability = min(
        1.0,
        max(0.0, float(risk_probability)),
    )

    diagnosis_confidence = min(
        1.0,
        max(0.0, float(diagnosis_confidence)),
    )

    risk_uncertainty = 1.0 - abs(risk_probability - 0.5) * 2
    diagnosis_uncertainty = 1.0 - diagnosis_confidence

    return round(
        min(
            1.0,
            max(
                0.0,
                risk_uncertainty * 0.6
                + diagnosis_uncertainty * 0.4,
            ),
        ),
        4,
    )


def _safe_action(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    action = value.strip().upper()

    if action in ALLOWED_ACTIONS:
        return action

    return None


def _discount_for_action(action: str) -> float:
    if action == "INCENTIVE":
        return 5.0

    return 0.0


def _policy_for_action(
    action: str,
    amount: float,
    attempt_count: int,
    contacts_24h: int,
) -> dict[str, Any]:
    if action == "HUMAN_REVIEW":
        return {
            "decision": "HUMAN_REVIEW",
            "reason": "Action requires human authorization.",
        }

    request = ActionRequest(
        action=action,
        amount=amount,
        attempt_count=attempt_count,
        contacts_24h=contacts_24h,
        discount_percent=_discount_for_action(action),
    )

    return evaluate_action(
        request,
        Policy(),
    )



def _deterministic_diagnosis(case: dict[str, Any], risk_probability: float, risk_score: float) -> dict[str, Any]:
    reason = str(case.get("failure_reason") or "unknown_failure").strip().lower()
    event_type = str(case.get("event_type") or case.get("event") or "payment.failed")
    payment_method = str(case.get("payment_method") or "unknown")
    successful = int(case.get("successful_payments", case.get("successes", 0)) or 0)
    failed = int(case.get("failed_payments", case.get("failures", 0)) or 0)
    attempts = int(case.get("attempt_count", case.get("attempts", 0)) or 0)
    contacts = int(case.get("contacts_24h", 0) or 0)

    causes = {
        "insufficient_funds": "Insufficient funds caused the payment attempt to fail.",
        "temporary_bank_failure": "A temporary bank failure interrupted payment processing.",
        "transient_failure": "A transient payment-processing failure interrupted the transaction.",
        "network_timeout": "A network timeout interrupted payment processing.",
        "repeated_failure": "Repeated payment failures indicate a low-confidence recovery case.",
        "checkout_abandoned": "The checkout was abandoned before payment completion.",
    }
    root_cause = causes.get(reason, f"{event_type} occurred with failure reason {reason}.")

    customer_context = (
        f"Customer has {successful} successful payments and {failed} failed payments. "
        f"Customer lifetime value is {float(case.get('customer_lifetime_value', case.get('lifetime_value', 0)) or 0):.2f} INR."
    )
    recovery_context = (
        f"Recovery probability is {risk_probability:.2%} with risk score {risk_score:.2f}. "
        f"There have been {attempts} recovery attempts and {contacts} contacts in the last 24 hours."
    )
    evidence = [
        f"failure_reason is {reason}",
        f"payment_method is {payment_method}",
        f"successful_payments is {successful} and failed_payments is {failed}",
        f"recovery_probability is {risk_probability:.4f} and risk_score is {risk_score:.4f}",
        f"attempt_count is {attempts} and contacts_24h is {contacts}",
    ]
    return {
        "root_cause": root_cause,
        "confidence": 0.75,
        "customer_context": customer_context,
        "recovery_context": recovery_context,
        "evidence": evidence,
    }


def _deterministic_strategy(case: dict[str, Any], risk: dict[str, Any], economics: dict[str, Any] | None = None) -> dict[str, Any]:
    recommendation = _safe_action(risk.get("recommendation")) or "STOP"
    if economics:
        economic_action = _safe_action(economics.get("recommended_action"))
        if economic_action:
            recommendation = economic_action
    reason = str(case.get("failure_reason") or "payment event").replace("_", " ")
    rationale = f"Deterministic fallback selected {recommendation} from the risk and recovery signals after AI provider unavailability. Trigger: {reason}."
    return {
        "action": recommendation,
        "rationale": rationale,
        "confidence": 0.75,
        "risks": ["Live Gemini reasoning was unavailable; deterministic controls remain authoritative."],
        "alternatives": [],
    }

def _build_risk_payload(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "amount": float(case.get("amount", 0) or 0),
        "event_type": case.get(
            "event_type",
            case.get("event", "payment.failed"),
        ),
        "payment_method": case.get(
            "payment_method",
            "upi",
        ),
        "failure_reason": case.get("failure_reason"),
        "attempt_count": int(
            case.get(
                "attempt_count",
                case.get("attempts", 0),
            )
            or 0
        ),
        "successful_payments": int(
            case.get(
                "successful_payments",
                case.get("successes", 0),
            )
            or 0
        ),
        "failed_payments": int(
            case.get(
                "failed_payments",
                case.get("failures", 0),
            )
            or 0
        ),
        "customer_age_days": int(
            case.get("customer_age_days", 180)
            or 180
        ),
        "customer_lifetime_value": float(
            case.get(
                "customer_lifetime_value",
                case.get("lifetime_value", 5000),
            )
            or 5000
        ),
        "days_since_last_payment": float(
            case.get("days_since_last_payment", 7)
            or 7
        ),
        "checkout_duration_seconds": float(
            case.get("checkout_duration_seconds", 120)
            or 120
        ),
        "prior_recovery_rate": float(
            case.get("prior_recovery_rate", 0)
            or 0
        ),
        "contacts_24h": int(
            case.get("contacts_24h", 0)
            or 0
        ),
    }


def _normalize_opportunities(
    opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for opportunity in opportunities:
        if not isinstance(opportunity, dict):
            continue

        action = _safe_action(
            opportunity.get("action")
        )

        if not action:
            continue

        try:
            expected_value = float(
                opportunity.get(
                    "expected_recovery_value",
                    0,
                )
                or 0
            )
        except (TypeError, ValueError):
            expected_value = 0.0

        try:
            incremental_value = float(
                opportunity.get(
                    "incremental_value",
                    0,
                )
                or 0
            )
        except (TypeError, ValueError):
            incremental_value = 0.0

        normalized.append(
            {
                **opportunity,
                "action": action,
                "expected_recovery_value": round(
                    max(expected_value, 0.0),
                    2,
                ),
                "incremental_value": round(
                    max(incremental_value, 0.0),
                    2,
                ),
            }
        )

    return sorted(
        normalized,
        key=lambda item: (
            item["expected_recovery_value"],
            item["incremental_value"],
        ),
        reverse=True,
    )


def _ai_metadata(result: Any) -> dict[str, Any]:
    structured = (
        result.structured
        if isinstance(result.structured, dict)
        else {}
    )

    return {
        "provider": result.provider,
        "model": result.model,
        "live": result.live,
        "latency_ms": round(
            float(result.latency_ms or 0),
            2,
        ),
        "error": result.error,
        "structured": structured,
    }


async def decide_recovery(
    case: dict[str, Any],
) -> dict[str, Any]:
    case_id = case.get(
        "case_id",
        case.get("id", "UNKNOWN"),
    )

    amount = float(
        case.get("amount", 0)
        or 0
    )

    event_type = case.get(
        "event_type",
        case.get(
            "event",
            "payment.failed",
        ),
    )

    current_status = str(
        case.get(
            "status",
            "at_risk",
        )
    ).lower()

    recovery_history = case.get(
        "recovery_history",
        {},
    )

    if not isinstance(
        recovery_history,
        dict,
    ):
        recovery_history = {}

    attempt_count = int(
        case.get(
            "attempt_count",
            case.get(
                "attempts",
                recovery_history.get(
                    "previous_attempts",
                    0,
                ),
            ),
        )
        or 0
    )

    contacts_24h = int(
        case.get(
            "contacts_24h",
            0,
        )
        or 0
    )

    if amount <= 0:
        return {
            "case_id": case_id,
            "status": "rejected",
            "final_action": "STOP",
            "execution_status": "not_executed",
            "reason": "Invalid transaction amount.",
        }

    if current_status in TERMINAL_STATUSES:
        return {
            "case_id": case_id,
            "status": "rejected",
            "final_action": "STOP",
            "execution_status": "not_executed",
            "reason": (
                f"Case is already in terminal state: "
                f"{current_status}"
            ),
        }

    risk_payload = _build_risk_payload(case)

    try:
        risk = risk_engine.predict(
            risk_payload
        )
    except Exception as exc:
        return {
            "case_id": case_id,
            "status": "human_review",
            "final_action": "HUMAN_REVIEW",
            "execution_status": "human_review",
            "reason": "Risk engine failed.",
            "error": str(exc),
        }

    recovery_probability = float(
        risk.get(
            "recovery_probability",
            0,
        )
        or 0
    )

    risk_score = float(
        risk.get(
            "risk_score",
            0,
        )
        or 0
    )

    complexity = _complexity(case)
    high_value = amount >= 10000

    diagnosis = await run_ai(
        task="diagnosis",
        case=case,
        complexity=complexity,
        uncertainty=0.4,
        high_value=high_value,
        force_provider=None,
    )

    diagnosis_data = (
        diagnosis.structured
        if isinstance(
            diagnosis.structured,
            dict,
        )
        else {}
    )

    diagnosis_confidence = float(
        diagnosis_data.get(
            "confidence",
            0,
        )
        or 0
    )

    uncertainty = _uncertainty(
        recovery_probability,
        diagnosis_confidence,
    )

    fallback_error = None
    if diagnosis.error or not diagnosis.live:
        fallback_error = diagnosis.error or "Gemini Investigator unavailable"
        diagnosis_data = _deterministic_diagnosis(
            case,
            recovery_probability,
            risk_score,
        )

    strategy_case = {
        **case,
        "risk": risk,
        "investigator": diagnosis_data,
    }

    strategy = await run_ai(
        task="strategy",
        case=strategy_case,
        complexity=min(
            100,
            complexity + 10,
        ),
        uncertainty=uncertainty,
        high_value=high_value,
        force_provider=None,
    )

    strategy_data = (
        strategy.structured
        if isinstance(
            strategy.structured,
            dict,
        )
        else {}
    )

    proposed_action = _safe_action(
        strategy_data.get(
            "action",
            strategy_data.get(
                "recommended_action"
            ),
        )
    )

    strategy_fallback_error = None
    if strategy.error or not strategy.live:
        strategy_fallback_error = strategy.error or "Gemini Strategy unavailable"
        strategy_data = _deterministic_strategy(case, risk)

    proposed_action = _safe_action(
        strategy_data.get(
            "action",
            strategy_data.get(
                "recommended_action"
            ),
        )
    )

    economics_payload = {
        "amount": amount,
        "recovery_probability": recovery_probability,
        "event_type": event_type,
        "payment_method": case.get(
            "payment_method",
            "upi",
        ),
        "failure_reason": case.get(
            "failure_reason"
        ),
        "attempt_count": attempt_count,
        "contacts_24h": contacts_24h,
        "customer_lifetime_value": float(
            case.get(
                "customer_lifetime_value",
                case.get(
                    "lifetime_value",
                    5000,
                ),
            )
            or 5000
        ),
        "hours_since_event": float(
            case.get(
                "hours_since_event",
                1,
            )
            or 1
        ),
    }

    economics = evaluate_opportunities(
        economics_payload
    )

    opportunities = _normalize_opportunities(
        economics.get(
            "opportunities",
            [],
        )
    )

    stopping_rules = economics.get(
        "stopping_rules",
        {},
    )

    policy_checks: list[dict[str, Any]] = []
    approved_opportunities: list[dict[str, Any]] = []
    human_review_actions: list[dict[str, Any]] = []

    for opportunity in opportunities:
        action = opportunity["action"]

        if action == "STOP":
            continue

        if not opportunity.get(
            "allowed_by_stopping_rules",
            True,
        ):
            policy_checks.append(
                {
                    "action": action,
                    "expected_recovery_value": opportunity[
                        "expected_recovery_value"
                    ],
                    "policy": {
                        "decision": "STOPPED",
                        "reason": opportunity.get(
                            "stopping_reason"
                        ),
                    },
                }
            )
            continue

        policy_result = _policy_for_action(
            action=action,
            amount=amount,
            attempt_count=attempt_count,
            contacts_24h=contacts_24h,
        )

        check = {
            "action": action,
            "expected_recovery_value": opportunity[
                "expected_recovery_value"
            ],
            "incremental_value": opportunity.get(
                "incremental_value",
                0,
            ),
            "policy": policy_result,
        }

        policy_checks.append(check)

        decision = policy_result.get(
            "decision"
        )

        if decision == "APPROVED":
            approved_opportunities.append(
                {
                    "opportunity": opportunity,
                    "policy": policy_result,
                }
            )

        elif decision == "HUMAN_REVIEW":
            human_review_actions.append(
                {
                    "opportunity": opportunity,
                    "policy": policy_result,
                }
            )

    final_action = "STOP"

    final_policy: dict[str, Any] = {
        "decision": "STOP",
        "reason": (
            stopping_rules.get("reason")
            or "No policy-approved recovery action."
        ),
    }

    selected_opportunity: dict[str, Any] | None = None

    if not stopping_rules.get(
        "allowed",
        True,
    ):
        final_action = "STOP"
        final_policy = {
            "decision": "STOP",
            "reason": (
                "Stopping rule prevented intervention: "
                f"{stopping_rules.get('reason', 'Unknown reason')}"
            ),
        }

    elif approved_opportunities:
        selected = max(
            approved_opportunities,
            key=lambda item: (
                item["opportunity"].get(
                    "expected_recovery_value",
                    0,
                ),
                item["opportunity"].get(
                    "incremental_value",
                    0,
                ),
            ),
        )

        selected_opportunity = selected[
            "opportunity"
        ]

        final_action = selected_opportunity[
            "action"
        ]

        final_policy = selected[
            "policy"
        ]

    elif human_review_actions:
        selected_opportunity = human_review_actions[0][
            "opportunity"
        ]

        final_action = "HUMAN_REVIEW"

        final_policy = {
            "decision": "HUMAN_REVIEW",
            "reason": (
                "Recovery opportunities require "
                "human authorization."
            ),
        }

    economics_action = _safe_action(
        economics.get(
            "recommended_action"
        )
    )

    strategy_agreement = (
        proposed_action == economics_action
        if proposed_action
        else False
    )

    if final_action == "WAIT":
        execution_status = "waiting"

    elif final_action == "STOP":
        execution_status = "not_executed"

    elif final_action == "HUMAN_REVIEW":
        execution_status = "human_review"

    elif (
        final_policy.get("decision")
        == "APPROVED"
    ):
        execution_status = "ready_for_execution"

    else:
        execution_status = "not_executed"

    expected_recovery_value = 0.0
    incremental_recovery_value = 0.0

    if selected_opportunity:
        expected_recovery_value = float(
            selected_opportunity.get(
                "expected_recovery_value",
                0,
            )
            or 0
        )

        incremental_recovery_value = float(
            selected_opportunity.get(
                "incremental_value",
                0,
            )
            or 0
        )

    return {
        "case_id": case_id,
        "status": "decision_ready",
        "case": {
            "amount": amount,
            "currency": case.get(
                "currency",
                "INR",
            ),
            "event_type": event_type,
            "payment_method": case.get(
                "payment_method",
                "unknown",
            ),
            "failure_reason": case.get(
                "failure_reason"
            ),
            "attempt_count": attempt_count,
            "contacts_24h": contacts_24h,
        },
        "risk": {
            "recovery_probability": round(
                recovery_probability,
                4,
            ),
            "expected_recovery": risk.get(
                "expected_recovery",
                amount * recovery_probability,
            ),
            "risk_score": round(
                risk_score,
                4,
            ),
            "recommendation": risk.get(
                "recommendation"
            ),
        },
        "investigator": {
            "provider": diagnosis.provider if diagnosis.live else "revera-deterministic",
            "model": diagnosis.model if diagnosis.live else "revera-fallback-v1",
            "live": diagnosis.live,
            "latency_ms": round(
                float(diagnosis.latency_ms or 0),
                2,
            ),
            "root_cause": diagnosis_data.get(
                "root_cause"
            ),
            "confidence": diagnosis_data.get(
                "confidence"
            ),
            "customer_context": diagnosis_data.get(
                "customer_context"
            ),
            "recovery_context": diagnosis_data.get(
                "recovery_context"
            ),
            "evidence": diagnosis_data.get(
                "evidence",
                [],
            ),
            "error": diagnosis.error if diagnosis.live else fallback_error,
        },
        "strategy": {
            "provider": strategy.provider if strategy.live else "revera-deterministic",
            "model": strategy.model if strategy.live else "revera-fallback-v1",
            "live": strategy.live,
            "latency_ms": round(
                float(strategy.latency_ms or 0),
                2,
            ),
            "proposed_action": proposed_action,
            "rationale": strategy_data.get(
                "rationale"
            ),
            "confidence": strategy_data.get(
                "confidence"
            ),
            "risks": strategy_data.get(
                "risks",
                [],
            ),
            "alternatives": strategy_data.get(
                "alternatives",
                [],
            ),
            "agrees_with_economics": strategy_agreement,
            "error": strategy.error if strategy.live else strategy_fallback_error,
        },
        "economics": {
            "amount_at_risk": economics.get(
                "amount_at_risk",
                amount,
            ),
            "base_recovery_probability": economics.get(
                "base_recovery_probability",
                recovery_probability,
            ),
            "baseline_recovery_value": economics.get(
                "baseline_recovery_value",
                amount * recovery_probability,
            ),
            "recommended_action": economics.get(
                "recommended_action"
            ),
            "expected_recovery_value": economics.get(
                "expected_recovery_value",
                0,
            ),
            "incremental_recovery_value": economics.get(
                "incremental_recovery_value",
                0,
            ),
            "recommended_probability": economics.get(
                "recommended_probability",
                0,
            ),
            "decision_reason": economics.get(
                "decision_reason"
            ),
            "stopping_rules": stopping_rules,
            "opportunities": opportunities,
        },
        "policy": {
            "decision": final_policy.get(
                "decision"
            ),
            "reason": final_policy.get(
                "reason"
            ),
            "checks": policy_checks,
        },
        "final_decision": {
            "action": final_action,
            "execution_status": execution_status,
            "llm_proposed_action": proposed_action,
            "economics_recommended_action": economics_action,
            "selected_expected_recovery_value": round(
                expected_recovery_value,
                2,
            ),
            "selected_incremental_recovery_value": round(
                incremental_recovery_value,
                2,
            ),
            "policy_authorized": (
                final_policy.get(
                    "decision"
                )
                == "APPROVED"
            ),
            "uncertainty": uncertainty,
        },
    }