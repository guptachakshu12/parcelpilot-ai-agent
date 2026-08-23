from pathlib import Path
import pandas as pd


# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Location of the Excel assessment data
EXCEL_FILE = PROJECT_ROOT / "data" / "ParcelPilot_Assessment_Data.xlsx"


def load_excel_data():
    """
    Load all sheets from the ParcelPilot assessment Excel workbook.
    """

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Excel file not found at: {EXCEL_FILE}"
        )

    # Read every sheet
    sheets = pd.read_excel(EXCEL_FILE, sheet_name=None)

    print("\nAvailable Excel sheets:")
    for sheet_name, df in sheets.items():
        print(f"- {sheet_name}: {len(df)} rows")

    return sheets


def get_sheet(sheets, possible_names):
    """
    Find a sheet using a list of possible sheet names.
    """

    for name in possible_names:
        if name in sheets:
            return sheets[name]

    return None


def load_parcelpilot_data():
    """
    Load the three main structured datasets:
    accounts, orders and tickets.
    """

    sheets = load_excel_data()

    accounts = get_sheet(
        sheets,
        ["Accounts", "accounts", "Account", "account"]
    )

    orders = get_sheet(
        sheets,
        ["Orders", "orders", "Order", "order"]
    )

    tickets = get_sheet(
        sheets,
        ["Tickets", "tickets", "Ticket", "ticket"]
    )

    print("\nLoaded datasets:")

    if accounts is not None:
        print(f"Accounts: {len(accounts)} rows")
    else:
        print("Accounts sheet not found")

    if orders is not None:
        print(f"Orders: {len(orders)} rows")
    else:
        print("Orders sheet not found")

    if tickets is not None:
        print(f"Tickets: {len(tickets)} rows")
    else:
        print("Tickets sheet not found")

    return {
        "accounts": accounts,
        "orders": orders,
        "tickets": tickets,
    }


if __name__ == "__main__":
    data = load_parcelpilot_data()

    print("\n--- Accounts ---")
    if data["accounts"] is not None:
        print(data["accounts"].head())

    print("\n--- Orders ---")
    if data["orders"] is not None:
        print(data["orders"].head())

    print("\n--- Tickets ---")
    if data["tickets"] is not None:
        print(data["tickets"].head())