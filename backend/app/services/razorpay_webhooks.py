from __future__ import annotations

import hashlib
import hmac
import json
from decimal import Decimal

from app.config import settings

from app.db import (
    add_audit_event,
    mark_case_recovered,
    mark_webhook_processed,
    store_webhook_event,
    update_case_status,
    update_recovery_action_status,
)


def verify_signature(
    body: bytes,
    signature: str,
) -> bool:
    secret = settings.razorpay_webhook_secret

    if not secret or not signature:
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected,
        signature,
    )


def _extract_payment_link(
    payload: dict,
) -> dict:
    return (
        payload
        .get("payload", {})
        .get("payment_link", {})
        .get("entity", {})
    )


def _extract_case_id(
    payment_link: dict,
) -> str | None:
    notes = payment_link.get("notes")

    if isinstance(notes, dict):
        for key in (
            "recoveros_case_id",
            "revera_case_id",
            "case_id",
        ):
            value = notes.get(key)

            if value:
                return str(value)

    reference_id = payment_link.get("reference_id")

    if isinstance(reference_id, str):
        for prefix in (
            "recoveros_",
            "revera_",
        ):
            if reference_id.startswith(prefix):
                value = reference_id[len(prefix):]

                if value:
                    return value

    return None


def _extract_recovered_amount(
    payment_link: dict,
) -> float:
    amount_paid = payment_link.get("amount_paid")

    if amount_paid is None:
        amount_paid = payment_link.get("amount")

    if amount_paid is None:
        return 0.0

    try:
        return float(
            Decimal(str(amount_paid))
            / Decimal("100")
        )
    except Exception:
        return 0.0


def _safe_currency(
    payment_link: dict,
) -> str:
    currency = payment_link.get(
        "currency",
        "INR",
    )

    if not isinstance(currency, str):
        return "INR"

    return currency.upper()


def _sync_paid_recovery(
    payment_link: dict,
    event_type: str,
    case_id: str | None,
) -> dict:
    payment_link_id = payment_link.get("id")

    recovered_amount = _extract_recovered_amount(
        payment_link
    )

    currency = _safe_currency(
        payment_link
    )

    action = None

    if payment_link_id:
        action = update_recovery_action_status(
            provider_id=payment_link_id,
            status="paid",
            recovered_amount=recovered_amount,
        )

    case = None

    if case_id:
        case = mark_case_recovered(
            case_id=case_id,
            recovered_amount=recovered_amount,
        )

        if case:
            add_audit_event(
                case_id=case_id,
                event_type="recovery.verified",
                actor="razorpay_webhook",
                details={
                    "event": event_type,
                    "payment_link_id": payment_link_id,
                    "verified_recovery": round(
                        recovered_amount,
                        2,
                    ),
                    "currency": currency,
                    "action_id": (
                        action.get("id")
                        if action
                        else None
                    ),
                },
            )

    return {
        "action": action,
        "case": case,
        "recovered_amount": recovered_amount,
    }


def process_webhook(
    body: bytes,
    event_id: str,
) -> dict:
    if not event_id:
        raise ValueError(
            "Webhook event ID is required."
        )

    try:
        raw_payload = body.decode(
            "utf-8"
        )

        payload = json.loads(
            raw_payload
        )

    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise ValueError(
            "Invalid webhook payload."
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "Webhook payload must be a JSON object."
        )

    event_type = payload.get(
        "event",
        "unknown",
    )

    payment_link = _extract_payment_link(
        payload
    )

    payment_link_id = payment_link.get(
        "id"
    )

    case_id = _extract_case_id(
        payment_link
    )

    inserted = store_webhook_event(
        event_id=event_id,
        event_type=event_type,
        payload=raw_payload,
        case_id=case_id,
    )

    if not inserted:
        if event_type == "payment_link.paid":
            synced = _sync_paid_recovery(
                payment_link=payment_link,
                event_type=event_type,
                case_id=case_id,
            )

            return {
                "status": "duplicate_reconciled",
                "event_id": event_id,
                "event_type": event_type,
                "payment_link_id": payment_link_id,
                "case_id": case_id,
                "recovered_amount": synced[
                    "recovered_amount"
                ],
            }

        return {
            "status": "duplicate",
            "event_id": event_id,
            "event_type": event_type,
            "payment_link_id": payment_link_id,
            "case_id": case_id,
        }

    if event_type == "payment_link.paid":
        _sync_paid_recovery(
            payment_link=payment_link,
            event_type=event_type,
            case_id=case_id,
        )

    elif event_type == "payment_link.partially_paid":
        partial_amount = _extract_recovered_amount(
            payment_link
        )

        if payment_link_id:
            update_recovery_action_status(
                provider_id=payment_link_id,
                status="partially_paid",
                recovered_amount=partial_amount,
            )

        if case_id:
            mark_case_recovered(
                case_id=case_id,
                recovered_amount=partial_amount,
            )

            add_audit_event(
                case_id=case_id,
                event_type="recovery.partial",
                actor="razorpay_webhook",
                details={
                    "event": event_type,
                    "payment_link_id": payment_link_id,
                    "amount_received": round(
                        partial_amount,
                        2,
                    ),
                    "currency": _safe_currency(
                        payment_link
                    ),
                },
            )

    elif event_type in {
        "payment_link.cancelled",
        "payment_link.expired",
    }:
        status = event_type.replace(
            "payment_link.",
            "",
        )

        if payment_link_id:
            update_recovery_action_status(
                provider_id=payment_link_id,
                status=status,
            )

        if case_id:
            update_case_status(
                case_id=case_id,
                status=status,
            )

            add_audit_event(
                case_id=case_id,
                event_type="recovery.closed",
                actor="razorpay_webhook",
                details={
                    "event": event_type,
                    "payment_link_id": payment_link_id,
                    "status": status,
                },
            )

    else:
        if case_id:
            add_audit_event(
                case_id=case_id,
                event_type="webhook.received",
                actor="razorpay_webhook",
                details={
                    "event": event_type,
                    "payment_link_id": payment_link_id,
                },
            )

    processed = mark_webhook_processed(
        event_id
    )

    return {
        "status": (
            "processed"
            if processed
            else "received"
        ),
        "event_id": event_id,
        "event_type": event_type,
        "payment_link_id": payment_link_id,
        "case_id": case_id,
    }