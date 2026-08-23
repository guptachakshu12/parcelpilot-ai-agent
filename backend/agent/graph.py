from langchain_google_genai import ChatGoogleGenerativeAI
import sys
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent


# ---------------------------------------------------------
# Project setup
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------
# Import tools
# ---------------------------------------------------------

from backend.tools.data_tool import (
    get_account,
    get_order,
    get_ticket,
    get_ticket_by_order_id,
)

from backend.tools.document_tool import (
    search_parcelpilot_documents,
)

from backend.tools.action_tool import (
    prepare_escalation,
    confirm_escalation,
)


# ---------------------------------------------------------
# Tool list
# ---------------------------------------------------------

# IMPORTANT:
# confirm_escalation is NOT exposed to Gemini.
#
# It is executed by the application only after the user
# explicitly confirms a prepared escalation.

TOOLS = [
    get_account,
    get_order,
    get_ticket,
    get_ticket_by_order_id,
    search_parcelpilot_documents,
    prepare_escalation,
]


# ---------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are ParcelPilot Support Agent.

Your job is to answer customer-support questions using ONLY
the supplied ParcelPilot data and documents.


IMPORTANT SOURCE PRIORITY:

1. Signed customer agreement
2. Current ParcelPilot Support Policy
3. Current Product Operations documentation
4. Historical tickets and internal notes are context only
5. Deprecated policies must NOT be used for current answers

When sources conflict, follow the higher-priority source.


IMPORTANT RULES:

- Do not invent facts.

- Always use the available tools when factual information is needed.

- For an order-related question, ALWAYS call get_order()
  before answering.

- If the order belongs to an account, call get_account()
  before applying customer-specific terms.

- When the question involves a policy, agreement, SOP,
  or product issue, call search_parcelpilot_documents().

- Do not simply recommend checking a document. Actually use
  the document search tool yourself.

- If a customer has a signed agreement, that agreement
  overrides the default policy.

- Historical ticket resolutions may be incorrect and must
  never override current policy or a signed customer agreement.

- The deprecated Support Policy v2 must NOT be used for
  current requests.

- If the available evidence is insufficient or conflicting,
  clearly state the uncertainty instead of guessing.


CRITICAL TIME-BASED REASONING RULE:

For ANY policy that depends on elapsed time, you MUST verify
the time condition separately before declaring eligibility.

For a failed-pickup service credit, follow this reasoning:

1. Identify pickup_window_end from the order data.

2. Identify the required delay from the applicable policy
   or signed customer agreement.

3. Calculate:

   eligibility_time = pickup_window_end + required_delay

4. Find an EXPLICIT reference/current timestamp in the
   available evidence.

5. Compare the explicit reference/current timestamp with
   eligibility_time.

6. The time condition is satisfied ONLY if the explicit
   reference/current timestamp is later than eligibility_time.

7. If no explicit reference/current timestamp exists, the
   time condition is UNKNOWN.

8. If the time condition is UNKNOWN, eligibility MUST NOT
   be declared.


TIME-BASED EVIDENCE RULES:

- Never assume a time-based threshold has been satisfied merely
  because an order is in BOOKED status.

- Never assume a time-based threshold has been satisfied merely
  because pickup_actual_at is null.

- pickup_actual_at = null means only that the pickup has not
  occurred. It does NOT establish how much time has elapsed.

- Never assume a time-based threshold has been satisfied merely
  because a note says "pickup missed".

- Never assume a time-based threshold has been satisfied merely
  because a note says "still not picked up at dataset snapshot".

- Treat "still not picked up at dataset snapshot" only as evidence
  that the pickup had not occurred at the time represented by
  the dataset.

- Do NOT infer when the dataset snapshot occurred unless an
  explicit timestamp is provided.

- The phrase "dataset snapshot" is NOT itself a timestamp.

- Never infer the timestamp of a dataset snapshot.

- Never use the machine's current time as the reference time.

- Never use the actual current date or time unless that timestamp
  is explicitly supplied as evidence available to the agent.

- Never invent, assume, estimate, or infer a missing timestamp.

- Do not treat the order's booked_at timestamp as the current
  reference timestamp.

- Do not treat pickup_window_end as evidence that the required
  delay has already elapsed.

- Do not treat the existence of carrier_fault = true and
  customer_fault = false as sufficient for eligibility when
  a required time condition remains unknown.


FAILED-PICKUP CREDIT REASONING:

When evaluating a failed-pickup credit, evaluate ALL conditions
independently:

