from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionConfig:
    probability_uplift: float
    friction_rate: float
    operational_cost: float
    incentive_rate: float = 0.0


ACTION_CONFIG: dict[str, ActionConfig] = {
    "PAYMENT_LINK": ActionConfig(0.09, 0.005, 8.0),
    "RETRY": ActionConfig(0.08, 0.012, 5.0),
    "ALTERNATIVE_METHOD": ActionConfig(0.10, 0.008, 6.0),
    "REMINDER": ActionConfig(0.07, 0.004, 2.0),
    "WAIT": ActionConfig(0.15, 0.001, 0.5),
    "INCENTIVE": ActionConfig(0.13, 0.010, 3.0, 0.05),
    "STOP": ActionConfig(0.0, 0.0, 0.0),
}


def clamp_probability(value: float) -> float:
    return round(min(max(float(value), 0.0), 0.98), 4)


def action_probability(
    base: float,
    action: str,
    event_type: str = "payment.failed",
    failure_reason: str | None = None,
    attempts: int = 0,
    hours: float = 1.0,
) -> float:
    base = float(base)
    attempts = int(attempts)
    hours = float(hours)

    if action == "PAYMENT_LINK":
        uplift = (
            0.09
            if event_type in {
                "payment.failed",
                "checkout.abandoned",
                "subscription.failed",
            }
            else 0.04
        )
    elif action == "RETRY":
        uplift = (
            0.08
            if failure_reason in {
                "transient_failure",
                "network_timeout",
            }
            else -0.05
        )
        uplift -= 0.08 * attempts
    elif action == "ALTERNATIVE_METHOD":
        uplift = 0.10 if event_type == "payment.failed" else 0.04
        if failure_reason == "insufficient_funds":
            uplift += 0.04
    elif action == "REMINDER":
        uplift = 0.07 if event_type == "checkout.abandoned" else 0.015
    elif action == "WAIT":
        uplift = min(max(hours, 0.0) / 24.0, 0.20) * 0.15
    elif action == "INCENTIVE":
        uplift = 0.13
    else:
        uplift = 0.0

    if action == "STOP":
        return 0.0

    return clamp_probability(base + uplift)


def action_costs(
    action: str,
    amount: float,
) -> dict[str, float]:
    config = ACTION_CONFIG[action]
    amount = float(amount)
    return {
        "incentive_cost": round(amount * config.incentive_rate, 2),
        "friction_cost": round(amount * config.friction_rate, 2),
        "operational_cost": round(config.operational_cost, 2),
    }
