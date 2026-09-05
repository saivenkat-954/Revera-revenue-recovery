from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import random

from app.models import ActionRequest, Policy
from app.services.economics import evaluate_opportunities
from app.services.action_model import action_probability
from app.services.policy import evaluate_action


ACTIONS = [
    "PAYMENT_LINK",
    "RETRY",
    "ALTERNATIVE_METHOD",
    "REMINDER",
    "WAIT",
    "INCENTIVE",
    "STOP",
]


@dataclass(frozen=True)
class Scenario:
    case_id: str
    event_type: str
    failure_reason: str
    payment_method: str
    amount: float
    recovery_probability: float
    attempt_count: int
    contacts_24h: int
    hours_since_event: float
    customer_lifetime_value: float
    true_probability: float


TEMPLATES = [
    (
        "payment.failed",
        "insufficient_funds",
        "card",
        0.34,
        0,
        0.18,
        0.52,
    ),
    (
        "payment.failed",
        "transient_failure",
        "upi",
        0.62,
        0,
        0.30,
        0.70,
    ),
    (
        "payment.failed",
        "network_timeout",
        "card",
        0.58,
        0,
        0.22,
        0.66,
    ),
    (
        "payment.failed",
        "repeated_failure",
        "upi",
        0.12,
        2,
        0.60,
        0.16,
    ),
    (
        "checkout.abandoned",
        "checkout_abandonment",
        "card",
        0.56,
        0,
        0.70,
        0.61,
    ),
    (
        "checkout.abandoned",
        "low_intent",
        "upi",
        0.27,
        0,
        1.40,
        0.30,
    ),
    (
        "subscription.failed",
        "mandate_failure",
        "card",
        0.51,
        1,
        0.40,
        0.59,
    ),
    (
        "invoice.overdue",
        "overdue_receivable",
        "bank_transfer",
        0.43,
        0,
        18.0,
        0.49,
    ),
]


def _clamp(
    value: float,
    minimum: float = 0.02,
    maximum: float = 0.96,
) -> float:
    return min(
        maximum,
        max(minimum, value),
    )


def _generate_amount(
    rng: random.Random,
) -> float:
    bucket = rng.random()

    if bucket < 0.65:
        return round(
            rng.uniform(499, 10000),
            2,
        )

    if bucket < 0.90:
        return round(
            rng.uniform(10000, 25000),
            2,
        )

    return round(
        rng.uniform(25000, 50000),
        2,
    )


def build_cases(
    limit: int = 1000,
    seed: int = 20260905,
) -> list[Scenario]:
    rng = random.Random(seed)
    cases: list[Scenario] = []

    for index in range(limit):
        (
            event_type,
            failure_reason,
            payment_method,
            base,
            attempts,
            hours,
            truth,
        ) = TEMPLATES[
            index % len(TEMPLATES)
        ]

        amount = _generate_amount(
            rng
        )

        jitter = rng.uniform(
            -0.07,
            0.07,
        )

        recovery_probability = _clamp(
            base + jitter
        )

        true_probability = _clamp(
            truth + jitter * 0.55
        )

        contacts = 0

        if attempts >= 2:
            contacts = 1

        if index % 11 == 0:
            contacts = 1

        if index % 37 == 0:
            contacts = 2

        clv = round(
            amount * rng.uniform(
                1.5,
                5.0,
            ),
            2,
        )

        cases.append(
            Scenario(
                case_id=(
                    f"BENCH-{index + 1:04d}"
                ),
                event_type=event_type,
                failure_reason=failure_reason,
                payment_method=payment_method,
                amount=amount,
                recovery_probability=(
                    recovery_probability
                ),
                attempt_count=attempts,
                contacts_24h=contacts,
                hours_since_event=hours,
                customer_lifetime_value=clv,
                true_probability=true_probability,
            )
        )

    return cases


def _action_probability(
    case: Scenario,
    action: str,
) -> float:
    return action_probability(
        base=case.true_probability,
        action=action,
        event_type=case.event_type,
        failure_reason=case.failure_reason,
        attempts=case.attempt_count,
        hours=case.hours_since_event,
    )

def _simulate(
    probability: float,
    draw: float,
) -> bool:
    return draw < probability


def _baseline_result(
    case: Scenario,
    draw: float,
) -> dict[str, float | int]:
    recovered = (
        case.amount
        if _simulate(
            case.true_probability,
            draw,
        )
        else 0.0
    )

    return {
        "recovered": round(
            recovered,
            2,
        ),
        "intervention_cost": 0.0,
        "net_recovered": round(
            recovered,
            2,
        ),
        "successes": int(
            recovered > 0
        ),
    }