1. Was the pickup supposed to occur?
2. Has the pickup actually occurred?
3. Is the carrier at fault?
4. Is the customer at fault?
5. Has the required amount of time elapsed?

Do not allow conditions 1-4 to imply condition 5.

If condition 5 cannot be established from an explicit timestamp,
the final result must be that eligibility cannot be confirmed.


EXAMPLE OF CORRECT REASONING:

If:

pickup_window_end = 06:30
required_delay = 4 hours

then:

eligibility_time = 10:30

If the available data says:

pickup_actual_at = null
carrier_fault = true
customer_fault = false
notes = "Still not picked up at dataset snapshot"

but provides NO explicit snapshot/current timestamp,

then the correct conclusion is:

"The pickup has not occurred and the carrier/customer fault
conditions are satisfied, but the available evidence does not
establish whether the 10:30 threshold has passed. Therefore,
eligibility cannot be confirmed."

The incorrect conclusion is:

"The order is BOOKED and has not been picked up, therefore
more than 4 hours have passed."

Never make that inference.


GENERAL UNCERTAINTY RULE:

If a required policy condition is UNKNOWN because the necessary
evidence is missing, do not replace UNKNOWN with YES or NO.

Clearly explain which condition cannot be verified and why.

Give a concise answer based on the retrieved evidence.
Mention the relevant source when useful.


SEVERITY:

P1 = Critical
P2 = High
P3 = Normal

P1 incidents should be escalated immediately.


ESCALATION RULES:

- For a P1 incident, identify that it requires immediate
  escalation.

- Use prepare_escalation() to prepare the escalation.

- NEVER execute a state-changing escalation yourself.

- Explicit user confirmation is required before an escalation
  can actually be created.

- Do not claim that an escalation was created merely because
  it was prepared.

- If the user has not explicitly confirmed the action,
  report that the escalation is awaiting confirmation.


AVAILABLE TOOLS:

1. get_account
   Use for customer/account information.

2. get_order
   Use for shipment/order information.

3. get_ticket
   Use when the user provides a ticket ID.

4. get_ticket_by_order_id
   Use when the user asks for a support ticket using an order ID.

   For example:
   "Show me the support ticket for ORD-2002."

   When an order ID is provided instead of a ticket ID,
   use get_ticket_by_order_id() to find the associated ticket.

5. search_parcelpilot_documents
   Use for policies, SOPs, customer agreements,
   and product documentation.

6. prepare_escalation
   Use to prepare a support escalation that requires
   explicit user confirmation before creation.


IMPORTANT TICKET WORKFLOW:

If the user asks for a support ticket using an order ID,
such as:

"Show me the support ticket for ORD-2002."
"What is the ticket status for ORD-2002?"
"Find the support issue associated with ORD-2002."

you MUST:

1. Identify the order ID.
2. Call get_ticket_by_order_id() with that order ID.
3. If a ticket is found, report the ticket ID and its current
   status and relevant details.
4. If multiple tickets are found, summarize them clearly.
5. If no ticket is found, state that no ticket could be found
   for that order.
6. Do not ask the user for a ticket ID when an order ID is
   already provided.


IMPORTANT WORKFLOW:

For a question such as:

"Can Northstar cancel ORD-1001 without a fee?"

you MUST:

1. Call get_order with ORD-1001.
2. Identify the account_id.
3. Call get_account with that account_id.
4. Search the supplied documents for the applicable
   cancellation policy.
5. Apply the signed customer agreement before the
   default SOP if they conflict.
6. Give the final answer.


For an escalation request such as:

"Can you escalate TKT-505?"

you MUST:

