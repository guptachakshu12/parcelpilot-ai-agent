from pathlib import Path
import json
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ESCALATION_FILE = PROJECT_ROOT / "backend" / "data" / "escalations.json"


def _load_escalations():
    """Load previously created escalations."""

    if not ESCALATION_FILE.exists():
        return []

    with open(ESCALATION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_escalations(escalations):
    """Save escalations to the local JSON file."""

    ESCALATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(ESCALATION_FILE, "w", encoding="utf-8") as file:
        json.dump(
            escalations,
            file,
            indent=2,
            ensure_ascii=False
        )


def prepare_escalation(
    ticket_id: str,
    reason: str,
    priority: str = "P2"
):
    """
    Prepare an escalation without executing it.

    This function does NOT change system state.
    The user must explicitly confirm before the escalation is created.
    """

    return {
        "action": "create_escalation",
        "status": "awaiting_confirmation",
        "ticket_id": ticket_id,
        "reason": reason,
        "priority": priority,
        "message": (
            f"Escalation prepared for {ticket_id}. "
            "Explicit user confirmation is required before creation."
        )
    }


def confirm_escalation(
    ticket_id: str,
    reason: str,
    priority: str = "P2"
):
    """
    Actually create an escalation.

    This function should only be called after explicit
    confirmation from the user.
    """

    escalations = _load_escalations()

    escalation_id = f"ESC-{len(escalations) + 1:03d}"

    escalation = {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "priority": priority,
        "status": "created",
        "created_at": datetime.now().isoformat()
    }

    escalations.append(escalation)

    _save_escalations(escalations)

    return {
        "success": True,
        "message": f"Escalation {escalation_id} created successfully.",
        "data": escalation
    }


if __name__ == "__main__":

    print("\n========== TESTING ACTION TOOL ==========\n")

    # Step 1: Prepare an escalation
    prepared = prepare_escalation(
        ticket_id="TKT-505",
        reason="Possible production API key exposure",
        priority="P1"
    )

    print("Prepared escalation:")
    print(prepared)

    # Step 2: Simulate explicit confirmation
    user_confirmation = input(
        "\nType 'yes' to confirm the escalation: "
    )

    if user_confirmation.strip().lower() == "yes":

        result = confirm_escalation(
            ticket_id="TKT-505",
            reason="Possible production API key exposure",
            priority="P1"
        )

        print("\nAction executed:")
        print(result)

    else:

        print("\nAction cancelled.")
        print("No escalation was created.")