def _fixed_strategy_result(
    case: Scenario,
    action: str,
    draw: float,
) -> dict[str, float | int]:
    probability = _action_probability(
        case,
        action,
    )

    recovered = (
        case.amount
        if _simulate(
            probability,
            draw,
        )
        else 0.0
    )

    friction_rates = {
        "RETRY": 0.012,
        "REMINDER": 0.004,
    }

    operational_costs = {
        "RETRY": 5.0,
        "REMINDER": 2.0,
    }

    cost = (
        case.amount
        * friction_rates[action]
        + operational_costs[action]
    )

    net = max(
        0.0,
        recovered - cost,
    )

    return {
        "recovered": round(
            recovered,
            2,
        ),
        "intervention_cost": round(
            cost,
            2,
        ),
        "net_recovered": round(
            net,
            2,
        ),
        "successes": int(
            recovered > 0
        ),
    }


def _evaluate_policy(
    action: str,
    case: Scenario,
) -> dict[str, Any]:
    if action == "STOP":
        return {
            "decision": "STOP",
            "reason": "Stopping rule selected STOP.",
        }

    request = ActionRequest(
        action=action,
        amount=case.amount,
        attempt_count=case.attempt_count,
        contacts_24h=case.contacts_24h,
        discount_percent=(
            5.0
            if action == "INCENTIVE"
            else 0.0
        ),
    )

    return evaluate_action(
        request,
        Policy(),
    )


def _revera_result(
    case: Scenario,
    draw: float,
) -> tuple[
    dict[str, float | int],
    dict[str, Any],
]:
    economics = evaluate_opportunities(
    {
        "amount": case.amount,
        "recovery_probability": case.recovery_probability,
        "event_type": case.event_type,
        "failure_reason": case.failure_reason,
        "attempt_count": case.attempt_count,
        "hours_since_event": case.hours_since_event,
        "contacts_24h": case.contacts_24h,
    }
)

    stopping_rules = economics.get(
        "stopping_rules",
        {},
    )

    stopping_allowed = bool(
        stopping_rules.get(
            "allowed",
            True,
        )
    )

    opportunities = economics.get(
        "opportunities",
        [],
    )

    if not stopping_allowed:
        return (
            {
                "recovered": 0.0,
                "intervention_cost": 0.0,
                "net_recovered": 0.0,
                "successes": 0,
            },
            {
                "selected_action": "STOP",
                "policy_decision": "STOP",
                "automatic_action": False,
                "stopping_allowed": False,
                "expected_recovery_value": 0.0,
                "incremental_recovery_value": 0.0,
                "human_review": False,
            },
        )

    approved: list[
        dict[str, Any]
    ] = []

    human_review_required = False

    policy_checks = []

    for opportunity in opportunities:
        action = str(
            opportunity.get(
                "action",
                "STOP",
            )
        ).upper()

        if action == "STOP":
            continue

        policy_result = _evaluate_policy(
            action,
            case,
        )

        policy_checks.append(
            {
                "action": action,
                "policy": policy_result,
                "expected_recovery_value": (
                    opportunity.get(
                        "expected_recovery_value",
                        0.0,
                    )
                ),
            }
        )

        decision = policy_result.get(
            "decision"
        )

        if decision == "APPROVED":
            approved.append(
                {
                    "opportunity": opportunity,
                    "policy": policy_result,
                }
            )

        elif decision == "HUMAN_REVIEW":
            human_review_required = True

    if approved:
        selected = max(
            approved,
            key=lambda item: (
                float(
                    item[
                        "opportunity"
                    ].get(
                        "expected_recovery_value",
                        0.0,
                    )
                ),
                float(
                    item[
                        "opportunity"
                    ].get(
                        "incremental_value",
                        0.0,
                    )
                ),
            ),
        )

        selected_opportunity = selected[
            "opportunity"
        ]

        selected_action = str(
            selected_opportunity[
                "action"
            ]
        )

        policy_decision = selected[
            "policy"
        ].get(
            "decision",
            "HUMAN_REVIEW",
        )

        automatic_action = (
            policy_decision
            == "APPROVED"
        )

        probability = (
            _action_probability(
                case,
                selected_action,
            )
            if automatic_action
            else 0.0
        )

        recovered = (
            case.amount
            if _simulate(
                probability,
                draw,
            )
            else 0.0
        )

        cost = (
            float(
                selected_opportunity.get(
                    "incentive_cost",
                    0.0,
                )
            )
            + float(
                selected_opportunity.get(
                    "friction_cost",
                    0.0,
                )
            )
            + float(
                selected_opportunity.get(
                    "operational_cost",
                    0.0,
                )
            )
        )

        net = max(
            0.0,
            recovered - cost,
        )

        return (
            {
                "recovered": round(
                    recovered,
                    2,
                ),
                "intervention_cost": round(
                    cost,
                    2,
                ),
                "net_recovered": round(
                    net,
                    2,
                ),
                "successes": int(
                    recovered > 0
                ),
            },
            {
                "selected_action": (
                    selected_action
                ),
                "policy_decision": (
                    policy_decision
                ),
                "automatic_action": (
                    automatic_action
                ),
                "stopping_allowed": True,
                "expected_recovery_value": float(
                    selected_opportunity.get(
                        "expected_recovery_value",
                        0.0,
                    )
                ),
                "incremental_recovery_value": float(
                    selected_opportunity.get(
                        "incremental_value",
                        0.0,
                    )
                ),
                "human_review": False,
                "policy_checks": policy_checks,
            },
        )

    if human_review_required:
        return (
            {
                "recovered": 0.0,
                "intervention_cost": 0.0,
                "net_recovered": 0.0,
                "successes": 0,
            },
            {
                "selected_action": "HUMAN_REVIEW",
                "policy_decision": "HUMAN_REVIEW",
                "automatic_action": False,
                "stopping_allowed": True,
                "expected_recovery_value": 0.0,
                "incremental_recovery_value": 0.0,
                "human_review": True,
                "escalated_amount_at_risk": case.amount,
                "escalated_expected_recovery_value": max(
                    (
                        float(
                            opportunity.get(
                                "expected_recovery_value",
                                0.0,
                            )
                        )
                        for opportunity in opportunities
                        if str(
                            opportunity.get(
                                "action",
                                "STOP",
                            )
                        ).upper() != "STOP"
                    ),
                    default=0.0,
                ),
                "policy_checks": policy_checks,
            },
        )

    return (
        {
            "recovered": 0.0,
            "intervention_cost": 0.0,
            "net_recovered": 0.0,
            "successes": 0,
        },
        {
            "selected_action": "STOP",
            "policy_decision": "STOP",
            "automatic_action": False,
            "stopping_allowed": True,
            "expected_recovery_value": 0.0,
            "incremental_recovery_value": 0.0,
            "human_review": False,
            "policy_checks": policy_checks,
        },
    )


