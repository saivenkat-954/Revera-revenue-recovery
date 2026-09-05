from app.models import ActionRequest, Policy


def evaluate_action(
    req: ActionRequest,
    policy: Policy,
) -> dict:
    if req.discount_percent > policy.max_discount_percent:
        return {
            "decision": "BLOCK",
            "reason": (
                "Requested discount exceeds "
                "merchant policy"
            ),
        }

    if req.amount > policy.human_review_limit:
        return {
            "decision": "HUMAN_REVIEW",
            "reason": (
                "Transaction exceeds the maximum "
                "automated recovery limit"
            ),
        }

    if req.amount > policy.auto_action_limit:
        return {
            "decision": "HUMAN_REVIEW",
            "reason": (
                "Transaction requires human approval"
            ),
        }

    if req.contacts_24h >= policy.max_contacts_24h:
        return {
            "decision": "STOP",
            "reason": (
                "Customer contact limit reached"
            ),
        }

    if req.attempt_count >= policy.max_attempts:
        return {
            "decision": "STOP",
            "reason": (
                "Maximum recovery attempts reached"
            ),
        }

    return {
        "decision": "APPROVED",
        "reason": (
            "Action satisfies recovery policy"
        ),
    }

