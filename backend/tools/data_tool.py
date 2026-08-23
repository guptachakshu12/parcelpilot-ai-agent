from pathlib import Path
import sys
import pandas as pd

from langchain_core.tools import tool


# ---------------------------------------------------------
# Project setup
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.data.loader import load_parcelpilot_data


# ---------------------------------------------------------
# Load data once
# ---------------------------------------------------------

DATA = load_parcelpilot_data()

ACCOUNTS = DATA["accounts"]
ORDERS = DATA["orders"]
TICKETS = DATA["tickets"]


# ---------------------------------------------------------
# Convert Pandas values to JSON-safe values
# ---------------------------------------------------------

def clean_record(record):
    """
    Convert Pandas/NumPy values into JSON-safe Python values.

    In particular:
    NaN -> None
    """

    cleaned = {}

    for key, value in record.items():

        if pd.isna(value):
            cleaned[key] = None

        else:
            # Convert NumPy scalar values to normal Python values
            if hasattr(value, "item"):
                try:
                    value = value.item()
                except (ValueError, TypeError):
                    pass

            cleaned[key] = value

    return cleaned


# ---------------------------------------------------------
# Account tool
# ---------------------------------------------------------

@tool
def get_account(account_id: str):
    """
    Look up a ParcelPilot customer account using its account ID.

    Returns account name, plan, status, CSM, contract information,
    premium support status, and account notes.
    """

    if ACCOUNTS is None:
        return {
            "success": False,
            "error": "Accounts data is unavailable."
        }

    result = ACCOUNTS[
        ACCOUNTS["account_id"].astype(str).str.upper()
        == account_id.upper()
    ]

    if result.empty:
        return {
            "success": False,
            "error": f"Account {account_id} was not found."
        }

    return {
        "success": True,
        "data": clean_record(result.iloc[0].to_dict())
    }


# ---------------------------------------------------------
# Order tool
# ---------------------------------------------------------

@tool
def get_order(order_id: str):
    """
    Look up a ParcelPilot shipment order using its order ID.

    Returns account, carrier, shipment status, booking time,
    pickup information, shipment fee, fault information,
    cancellation request information, and notes.
    """

    if ORDERS is None:
        return {
            "success": False,
            "error": "Orders data is unavailable."
        }

    result = ORDERS[
        ORDERS["order_id"].astype(str).str.upper()
        == order_id.upper()
    ]

    if result.empty:
        return {
            "success": False,
            "error": f"Order {order_id} was not found."
        }

    return {
        "success": True,
        "data": clean_record(result.iloc[0].to_dict())
    }


# ---------------------------------------------------------
# Ticket tool
# ---------------------------------------------------------

@tool
def get_ticket(ticket_id: str):
    """
    Look up a ParcelPilot support ticket using its ticket ID.

    Returns account, status, subject, description, channel,
    assignment, timestamps, and historical resolution if available.
    """

    if TICKETS is None:
        return {
            "success": False,
            "error": "Tickets data is unavailable."
        }

    result = TICKETS[
        TICKETS["ticket_id"].astype(str).str.upper()
        == ticket_id.upper()
    ]

    if result.empty:
        return {
            "success": False,
            "error": f"Ticket {ticket_id} was not found."
        }

    return {
        "success": True,
        "data": clean_record(result.iloc[0].to_dict())
    }


# ---------------------------------------------------------
# Ticket lookup by order ID
# ---------------------------------------------------------

@tool
def get_ticket_by_order_id(order_id: str):
    """
    Find ParcelPilot support tickets associated with an order ID.

    Returns matching ticket details including ticket ID, status,
    subject, description, channel, assignment, timestamps,
    and historical resolution if available.
    """

    if TICKETS is None:
        return {
            "success": False,
            "error": "Tickets data is unavailable."
        }

    result = TICKETS[
        TICKETS["order_id"].astype(str).str.upper()
        == order_id.upper()
    ]

    if result.empty:
        return {
            "success": False,
            "error": f"No support ticket was found for order {order_id}."
        }

    return {
        "success": True,
        "data": [
            clean_record(row.to_dict())
            for _, row in result.iterrows()
        ]
    }


# ---------------------------------------------------------
# Test tools
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\n========== TESTING LLM TOOLS ==========\n")

    print("Available tools:")

    print("-", get_account.name)
    print("-", get_order.name)
    print("-", get_ticket.name)
    print("-", get_ticket_by_order_id.name)

    print("\nTesting get_account:")
    print(
        get_account.invoke({
            "account_id": "ACCT-001"
        })
    )

    print("\nTesting get_order:")
    print(
        get_order.invoke({
            "order_id": "ORD-1001"
        })
    )

    print("\nTesting get_ticket:")
    print(
        get_ticket.invoke({
            "ticket_id": "TKT-505"
        })
    )

    print("\nTesting get_ticket_by_order_id:")
    print(
        get_ticket_by_order_id.invoke({
            "order_id": "ORD-2002"
        })
    )