def _aggregate(
    rows: list[
        dict[str, float | int]
    ],
) -> dict[str, Any]:
    total = len(rows)

    recovered = round(
        sum(
            float(
                row["recovered"]
            )
            for row in rows
        ),
        2,
    )

    intervention_cost = round(
        sum(
            float(
                row["intervention_cost"]
            )
            for row in rows
        ),
        2,
    )

    net_recovered = round(
        sum(
            float(
                row["net_recovered"]
            )
            for row in rows
        ),
        2,
    )

    successes = sum(
        int(
            row["successes"]
        )
        for row in rows
    )

    return {
        "recovered": recovered,
        "intervention_cost": intervention_cost,
        "net_recovered": net_recovered,
        "recovery_rate": round(
            successes / total,
            4,
        ) if total else 0.0,
        "successes": successes,
        "cases": total,
    }


def benchmark(
    limit: int = 1000,
    live: bool = False,
) -> dict[str, Any]:
    limit = max(
        1,
        min(
            int(limit),
            1000,
        ),
    )

    cases = build_cases(
        limit=limit,
        seed=20260905,
    )

    rng = random.Random(
        20260905
    )

    baseline_rows = []
    retry_rows = []
    reminder_rows = []
    revera_rows = []

    details = []

    stopping_compliant = 0
    policy_compliant = 0
    policy_violations = 0
    stopping_violations = 0
    human_review = 0
    automatic_actions = 0
    schema_valid = 0
    action_counts = {action: 0 for action in ACTIONS}
    action_counts["HUMAN_REVIEW"] = 0

    escalated_amount_at_risk = 0.0
    escalated_expected_recovery_value = 0.0

    for case in cases:
        draw = rng.random()

        baseline = _baseline_result(
            case,
            draw,
        )

        retry = _fixed_strategy_result(
            case,
            "RETRY",
            draw,
        )

        reminder = _fixed_strategy_result(
            case,
            "REMINDER",
            draw,
        )

        revera, decision = _revera_result(
            case,
            draw,
        )

        baseline_rows.append(
            baseline
        )

        retry_rows.append(
            retry
        )

        reminder_rows.append(
            reminder
        )

        revera_rows.append(
            revera
        )

        selected_action = str(
            decision.get(
                "selected_action",
                "STOP",
            )
        )

        policy_decision = str(
            decision.get(
                "policy_decision",
                "STOP",
            )
        )

        if selected_action in ACTIONS or selected_action == "HUMAN_REVIEW":
            schema_valid += 1

        stopping_allowed = bool(
            decision.get(
                "stopping_allowed",
                True,
            )
        )

        if stopping_allowed:
            stopping_compliant += 1
        else:
            if selected_action == "STOP":
                stopping_compliant += 1
            else:
                stopping_violations += 1

        if policy_decision in {
            "APPROVED",
            "STOP",
            "HUMAN_REVIEW",
        }:
            policy_compliant += 1
        else:
            policy_violations += 1

        if decision.get(
            "human_review",
            False,
        ):
            human_review += 1

        if decision.get(
            "automatic_action",
            False,
        ):
            automatic_actions += 1

        if selected_action in action_counts:
            action_counts[selected_action] += 1

        if decision.get(
            "human_review",
            False,
        ):
            escalated_amount_at_risk += case.amount
            escalated_expected_recovery_value += float(
                decision.get(
                    "escalated_expected_recovery_value",
                    0.0,
                )
            )

        details.append(
            {
                "case_id": case.case_id,
                "event_type": case.event_type,
                "failure_reason": case.failure_reason,
                "amount": case.amount,
                "base_recovery_probability": round(
                    case.recovery_probability,
                    4,
                ),
                "true_probability": round(
                    case.true_probability,
                    4,
                ),
                "revera_action": selected_action,
                "policy_decision": policy_decision,
                "automatic_action": bool(
                    decision.get(
                        "automatic_action",
                        False,
                    )
                ),
                "human_review": bool(
                    decision.get(
                        "human_review",
                        False,
                    )
                ),
                "expected_recovery_value": round(
                    float(
                        decision.get(
                            "expected_recovery_value",
                            0.0,
                        )
                    ),
                    2,
                ),
                "incremental_recovery_value": round(
                    float(
                        decision.get(
                            "incremental_recovery_value",
                            0.0,
                        )
                    ),
                    2,
                ),
                "escalated_amount_at_risk": round(
                    float(
                        decision.get(
                            "escalated_amount_at_risk",
                            0.0,
                        )
                    ),
                    2,
                ),
                "escalated_expected_recovery_value": round(
                    float(
                        decision.get(
                            "escalated_expected_recovery_value",
                            0.0,
                        )
                    ),
                    2,
                ),
            }
        )

    baseline = _aggregate(
        baseline_rows
    )

    retry = _aggregate(
        retry_rows
    )

    reminder = _aggregate(
        reminder_rows
    )

    revera = _aggregate(
        revera_rows
    )

    incremental_recovery = round(
        revera["recovered"]
        - baseline["recovered"],
        2,
    )

    incremental_net_recovery = round(
        revera["net_recovered"]
        - baseline["net_recovered"],
        2,
    )

    relative_uplift = round(
        incremental_net_recovery
        / baseline["net_recovered"],
        4,
    ) if baseline[
        "net_recovered"
    ] else 0.0

    return {
        "mode": "synthetic",
        "cases": limit,
        "seed": 20260905,
        "schema_validity": round(
            schema_valid / limit,
            4,
        ),
        "avg_latency_ms": 0.0,
        "revenue_recovery_benchmark": {
            "baseline": baseline,
            "blind_retry": retry,
            "fixed_reminder": reminder,
            "recoveros": revera,
            "incremental_recovery": incremental_recovery,
            "incremental_net_recovery": incremental_net_recovery,
            "relative_uplift": relative_uplift,
            "safety": {
                "stopping_compliance": round(
                    stopping_compliant / limit,
                    4,
                ),
                "policy_compliance": round(
                    policy_compliant / limit,
                    4,
                ),
                "policy_violations": policy_violations,
                "stopping_rule_violations": (
                    stopping_violations
                ),
                "human_review_rate": round(
                    human_review / limit,
                    4,
                ),
                "automatic_action_rate": round(
                    automatic_actions / limit,
                    4,
                ),
                "action_distribution": action_counts,
                "escalated_amount_at_risk": round(
                    escalated_amount_at_risk,
                    2,
                ),
                "escalated_expected_recovery_value": round(
                    escalated_expected_recovery_value,
                    2,
                ),
            },
        },
        "comparators": {
            "NO_INTERVENTION": baseline,
            "BLIND_RETRY": retry,
            "FIXED_REMINDER": reminder,
            "REVERA": revera,
        },
        "rows": details[:100],
        "notes": [
            "Synthetic benchmark only; not production merchant performance.",
            "All strategies use the same generated scenarios and seeded outcome draws.",
            "REVERA evaluates economics before deterministic policy authorization.",
            "Policy-rejected actions are not counted as autonomous recoveries.",
            "Human-review cases are reported separately and are not credited with automatic recovery.",
            "Escalated amount represents revenue at risk routed to human review under policy.",
            "Escalated expected recovery value is an economic estimate, not verified recovered revenue.",
            "No live Gemini calls are required for the batch benchmark.",
        ],
    }