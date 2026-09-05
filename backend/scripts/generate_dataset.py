from __future__ import annotations

import csv
import math
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 20260901
N_EVENTS = 12000
N_CUSTOMERS = 3000
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "revenue_events.csv"

EVENT_TYPES = [
    "payment.failed",
    "checkout.abandoned",
    "subscription.failed",
    "invoice.overdue",
    "payment.degraded",
]
PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet"]
FAILURE_REASONS = [
    "transient_failure",
    "insufficient_balance",
    "bank_decline",
    "network_error",
    "expired_method",
    "repeated_failure",
    "customer_abandonment",
    "invoice_delay",
    "systemic_degradation",
]
ACTIONS = ["RETRY", "PAYMENT_LINK", "REMINDER", "ALTERNATIVE_METHOD", "WAIT", "HUMAN_REVIEW", "STOP"]


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, x))))


def main() -> None:
    rng = random.Random(SEED)
    customers = {}
    for i in range(N_CUSTOMERS):
        cid = f"CUS-{100000+i}"
        latent = rng.betavariate(5, 2)
        customers[cid] = {
            "customer_id": cid,
            "customer_age_days": rng.randint(20, 1400),
            "lifetime_value": round(rng.uniform(1500, 250000), 2),
            "propensity": latent,
            "preferred_method": rng.choice(PAYMENT_METHODS),
        }

    rows = []
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    customer_events = defaultdict(int)

    for i in range(N_EVENTS):
        c = rng.choice(list(customers.values()))
        cid = c["customer_id"]
        event_type = rng.choices(
            EVENT_TYPES,
            weights=[42, 24, 15, 12, 7],
            k=1,
        )[0]
        amount = round(max(199, rng.lognormvariate(math.log(4200), 0.9)), 2)
        amount = min(amount, 75000)
        method = c["preferred_method"] if rng.random() < 0.62 else rng.choice(PAYMENT_METHODS)
        success = min(customer_events[cid], rng.randint(0, 12))
        failed = rng.randint(0, min(7, success + 4))
        attempts = rng.randint(0, 3 if event_type != "checkout.abandoned" else 1)
        days_since_last = round(rng.uniform(0.2, 120), 2)
        checkout_duration = round(rng.uniform(12, 900), 1)
        prior_recovery_rate = round(rng.uniform(0.0, 0.95), 3) if customer_events[cid] else 0.0
        failure_reason = None
        if event_type == "payment.failed":
            failure_reason = rng.choices(
                FAILURE_REASONS[:6], weights=[24, 18, 14, 14, 10, 20], k=1
            )[0]
        elif event_type == "checkout.abandoned":
            failure_reason = "customer_abandonment"
        elif event_type == "subscription.failed":
            failure_reason = rng.choice(["insufficient_balance", "expired_method", "bank_decline", "transient_failure"])
        elif event_type == "invoice.overdue":
            failure_reason = "invoice_delay"
        else:
            failure_reason = "systemic_degradation"

        customer_events[cid] += 1

        event_time = start + timedelta(minutes=rng.randint(0, 330000))
        amount_score = math.log1p(amount) - math.log1p(5000)
        method_match = 1 if method == c["preferred_method"] else 0
        reason_bonus = {
            "transient_failure": 0.65,
            "network_error": 0.45,
            "systemic_degradation": 0.35,
            "customer_abandonment": 0.15,
            "insufficient_balance": -0.25,
            "bank_decline": -0.45,
            "expired_method": -0.55,
            "repeated_failure": -1.05,
            "invoice_delay": -0.15,
        }[failure_reason]
        event_bonus = {
            "payment.failed": 0.15,
            "checkout.abandoned": 0.05,
            "subscription.failed": 0.2,
            "invoice.overdue": -0.05,
            "payment.degraded": 0.3,
        }[event_type]
        score = (
            -0.75
            + 2.25 * (c["propensity"] - 0.5)
            + 0.42 * min(success, 8)
            - 0.28 * min(failed, 7)
            - 0.55 * attempts
            + 0.35 * prior_recovery_rate
            + 0.16 * amount_score
            + 0.30 * method_match
            + reason_bonus
            + event_bonus
            - 0.006 * max(days_since_last - 30, 0)
            - 0.12 * max(math.log1p(checkout_duration) - 5, 0)
        )
        true_probability = sigmoid(score)
        recovered = 1 if rng.random() < true_probability else 0
        recovered_amount = round(amount if recovered else 0, 2)
        intervention = rng.choices(ACTIONS, weights=[22, 25, 16, 12, 10, 5, 10], k=1)[0]
        if true_probability < 0.15:
            intervention = "STOP"
        elif true_probability > 0.72 and amount <= 10000:
            intervention = rng.choice(["PAYMENT_LINK", "ALTERNATIVE_METHOD", "RETRY"])

        rows.append({
            "event_id": f"EVT-{i+1:06d}",
            "customer_id": cid,
            "event_time": event_time.isoformat(),
            "event_type": event_type,
            "amount": amount,
            "currency": "INR",
            "payment_method": method,
            "failure_reason": failure_reason,
            "attempt_count": attempts,
            "successful_payments": success,
            "failed_payments": failed,
            "customer_age_days": c["customer_age_days"],
            "customer_lifetime_value": c["lifetime_value"],
            "days_since_last_payment": days_since_last,
            "checkout_duration_seconds": checkout_duration,
            "prior_recovery_rate": prior_recovery_rate,
            "intervention": intervention,
            "recovered": recovered,
            "recovered_amount": recovered_amount,
        })

    rows.sort(key=lambda r: r["event_time"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows):,} events for {N_CUSTOMERS:,} customers")
    print(f"Saved to {OUT}")


if __name__ == "__main__":
    main()