1. Call get_ticket with TKT-505.
2. Determine the severity using the current policy.
3. If it is P1, explain that it requires immediate escalation.
4. Call prepare_escalation().
5. Do NOT claim the escalation was created.
6. Tell the user that explicit confirmation is required.
"""


# ---------------------------------------------------------
# Create agent
# ---------------------------------------------------------

def create_parcelpilot_agent():

    model = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0,
        max_retries=2,
    )

    agent = create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


# ---------------------------------------------------------
# Helper: clean Gemini content
# ---------------------------------------------------------

def clean_content(content):
    """
    Convert Gemini structured content into plain text.
    """

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        text_parts = []

        for block in content:

            if isinstance(block, dict):

                if block.get("type") == "text":

                    text = block.get("text", "")

                    if text:
                        text_parts.append(text)

        return "\n".join(text_parts)

    return str(content)


# ---------------------------------------------------------
# Helper: parse tool output
# ---------------------------------------------------------

def parse_tool_content(content):
    """
    Convert a ToolMessage content into a Python dictionary
    when possible.
    """

    if isinstance(content, dict):
        return content

    if isinstance(content, str):

        try:
            return json.loads(content)

        except (json.JSONDecodeError, TypeError):
            return None

    return None


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\n==========================================")
    print("      PARCELPILOT AI SUPPORT AGENT")
    print("==========================================\n")

    agent = create_parcelpilot_agent()

    print("Agent is ready.")
    print("Type 'exit' to stop.\n")


    # -----------------------------------------------------
    # Stores a prepared escalation between user turns.
    # -----------------------------------------------------

    pending_escalation = None


    while True:

        user_input = input("You: ").strip()

        if user_input.lower() == "exit":

            print("Goodbye!")
            break

        if not user_input:
            continue


        # -------------------------------------------------
        # Handle explicit confirmation at APPLICATION level
        # -------------------------------------------------

        confirmation_words = {
            "yes",
            "y",
            "confirm",
            "confirmed",
            "approve",
            "approved",
            "do it",
            "proceed",
        }

        rejection_words = {
            "no",
            "n",
            "cancel",
            "cancel it",
            "don't",
            "do not",
            "reject",
            "rejected",
        }


        # -------------------------------------------------
        # User confirmed pending escalation
        # -------------------------------------------------

        if (
            pending_escalation is not None
            and user_input.lower() in confirmation_words
        ):

            try:

                result = confirm_escalation(
                    ticket_id=pending_escalation["ticket_id"],
                    reason=pending_escalation["reason"],
                    priority=pending_escalation["priority"],
                )

                print("\nAgent:")

                if result.get("success"):

                    print(
                        f"Escalation {result['data']['escalation_id']} "
                        f"was created successfully for "
                        f"{result['data']['ticket_id']}."
                    )

                    print(
                        f"Priority: {result['data']['priority']}"
                    )

                    print(
                        f"Reason: {result['data']['reason']}"
                    )

                else:

                    print(
                        "The escalation could not be created."
                    )

                print()

                # Clear pending action after confirmation.
                pending_escalation = None

            except Exception as e:

                print("\nAgent error:")
                print(str(e))
                print()

            continue


        # -------------------------------------------------
        # User rejected pending escalation
        # -------------------------------------------------

        if (
            pending_escalation is not None
            and user_input.lower() in rejection_words
        ):

            print("\nAgent:")

            print(
                f"Escalation for "
                f"{pending_escalation['ticket_id']} "
                "was cancelled. No escalation was created."
            )

            print()

            pending_escalation = None

            continue


        # -------------------------------------------------
        # Normal agent request
        # -------------------------------------------------

        try:

            result = agent.invoke({
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            })


            messages = result.get("messages", [])


            # -------------------------------------------------
            # Print trace
            # -------------------------------------------------

            print("\n========== AGENT TRACE ==========")

            for i, message in enumerate(messages):

                print(f"\n--- Message {i + 1} ---")
                print(f"Type: {message.type}")


                # ---------------------------------------------
                # Tool calls
                # ---------------------------------------------

                if (
                    hasattr(message, "tool_calls")
                    and message.tool_calls
                ):

                    print("Tool calls:")

                    for tool_call in message.tool_calls:
                        print(tool_call)


                # ---------------------------------------------
                # Message content
                # ---------------------------------------------

                if message.content:

                    print("Content:")

                    print(
                        clean_content(message.content)
                    )


            print("\n========== END TRACE ==========")


            # -------------------------------------------------
            # Detect prepared escalation
            # -------------------------------------------------

            for message in messages:

                if message.type != "tool":
                    continue

                tool_data = parse_tool_content(
                    message.content
                )

                if not isinstance(tool_data, dict):
                    continue


                if (
                    tool_data.get("action")
                    == "create_escalation"
                    and tool_data.get("status")
                    == "awaiting_confirmation"
                ):

                    pending_escalation = {
                        "ticket_id": tool_data["ticket_id"],
                        "reason": tool_data["reason"],
                        "priority": tool_data["priority"],
                    }

                    break


            # -------------------------------------------------
            # Print clean final response
            # -------------------------------------------------

            if messages:

                final_message = messages[-1]

                content = clean_content(
                    final_message.content
                )

                print("\nAgent:")
                print(content)
                print()


        except Exception as e:

            print("\nAgent error:")
            print(str(e))
            print()