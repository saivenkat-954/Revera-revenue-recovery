from __future__ import annotations

import time

import httpx

from app.config import settings

from app.db import (
    add_audit_event,
    create_recovery_action,
)


RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"


class RazorpayExecutionError(Exception):
    pass


def _require_test_mode() -> None:
    if not settings.razorpay_key_id:
        raise RazorpayExecutionError(
            "Razorpay key ID is not configured."
        )

    if not settings.razorpay_key_secret:
        raise RazorpayExecutionError(
            "Razorpay key secret is not configured."
        )

    if not settings.razorpay_key_id.startswith(
        "rzp_test_"
    ):
        raise RazorpayExecutionError(
            "REVERA executor only allows Razorpay Test Mode keys."
        )


def _validate_case(case: dict) -> None:
    if not case.get("case_id"):
        raise RazorpayExecutionError(
            "Recovery case ID is required."
        )

    if not case.get("customer_id"):
        raise RazorpayExecutionError(
            "Customer ID is required."
        )

    try:
        amount = float(
            case.get(
                "amount",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise RazorpayExecutionError(
            "Recovery amount is invalid."
        ) from exc

    if amount <= 0:
        raise RazorpayExecutionError(
            "Recovery amount must be greater than zero."
        )

    currency = str(
        case.get(
            "currency",
            "INR",
        )
        or "INR"
    ).upper()

    if len(currency) != 3:
        raise RazorpayExecutionError(
            "Currency must be a valid three-letter currency code."
        )


async def create_payment_link(
    case: dict,
) -> dict:
    _require_test_mode()
    _validate_case(case)

    case_id = str(
        case["case_id"]
    )

    customer_id = str(
        case["customer_id"]
    )

    amount = float(
        case["amount"]
    )

    currency = str(
        case.get(
            "currency",
            "INR",
        )
        or "INR"
    ).upper()

    timestamp = int(
        time.time() * 1000
    )

    reference_id = (
        f"recoveros_{case_id}_{timestamp}"
    )[:40]

    payload = {
        "amount": int(
            round(
                amount * 100
            )
        ),
        "currency": currency,
        "accept_partial": False,
        "reference_id": reference_id,
        "description": (
            f"REVERA recovery for {case_id}"
        ),
        "reminder_enable": False,
        "notify": {
            "sms": False,
            "email": False,
        },
        "notes": {
            "recoveros_case_id": case_id,
            "recoveros_customer_id": customer_id,
            "recoveros_action": "PAYMENT_LINK",
        },
    }

    customer = {}

    if case.get("customer_name"):
        customer["name"] = str(
            case["customer_name"]
        )

    if case.get("customer_email"):
        customer["email"] = str(
            case["customer_email"]
        )

    if case.get("customer_contact"):
        customer["contact"] = str(
            case["customer_contact"]
        )

    if customer:
        payload["customer"] = customer

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                20.0,
                connect=10.0,
            )
        ) as client:
            response = await client.post(
                f"{RAZORPAY_BASE_URL}/payment_links",
                auth=(
                    settings.razorpay_key_id,
                    settings.razorpay_key_secret,
                ),
                json=payload,
            )

    except httpx.TimeoutException as exc:
        raise RazorpayExecutionError(
            "Razorpay API request timed out."
        ) from exc

    except httpx.HTTPError as exc:
        raise RazorpayExecutionError(
            f"Razorpay network error: {exc}"
        ) from exc

    if response.status_code >= 400:
        try:
            error_body = response.json()
        except Exception:
            error_body = {
                "message": response.text
            }

        raise RazorpayExecutionError(
            f"Razorpay API error {response.status_code}: "
            f"{error_body}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RazorpayExecutionError(
            "Razorpay returned invalid JSON."
        ) from exc

    provider_id = data.get(
        "id"
    )

    provider_url = data.get(
        "short_url"
    )

    if not provider_id:
        raise RazorpayExecutionError(
            "Razorpay response did not contain a Payment Link ID."
        )

    if not provider_url:
        raise RazorpayExecutionError(
            "Razorpay response did not contain a Payment Link URL."
        )

    try:
        action_id = create_recovery_action(
            case_id=case_id,
            customer_id=customer_id,
            action="PAYMENT_LINK",
            amount=amount,
            currency=currency,
            provider="razorpay",
            provider_id=provider_id,
            payment_link=provider_url,
            status="issued",
        )
    except Exception as exc:
        raise RazorpayExecutionError(
            f"Payment Link was created, but recovery action "
            f"could not be saved: {exc}"
        ) from exc

    try:
        add_audit_event(
            case_id=case_id,
            event_type="action.executed",
            actor="razorpay_executor",
            details=(
                f"Created Razorpay Payment Link "
                f"{provider_id} for "
                f"{amount:.2f} {currency}"
            ),
        )
    except Exception as exc:
        raise RazorpayExecutionError(
            f"Payment Link was created and recovery action "
            f"{action_id} was saved, but audit logging failed: {exc}"
        ) from exc

    return {
        "success": True,
        "action": "PAYMENT_LINK",
        "case_id": case_id,
        "customer_id": customer_id,
        "amount": amount,
        "currency": currency,
        "provider": "razorpay",
        "provider_id": provider_id,
        "payment_link": provider_url,
        "reference_id": reference_id,
        "action_id": action_id,
        "status": "issued",
        "live_mode": False,
    }