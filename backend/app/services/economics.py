from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from app.services.action_model import ACTION_CONFIG, action_probability, action_costs


@dataclass
class ActionEvaluation:
    action: str
    probability: float
    gross_recovery: float
    baseline_value: float
    incremental_value: float
    incentive_cost: float
    friction_cost: float
    operational_cost: float
    expected_recovery_value: float
    allowed_by_stopping_rules: bool
    stopping_reason: str | None
    rationale: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


ACTIONS = [
    "PAYMENT_LINK",
    "RETRY",
    "ALTERNATIVE_METHOD",
    "REMINDER",
    "WAIT",
    "INCENTIVE",
    "STOP",
]


ACTION_RATIONALES = {
    "PAYMENT_LINK": "Strong bounded recovery path with low customer friction.",
    "RETRY": "Useful when the failure is transient, but value falls with repeated attempts.",
    "ALTERNATIVE_METHOD": "Useful when the current payment method is likely the failure point.",
    "REMINDER": "Low-cost intervention suited to abandonment or uncertain intent.",
    "WAIT": "Defers intervention to allow a transient condition to clear.",
    "INCENTIVE": "Raises conversion probability while consuming merchant margin.",
    "STOP": "Preserves customer experience and recovery budget when intervention is not justified.",
}


def _probability(
    base: float,
    action: str,
    event_type: str,
    attempts: int,
    hours: float,
    failure_reason: str | None = None,
) -> float:
    return action_probability(
        base=base,
        action=action,
        event_type=event_type,
        failure_reason=failure_reason,
        attempts=attempts,
        hours=hours,
    )


def _stopping_rule(
    base: float,
    attempts: int,
    contacts: int,
    amount: float,
) -> tuple[bool, str | None]:
    if contacts >= 2:
        return False, "Customer contact limit reached."

    if attempts >= 2:
        return False, "Payment attempt limit reached."

    if base < 0.10:
        return False, "Recovery probability below minimum threshold."

    if amount <= 0:
        return False, "Invalid recovery amount."

    return True, None


def _evaluate_action(
    action: str,
    amount: float,
    base: float,
    event_type: str,
    attempts: int,
    hours: float,
    failure_reason: str | None,
    action_allowed: bool,
    stopping_reason: str | None,
) -> ActionEvaluation:
    probability = _probability(
        base=base,
        action=action,
        event_type=event_type,
        attempts=attempts,
        hours=hours,
        failure_reason=failure_reason,
    )

    gross_recovery = amount * probability
    baseline_value = amount * base
    incremental_value = max(
        0.0,
        gross_recovery - baseline_value,
    )

    costs = action_costs(action, amount)

    incentive_cost = costs["incentive_cost"]
    friction_cost = costs["friction_cost"]
    operational_cost = costs["operational_cost"]

    expected_value = max(
        0.0,
        gross_recovery
        - incentive_cost
        - friction_cost
        - operational_cost,
    )

    if action == "STOP":
        expected_value = 0.0
        incremental_value = 0.0

    if not action_allowed and action != "STOP":
        expected_value = 0.0

    return ActionEvaluation(
        action=action,
        probability=probability,
        gross_recovery=round(gross_recovery, 2),
        baseline_value=round(baseline_value, 2),
        incremental_value=round(incremental_value, 2),
        incentive_cost=round(incentive_cost, 2),
        friction_cost=round(friction_cost, 2),
        operational_cost=round(operational_cost, 2),
        expected_recovery_value=round(expected_value, 2),
        allowed_by_stopping_rules=action_allowed,
        stopping_reason=stopping_reason,
        rationale=ACTION_RATIONALES[action],
    )


def evaluate_opportunities(
    payload: dict[str, Any],
) -> dict[str, Any]:
    amount = float(payload["amount"])
    base = float(payload["recovery_probability"])

    event_type = payload.get(
        "event_type",
        "payment.failed",
    )

    attempts = int(
        payload.get(
            "attempt_count",
            0,
        )
    )

    hours = float(
        payload.get(
            "hours_since_event",
            1,
        )
    )

    contacts = int(
        payload.get(
            "contacts_24h",
            0,
        )
    )

    failure_reason = payload.get("failure_reason")

    action_allowed, stopping_reason = _stopping_rule(
        base=base,
        attempts=attempts,
        contacts=contacts,
        amount=amount,
    )

    results: list[ActionEvaluation] = []

    for action in ACTIONS:
        evaluation = _evaluate_action(
            action=action,
            amount=amount,
            base=base,
            event_type=event_type,
            attempts=attempts,
            hours=hours,
            failure_reason=failure_reason,
            action_allowed=(
                action_allowed
                or action == "STOP"
            ),
            stopping_reason=(
                stopping_reason
                if not action_allowed
                else None
            ),
        )

        results.append(evaluation)

    if not action_allowed:
        best = next(
            item
            for item in results
            if item.action == "STOP"
        )

        decision_reason = (
            "Stopping rule overrides economic ranking: "
            f"{stopping_reason}"
        )
    else:
        candidates = [
            item
            for item in results
            if (
                item.action != "STOP"
                and item.allowed_by_stopping_rules
                and item.expected_recovery_value > 0
            )
        ]

        if not candidates:
            best = next(
                item
                for item in results
                if item.action == "STOP"
            )

            decision_reason = (
                "No intervention produced positive "
                "expected recovery value."
            )
        else:
            best = max(
                candidates,
                key=lambda item: (
                    item.expected_recovery_value,
                    item.incremental_value,
                    item.probability,
                ),
            )

            decision_reason = (
                "Highest positive expected recovery "
                "value before policy authorization."
            )

    results.sort(
        key=lambda item: (
            item.expected_recovery_value,
            item.incremental_value,
            item.probability,
        ),
        reverse=True,
    )

    return {
        "amount_at_risk": round(amount, 2),
        "base_recovery_probability": round(base, 4),
        "baseline_recovery_value": round(
            amount * base,
            2,
        ),
        "stopping_rules": {
            "allowed": action_allowed,
            "reason": stopping_reason,
            "attempts": attempts,
            "contacts_24h": contacts,
            "minimum_probability": 0.10,
        },
        "recommended_action": best.action,
        "expected_recovery_value": best.expected_recovery_value,
        "recommended_probability": best.probability,
        "incremental_recovery_value": best.incremental_value,
        "decision_reason": decision_reason,
        "opportunities": [
            item.as_dict()
            for item in results
        ],
    }
